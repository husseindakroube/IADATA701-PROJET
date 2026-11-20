"""Tests des synthèses descriptives sans analyse inférentielle."""

import polars as pl
import pytest

from projet_kit_data.graph.descriptive import (
    _write_report,
    build_descriptive_summaries,
)
from projet_kit_data.graph.presentation import (
    METRIC_PRESENTATION,
    format_metric_value,
)


def fixture_frames():
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
    metric_rows = []
    for period in ["overall", "2024-01", "2024-02"]:
        for service, station_ids in [
            ("National", ["A", "B", "C"]),
            ("International", ["A", "B"]),
        ]:
            for index, node_id in enumerate(station_ids):
                metric_rows.append(
                    {
                        "period": period,
                        "service": service,
                        "node_id": node_id,
                        "station_name": nodes.filter(pl.col("node_id") == node_id)[
                            "station_name"
                        ][0],
                        "in_degree": index,
                        "out_degree": 2 - index,
                        "degree": 2,
                        "in_degree_centrality": 0.1 * index,
                        "out_degree_centrality": 0.1 * (2 - index),
                        "betweenness_centrality": 0.2 * index,
                        "in_closeness": 0.3 * index,
                        "out_closeness": 0.2 * index,
                        "pagerank": 0.1 * (index + 1),
                    }
                )
    node_metrics = pl.DataFrame(metric_rows)
    edge_metrics = pl.DataFrame(
        {
            "period": [
                "overall",
                "overall",
                "overall",
                "2024-01",
                "2024-01",
                "2024-01",
            ],
            "service": [
                "National",
                "National",
                "International",
                "National",
                "National",
                "International",
            ],
            "edge_id": ["e1", "e2", "e3", "e1", "e2", "e3"],
            "source": ["A", "B", "A", "A", "B", "A"],
            "target": ["B", "C", "B", "B", "C", "B"],
            "edge_betweenness": [0.5, 0.2, 0.8, 0.5, 0.2, 0.8],
        }
    )
    research = pl.DataFrame(
        {
            "date": ["2024-01", "2024-01", "2024-01", "2024-02"],
            "service": ["National", "National", "International", "National"],
            "gare_depart": ["Alpha", "Beta", "Alpha", "Alpha"],
            "gare_arrivee": ["Beta", "Gamma", "Beta", "Beta"],
            "retard_moyen_tous_trains_arrivee": [-20.0, 5.0, None, 12.0],
            "cancellation_rate": [0.1, None, 0.0, 0.2],
            "retard_moyen_arrivee": [-3.0, 6.0, None, 10.0],
        }
    )
    return research, node_metrics, edge_metrics, nodes, edges


def test_descriptive_summaries_separate_services_and_use_station_names() -> None:
    inputs = fixture_frames()
    result = build_descriptive_summaries(*inputs, top_n=2)

    assert set(result.network_summary["service"]) == {"National", "International"}
    assert (
        result.network_summary.filter(pl.col("service") == "National")[
            "node_count"
        ].item()
        == 3
    )
    assert result.node_metric_summary.height == 2
    degree_rows = result.node_rankings.filter(
        pl.col("ranking_metric") == "connectivity_degree"
    )
    assert degree_rows.height == 5  # all stations tie for rank 1; cutoff ties survive
    assert set(degree_rows["rank"]) == {1}
    assert (
        result.node_rankings.filter(
            pl.col("ranking_metric") == "betweenness_centrality"
        )
        .filter(pl.col("value") <= 0)
        .is_empty()
    )
    assert set(result.node_rankings["station_name"]) <= {"Alpha", "Beta", "Gamma"}
    assert result.edge_rankings.height == 3
    assert (
        result.edge_rankings.filter(pl.col("edge_id") == "e3")["origin_name"].item()
        == "Alpha"
    )
    assert result.monthly_summary.height == 4
    assert result.operational_summary.height == 2
    national = result.operational_summary.filter(pl.col("service") == "National").row(
        0, named=True
    )
    assert national["retard_moyen_tous_trains_arrivee_missing"] == 0
    assert national["cancellation_rate_missing"] == 1
    assert result.metadata["outlier_definition"].startswith("Règle de Tukey")
    assert result.node_rankings.columns == [
        "rank",
        "service",
        "ranking_metric",
        "node_id",
        "station_name",
        "value",
    ]
    assert result.edge_rankings.columns == [
        "service",
        "edge_id",
        "source",
        "origin_name",
        "target",
        "destination_name",
        "edge_betweenness",
    ]


def test_metric_presentation_and_display_format_do_not_change_numeric_values() -> None:
    source_value = 0.123456789

    assert (
        METRIC_PRESENTATION["betweenness_centrality"].label
        == "Centralité d’intermédiarité"
    )
    assert format_metric_value("betweenness_centrality", source_value) == "0.1235"
    assert source_value == 0.123456789


def test_construction_metadata_mismatch_is_visible() -> None:
    inputs = fixture_frames()
    metadata = {
        "network_diagnostics_by_service": {"National": {"nodes": 99, "edges": 2}}
    }
    with pytest.raises(ValueError, match="métadonnées de construction et la topologie"):
        build_descriptive_summaries(*inputs, construction_metadata=metadata)


def test_unified_report_uses_french_human_tables_and_preserves_other_sections(
    tmp_path,
) -> None:
    result = build_descriptive_summaries(*fixture_frames(), top_n=10)
    result.metadata["observation_count"] = 4
    result.metadata["date_coverage"] = {"min": "2024-01", "max": "2024-02"}
    result.metadata["services"] = ["International", "National"]
    report = tmp_path / "research_report.md"
    report.write_text(
        "# Rapport de recherche\n\n"
        "Avant.\n\n"
        "<!-- BEGIN GENERATED DESCRIPTIVE CONTENT -->\nancien\n"
        "<!-- END GENERATED DESCRIPTIVE CONTENT -->\n\n"
        "## Résultats complémentaires\n\nTexte conservé.\n",
        encoding="utf-8",
    )

    _write_report(result, report)
    content = report.read_text(encoding="utf-8")

    assert "## 2. Structure du réseau" in content
    assert "### Importance des gares" in content
    assert "## 3. Évolution temporelle" in content
    assert "## 4. Régularité opérationnelle" in content
    assert "Composantes fortement connexes" in content
    assert (
        "ne teste pas l’association entre structure du réseau et régularité" in content
    )
    assert "![Réseau National](../../processed/graph/visualizations/" in content
    assert "Texte conservé." in content
    assert "node_id" not in content
    assert "edge_id" not in content
    assert "ranking_metric" not in content
    assert "node_count" not in content
    assert "retard_moyen_tous_trains_arrivee_" not in content
    assert "<!-- BEGIN GENERATED DESCRIPTIVE CONTENT -->" in content
    assert "Degré" in content
    assert "betweenness centrality" in content
    assert "valeurs égales à zéro" in content
    assert "node_id" not in content
    assert "edge_id" not in content
