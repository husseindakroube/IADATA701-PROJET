"""Tests for the SNCF raw-data ingestion helpers."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from projet_kit_data.ingestion import sncf_api


def make_response(
    payload: object,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    """Create a real Requests response object without network access."""
    response = requests.Response()
    response.status_code = status_code
    response.headers.update(headers or {})
    response.url = sncf_api.SNCF_EXPORT_URL
    response._content = json.dumps(payload).encode("utf-8")
    return response


def test_fetch_raw_data_returns_records_and_uses_export_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = [{"date": "2026-09", "gare_depart": "Lyon Part-Dieu"}]
    get = Mock(return_value=make_response(records))
    monkeypatch.setattr(sncf_api.requests, "get", get)

    result = sncf_api.fetch_raw_data()

    assert result == records
    get.assert_called_once_with(
        sncf_api.SNCF_EXPORT_URL,
        params={"limit": -1},
        timeout=(5.0, 60.0),
    )


@pytest.mark.parametrize(
    ("status_code", "headers", "expected_delay"),
    [
        (429, {"Retry-After": "7"}, 7.0),
        (503, {}, 1.0),
    ],
)
def test_fetch_raw_data_retries_transient_statuses(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    headers: dict[str, str],
    expected_delay: float,
) -> None:
    get = Mock(
        side_effect=[
            make_response([], status_code=status_code, headers=headers),
            make_response([]),
        ]
    )
    sleep = Mock()
    monkeypatch.setattr(sncf_api.requests, "get", get)
    monkeypatch.setattr(sncf_api.time, "sleep", sleep)

    assert sncf_api.fetch_raw_data() == []
    assert get.call_count == 2
    sleep.assert_called_once_with(expected_delay)


@pytest.mark.parametrize(
    "request_error",
    [requests.ConnectionError("offline"), requests.Timeout("slow response")],
)
def test_fetch_raw_data_retries_connection_errors_and_timeouts(
    monkeypatch: pytest.MonkeyPatch,
    request_error: requests.RequestException,
) -> None:
    get = Mock(side_effect=[request_error, make_response([])])
    sleep = Mock()
    monkeypatch.setattr(sncf_api.requests, "get", get)
    monkeypatch.setattr(sncf_api.time, "sleep", sleep)

    assert sncf_api.fetch_raw_data() == []
    assert get.call_count == 2
    sleep.assert_called_once_with(1.0)


def test_fetch_raw_data_raises_after_retry_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get = Mock(return_value=make_response([], status_code=500))
    sleep = Mock()
    monkeypatch.setattr(sncf_api.requests, "get", get)
    monkeypatch.setattr(sncf_api.time, "sleep", sleep)

    with pytest.raises(sncf_api.SNCFAPIError, match="after 3 retries"):
        sncf_api.fetch_raw_data()

    assert get.call_count == 4
    assert [call.args[0] for call in sleep.call_args_list] == [1.0, 2.0, 4.0]


def test_fetch_raw_data_does_not_retry_non_transient_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get = Mock(return_value=make_response({}, status_code=404))
    sleep = Mock()
    monkeypatch.setattr(sncf_api.requests, "get", get)
    monkeypatch.setattr(sncf_api.time, "sleep", sleep)

    with pytest.raises(sncf_api.SNCFAPIError, match="HTTP 404"):
        sncf_api.fetch_raw_data()

    get.assert_called_once()
    sleep.assert_not_called()


@pytest.mark.parametrize("payload", [{"results": []}, [1], [None]])
def test_fetch_raw_data_rejects_unexpected_response_structure(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
) -> None:
    monkeypatch.setattr(
        sncf_api.requests,
        "get",
        Mock(return_value=make_response(payload)),
    )

    with pytest.raises(sncf_api.SNCFAPIError, match="expected a JSON array"):
        sncf_api.fetch_raw_data()


def test_fetch_raw_data_preserves_json_decode_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response([])
    response._content = b"not-json"
    monkeypatch.setattr(sncf_api.requests, "get", Mock(return_value=response))

    with pytest.raises(requests.exceptions.JSONDecodeError):
        sncf_api.fetch_raw_data()


def test_save_and_load_raw_data_round_trip(tmp_path: Path) -> None:
    records = [
        {
            "date": "2026-09",
            "gare_depart": "Lyon Part-Dieu",
            "commentaire": "retard dû à la météo",
            "nb_annulation": 0,
            "retard_moyen": 2.75,
            "optional": None,
        }
    ]
    output_path = tmp_path / "nested" / "raw.json"

    saved_path = sncf_api.save_raw_data(records, output_path)

    assert saved_path == output_path
    assert "retard dû à la météo" in output_path.read_text(encoding="utf-8")
    assert sncf_api.load_raw_data(output_path) == records


def test_save_raw_data_cleans_temporary_file_if_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "raw.json"
    output_path.write_text("previous", encoding="utf-8")
    replace = Mock(side_effect=OSError("replace failed"))
    monkeypatch.setattr(sncf_api.os, "replace", replace)

    with pytest.raises(OSError, match="replace failed"):
        sncf_api.save_raw_data([], output_path)

    assert output_path.read_text(encoding="utf-8") == "previous"
    assert list(tmp_path.iterdir()) == [output_path]


def test_save_raw_data_preserves_serialization_errors(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        sncf_api.save_raw_data([{"value": object()}], tmp_path / "raw.json")

    assert list(tmp_path.iterdir()) == []


def test_load_raw_data_preserves_file_and_json_errors(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        sncf_api.load_raw_data(missing_path)

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        sncf_api.load_raw_data(invalid_path)


@pytest.mark.parametrize("payload", [{"record": 1}, ["not-an-object"]])
def test_load_raw_data_rejects_unexpected_structure(
    tmp_path: Path,
    payload: object,
) -> None:
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="expected a JSON array"):
        sncf_api.load_raw_data(path)
