"""Orchestrate the local SNCF ETL preparation flow."""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl

from projet_kit_data.etl import cleaning, preprocessing
from projet_kit_data.ingestion import sncf_api

DEFAULT_PROCESSED_DATA_PATH = Path("data/processed/sncf.parquet")


def run_etl_pipeline(
    raw_data_path: str | os.PathLike[str] = sncf_api.DEFAULT_RAW_DATA_PATH,
) -> pl.DataFrame:
    """Load, type, and annotate the local SNCF raw dataset.

    The function delegates to the existing ingestion, preprocessing, and
    cleaning modules in that order. It does not download data, run the audit,
    modify the raw file, or correct and remove anomalous records.

    :param raw_data_path: Path to the existing raw JSON file. Defaults to the
        raw-data path configured by the ingestion module.
    :type raw_data_path: str | os.PathLike[str]
    :returns: The typed Polars DataFrame with the existing diagnostic flags.
    :rtype: polars.DataFrame
    :raises OSError: If the raw file cannot be read.
    :raises json.JSONDecodeError: If the raw file contains invalid JSON.
    :raises TypeError: If the decoded records or intermediate values have an
        unsupported type.
    :raises ValueError: If the raw JSON structure, canonical schema, or field
        values are invalid.
    """
    records = sncf_api.load_raw_data(path=Path(raw_data_path))
    typed_data = preprocessing.preprocess_data(records)
    return cleaning.clean_data(typed_data)


def run_and_save_etl(
    raw_data_path: str | os.PathLike[str] = sncf_api.DEFAULT_RAW_DATA_PATH,
    output_path: str | os.PathLike[str] = DEFAULT_PROCESSED_DATA_PATH,
) -> pl.DataFrame:
    """Run the local ETL pipeline and save its output as Parquet.

    The existing pipeline loads the raw JSON, prepares the canonical typed
    DataFrame, and adds diagnostic flags. This function creates the output
    directory if needed, writes the DataFrame without additional transformations,
    and returns the same DataFrame.

    :param raw_data_path: Path to the existing raw JSON input. Defaults to the
        ingestion module's configured raw-data path.
    :type raw_data_path: str | os.PathLike[str]
    :param output_path: Parquet destination. Defaults to
        ``data/processed/sncf.parquet``.
    :type output_path: str | os.PathLike[str]
    :returns: The processed Polars DataFrame that was written.
    :rtype: polars.DataFrame
    :raises OSError: If the raw data cannot be read or the output directory or
        Parquet file cannot be created.
    :raises json.JSONDecodeError: If the raw JSON contains invalid JSON.
    :raises TypeError: If records or intermediate values have an unsupported
        type.
    :raises ValueError: If raw records do not match the canonical schema or
        contain values that cannot be converted.
    """
    processed_data = run_etl_pipeline(raw_data_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    processed_data.write_parquet(destination)
    return processed_data
