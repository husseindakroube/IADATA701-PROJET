"""Presentation metadata for graph metrics.

This module translates internal metric columns into stable chart and report
labels without changing the underlying numeric values.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricPresentation:
    """Human-facing metadata for one graph metric."""

    column: str
    label: str
    explanation_fr: str
    unit: str
    precision: int


METRIC_PRESENTATION: dict[str, MetricPresentation] = {
    "in_degree": MetricPresentation(
        "in_degree",
        "In-degree",
        "Nombre de gares distinctes reliées vers cette gare.",
        "voisins",
        0,
    ),
    "out_degree": MetricPresentation(
        "out_degree",
        "Out-degree",
        "Nombre de gares distinctes atteintes depuis cette gare.",
        "voisins",
        0,
    ),
    "degree": MetricPresentation(
        "degree",
        "Degree",
        "Somme des voisins entrants et sortants distincts selon la mesure source.",
        "voisins",
        0,
    ),
    "in_degree_centrality": MetricPresentation(
        "in_degree_centrality",
        "In-degree centrality",
        "Degré entrant normalisé par la taille du réseau.",
        "proportion",
        3,
    ),
    "out_degree_centrality": MetricPresentation(
        "out_degree_centrality",
        "Out-degree centrality",
        "Degré sortant normalisé par la taille du réseau.",
        "proportion",
        3,
    ),
    "betweenness_centrality": MetricPresentation(
        "betweenness_centrality",
        "Betweenness centrality",
        "Part normalisée des plus courts chemins dirigés passant par la gare.",
        "proportion",
        4,
    ),
    "in_closeness": MetricPresentation(
        "in_closeness",
        "In-closeness centrality",
        "Proximité calculée à partir des distances entrantes.",
        "proportion",
        4,
    ),
    "out_closeness": MetricPresentation(
        "out_closeness",
        "Out-closeness centrality",
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
        "Edge betweenness",
        "Part normalisée des plus courts chemins dirigés passant par la liaison.",
        "proportion",
        4,
    ),
}


def format_metric_value(column: str, value: float) -> str:
    """Format a metric value for display, without changing source data.

    :param column: Internal metric column name.
    :type column: str
    :param value: Numeric value to format.
    :type value: float
    :returns: Value rendered at the metric's presentation precision.
    :rtype: str
    :raises KeyError: If no presentation metadata exists for ``column``.
    """
    precision = METRIC_PRESENTATION[column].precision
    return f"{value:.{precision}f}"
