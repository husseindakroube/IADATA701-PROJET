"""Tests for overall and monthly graph metric calculation."""

import json

import networkx as nx
import polars as pl
import pytest

from projet_kit_data.graph import metrics
from projet_kit_data.graph.metrics import run_graph_metrics_pipeline


def make_artifacts(tmp_path):
    nodes = pl.DataFrame(
        {
            "node_id": ["A", "B", "C", "D", "unused"],
            "station_name": ["Alpha", "Beta", "Gamma", "Delta", "Unused"],
        }
    )
    edges = pl.DataFrame(
        {
            "edge_id": ["e1", "e2", "e3", "e4"],
            "service": ["National", "National", "National", "International"],
            "source": ["A", "B", "C", "A"],
            "target": ["B", "C", "D", "B"],
        }
    )
    observations = pl.DataFrame(
        {
            "edge_id": ["e1", "e2", "e3", "e4"],
            "date": ["2024-01", "2024-01", "2024-02", "2024-01"],
            "service": ["National", "National", "National", "International"],
            "source": ["A", "B", "C", "A"],
            "target": ["B", "C", "D", "B"],
            "gare_depart": ["Alpha", "Beta", "Gamma", "Alpha"],
            "gare_arrivee": ["Beta", "Gamma", "Delta", "Beta"],
        }
    )
    paths = []
    for name, frame in (
        ("nodes", nodes),
        ("edges", edges),
        ("observations", observations),
    ):
        path = tmp_path / f"{name}.parquet"
        frame.write_parquet(path)
        paths.append(path)
    return nodes, edges, observations, paths


def run(tmp_path, paths, **kwargs):
    return run_graph_metrics_pipeline(
        nodes_path=paths[0],
        edges_path=paths[1],
        observations_path=paths[2],
        output_dir=tmp_path / "output" / "metrics",
        report_path=tmp_path / "reports" / "metrics.md",
        **kwargs,
    )


def test_directed_overall_metrics_and_endpoint_fields(tmp_path) -> None:
    _, _, _, paths = make_artifacts(tmp_path)
    result = run(tmp_path, paths)
    overall = result.node_metrics.filter(
        (pl.col("period") == "overall") & (pl.col("service") == "National")
    )
    beta = overall.filter(pl.col("node_id") == "B").row(0, named=True)
    assert beta["in_degree"] == 1
    assert beta["out_degree"] == 1
    assert beta["degree"] == 2
    assert beta["in_degree_centrality"] == pytest.approx(1 / 3)
    assert beta["out_degree_centrality"] == pytest.approx(1 / 3)
    assert beta["betweenness_centrality"] == pytest.approx(1 / 3)
    assert beta["in_closeness"] == pytest.approx(1 / 3)
    assert beta["out_closeness"] == pytest.approx(4 / 9)
    expected_pr = nx.pagerank(nx.DiGraph([("A", "B"), ("B", "C"), ("C", "D")]))
    assert beta["pagerank"] == pytest.approx(expected_pr["B"])
    edge = result.edge_metrics.filter(
        (pl.col("period") == "overall")
        & (pl.col("service") == "National")
        & (pl.col("edge_id") == "e1")
    ).row(0, named=True)
    assert edge["edge_betweenness"] == pytest.approx(0.25)
    assert edge["source_out_degree"] == 1
    assert edge["target_in_degree"] == 1
    assert edge["target_out_degree"] == 1
    assert result.node_metrics.filter(pl.col("period") == "overall").height == 6
    assert result.node_metrics.filter(pl.col("station_name") == "Unused").is_empty()
    assert result.edge_metrics.height == 4 + 2 + 1 + 1


