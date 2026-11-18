"Tests des jointures de recherche et des taux d’annulation calculés."

import json

import polars as pl
import pytest

from projet_kit_data.graph.analysis import (
    prepare_research_dataset,
    run_research_data_preparation_pipeline,
)


def inputs():
    observations = pl.DataFrame(
        {
            "edge_id": ["e1", "e2", "e3", "e4", "e5"],
            "date": ["2024-01", "2024-01", "2024-02", "2024-01", "2024-02"],
            "service": [
                "National",
                "National",
                "National",
                "International",
                "National",
            ],
            "gare_depart": ["A", "B", "A", "A", "C"],
            "gare_arrivee": ["B", "C", "B", "B", "D"],
            "source": ["A", "B", "A", "A", "C"],
            "target": ["B", "C", "B", "B", "D"],
            "nb_train_prevu": [10, 0, 10, 2, 5],
            "nb_annulation": [2, 1, -1, 3, 1],
            "nb_train_retard_arrivee": [3, 0, 2, 1, None],
            "nb_train_retard_sup_15": [1, 0, 1, 0, None],
            "nb_train_retard_sup_30": [0, 0, 0, 0, None],
            "nb_train_retard_sup_60": [0, 0, 0, 0, None],
            "retard_moyen_tous_trains_arrivee": [-20.0, None, -472.6, 4.0, None],
            "retard_moyen_arrivee": [-2.0, None, -40.1, 5.0, None],
            "prct_cause_externe": [10.0, None, 20.0, 0.0, None],
            "flag_negative_count": [False, False, True, False, False],
            "flag_cancellations_gt_planned": [False, False, False, True, False],
        }
    )
    edge_metrics = pl.DataFrame(
        {
            "period": [
                "overall",
                "overall",
                "overall",
                "overall",
                "2024-01",
                "2024-01",
                "2024-02",
                "2024-01",
            ],
            "service": ["National"] * 3
            + ["International"]
            + ["National"] * 2
            + ["National", "International"],
            "edge_id": ["e1", "e2", "e3", "e4", "e1", "e2", "e3", "e4"],
            "source": ["A", "B", "A", "A", "A", "B", "A", "A"],
            "target": ["B", "C", "B", "B", "B", "C", "B", "B"],
            "edge_betweenness": [0.9, 0.9, 0.8, 0.7, 0.11, 0.12, 0.13, 0.91],
        }
    )
    node_rows = []
    for period, service, station_ids, pagerank in [
        ("2024-01", "National", ["A", "B", "C"], [0.1, 0.2, 0.3]),
        ("2024-02", "National", ["A", "B"], [0.4, 0.5]),
        ("2024-01", "International", ["A", "B"], [0.8, 0.9]),
        ("2024-02", "National", ["C", "D"], [0.6, 0.7]),
        ("overall", "National", ["A", "B", "C", "D"], [0.91, 0.92, 0.93, 0.94]),
        ("overall", "International", ["A", "B"], [0.98, 0.99]),
    ]:
        for index, node_id in enumerate(station_ids):
            node_rows.append(
                {
                    "period": period,
                    "service": service,
                    "node_id": node_id,
                    "station_name": node_id,
                    "in_degree": index,
                    "out_degree": index + 1,
                    "degree": index * 2 + 1,
                    "in_degree_centrality": 0.01 * (index + 1),
                    "out_degree_centrality": 0.02 * (index + 1),
                    "betweenness_centrality": 0.03 * (index + 1),
                    "in_closeness": 0.04 * (index + 1),
                    "out_closeness": 0.05 * (index + 1),
                    "pagerank": pagerank[index],
                }
            )
    return observations, edge_metrics, pl.DataFrame(node_rows)


