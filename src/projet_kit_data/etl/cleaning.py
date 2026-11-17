"""Non-destructive row-level data quality flags for SNCF records."""

from __future__ import annotations

import polars as pl

COUNT_COLUMNS = (
    "nb_train_prevu",
    "nb_annulation",
    "nb_train_depart_retard",
    "nb_train_retard_arrivee",
    "nb_train_retard_sup_15",
    "nb_train_retard_sup_30",
    "nb_train_retard_sup_60",
)

FLAG_COLUMNS = (
    "flag_negative_count",
    "flag_sup30_lt_sup60",
    "flag_sup15_lt_sup30",
    "flag_cancellations_gt_planned",
)


def clean_data(df: pl.DataFrame) -> pl.DataFrame:
    """Return a non-destructive analysis copy with row-level quality flags.

    The function preserves all input columns, values, row order, and row count.
    It adds four Boolean diagnostic columns; it does not correct, remove, or
    otherwise transform source data. Polars is used here to match the current
    audit implementation, but the shared data contract does not require
    Pandas consumers to migrate to Polars.

    All count columns used by the flags must be present. Integer columns and
    columns with only null values are accepted; other data types are rejected
    so a failed comparison cannot be silently skipped. Existing input columns
    with a diagnostic flag name are rejected to avoid overwriting source data.

    :param df: Input SNCF data as a Polars DataFrame.
    :type df: polars.DataFrame
    :returns: A new DataFrame containing the original data and diagnostic
        flags. Flags identify records for review but do not determine corrected
        values.
    :rtype: polars.DataFrame
    :raises TypeError: If ``df`` is not a Polars DataFrame.
    :raises ValueError: If a required count column is missing, has a
        non-integer type other than ``pl.Null``, or conflicts with a
        diagnostic flag name.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("df must be a Polars DataFrame.")

    missing_columns = sorted(set(COUNT_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"Missing required count columns for cleaning flags: {missing_columns}"
        )

    conflicting_flags = sorted(set(FLAG_COLUMNS) & set(df.columns))
    if conflicting_flags:
        raise ValueError(
            "Input already contains reserved diagnostic flag columns: "
            f"{conflicting_flags}"
        )

    invalid_types = {
        column: str(df.schema[column])
        for column in COUNT_COLUMNS
        if df.schema[column] != pl.Null and not df.schema[column].is_integer()
    }
    if invalid_types:
        raise ValueError(
            "Required count columns must have integer or all-null types: "
            f"{invalid_types}"
        )

    negative_count_checks = [
        (pl.col(column) < 0).fill_null(False) for column in COUNT_COLUMNS
    ]

    return df.with_columns(
        pl.any_horizontal(negative_count_checks)
        .fill_null(False)
        .alias("flag_negative_count"),
        (pl.col("nb_train_retard_sup_30") < pl.col("nb_train_retard_sup_60"))
        .fill_null(False)
        .alias("flag_sup30_lt_sup60"),
        (pl.col("nb_train_retard_sup_15") < pl.col("nb_train_retard_sup_30"))
        .fill_null(False)
        .alias("flag_sup15_lt_sup30"),
        (pl.col("nb_annulation") > pl.col("nb_train_prevu"))
        .fill_null(False)
        .alias("flag_cancellations_gt_planned"),
    )
