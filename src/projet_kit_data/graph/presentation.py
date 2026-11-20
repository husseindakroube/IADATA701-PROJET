"""Métadonnées de présentation des métriques de graphe.

Ce module associe aux colonnes internes des métriques des libellés stables pour
les figures et les rapports, sans modifier les valeurs numériques sous-jacentes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricPresentation:
    """Métadonnées destinées à l’affichage d’une métrique de graphe."""

    column: str
    label: str
    explanation_fr: str
    unit: str
    precision: int


METRIC_PRESENTATION: dict[str, MetricPresentation] = {
    "in_degree": MetricPresentation(
        "in_degree",
        "Degré entrant",
        "Nombre de gares distinctes reliées vers cette gare.",
        "voisins",
        0,
    ),
    "out_degree": MetricPresentation(
        "out_degree",
        "Degré sortant",
        "Nombre de gares distinctes atteintes depuis cette gare.",
        "voisins",
        0,
    ),
    "degree": MetricPresentation(
        "degree",
        "Degré",
        "Somme des voisins entrants et sortants distincts selon la mesure source.",
        "voisins",
        0,
    ),
    "in_degree_centrality": MetricPresentation(
        "in_degree_centrality",
        "Centralité de degré entrant",
        "Degré entrant normalisé par la taille du réseau.",
        "proportion",
        3,
    ),
    "out_degree_centrality": MetricPresentation(
        "out_degree_centrality",
        "Centralité de degré sortant",
        "Degré sortant normalisé par la taille du réseau.",
        "proportion",
        3,
    ),
    "betweenness_centrality": MetricPresentation(
        "betweenness_centrality",
        "Centralité d’intermédiarité",
        "Part normalisée des plus courts chemins dirigés passant par la gare.",
        "proportion",
        4,
    ),
    "in_closeness": MetricPresentation(
        "in_closeness",
        "Centralité de proximité entrante",
        "Proximité calculée à partir des distances entrantes.",
        "proportion",
        4,
    ),
    "out_closeness": MetricPresentation(
        "out_closeness",
        "Centralité de proximité sortante",
        "Proximité calculée à partir des distances sortantes.",
        "proportion",
        4,
    ),
    "pagerank": MetricPresentation(
        "pagerank",
        "PageRank",
        "Importance topologique selon la structure des liens dirigés.",
        "proportion",
        4,
    ),
    "edge_betweenness": MetricPresentation(
        "edge_betweenness",
        "Betweenness de l’arête",
        "Part normalisée des plus courts chemins dirigés passant par la liaison.",
        "proportion",
        4,
    ),
}


def format_metric_value(column: str, value: float) -> str:
    """Mettre en forme une valeur de métrique pour l’affichage, sans modifier la source.

    :param column: Nom interne de la colonne de métrique.
    :type column: str
    :param value: Valeur numérique à mettre en forme.
    :type value: float
    :returns: Valeur rendue avec la précision d’affichage de la métrique.
    :rtype: str
    :raises KeyError: Si aucune métadonnée de présentation n’existe pour ``column``.
    """
    precision = METRIC_PRESENTATION[column].precision
    return f"{value:.{precision}f}"
