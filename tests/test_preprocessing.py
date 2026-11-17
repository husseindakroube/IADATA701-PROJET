"""Tests for typed preparation of raw SNCF records."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import polars as pl
import pytest

from projet_kit_data.etl.preprocessing import (
    FLOAT_COLUMNS,
    INTEGER_COLUMNS,
    POLARS_SCHEMA,
    STRING_COLUMNS,
    preprocess_data,
)

EXPECTED_COLUMNS = [
    "date",
    "service",
    "gare_depart",
    "gare_arrivee",
    "duree_moyenne",
    "nb_train_prevu",
    "nb_annulation",
    "commentaire_annulation",
    "nb_train_depart_retard",
    "retard_moyen_depart",
    "retard_moyen_tous_trains_depart",
    "commentaire_retards_depart",
    "nb_train_retard_arrivee",
    "retard_moyen_arrivee",
    "retard_moyen_tous_trains_arrivee",
    "commentaires_retard_arrivee",
    "nb_train_retard_sup_15",
    "retard_moyen_trains_retard_sup15",
    "nb_train_retard_sup_30",
    "nb_train_retard_sup_60",
    "prct_cause_externe",
    "prct_cause_infra",
    "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant",
    "prct_cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs",
]


def make_record(**overrides: Any) -> dict[str, Any]:
    """Build a complete, valid record using the canonical schema."""
    record: dict[str, Any] = {
        "date": "2025-01",
        "service": "National",
        "gare_depart": "LYON PART DIEU",
        "gare_arrivee": "PARIS LYON",
        "duree_moyenne": 120,
        "nb_train_prevu": 10,
        "nb_annulation": 1,
        "commentaire_annulation": None,
        "nb_train_depart_retard": 2,
        "retard_moyen_depart": 3.5,
        "retard_moyen_tous_trains_depart": 2.5,
        "commentaire_retards_depart": None,
        "nb_train_retard_arrivee": 3,
        "retard_moyen_arrivee": 4.5,
        "retard_moyen_tous_trains_arrivee": 3.0,
        "commentaires_retard_arrivee": None,
        "nb_train_retard_sup_15": 3,
        "retard_moyen_trains_retard_sup15": 18.0,
        "nb_train_retard_sup_30": 2,
        "nb_train_retard_sup_60": 1,
        "prct_cause_externe": 10.0,
        "prct_cause_infra": 20.0,
        "prct_cause_gestion_trafic": 30.0,
        "prct_cause_materiel_roulant": 15.0,
        "prct_cause_gestion_gare": 15.0,
        "prct_cause_prise_en_charge_voyageurs": 10.0,
    }
    record.update(overrides)
    return record


def test_valid_record_has_all_canonical_columns_in_order() -> None:
    result = preprocess_data([make_record()])

    assert result.shape == (1, 26)
    assert result.columns == EXPECTED_COLUMNS
    assert result.row(0, named=True)["date"] == "2025-01"


def test_every_field_group_has_expected_polars_dtype() -> None:
    result = preprocess_data([make_record()])

    assert all(result.schema[field] == pl.String for field in STRING_COLUMNS)
    assert all(result.schema[field] == pl.Int64 for field in INTEGER_COLUMNS)
    assert all(result.schema[field] == pl.Float64 for field in FLOAT_COLUMNS)


def test_all_null_comment_columns_remain_string_dtype() -> None:
    result = preprocess_data([make_record()])

    for field in (
        "commentaire_annulation",
        "commentaire_retards_depart",
        "commentaires_retard_arrivee",
    ):
        assert result.schema[field] == pl.String
        assert result[field].null_count() == 1


def test_null_values_remain_null_and_zero_remains_zero() -> None:
    result = preprocess_data(
        [make_record(commentaire_annulation=None, nb_annulation=0)]
    )

    assert result["commentaire_annulation"].item() is None
    assert result["nb_annulation"].item() == 0


def test_multiple_records_preserve_input_order() -> None:
    records = [
        make_record(date="2024-12", gare_depart="FIRST"),
        make_record(date="2025-01", gare_depart="SECOND"),
        make_record(date="2025-02", gare_depart="THIRD"),
    ]

    result = preprocess_data(records)

    assert result["gare_depart"].to_list() == ["FIRST", "SECOND", "THIRD"]
    assert result["date"].to_list() == ["2024-12", "2025-01", "2025-02"]


def test_input_records_and_dictionaries_are_not_modified() -> None:
    records = [make_record(), make_record(date="2024-09")]
    original = deepcopy(records)

    preprocess_data(records)

    assert records == original


def test_missing_field_raises_with_field_and_source_row_index() -> None:
    first = make_record()
    second = make_record()
    del second["nb_train_prevu"]

    with pytest.raises(ValueError, match="nb_train_prevu.*source row index 1"):
        preprocess_data([first, second])


def test_unexpected_field_is_rejected_with_source_row_index() -> None:
    record = make_record(unexpected_metric=1)

    with pytest.raises(ValueError, match="unexpected_metric.*source row index 0"):
        preprocess_data([record])


@pytest.mark.parametrize("date", ["2025/01", "25-01", "2025-1", "2025-01-01"])
def test_invalid_date_format_raises_with_field_and_row(
    date: str,
) -> None:
    with pytest.raises(ValueError, match="date.*source row index 0"):
        preprocess_data([make_record(date=date)])


@pytest.mark.parametrize("date", ["2025-00", "2025-13"])
def test_invalid_calendar_month_raises(date: str) -> None:
    with pytest.raises(ValueError, match="date.*valid YYYY-MM month"):
        preprocess_data([make_record(date=date)])


def test_fractional_integer_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="nb_train_prevu.*integer value"):
        preprocess_data([make_record(nb_train_prevu=1.5)])


def test_non_numeric_integer_string_is_rejected() -> None:
    with pytest.raises(ValueError, match="nb_train_prevu.*expected a number"):
        preprocess_data([make_record(nb_train_prevu="many")])


def test_valid_integer_in_decimal_field_is_converted_to_float64() -> None:
    result = preprocess_data([make_record(retard_moyen_depart=4)])

    assert result.schema["retard_moyen_depart"] == pl.Float64
    assert result["retard_moyen_depart"].item() == 4.0


def test_non_numeric_decimal_value_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="prct_cause_externe.*source row index 0.*expected a number",
    ):
        preprocess_data([make_record(prct_cause_externe="unknown")])


def test_numeric_value_in_string_field_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="gare_depart.*source row index 0.*expected a string or null",
    ):
        preprocess_data([make_record(gare_depart=123)])


def test_empty_input_returns_typed_empty_canonical_frame() -> None:
    result = preprocess_data([])

    assert result.shape == (0, 26)
    assert result.columns == EXPECTED_COLUMNS
    assert result.schema == POLARS_SCHEMA


def test_conversion_error_identifies_field_and_source_row_index() -> None:
    records = [make_record(), make_record(prct_cause_infra="bad-number")]

    with pytest.raises(
        ValueError,
        match="prct_cause_infra.*source row index 1",
    ):
        preprocess_data(records)


def test_integer_numeric_string_is_explicitly_parsed_without_truncation() -> None:
    result = preprocess_data([make_record(nb_train_prevu="12")])

    assert result["nb_train_prevu"].item() == 12
    assert result.schema["nb_train_prevu"] == pl.Int64
