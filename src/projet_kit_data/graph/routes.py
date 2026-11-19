"""Calcul des caractéristiques des liaisons ferroviaires."""

import networkx as nx
import pandas as pd


def compute_edge_features(graph: nx.DiGraph) -> pd.DataFrame:
    """Calcule les caractéristiques de chaque liaison orientée.

    Le graphe doit être pondéré par le nombre de trains circulés.

    Pour chaque liaison A → B :
        - edge_volume : trafic de A vers B ;
        - edge_traffic_share : part du trafic sortant de A
          qui emprunte la liaison A → B ;
        - edge_reverse_volume : trafic de B vers A.

    Args:
        graph: Graphe orienté pondéré par le trafic.

    Returns:
        DataFrame contenant une ligne par liaison orientée.
    """
    records = []

    for departure, arrival, attributes in graph.edges(data=True):
        volume = attributes["weight"]

        total_out = graph.out_degree(
            departure,
            weight="weight",
        )

        reverse_volume = graph.get_edge_data(
            arrival,
            departure,
            default={},
        ).get("weight", 0)

        records.append(
            {
                "departure": departure,
                "arrival": arrival,
                "edge_volume": volume,
                "edge_traffic_share": (volume / total_out if total_out > 0 else 0),
                "edge_reverse_volume": reverse_volume,
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "departure",
            "arrival",
            "edge_volume",
            "edge_traffic_share",
            "edge_reverse_volume",
        ],
    )
