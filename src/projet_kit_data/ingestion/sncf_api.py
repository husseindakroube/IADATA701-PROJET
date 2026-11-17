"""Fetch and store raw monthly SNCF TGV regularity records."""

from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, TypeGuard

import requests

SNCF_EXPORT_URL = (
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/"
    "regularite-mensuelle-tgv-aqst/exports/json"
)
DEFAULT_RAW_DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.json")
_RETRYABLE_STATUS_CODES = {429, *range(500, 600)}


class SNCFAPIError(RuntimeError):
    """Represent an HTTP or response-structure failure from the SNCF API.

    :param message: A description of the API failure.
    :type message: str
    """

    def __init__(self, message: str) -> None:
        """Initialize the API error with a descriptive message.

        :param message: A description of the API failure.
        :type message: str
        :returns: No value.
        :rtype: None
        """
        super().__init__(message)


def _is_record_array(value: Any) -> TypeGuard[list[dict[str, Any]]]:
    """Return whether *value* is a JSON array containing only objects."""
    return isinstance(value, list) and all(isinstance(record, dict) for record in value)


def _retry_after_seconds(value: str | None) -> float | None:
    """Parse an HTTP Retry-After value into a non-negative delay."""
    if value is None:
        return None

    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())


def _wait_before_retry(
    retry_number: int,
    backoff_factor: float,
    retry_after: str | None = None,
) -> None:
    """Wait with exponential backoff, honoring a valid Retry-After value."""
    backoff = backoff_factor * (2**retry_number)
    retry_after_delay = _retry_after_seconds(retry_after)
    time.sleep(max(backoff, retry_after_delay or 0.0))


def fetch_raw_data(
    *,
    connect_timeout: float = 5.0,
    read_timeout: float = 60.0,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> list[dict[str, Any]]:
    """Fetch all SNCF TGV regularity records without transforming them.

    The function calls the SNCF Explore API v2.1 JSON export endpoint with
    ``limit=-1``. Transient connection failures, timeouts, HTTP 429 responses,
    and HTTP 5xx responses are retried up to ``max_retries`` times.

    :param connect_timeout: Maximum seconds to wait when establishing a
        connection.
    :type connect_timeout: float
    :param read_timeout: Maximum seconds to wait for response data.
    :type read_timeout: float
    :param max_retries: Number of retries after the initial request.
    :type max_retries: int
    :param backoff_factor: Base delay in seconds for exponential backoff.
    :type backoff_factor: float
    :returns: The records as a list of dictionaries, preserving field names
        and values from the JSON response.
    :rtype: list[dict[str, Any]]
    :raises SNCFAPIError: If the request fails after retries, the server
        returns a non-retryable unsuccessful status, or the JSON structure is
        not an array of objects.
    :raises requests.exceptions.JSONDecodeError: If the response body is not
        valid JSON. This exception is intentionally allowed to propagate.
    :raises ValueError: If a timeout, retry count, or backoff factor is
        negative or otherwise invalid.
    """
    if connect_timeout <= 0 or read_timeout <= 0:
        raise ValueError("Timeout values must be greater than zero.")
    if max_retries < 0:
        raise ValueError("max_retries must be zero or greater.")
    if backoff_factor < 0:
        raise ValueError("backoff_factor must be zero or greater.")

    timeout = (connect_timeout, read_timeout)
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                SNCF_EXPORT_URL,
                params={"limit": -1},
                timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt < max_retries:
                _wait_before_retry(attempt, backoff_factor)
                continue
            raise SNCFAPIError(
                f"SNCF API request failed after {max_retries} retries: {exc}"
            ) from exc
        except requests.RequestException as exc:
            raise SNCFAPIError(f"SNCF API request failed: {exc}") from exc

        if response.status_code in _RETRYABLE_STATUS_CODES:
            if attempt < max_retries:
                _wait_before_retry(
                    attempt,
                    backoff_factor,
                    response.headers.get("Retry-After"),
                )
                continue
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                raise SNCFAPIError(
                    f"SNCF API returned HTTP {response.status_code} after "
                    f"{max_retries} retries."
                ) from exc
            raise SNCFAPIError(
                f"SNCF API returned retryable HTTP {response.status_code} "
                f"after {max_retries} retries."
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise SNCFAPIError(
                f"SNCF API returned HTTP {response.status_code}: {exc}"
            ) from exc

        records = response.json()
        if not _is_record_array(records):
            raise SNCFAPIError(
                "Unexpected SNCF API response: expected a JSON array "
                "containing only objects."
            )
        return records

    raise SNCFAPIError("SNCF API request failed without a response.")


def save_raw_data(
    records: Sequence[dict[str, Any]],
    path: str | os.PathLike[str] = DEFAULT_RAW_DATA_PATH,
) -> Path:
    """Atomically save raw records as a UTF-8 JSON array.

    Parent directories are created as needed. A temporary file in the target
    directory is replaced into place with :func:`os.replace` so readers do not
    observe a partially written output.

    :param records: Raw record dictionaries to serialize without ETL or
        cleaning.
    :type records: Sequence[dict[str, Any]]
    :param path: Destination file path. Defaults to the project raw-data path.
    :type path: str | os.PathLike[str]
    :returns: The destination path.
    :rtype: pathlib.Path
    :raises OSError: If creating directories, writing the temporary file, or
        replacing the destination fails. Any temporary file is removed when
        possible before the error is re-raised.
    :raises TypeError: If a record contains a value that cannot be encoded as
        JSON.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as output_file:
            json.dump(records, output_file, ensure_ascii=False, indent=2)
            output_file.write("\n")
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    return destination


def load_raw_data(
    path: str | os.PathLike[str] = DEFAULT_RAW_DATA_PATH,
) -> list[dict[str, Any]]:
    """Load a previously saved raw SNCF JSON array.

    :param path: JSON file path. Defaults to the project raw-data path.
    :type path: str | os.PathLike[str]
    :returns: The decoded record dictionaries with original field names and
        values.
    :rtype: list[dict[str, Any]]
    :raises OSError: If the file cannot be opened or read. This includes
        :class:`FileNotFoundError` when the path does not exist.
    :raises json.JSONDecodeError: If the file does not contain valid JSON.
    :raises ValueError: If the decoded JSON is not an array containing only
        objects.
    """
    with Path(path).open("r", encoding="utf-8") as input_file:
        records = json.load(input_file)

    if not _is_record_array(records):
        raise ValueError(
            "Unexpected raw data structure: expected a JSON array "
            "containing only objects."
        )
    return records
