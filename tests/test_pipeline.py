"""Tests du point d’entrée partagé d’orchestration ETL."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import polars as pl
import pytest

from projet_kit_data.etl import (
    audit,
    cleaning,
    pipeline,
    preprocessing,
    run_and_save_etl,
    run_etl_pipeline,
)
from projet_kit_data.ingestion import download_data, sncf_api


def test_pipeline_calls_modules_in_order_and_returns_cleaned_frame(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    raw_path = tmp_path / "raw.json"
    records = [{"raw": "record"}]
    typed_frame = pl.DataFrame({"stage": ["typed"]})
    clean_frame = pl.DataFrame({"stage": ["cleaned"]})
    calls: list[str] = []

    def load(*, path: Path) -> list[dict[str, str]]:
        calls.append("load")
        assert path == raw_path
        return records

    def preprocess(received: list[dict[str, str]]) -> pl.DataFrame:
        calls.append("preprocess")
        assert received is records
        return typed_frame

    def clean(received: pl.DataFrame) -> pl.DataFrame:
        calls.append("clean")
        assert received is typed_frame
        return clean_frame

    monkeypatch.setattr(sncf_api, "load_raw_data", load)
    monkeypatch.setattr(preprocessing, "preprocess_data", preprocess)
    monkeypatch.setattr(cleaning, "clean_data", clean)
    audit_call = Mock()
    fetch_call = Mock()
    download_call = Mock()
    monkeypatch.setattr(audit, "audit_raw_data", audit_call)
    monkeypatch.setattr(sncf_api, "fetch_raw_data", fetch_call)
    monkeypatch.setattr(download_data, "main", download_call)

    result = pipeline.run_etl_pipeline(raw_path)

    assert calls == ["load", "preprocess", "clean"]
    assert result is clean_frame
    audit_call.assert_not_called()
    fetch_call.assert_not_called()
    download_call.assert_not_called()


def test_pipeline_uses_ingestion_default_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load = Mock(return_value=[])
    preprocess = Mock(return_value=pl.DataFrame())
    clean = Mock(return_value=pl.DataFrame())
    monkeypatch.setattr(sncf_api, "load_raw_data", load)
    monkeypatch.setattr(preprocessing, "preprocess_data", preprocess)
    monkeypatch.setattr(cleaning, "clean_data", clean)

    pipeline.run_etl_pipeline()

    load.assert_called_once_with(path=sncf_api.DEFAULT_RAW_DATA_PATH)


@pytest.mark.parametrize("failing_stage", ["load", "preprocess", "clean"])
def test_pipeline_propagates_module_exceptions(
    monkeypatch: pytest.MonkeyPatch,
    failing_stage: str,
) -> None:
    failure = RuntimeError(f"{failing_stage} failed")
    load = Mock(return_value=[])
    preprocess = Mock(return_value=pl.DataFrame())
    clean = Mock(return_value=pl.DataFrame())

    if failing_stage == "load":
        load.side_effect = failure
    elif failing_stage == "preprocess":
        preprocess.side_effect = failure
    else:
        clean.side_effect = failure

    monkeypatch.setattr(sncf_api, "load_raw_data", load)
    monkeypatch.setattr(preprocessing, "preprocess_data", preprocess)
    monkeypatch.setattr(cleaning, "clean_data", clean)

    with pytest.raises(RuntimeError, match=f"{failing_stage} failed") as caught:
        pipeline.run_etl_pipeline()

    assert caught.value is failure
    if failing_stage == "load":
        preprocess.assert_not_called()
        clean.assert_not_called()
    elif failing_stage == "preprocess":
        clean.assert_not_called()


def test_pipeline_is_exported_from_etl_package() -> None:
    assert run_etl_pipeline is pipeline.run_etl_pipeline


def test_run_and_save_etl_runs_pipeline_once_and_saves_parquet(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    processed_frame = pl.DataFrame({"value": [1, None, 3]})
    raw_path = tmp_path / "raw.json"
    output_path = tmp_path / "nested" / "result.parquet"
    run_pipeline = Mock(return_value=processed_frame)
    monkeypatch.setattr(pipeline, "run_etl_pipeline", run_pipeline)

    result = pipeline.run_and_save_etl(raw_path, output_path)

    run_pipeline.assert_called_once_with(raw_path)
    assert result is processed_frame
    assert output_path.is_file()
    assert pl.read_parquet(output_path).equals(processed_frame)


def test_run_and_save_etl_uses_default_output_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processed_frame = pl.DataFrame({"value": [1]})
    write_parquet = Mock()
    mkdir = Mock()
    monkeypatch.setattr(
        pipeline, "run_etl_pipeline", Mock(return_value=processed_frame)
    )
    monkeypatch.setattr(pl.DataFrame, "write_parquet", write_parquet)
    monkeypatch.setattr(Path, "mkdir", mkdir)

    result = pipeline.run_and_save_etl()

    assert result is processed_frame
    mkdir.assert_called_once_with(parents=True, exist_ok=True)
    write_parquet.assert_called_once_with(pipeline.DEFAULT_PROCESSED_DATA_PATH)


def test_run_and_save_etl_creates_missing_parent_directories(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    processed_frame = pl.DataFrame({"value": [1]})
    output_path = tmp_path / "not-created" / "child" / "data.parquet"
    monkeypatch.setattr(
        pipeline, "run_etl_pipeline", Mock(return_value=processed_frame)
    )

    pipeline.run_and_save_etl(output_path=output_path)

    assert output_path.parent.is_dir()
    assert output_path.is_file()


def test_run_and_save_etl_propagates_pipeline_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    failure = RuntimeError("pipeline failed")
    run_pipeline = Mock(side_effect=failure)
    write_parquet = Mock()
    monkeypatch.setattr(pipeline, "run_etl_pipeline", run_pipeline)
    monkeypatch.setattr(pl.DataFrame, "write_parquet", write_parquet)

    with pytest.raises(RuntimeError, match="pipeline failed") as caught:
        pipeline.run_and_save_etl(output_path=tmp_path / "data.parquet")

    assert caught.value is failure
    write_parquet.assert_not_called()


def test_run_and_save_etl_propagates_parquet_write_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    failure = OSError("write failed")
    processed_frame = pl.DataFrame({"value": [1]})
    monkeypatch.setattr(
        pipeline, "run_etl_pipeline", Mock(return_value=processed_frame)
    )
    monkeypatch.setattr(
        pl.DataFrame,
        "write_parquet",
        Mock(side_effect=failure),
    )

    with pytest.raises(OSError, match="write failed") as caught:
        pipeline.run_and_save_etl(output_path=tmp_path / "data.parquet")

    assert caught.value is failure


def test_run_and_save_etl_is_exported_from_etl_package() -> None:
    assert run_and_save_etl is pipeline.run_and_save_etl
