"""Calcul des caractéristiques des gares du réseau SNCF."""

import networkx as nx
import pandas as pd


def compute_graph_features(graph: nx.DiGraph) -> pd.DataFrame:
    """Calcule les caractéristiques structurelles de chaque gare.

    Les arêtes sont considérées comme non pondérées,
    même si le graphe possède des poids.

    Métriques :
        - Degrés entrants, sortants et totaux
        - Centralité d'intermédiarité (betweenness)
        - PageRank non pondéré
    """
    betweenness = nx.betweenness_centrality(
        graph,
        normalized=True,
        weight=None,
    )

    pagerank = nx.pagerank(
        graph,
        alpha=0.85,
        weight=None,
    )

    return pd.DataFrame(
        [
            {
                "station": station,
                "in_degree": graph.in_degree(station),
                "out_degree": graph.out_degree(station),
                "total_degree": graph.degree(station),
                "betweenness": betweenness[station],
                "pagerank": pagerank[station],
            }
            for station in graph.nodes
        ]
    )


def compute_weighted_graph_features(
    graph: nx.DiGraph,
) -> pd.DataFrame:
    """Calcule les caractéristiques pondérées de chaque gare.

    Les poids représentent les volumes de trains circulés.

    Métriques :
        - Strength entrant et sortant
        - PageRank pondéré par le trafic
    """
    pagerank = nx.pagerank(
        graph,
        alpha=0.85,
        weight="weight",
    )

    return pd.DataFrame(
        [
            {
                "station": station,
                "in_strength": graph.in_degree(
                    station, weight="weight"
                ),
                "out_strength": graph.out_degree(
                    station, weight="weight"
                ),
                "weighted_pagerank": pagerank[station],
            }
            for station in graph.nodes
        ]
    )


def compute_all_graph_features(
    graph: nx.DiGraph,
) -> pd.DataFrame:
    """Calcule les caractéristiques structurelles et pondérées des gares.

    Args:
        graph: Graphe orienté pondéré représentant les circulations
            sur la période historique étudiée.

    Returns:
        DataFrame contenant une ligne par gare et les métriques :
        degrés, betweenness, PageRank, strengths et PageRank pondéré.
    """
    structural_features = compute_graph_features(graph)
    weighted_features = compute_weighted_graph_features(graph)

    return structural_features.merge(
        weighted_features,
        on="station",
        how="inner",
        validate="one_to_one",
    )
