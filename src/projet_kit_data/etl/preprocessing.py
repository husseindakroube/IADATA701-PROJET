"""Typed, shared-schema preparation for raw SNCF records."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

import polars as pl

STRING_COLUMNS = (
    "date",
    "service",
    "gare_depart",
    "gare_arrivee",
    "commentaire_annulation",
    "commentaire_retards_depart",
    "commentaires_retard_arrivee",
)

INTEGER_COLUMNS = (
    "duree_moyenne",
    "nb_train_prevu",
    "nb_annulation",
    "nb_train_depart_retard",
    "nb_train_retard_arrivee",
    "nb_train_retard_sup_15",
    "nb_train_retard_sup_30",
    "nb_train_retard_sup_60",
)

FLOAT_COLUMNS = (
    "retard_moyen_depart",
    "retard_moyen_tous_trains_depart",
    "retard_moyen_arrivee",
    "retard_moyen_tous_trains_arrivee",
    "retard_moyen_trains_retard_sup15",
    "prct_cause_externe",
    "prct_cause_infra",
    "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant",
    "prct_cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs",
)

POLARS_SCHEMA: dict[str, pl.DataType] = {
    "date": pl.String,
    "service": pl.String,
    "gare_depart": pl.String,
    "gare_arrivee": pl.String,
    "duree_moyenne": pl.Int64,
    "nb_train_prevu": pl.Int64,
    "nb_annulation": pl.Int64,
    "commentaire_annulation": pl.String,
    "nb_train_depart_retard": pl.Int64,
    "retard_moyen_depart": pl.Float64,
    "retard_moyen_tous_trains_depart": pl.Float64,
    "commentaire_retards_depart": pl.String,
    "nb_train_retard_arrivee": pl.Int64,
    "retard_moyen_arrivee": pl.Float64,
    "retard_moyen_tous_trains_arrivee": pl.Float64,
    "commentaires_retard_arrivee": pl.String,
    "nb_train_retard_sup_15": pl.Int64,
    "retard_moyen_trains_retard_sup15": pl.Float64,
    "nb_train_retard_sup_30": pl.Int64,
    "nb_train_retard_sup_60": pl.Int64,
    "prct_cause_externe": pl.Float64,
    "prct_cause_infra": pl.Float64,
    "prct_cause_gestion_trafic": pl.Float64,
    "prct_cause_materiel_roulant": pl.Float64,
    "prct_cause_gestion_gare": pl.Float64,
    "prct_cause_prise_en_charge_voyageurs": pl.Float64,
}

DATE_PATTERN = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])")
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1


def _conversion_error(
    field: str, row_index: int, value: Any, reason: str
) -> ValueError:
    """Build a concise conversion error with source location context."""
    value_description = repr(value)
    if len(value_description) > 80:
        value_description = f"{value_description[:77]}..."
    return ValueError(
        f"Invalid value for field {field!r} at source row index {row_index}: "
        f"{value_description} ({reason})."
    )


def _as_decimal(value: Any, field: str, row_index: int) -> Decimal:
    """Parse a supported numeric value as a finite Decimal."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise _conversion_error(field, row_index, value, "expected a number")

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise _conversion_error(field, row_index, value, "expected a number") from None

    if not parsed.is_finite():
        raise _conversion_error(field, row_index, value, "expected a finite number")
    return parsed


def _convert_value(field: str, value: Any, row_index: int) -> Any:
    """Convert one source value according to its canonical logical type."""
    if value is None:
        return None

    if field in STRING_COLUMNS:
        if not isinstance(value, str):
            raise _conversion_error(
                field, row_index, value, "expected a string or null"
            )
        if field == "date" and DATE_PATTERN.fullmatch(value) is None:
            raise _conversion_error(
                field,
                row_index,
                value,
                "expected a valid YYYY-MM month",
            )
        return value

    if field in INTEGER_COLUMNS:
        parsed = _as_decimal(value, field, row_index)
        if parsed != parsed.to_integral_value():
            raise _conversion_error(
                field, row_index, value, "expected an integer value"
            )
        converted = int(parsed)
        if not _INT64_MIN <= converted <= _INT64_MAX:
            raise _conversion_error(field, row_index, value, "outside the Int64 range")
        return converted

    parsed = _as_decimal(value, field, row_index)
    try:
        converted_float = float(parsed)
    except (OverflowError, ValueError):
        raise _conversion_error(
            field, row_index, value, "outside the Float64 range"
        ) from None
    if converted_float in (float("inf"), float("-inf")):
        raise _conversion_error(field, row_index, value, "outside the Float64 range")
    return converted_float


def preprocess_data(records: list[dict[str, Any]]) -> pl.DataFrame:
    """Convert raw SNCF records into the typed canonical 26-column schema.

    Source fields are converted explicitly and in the stable order declared by
    :data:`POLARS_SCHEMA`. The function preserves row order, nulls, and all
    conforming values, and does not mutate the input records. Missing or
    unexpected fields are rejected instead of silently inserting or dropping
    data. An empty record list returns a zero-row DataFrame with the complete
    canonical schema. This module uses Polars internally; Pandas consumers may
    adapt the typed output without changing the shared, library-neutral
    contract.

    The function performs schema and type preparation only. It does not call
    :func:`projet_kit_data.etl.cleaning.clean_data`, correct anomalies, or add
    analysis-specific features.

    :param records: Raw JSON records, such as those returned by
        :func:`projet_kit_data.ingestion.sncf_api.load_raw_data`.
    :type records: list[dict[str, Any]]
    :returns: A Polars DataFrame with all 26 canonical fields in stable order.
    :rtype: polars.DataFrame
    :raises TypeError: If ``records`` is not a list or any row is not a
        dictionary.
    :raises ValueError: If a row has missing or unexpected fields, or a value
        cannot be converted to the canonical type. Conversion errors identify
        the field and zero-based source row index.
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list of dictionaries.")

    expected_fields = set(POLARS_SCHEMA)
    converted_records: list[dict[str, Any]] = []

    for row_index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(
                f"Source row index {row_index} must be a dictionary; "
                f"received {type(record).__name__}."
            )

        unexpected_fields = sorted(set(record) - expected_fields)
        if unexpected_fields:
            field = unexpected_fields[0]
            raise ValueError(
                f"Unexpected field {field!r} at source row index {row_index}."
            )

        missing_fields = sorted(expected_fields - set(record))
        if missing_fields:
            field = missing_fields[0]
            raise ValueError(
                f"Missing required field {field!r} at source row index {row_index}; "
                "use null for an explicitly missing value."
            )

        converted_records.append(
            {
                field: _convert_value(field, record[field], row_index)
                for field in POLARS_SCHEMA
            }
        )

    if not converted_records:
        return pl.DataFrame(schema=POLARS_SCHEMA)

    return pl.DataFrame(converted_records, schema=POLARS_SCHEMA, strict=True)
