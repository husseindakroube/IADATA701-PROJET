"""Calcul des statistiques historiques de ponctualité par liaison."""

import pandas as pd


def compute_historical_delay_features(
    historical_data: pd.DataFrame,
) -> pd.DataFrame:
    """Calcule le taux de retard historique par liaison orientée.

    Pour chaque liaison, le taux est calculé en divisant
    le nombre total de trains en retard de plus de 15 minutes
    par le nombre total de trains ayant circulé.

    Seules les observations avec une cible valide sont utilisées.

    Args:
        historical_data: Observations des mois précédents,
            déjà préparées par prepare_graph_data().

    Returns:
        DataFrame contenant departure, arrival et
        historical_delay_rate_15.
    """
    valid_data = historical_data.loc[historical_data["valid_target"]]

    routes = valid_data.groupby(["departure", "arrival"], as_index=False).agg(
        historical_late_15=("late_15", "sum"),
        historical_circulated=("circulated", "sum"),
    )

    routes["historical_delay_rate_15"] = (
        routes["historical_late_15"] / routes["historical_circulated"]
    )

    return routes[
        [
            "departure",
            "arrival",
            "historical_delay_rate_15",
        ]
    ]
