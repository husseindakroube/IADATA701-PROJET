"""Enrichissement des observations avec les caractéristiques des gares."""

import pandas as pd


def add_station_features(
    data: pd.DataFrame,
    station_features: pd.DataFrame,
) -> pd.DataFrame:
    """Ajoute les caractéristiques des gares de départ et d'arrivée.

    Pour chaque liaison, les métriques des deux gares sont
    ajoutées avec les préfixes `departure_` et `arrival_`.

    Les gares absentes du graphe historique conservent
    des valeurs manquantes pour leurs caractéristiques.

    Args:
        data: Observations à enrichir.
        station_features: DataFrame contenant une ligne par gare,
            identifiée par la colonne `station`.

    Returns:
        DataFrame enrichi avec les caractéristiques des gares
        de départ et d'arrivée.
    """
    result = data.copy()

    feature_columns = [
        column
        for column in station_features.columns
        if column != "station"
    ]

    for direction in ("departure", "arrival"):
        renamed_features = station_features.rename(
            columns={
                "station": direction,
                **{
                    column: f"{direction}_{column}"
                    for column in feature_columns
                },
            }
        )

        result = result.merge(
            renamed_features,
            on=direction,
            how="left",
            validate="many_to_one",
        )

    return result
