"""Calcul des statistiques historiques de ponctualité par liaison."""

import pandas as pd


def _compute_delay_rate(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """Calcule le taux de retard agrégé pour chaque liaison orientée."""
    valid_data = data.loc[data["valid_target"]]

    routes = (
        valid_data.groupby(["departure", "arrival"], as_index=False)
        .agg(
            late_15=("late_15", "sum"),
            circulated=("circulated", "sum"),
        )
    )

    routes[column] = routes["late_15"] / routes["circulated"]

    return routes[["departure", "arrival", column]]

def compute_historical_delay_features(
    historical_data: pd.DataFrame,
    recent_data: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calcule les taux de retard historiques par liaison orientée.

    Les taux sont pondérés par le nombre de trains ayant circulé.
    Seules les observations dont la cible est valide sont utilisées.

    Args:
        historical_data: Observations de la fenêtre historique principale.
        recent_data: Observations des 3 derniers mois, facultatives.

    Returns:
        Taux historique, et éventuellement taux récent et tendance.
    """
    routes = _compute_delay_rate(
        historical_data, "historical_delay_rate_15"
    )

    if recent_data is not None:
        recent = _compute_delay_rate(recent_data, "recent_delay_rate_15")

        routes = routes.merge(
            recent,
            on=["departure", "arrival"],
            how="left",
            validate="one_to_one",
        )

        routes["delay_rate_trend_15"] = (
            routes["recent_delay_rate_15"]
            - routes["historical_delay_rate_15"]
        )

    return routes
