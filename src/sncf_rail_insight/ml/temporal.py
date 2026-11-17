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
) -> pd.DataFrame:
    """Construit le dataset ML à partir de fenêtres historiques glissantes.

    Pour chaque mois t, les caractéristiques sont calculées uniquement
    sur l'intervalle [t - window_months, t[.

    Le mois courant n'intervient jamais dans le calcul des variables
    historiques utilisées pour sa propre prédiction.

    Les premiers mois, ne disposant pas d'un historique suffisamment
    ancien, sont exclus du dataset final.

    Args:
        data: Observations mensuelles issues de prepare_graph_data().
        window_months: Nombre de mois d'historique utilisés (12 par défaut).

    Returns:
        DataFrame contenant les observations mensuelles enrichies avec :
            - les centralités structurelles des gares
            - les caractéristiques pondérées des gares
            - les caractéristiques des liaisons orientées
            - les taux historiques de retard par liaison.

        Les caractéristiques indisponibles pour une gare ou une liaison
        absente de l'historique restent à NaN.

    Raises:
        ValueError: Si la fenêtre est invalide ou si l'historique est
            insuffisant pour construire le dataset.
    """
    if window_months < 1:
        raise ValueError("window_months doit être supérieur à zéro.")

    data = data.sort_values("date").copy()
    first_date = data["date"].min()

    enriched_months = []

    for current_date in sorted(data["date"].unique()):
        # 1. Sélectionner exclusivement les mois antérieurs
        start_date = current_date - pd.DateOffset(
            months=window_months
        )

        if start_date < first_date:
            continue

        historical_data = data.loc[
            (data["date"] >= start_date)
            & (data["date"] < current_date)
        ]

        current_data = data.loc[
            data["date"] == current_date
        ]

        # 2. Construire une seule fois le graphe historique pondéré
        graph = build_weighted_railway_graph(historical_data)

        # 3. Calculer les caractéristiques du réseau
        station_features = compute_all_graph_features(graph)
        route_features = compute_edge_features(graph)

        # 4. Calculer les taux de retard historiques
        delay_features = compute_historical_delay_features(
            historical_data
        )

        # 5. Ajouter les caractéristiques aux observations courantes
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
