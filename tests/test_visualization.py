'Tests de génération de graphiques descriptifs réutilisables.'

import polars as pl

from projet_kit_data.graph.visualization import generate_visualizations


def test_visualizations_generate_reusable_service_specific_pngs(tmp_path) -> None:
    nodes = pl.DataFrame(
        {"node_id": ["A", "B", "C"], "station_name": ["Alpha", "Beta", "Gamma"]}
    )
    edges = pl.DataFrame(
        {
            "edge_id": ["e1", "e2", "e3"],
            "service": ["National", "National", "International"],
            "source": ["A", "B", "A"],
            "target": ["B", "C", "B"],
        }
    )
    node_rows = []
    for period in ("overall", "2024-01"):
        for service, ids in (
            ("National", ["A", "B", "C"]),
            ("International", ["A", "B"]),
        ):
            for idx, node_id in enumerate(ids):
                node_rows.append(
                    {
                        "period": period,
                        "service": service,
                        "node_id": node_id,
                        "in_degree": idx,
                        "out_degree": len(ids) - idx - 1,
                        "degree": len(ids) - 1,
                        "betweenness_centrality": idx / 10,
                        "pagerank": 1 / len(ids),
                    }
                )
    node_metrics = pl.DataFrame(node_rows)
    edge_metrics = pl.DataFrame(
        {
            "period": ["overall"] * 3 + ["2024-01"] * 3,
            "service": ["National", "National", "International"] * 2,
            "edge_betweenness": [0.5, 0.2, 0.8] * 2,
            "edge_id": ["e1", "e2", "e3"] * 2,
        }
    )
    research = pl.DataFrame(
        {
            "date": ["2024-01"] * 4,
            "service": ["National", "National", "International", "International"],
            "retard_moyen_tous_trains_arrivee": [-12.0, 20.0, 3.0, None],
            "retard_moyen_arrivee": [-2.0, 12.0, 4.0, None],
            "cancellation_rate": [0.02, None, 0.1, 0.0],
        }
    )
    research_before = research.clone()

    paths = generate_visualizations(
        research, node_metrics, edge_metrics, nodes, edges, tmp_path
    )

    assert research.equals(research_before)
    assert set(paths) == {
        "network_national",
        "network_international",
        "degree_distributions",
        "node_centrality_distributions",
        "edge_betweenness_distribution",
        "top10_station_rankings",
        "top10_edge_rankings",
        "monthly_network_evolution",
        "operational_outcome_distributions",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())
