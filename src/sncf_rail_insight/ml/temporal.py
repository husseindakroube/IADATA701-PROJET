"""Construction du dataset ML à partir de fenêtres historiques glissantes."""

import pandas as pd

from sncf_rail_insight.graph.centrality import compute_all_graph_features
from sncf_rail_insight.graph.network import build_weighted_railway_graph
from sncf_rail_insight.graph.routes import compute_edge_features
from sncf_rail_insight.ml.enrichment import add_station_features
from sncf_rail_insight.ml.historical import compute_historical_delay_features


def build_temporal_graph_dataset(
    data: pd.DataFrame,
    window_months: int = 12,
    recent_window_months: int | None = None,
) -> pd.DataFrame:
    """Construit le dataset ML à partir de fenêtres historiques glissantes.

    Pour chaque mois t, les caractéristiques sont calculées uniquement
    sur l'intervalle [t - window_months, t[.

    Une fenêtre récente optionnelle permet de calculer le taux de retard
    récent et sa tendance par rapport au taux historique.

    Les premiers mois sans historique suffisant sont exclus.
    Les caractéristiques indisponibles restent à NaN.

    Args:
        data: Observations mensuelles issues de prepare_graph_data().
        window_months: Fenêtre historique principale (12 mois par défaut).
        recent_window_months: Fenêtre récente optionnelle, en mois.

    Returns:
        DataFrame enrichi avec les caractéristiques des gares,
        des liaisons et les statistiques historiques de retard.

    Raises:
        ValueError: Si les fenêtres sont invalides ou si
            l'historique est insuffisant.
    """
    if window_months < 1:
        raise ValueError("window_months doit être supérieur à zéro.")

    if recent_window_months is not None and not (
        1 <= recent_window_months <= window_months
    ):
        raise ValueError(
            "recent_window_months doit être compris entre 1 et window_months."
        )

    data = data.sort_values("date").copy()
    first_date = data["date"].min()

    enriched_months = []

    for current_date in sorted(data["date"].unique()):
        # 1. Sélectionner exclusivement les mois antérieurs
        start_date = current_date - pd.DateOffset(months=window_months)

        if start_date < first_date:
            continue

        historical_data = data.loc[
            (data["date"] >= start_date)
            & (data["date"] < current_date)
        ]

        current_data = data.loc[data["date"] == current_date]

        # 2. Construire une seule fois le graphe historique pondéré
        graph = build_weighted_railway_graph(historical_data)

        # 3. Calculer les caractéristiques du réseau
        station_features = compute_all_graph_features(graph)
        route_features = compute_edge_features(graph)

        # 4. Calculer les statistiques historiques de retard
        recent_data = None

        if recent_window_months is not None:
            recent_start = current_date - pd.DateOffset(
                months=recent_window_months
            )
            recent_data = historical_data.loc[
                historical_data["date"] >= recent_start
            ]

        delay_features = compute_historical_delay_features(
            historical_data,
            recent_data=recent_data,
        )

        # 5. Enrichir les observations du mois courant
        enriched = add_station_features(
            current_data,
            station_features,
        )

        enriched = enriched.merge(
            route_features,
            on=["departure", "arrival"],
            how="left",
            validate="many_to_one",
        )

        enriched = enriched.merge(
            delay_features,
            on=["departure", "arrival"],
            how="left",
            validate="many_to_one",
        )

        enriched_months.append(enriched)

    if not enriched_months:
        raise ValueError(
            "Historique insuffisant pour construire le dataset temporel."
        )

    return pd.concat(enriched_months, ignore_index=True)
