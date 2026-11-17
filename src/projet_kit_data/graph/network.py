"""Construction des graphes ferroviaires orientés.

Deux représentations du réseau sont disponibles :

- Graphe non pondéré : représente l'existence des liaisons.
- Graphe pondéré : représente le volume de trains circulés.

Dans les deux cas, une liaison A -> B est distincte
d'une liaison B -> A.
"""

import networkx as nx
import pandas as pd


def build_railway_graph(data: pd.DataFrame) -> nx.DiGraph:
    """Construit un graphe orienté non pondéré.

    Une gare est un noeud. Une liaison orientée est une arête
    si au moins une circulation était prévue sur la période.

    Args:
        data: Observations prétraitées, contenant departure,
            arrival et planned.

    Returns:
        Graphe orienté des liaisons observées.
    """
    routes = (
        data.loc[
            data["planned"] > 0,
            ["departure", "arrival"],
        ]
        .drop_duplicates()
    )

    graph = nx.DiGraph()
    graph.add_edges_from(
        routes.itertuples(index=False, name=None)
    )

    return graph


def build_weighted_railway_graph(
    data: pd.DataFrame,
) -> nx.DiGraph:
    """Construit un graphe orienté pondéré par le trafic.

    Le poids d'une arête est la somme des trains ayant
    effectivement circulé sur cette liaison pendant
    la période représentée par `data`.

    Les observations ayant des volumes incohérents
    sont exclues de l'agrégation.

    Args:
        data: Observations prétraitées contenant departure,
            arrival, planned, cancelled et circulated.

    Returns:
        Graphe orienté avec un attribut `weight` par arête.
    """
    valid_data = data.loc[
        (data["planned"] > 0)
        & (data["circulated"] > 0)
        & (data["cancelled"] >= 0)
        & (data["cancelled"] <= data["planned"])
    ]

    routes = (
        valid_data
        .groupby(
            ["departure", "arrival"],
            as_index=False,
        )["circulated"]
        .sum()
    )

    graph = nx.DiGraph()
    graph.add_weighted_edges_from(
        routes.itertuples(index=False, name=None)
    )

    return graph
