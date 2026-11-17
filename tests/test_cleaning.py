"""Tests for non-destructive row-level cleaning flags."""

from __future__ import annotations

import polars as pl
import pytest

from projet_kit_data.etl.cleaning import COUNT_COLUMNS, FLAG_COLUMNS, clean_data


def make_frame(
    rows: list[dict[str, int | None]] | None = None,
) -> pl.DataFrame:
    """Build a small input frame with the required count columns."""
    if rows is None:
        rows = [
            {
                "nb_train_prevu": 10,
                "nb_annulation": 1,
                "nb_train_depart_retard": 2,
                "nb_train_retard_arrivee": 3,
                "nb_train_retard_sup_15": 3,
                "nb_train_retard_sup_30": 2,
                "nb_train_retard_sup_60": 1,
            }
        ]
    return pl.DataFrame(rows)


def test_normal_record_has_no_flags() -> None:
    result = clean_data(make_frame())

    assert result.select(FLAG_COLUMNS).row(0) == (False, False, False, False)


@pytest.mark.parametrize(
    ("column", "values"),
    [
        ("nb_train_prevu", [-2]),
        ("nb_annulation", [-2]),
        ("nb_train_depart_retard", [-2]),
        ("nb_train_retard_arrivee", [-2]),
        ("nb_train_retard_sup_15", [-2]),
        ("nb_train_retard_sup_30", [-2]),
        ("nb_train_retard_sup_60", [-2]),
    ],
)
def test_negative_count_sets_negative_flag(
    column: str,
    values: list[int],
) -> None:
    frame = make_frame().with_columns(pl.Series(column, values))

    result = clean_data(frame)

    assert result["flag_negative_count"].to_list() == [True]


def test_several_negative_counts_set_one_flag() -> None:
    frame = make_frame().with_columns(
        pl.Series("nb_train_prevu", [-1]),
        pl.Series("nb_train_retard_sup_30", [-2]),
    )

    result = clean_data(frame)

    assert result["flag_negative_count"].to_list() == [True]
    assert result["nb_train_prevu"].item() == -1
    assert result["nb_train_retard_sup_30"].item() == -2


def test_threshold_ordering_flags_are_independent() -> None:
    frame = make_frame(
        [
            {
                "nb_train_prevu": 20,
                "nb_annulation": 0,
                "nb_train_depart_retard": 0,
                "nb_train_retard_arrivee": 0,
                "nb_train_retard_sup_15": 2,
                "nb_train_retard_sup_30": 4,
                "nb_train_retard_sup_60": 6,
            },
            {
                "nb_train_prevu": 20,
                "nb_annulation": 0,
                "nb_train_depart_retard": 0,
                "nb_train_retard_arrivee": 0,
                "nb_train_retard_sup_15": 5,
                "nb_train_retard_sup_30": 3,
                "nb_train_retard_sup_60": 1,
            },
        ]
    )

    result = clean_data(frame)

    assert result["flag_sup30_lt_sup60"].to_list() == [True, False]
    assert result["flag_sup15_lt_sup30"].to_list() == [True, False]


def test_cancellations_exceeding_planned_sets_flag() -> None:
    frame = make_frame().with_columns(
        pl.Series("nb_train_prevu", [0]),
        pl.Series("nb_annulation", [8]),
    )

    result = clean_data(frame)

    assert result["flag_cancellations_gt_planned"].to_list() == [True]
    assert result["nb_train_prevu"].item() == 0
    assert result["nb_annulation"].item() == 8


def test_null_comparison_values_do_not_set_flags() -> None:
    frame = make_frame().with_columns(
        pl.Series("nb_train_prevu", [None], dtype=pl.Int64),
        pl.Series("nb_train_retard_sup_15", [None], dtype=pl.Int64),
        pl.Series("nb_train_retard_sup_30", [None], dtype=pl.Int64),
        pl.Series("nb_train_retard_sup_60", [None], dtype=pl.Int64),
        pl.Series("nb_annulation", [4]),
    )

    result = clean_data(frame)

    assert result.select(FLAG_COLUMNS).row(0) == (False, False, False, False)
    assert result["nb_train_prevu"].null_count() == 1


def test_multiple_anomalies_are_flagged_without_correcting_values() -> None:
    frame = make_frame().with_columns(
        pl.Series("nb_train_prevu", [0]),
        pl.Series("nb_annulation", [2]),
        pl.Series("nb_train_retard_sup_15", [1]),
        pl.Series("nb_train_retard_sup_30", [-1]),
        pl.Series("nb_train_retard_sup_60", [3]),
    )

    result = clean_data(frame)

    assert result.select(FLAG_COLUMNS).row(0) == (True, True, False, True)
    assert result.select(COUNT_COLUMNS).row(0) == (0, 2, 2, 3, 1, -1, 3)


def test_missing_required_column_raises_instead_of_skipping_flag() -> None:
    frame = make_frame().drop("nb_train_retard_sup_60")

    with pytest.raises(ValueError, match="nb_train_retard_sup_60"):
        clean_data(frame)


def test_source_columns_values_order_and_input_are_preserved() -> None:
    frame = make_frame(
        [
            {
                "date": "2025-02",
                "gare_depart": "LYON PART DIEU",
                "nb_train_prevu": 10,
                "nb_annulation": 1,
                "nb_train_depart_retard": 2,
                "nb_train_retard_arrivee": 3,
                "nb_train_retard_sup_15": 3,
                "nb_train_retard_sup_30": 2,
                "nb_train_retard_sup_60": 1,
            },
            {
                "date": "2025-01",
                "gare_depart": "PARIS LYON",
                "nb_train_prevu": 8,
                "nb_annulation": 0,
                "nb_train_depart_retard": 1,
                "nb_train_retard_arrivee": 2,
                "nb_train_retard_sup_15": 2,
                "nb_train_retard_sup_30": 1,
                "nb_train_retard_sup_60": 0,
            },
        ]
    )
    before = frame.clone()

    result = clean_data(frame)

    assert result.height == frame.height == 2
    assert result.columns == [*frame.columns, *FLAG_COLUMNS]
    assert result.select(frame.columns).equals(before)
    assert frame.equals(before)
    assert result["date"].to_list() == ["2025-02", "2025-01"]


def test_flags_have_boolean_types() -> None:
    result = clean_data(make_frame())

    assert all(result.schema[column] == pl.Boolean for column in FLAG_COLUMNS)


def test_reserved_flag_column_is_not_overwritten() -> None:
    frame = make_frame().with_columns(pl.lit("source value").alias(FLAG_COLUMNS[0]))

    with pytest.raises(ValueError, match="reserved diagnostic flag"):
        clean_data(frame)


def test_non_numeric_required_count_column_raises() -> None:
    frame = make_frame().with_columns(pl.Series("nb_train_prevu", ["unknown"]))

    with pytest.raises(ValueError, match="integer or all-null"):
        clean_data(frame)


def test_float_count_column_raises() -> None:
    frame = make_frame().with_columns(
        pl.Series("nb_train_prevu", [10.0], dtype=pl.Float64)
    )

    with pytest.raises(ValueError, match="integer or all-null"):
        clean_data(frame)


def test_all_null_count_column_with_null_dtype_is_accepted() -> None:
    frame = make_frame().with_columns(
        pl.Series("nb_train_prevu", [None], dtype=pl.Null)
    )

    result = clean_data(frame)

    assert result.schema["nb_train_prevu"] == pl.Null
    assert result["nb_train_prevu"].null_count() == 1
    assert result.select(FLAG_COLUMNS).row(0) == (False, False, False, False)