def test_monthly_graphs_are_independent_and_services_separate(tmp_path) -> None:
    _, _, _, paths = make_artifacts(tmp_path)
    result = run(tmp_path, paths)
    january = result.node_metrics.filter(
        (pl.col("period") == "2024-01") & (pl.col("service") == "National")
    )
    february = result.node_metrics.filter(
        (pl.col("period") == "2024-02") & (pl.col("service") == "National")
    )
    international = result.node_metrics.filter(
        (pl.col("period") == "2024-01") & (pl.col("service") == "International")
    )
    assert set(january["node_id"]) == {"A", "B", "C"}
    assert set(february["node_id"]) == {"C", "D"}
    assert set(international["node_id"]) == {"A", "B"}
    assert result.edge_metrics.filter(pl.col("period") == "2024-02")[
        "edge_id"
    ].to_list() == ["e3"]
    assert result.metadata["overall_graph_count"] == 2
    assert result.metadata["monthly_graph_count"] == 3


def test_page_rank_failure_is_null_and_recorded(tmp_path, monkeypatch) -> None:
    _, _, _, paths = make_artifacts(tmp_path)

    def fail(*args, **kwargs):
        raise nx.PowerIterationFailedConvergence(2)

    monkeypatch.setattr(metrics.nx, "pagerank", fail)
    result = run(tmp_path, paths, alpha=0.9, max_iter=2, tol=1e-8)
    assert result.node_metrics["pagerank"].null_count() == result.node_metrics.height
    assert (
        result.edge_metrics["source_pagerank"].null_count()
        == result.edge_metrics.height
    )
    assert len(result.metadata["pagerank_convergence_failures"]) == 5
    assert result.metadata["pagerank_convergence_failures"][0]["alpha"] == 0.9
    assert (
        "PowerIterationFailedConvergence"
        in result.metadata["pagerank_convergence_failures"][0]["error"]
    )


def test_single_node_self_loop_and_artifact_outputs(tmp_path) -> None:
    nodes = pl.DataFrame({"node_id": ["A"], "station_name": ["Alpha"]})
    edges = pl.DataFrame(
        {"edge_id": ["loop"], "service": ["National"], "source": ["A"], "target": ["A"]}
    )
    observations = pl.DataFrame(
        {
            "edge_id": ["loop"],
            "date": ["2024-01"],
            "service": ["National"],
            "source": ["A"],
            "target": ["A"],
            "gare_depart": ["Alpha"],
            "gare_arrivee": ["Alpha"],
        }
    )
    paths = []
    for name, frame in (
        ("nodes", nodes),
        ("edges", edges),
        ("observations", observations),
    ):
        path = tmp_path / f"single-{name}.parquet"
        frame.write_parquet(path)
        paths.append(path)
    result = run(tmp_path, paths)
    assert result.node_metrics["in_degree"].to_list() == [1, 1]
    assert result.node_metrics["out_degree"].to_list() == [1, 1]
    assert result.node_metrics["in_degree_centrality"].to_list() == [0.0, 0.0]
    assert result.node_metrics["pagerank"].to_list() == [1.0, 1.0]
    assert pl.read_parquet(result.output_paths["node_metrics"]).equals(
        result.node_metrics
    )
    assert pl.read_parquet(result.output_paths["edge_metrics"]).equals(
        result.edge_metrics
    )
    metadata = json.loads(result.output_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["output_schemas"]["node_metrics"]["pagerank"] == "Float64"
    assert result.output_paths["report"].is_file()
    assert (
        result.node_metrics.select(
            pl.struct("period", "service", "node_id").n_unique()
        ).item()
        == result.node_metrics.height
    )


def test_invalid_parameters_and_inconsistent_artifacts_raise(tmp_path) -> None:
    _, _, _, paths = make_artifacts(tmp_path)
    with pytest.raises(ValueError, match="alpha"):
        run(tmp_path, paths, alpha=1.1)
    bad_edges = pl.read_parquet(paths[1]).with_columns(
        pl.lit("missing").alias("source")
    )
    bad_path = tmp_path / "bad-edges.parquet"
    bad_edges.write_parquet(bad_path)
    with pytest.raises(ValueError, match="absent from nodes"):
        run_graph_metrics_pipeline(
            paths[0], bad_path, paths[2], tmp_path / "out", tmp_path / "r.md"
        )
