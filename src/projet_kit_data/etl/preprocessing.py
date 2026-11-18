'Préparation typée des données brutes SNCF selon le schéma commun.'

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
    'Construit une erreur de conversion concise indiquant la position dans la source.'
    value_description = repr(value)
    if len(value_description) > 80:
        value_description = f"{value_description[:77]}..."
    return ValueError(
        f"Valeur invalide pour le champ {field!r} à l’indice de ligne source {row_index}: "
        f"{value_description} ({reason})."
    )


def _as_decimal(value: Any, field: str, row_index: int) -> Decimal:
    'Convertit une valeur numérique compatible en Decimal fini.'
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise _conversion_error(field, row_index, value, 'un nombre est attendu')

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise _conversion_error(field, row_index, value, 'un nombre est attendu') from None

    if not parsed.is_finite():
        raise _conversion_error(field, row_index, value, 'un nombre fini est attendu')
    return parsed


def _convert_value(field: str, value: Any, row_index: int) -> Any:
    'Convertit une valeur source selon son type logique canonique.'
    if value is None:
        return None

    if field in STRING_COLUMNS:
        if not isinstance(value, str):
            raise _conversion_error(
                field, row_index, value, 'une chaîne ou une valeur nulle est attendue'
            )
        if field == "date" and DATE_PATTERN.fullmatch(value) is None:
            raise _conversion_error(
                field,
                row_index,
                value,
                'un mois valide au format YYYY-MM est attendu',
            )
        return value

    if field in INTEGER_COLUMNS:
        parsed = _as_decimal(value, field, row_index)
        if parsed != parsed.to_integral_value():
            raise _conversion_error(
                field, row_index, value, 'une valeur entière est attendue'
            )
        converted = int(parsed)
        if not _INT64_MIN <= converted <= _INT64_MAX:
            raise _conversion_error(field, row_index, value, 'hors de la plage Int64')
        return converted

    parsed = _as_decimal(value, field, row_index)
    try:
        converted_float = float(parsed)
    except (OverflowError, ValueError):
        raise _conversion_error(
            field, row_index, value, 'hors de la plage Float64'
        ) from None
    if converted_float in (float("inf"), float("-inf")):
        raise _conversion_error(field, row_index, value, 'hors de la plage Float64')
    return converted_float


def preprocess_data(records: list[dict[str, Any]]) -> pl.DataFrame:
    """Convertit les observations brutes SNCF selon le schéma canonique typé à 26 colonnes.
    
    Les conversions sont explicites et suivent l’ordre stable de :data:`POLARS_SCHEMA`.
    L’ordre des lignes, les valeurs nulles et conformes sont préservés sans modifier
    les entrées. Les champs absents ou inattendus sont refusés, sans insertion ni
    suppression silencieuse. Une liste vide produit une table vide au schéma complet.
    Les consommateurs Pandas peuvent adapter la sortie Polars sans modifier le contrat
    commun indépendant des bibliothèques.
    
    Cette fonction prépare uniquement le schéma et les types. Elle n’appelle pas
    :func:`projet_kit_data.etl.cleaning.clean_data`, ne corrige pas les anomalies et
    n’ajoute aucune variable spécifique à une analyse.
    
    :param records: Observations JSON brutes, notamment celles de :func:`projet_kit_data.ingestion.sncf_api.load_raw_data`.
    :type records: list[dict[str, Any]]
    :returns: Table Polars avec les 26 champs canoniques dans un ordre stable.
    :rtype: polars.DataFrame
    :raises TypeError: Si ``records`` n’est pas une liste ou une ligne n’est pas un dictionnaire.
    :raises ValueError: Si un champ manque, est inattendu ou ne peut pas être converti ; l’erreur indique le champ et l’indice source à partir de zéro."""
    if not isinstance(records, list):
        raise TypeError('records doit être une liste de dictionnaires.')

    expected_fields = set(POLARS_SCHEMA)
    converted_records: list[dict[str, Any]] = []

    for row_index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(
                f"Indice de ligne source {row_index} must be a dictionary; "
                f"received {type(record).__name__}."
            )

        unexpected_fields = sorted(set(record) - expected_fields)
        if unexpected_fields:
            field = unexpected_fields[0]
            raise ValueError(
                f"Champ inattendu {field!r} à l’indice de ligne source {row_index}."
            )

        missing_fields = sorted(expected_fields - set(record))
        if missing_fields:
            field = missing_fields[0]
            raise ValueError(
                f"Champ obligatoire absent {field!r} à l’indice de ligne source {row_index}; "
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
