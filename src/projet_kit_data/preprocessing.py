"""Prétraitement des données SNCF pour l'analyse de réseau et le ML.

Ce module standardise les observations mensuelles et calcule
la variable cible : la proportion de trains en retard de plus
de 15 minutes parmi les trains ayant effectivement circulé.

Les observations dont la cible est invalide sont conservées,
mais identifiées par la colonne `valid_target`.
"""

import pandas as pd

# Correspondance entre les colonnes du CSV SNCF et les noms utilisés dans notre code Python.
COLUMN_MAPPING = {
    "Date": "date",
    "Service": "service",
    "Gare de départ": "departure",
    "Gare d'arrivée": "arrival",
    "Durée moyenne du trajet": "duration",
    "Nombre de circulations prévues": "planned",
    "Nombre de trains annulés": "cancelled",
    "Nombre trains en retard > 15min": "late_15",
}


def prepare_graph_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prépare les observations SNCF pour les traitements suivants.

    La cible est définie par :

        delay_rate_15 = late_15 / (planned - cancelled)

    Une observation est considérée comme valide si :
    - au moins un train a circulé
    - le nombre de trains en retard est compris entre
      zéro et le nombre de trains ayant circulé.

    Les observations invalides ne sont pas supprimées :
    leur cible est représentée par NaN.

    Args:
        df: Données SNCF brutes, avec leurs colonnes d'origine.

    Returns:
        DataFrame normalisé avec les colonnes nécessaires
        à la construction du graphe et à la prédiction.
    """
    missing_columns = set(COLUMN_MAPPING) - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Colonnes SNCF manquantes : " + ", ".join(sorted(missing_columns))
        )

    # 1. Sélectionner et renommer les colonnes utiles
    data = df[list(COLUMN_MAPPING)].rename(columns=COLUMN_MAPPING).copy()

    # 2. Normaliser les dates et les identifiants de gares
    data["date"] = pd.to_datetime(
        data["date"],
        format="%Y-%m",
    )

    for column in ("departure", "arrival"):
        data[column] = data[column].str.strip().str.upper()

    # 3. Déterminer le nombre de circulations réalisées
    data["circulated"] = data["planned"] - data["cancelled"]

    # 4. Identifier les observations avec une cible valide
    data["valid_target"] = (
        (data["planned"] >= 0)
        & (data["cancelled"] >= 0)
        & (data["cancelled"] <= data["planned"])
        & (data["circulated"] > 0)
        & (data["late_15"] >= 0)
        & (data["late_15"] <= data["circulated"])
    )

    # 5. Calculer le taux de retard sur les observations valides
    data["delay_rate_15"] = data["late_15"].div(
        data["circulated"].where(data["valid_target"])
    )

    return data
