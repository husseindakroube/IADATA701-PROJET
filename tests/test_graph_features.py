"""Tests des caractéristiques des liaisons ferroviaires."""

import networkx as nx
import pytest

from sncf_rail_insight.graph.routes import compute_edge_features


def test_edge_features() -> None:
    """Vérifie les volumes, proportions et circulations inverses."""
    graph = nx.DiGraph()
    graph.add_weighted_edges_from(
        [
            ("A", "B", 100),
            ("A", "C", 50),
            ("B", "A", 40),
        ]
    )

    features = compute_edge_features(graph)
    features = features.set_index(["departure", "arrival"])

    # Liaison A -> B
    route_ab = features.loc[("A", "B")]

    assert route_ab["edge_volume"] == 100
    assert route_ab["edge_traffic_share"] == pytest.approx(100 / 150)
    assert route_ab["edge_reverse_volume"] == 40

    # Liaison A -> C : aucun trajet inverse.
    route_ac = features.loc[("A", "C")]

    assert route_ac["edge_volume"] == 50
    assert route_ac["edge_traffic_share"] == pytest.approx(50 / 150)
    assert route_ac["edge_reverse_volume"] == 0

    # Liaison B -> A : tout le trafic sortant de B.
    route_ba = features.loc[("B", "A")]

    assert route_ba["edge_volume"] == 40
    assert route_ba["edge_traffic_share"] == pytest.approx(1.0)
    assert route_ba["edge_reverse_volume"] == 100
