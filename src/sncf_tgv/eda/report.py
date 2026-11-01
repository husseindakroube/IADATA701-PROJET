"""Génération du rapport de qualité des données SNCF."""

import pandas as pd

from sncf_tgv.eda.quality import (
    check_comments,
    check_durations,
    check_identifiers,
    check_percentages,
    check_train_counts,
    count_duplicates,
    get_column_types,
    get_dataset_overview,
    get_missing_values,
)


def generate_quality_report(
    data: pd.DataFrame,
) -> dict[str, pd.DataFrame | dict[str, int]]:
    """Génère un rapport global de qualité des données SNCF.

    Centralise les résultats des contrôles généraux
    et des différentes règles métier.

    Args:
        data: DataFrame contenant les données SNCF.

    Returns:
        Dictionnaire regroupant les dimensions,
        les types, les valeurs manquantes,
        les doublons et les contrôles métier.

    Raises:
        ValueError: Si certaines colonnes obligatoires
            pour les contrôles sont absentes.
    """
    key_columns = [
        "date",
        "service",
        "gare_depart",
        "gare_arrivee",
    ]

    # Construire les indicateurs généraux.
    overview = get_dataset_overview(data)
    column_types = get_column_types(data)
    missing_values = get_missing_values(data)

    duplicates = {
        "complete_rows": count_duplicates(data),
        "business_keys": count_duplicates(
            data,
            subset=key_columns,
        ),
    }

    # Exécuter les contrôles propres aux données SNCF.
    report = {
        "overview": overview,
        "column_types": column_types,
        "missing_values": missing_values,
        "duplicates": duplicates,
        "identifiers": check_identifiers(data),
        "train_counts": check_train_counts(data),
        "durations": check_durations(data),
        "percentages": check_percentages(data),
        "comments": check_comments(data),
    }

    return report
