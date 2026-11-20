"""Préparation typée des données SNCF brutes selon le schéma partagé."""

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
    """Créer une erreur de conversion concise avec le contexte de la source."""
    value_description = repr(value)
    if len(value_description) > 80:
        value_description = f"{value_description[:77]}..."
    return ValueError(
        f"Valeur invalide pour le champ {field!r} à la ligne source {row_index} : "
        f"{value_description} ({reason})."
    )


def _as_decimal(value: Any, field: str, row_index: int) -> Decimal:
    """Analyser une valeur numérique prise en charge en Decimal fini."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise _conversion_error(field, row_index, value, "un nombre était attendu")

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise _conversion_error(
            field, row_index, value, "un nombre était attendu"
        ) from None

    if not parsed.is_finite():
        raise _conversion_error(field, row_index, value, "un nombre fini était attendu")
    return parsed


def _convert_value(field: str, value: Any, row_index: int) -> Any:
    """Convertir une valeur source selon son type logique canonique."""
    if value is None:
        return None

    if field in STRING_COLUMNS:
        if not isinstance(value, str):
            raise _conversion_error(
                field,
                row_index,
                value,
                "une chaîne ou une valeur manquante (None) était attendue",
            )
        if field == "date" and DATE_PATTERN.fullmatch(value) is None:
            raise _conversion_error(
                field,
                row_index,
                value,
                "un mois valide au format YYYY-MM était attendu",
            )
        return value

    if field in INTEGER_COLUMNS:
        parsed = _as_decimal(value, field, row_index)
        if parsed != parsed.to_integral_value():
            raise _conversion_error(
                field, row_index, value, "une valeur entière était attendue"
            )
        converted = int(parsed)
        if not _INT64_MIN <= converted <= _INT64_MAX:
            raise _conversion_error(field, row_index, value, "hors de la plage Int64")
        return converted

    parsed = _as_decimal(value, field, row_index)
    try:
        converted_float = float(parsed)
    except (OverflowError, ValueError):
        raise _conversion_error(
            field, row_index, value, "hors de la plage Float64"
        ) from None
    if converted_float in (float("inf"), float("-inf")):
        raise _conversion_error(field, row_index, value, "hors de la plage Float64")
    return converted_float


def preprocess_data(records: list[dict[str, Any]]) -> pl.DataFrame:
    """Convertir les données SNCF brutes au schéma canonique typé de 26 colonnes.

    Les champs source sont convertis explicitement dans l’ordre stable déclaré
    par :data:`POLARS_SCHEMA`. La fonction conserve l’ordre des lignes, les
    valeurs manquantes et toutes les valeurs conformes, sans modifier les données
    d’entrée. Les champs manquants ou inattendus sont rejetés plutôt que
    silencieusement insérés ou supprimés. Une liste vide renvoie un DataFrame
    sans ligne, mais doté du schéma canonique complet. Ce module utilise
    Polars en interne ; les consommateurs Pandas peuvent adapter la sortie
    typée sans modifier le contrat partagé, indépendant des bibliothèques.

    La fonction se limite à la préparation du schéma et des types. Elle
    n’appelle pas :func:`projet_kit_data.etl.cleaning.clean_data`, ne corrige
    pas les anomalies et n’ajoute pas de caractéristiques propres à une analyse.

    :param records: Enregistrements JSON bruts, par exemple ceux renvoyés par
        :func:`projet_kit_data.ingestion.sncf_api.load_raw_data`.
    :type records: list[dict[str, Any]]
    :returns: DataFrame Polars contenant les 26 champs canoniques dans l’ordre stable.
    :rtype: polars.DataFrame
    :raises TypeError: Si ``records`` n’est pas une liste ou si une ligne
        n’est pas un dictionnaire.
    :raises ValueError: Si une ligne comporte des champs manquants ou inattendus,
        ou si une valeur ne peut pas être convertie vers le type canonique. Les
        erreurs de conversion indiquent le champ et l’index source de la ligne,
        numéroté à partir de zéro.
    """
    if not isinstance(records, list):
        raise TypeError("records doit être une liste de dictionnaires.")

    expected_fields = set(POLARS_SCHEMA)
    converted_records: list[dict[str, Any]] = []

    for row_index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(
                f"La ligne source {row_index} doit être un dictionnaire ; "
                f"type reçu : {type(record).__name__}."
            )

        unexpected_fields = sorted(set(record) - expected_fields)
        if unexpected_fields:
            field = unexpected_fields[0]
            raise ValueError(
                f"Champ inattendu {field!r} à la ligne source {row_index}."
            )

        missing_fields = sorted(expected_fields - set(record))
        if missing_fields:
            field = missing_fields[0]
            raise ValueError(
                f"Champ obligatoire {field!r} manquant à la ligne source {row_index} ; "
                "utilisez null pour indiquer explicitement une valeur absente."
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