def test_cancellation_rates_and_field_preservation() -> None:
    observations, edges, nodes = inputs()
    result = prepare_research_dataset(observations, edges, nodes)
    data = result.data.sort("edge_id")

    assert data.height == observations.height == 5
    assert (
        data.select(
            pl.struct("date", "service", "gare_depart", "gare_arrivee").n_unique()
        ).item()
        == 5
    )
    assert data["cancellation_rate"].to_list() == [0.2, None, None, None, 0.2]
    assert data["cancellation_rate_valid"].to_list() == [
        True,
        False,
        False,
        False,
        True,
    ]
    reasons = dict(
        zip(
            data.filter(pl.col("cancellation_rate_invalid_reason").is_not_null())[
                "edge_id"
            ].to_list(),
            data.filter(pl.col("cancellation_rate_invalid_reason").is_not_null())[
                "cancellation_rate_invalid_reason"
            ].to_list(),
        )
    )
    assert reasons == {
        "e2": "planned_count_not_positive",
        "e3": "negative_cancellation_count",
        "e4": "cancellations_exceed_planned",
    }
    assert (
        data.filter(pl.col("edge_id") == "e1")[
            "retard_moyen_tous_trains_arrivee"
        ].item()
        == -20.0
    )
    assert (
        data.filter(pl.col("edge_id") == "e3")[
            "retard_moyen_tous_trains_arrivee"
        ].item()
        == -472.6
    )
    assert data["flag_primary_arrival_delay_below_minus_15"].to_list() == [
        True,
        False,
        True,
        False,
        False,
    ]
    assert data.filter(pl.col("edge_id") == "e2")["prct_cause_externe"].item() is None
    assert "arrival_delay_rate" not in data.columns


def test_monthly_edge_and_node_joins_are_service_specific_and_keep_missing_metrics() -> (
    None
):
    observations, edges, nodes = inputs()
    # Remove the monthly source-node metric for e5; retain its observation.
    nodes = nodes.filter(
        ~((pl.col("period") == "2024-02") & (pl.col("node_id") == "C"))
    )
    result = prepare_research_dataset(observations, edges, nodes)
    data = result.data
    national = data.filter(pl.col("edge_id") == "e1").row(0, named=True)
    international = data.filter(pl.col("edge_id") == "e4").row(0, named=True)
    missing_edge = data.filter(pl.col("edge_id") == "e5").row(0, named=True)

    assert national["edge_betweenness"] == 0.11
    assert national["source_pagerank"] == 0.1
    assert national["target_pagerank"] == 0.2
    assert international["edge_betweenness"] == 0.91
    assert international["target_pagerank"] == 0.9
    assert missing_edge["edge_betweenness"] is None
    assert missing_edge["source_pagerank"] is None
    assert missing_edge["target_pagerank"] == 0.7
    assert data.height == observations.height
    assert result.metadata["missing_graph_metrics"]["edge_betweenness"] == 1
    assert result.metadata["join_validation"]["overall_metrics_excluded"] is True


def test_duplicate_keys_and_endpoint_mismatch_are_rejected() -> None:
    observations, edges, nodes = inputs()
    with pytest.raises(ValueError, match="clés dupliquées"):
        prepare_research_dataset(
            pl.concat([observations, observations.head(1)]), edges, nodes
        )
    bad_edges = edges.with_columns(
        pl.when(pl.col("edge_id") == "e1")
        .then(pl.lit("C"))
        .otherwise(pl.col("source"))
        .alias("source")
    )
    with pytest.raises(ValueError, match="extrémités orientées incohérentes"):
        prepare_research_dataset(observations, bad_edges, nodes)


def test_file_pipeline_exports_dataset_metadata_and_report(tmp_path) -> None:
    observations, edges, nodes = inputs()
    paths = []
    for name, frame in (
        ("observations", observations),
        ("edges", edges),
        ("nodes", nodes),
    ):
        path = tmp_path / "inputs" / f"{name}.parquet"
        path.parent.mkdir(exist_ok=True)
        frame.write_parquet(path)
        paths.append(path)
    result = run_research_data_preparation_pipeline(
        *paths,
        output_path=tmp_path / "nested" / "research.parquet",
        metadata_path=tmp_path / "nested" / "metadata.json",
        report_path=tmp_path / "reports" / "quality.md",
    )
    assert pl.read_parquet(result.output_paths["research_dataset"]).equals(result.data)
    metadata = json.loads(result.output_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["output_row_count"] == 5
    report = result.output_paths["quality_report"].read_text(encoding="utf-8")
    assert "Métriques de graphe manquantes" in report
    assert "Schéma de sortie" in report
