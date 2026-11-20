"""Tests de la construction déterministe du graphe SNCF par service."""

import json

import networkx as nx
import polars as pl
import pytest

from projet_kit_data.graph import (
    construct_graph_data,
    export_graph_artifacts,
    reconstruct_monthly_graph,
    run_graph_construction_pipeline,
)


def make_data(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Créer les jeux de données de test pour les clés et mesures représentatives du graphe."""
    schema = {
        "date": pl.String,
        "service": pl.String,
        "gare_depart": pl.String,
        "gare_arrivee": pl.String,
        "nb_train_prevu": pl.Int64,
        "retard_moyen_arrivee": pl.Float64,
        "flag_negative_count": pl.Boolean,
        "flag_sup30_lt_sup60": pl.Boolean,
        "flag_sup15_lt_sup30": pl.Boolean,
        "flag_cancellations_gt_planned": pl.Boolean,
    }
    normalized = [
        {
            "nb_train_prevu": 10,
            "retard_moyen_arrivee": None,
            "flag_negative_count": False,
            "flag_sup30_lt_sup60": False,
            "flag_sup15_lt_sup30": False,
            "flag_cancellations_gt_planned": False,
            **row,
        }
        for row in rows
    ]
    return pl.DataFrame(normalized, schema=schema)


def row(
    month: str,
    service: str = "National",
    origin: str = "Paris",
    destination: str = "Lyon",
    **values: object,
) -> dict[str, object]:
    return {
        "date": month,
        "service": service,
        "gare_depart": origin,
        "gare_arrivee": destination,
        **values,
    }


def test_direction_services_shared_nodes_and_deterministic_ids() -> None:
    data = make_data(
        [
            row("2024-01"),
            row("2024-02"),
            row("2024-01", origin="Lyon", destination="Paris"),
            row("2024-01", service="International"),
            row("2024-01", origin="Paris", destination="Paris"),
        ]
    )
    result = construct_graph_data(data)
    again = construct_graph_data(data.reverse())

    assert result.nodes.sort("station_name").equals(again.nodes.sort("station_name"))
    assert result.edges.sort("edge_id").equals(again.edges.sort("edge_id"))
    assert result.metadata == again.metadata
    assert result.graph.number_of_nodes() == 2
    assert result.graph.number_of_edges() == 4
    assert result.graph.has_edge(
        result.nodes.filter(pl.col("station_name") == "Paris")["node_id"][0],
        result.nodes.filter(pl.col("station_name") == "Lyon")["node_id"][0],
    )
    edge_table = result.edges
    assert (
        edge_table.select(pl.struct("service", "source", "target").n_unique()).item()
        == 4
    )
    assert edge_table["edge_id"].n_unique() == 4
    paris_id = result.nodes.filter(pl.col("station_name") == "Paris")["node_id"][0]
    lyon_id = result.nodes.filter(pl.col("station_name") == "Lyon")["node_id"][0]
    forward_ids = edge_table.filter(
        (pl.col("source") == paris_id) & (pl.col("target") == lyon_id)
    )["edge_id"].to_list()
    reverse_ids = edge_table.filter(
        (pl.col("source") == lyon_id) & (pl.col("target") == paris_id)
    )["edge_id"].to_list()
    assert len(forward_ids) == 2
    assert len(reverse_ids) == 1
    assert not set(forward_ids).intersection(reverse_ids)
    assert edge_table.filter(pl.col("source") == pl.col("target")).height == 1
    assert set(result.service_graphs) == {"National", "International"}
    assert (
        len(
            {
                result.nodes.filter(pl.col("station_name") == "Paris")["node_id"][0],
                result.nodes.filter(pl.col("station_name") == "Lyon")["node_id"][0],
            }
        )
        == 2
    )


def test_temporal_edge_aggregation_and_monthly_reconstruction() -> None:
    result = construct_graph_data(
        make_data(
            [
                row("2024-01"),
                row("2024-03"),
                row("2024-03", origin="Marseille", destination="Nice"),
            ]
        )
    )
    paris_lyon = result.edges.filter(
        (
            pl.col("source")
            == result.nodes.filter(pl.col("station_name") == "Paris")["node_id"][0]
        )
        & (
            pl.col("target")
            == result.nodes.filter(pl.col("station_name") == "Lyon")["node_id"][0]
        )
    ).row(0, named=True)
    assert paris_lyon["n_months_observed"] == 2
    assert paris_lyon["first_date"] == "2024-01"
    assert paris_lyon["last_date"] == "2024-03"
    marseille_nice = result.edges.filter(
        (
            pl.col("source")
            == result.nodes.filter(pl.col("station_name") == "Marseille")["node_id"][0]
        )
        & (
            pl.col("target")
            == result.nodes.filter(pl.col("station_name") == "Nice")["node_id"][0]
        )
    ).row(0, named=True)
    assert marseille_nice["n_months_observed"] == 1
    assert result.edge_observations.height == 3
    assert result.metadata["temporal_diagnostics"]["observations_per_month"] == {
        "2024-01": 1,
        "2024-03": 2,
    }
    assert result.metadata["temporal_diagnostics"]["missing_months"] == ["2024-02"]

    graph = reconstruct_monthly_graph(result.edge_observations, "National", "2024-01")
    assert isinstance(graph, nx.DiGraph)
    assert graph.number_of_edges() == 1
    assert next(iter(graph.edges(data=True)))[2]["date"] == "2024-01"
    assert (
        reconstruct_monthly_graph(
            result.edge_observations, "National", "2024-02"
        ).number_of_edges()
        == 0
    )
    assert (
        reconstruct_monthly_graph(
            result.edge_observations, "National", "2024-03"
        ).number_of_edges()
        == 2
    )


def test_invalid_keys_duplicates_and_flagged_valid_observations() -> None:
    data = make_data(
        [
            row("2024-01", flag_negative_count=True),
            row("2024-01", origin="", destination="Nice"),
            row("2024-02", service=None),
            row(None),
            row("2024-13"),
            row("2024/03"),
            row("2024-04", origin=None),
            row("2024-05", destination=None),
            row("2024-03", origin="Bordeaux", destination="Toulouse"),
            row("2024-03", origin="Bordeaux", destination="Toulouse"),
        ]
    )
    original = data.clone()
    result = construct_graph_data(data)

    assert data.equals(original)
    assert result.edge_observations.height == 1
    assert result.edge_observations["flag_negative_count"].to_list() == [True]
    assert result.edge_observations["retard_moyen_arrivee"].to_list() == [None]
    reasons = result.metadata["exclusion_reasons_and_counts"]
    assert reasons == {
        "duplicate_business_key": 2,
        "empty_gare_depart": 1,
        "invalid_date_format": 1,
        "invalid_date_value": 1,
        "missing_date": 1,
        "missing_gare_arrivee": 1,
        "missing_gare_depart": 1,
        "missing_service": 1,
    }
    assert result.metadata["excluded_record_count"] == 9
    assert (
        result.metadata["flagged_record_counts_in_source"]["flag_negative_count"] == 1
    )


def test_missing_required_columns_and_wrong_key_types_raise() -> None:
    with pytest.raises(ValueError, match="Colonnes de clé du graphe manquantes"):
        construct_graph_data(pl.DataFrame({"date": ["2024-01"]}))
    with pytest.raises(TypeError, match="type String Polars"):
        construct_graph_data(
            pl.DataFrame(
                {
                    "date": [202401],
                    "service": ["National"],
                    "gare_depart": ["Paris"],
                    "gare_arrivee": ["Lyon"],
                }
            )
        )


def test_export_schemas_metadata_report_and_pipeline(tmp_path) -> None:
    source = make_data(
        [row("2024-01"), row("2024-02", origin="Lyon", destination="Paris")]
    )
    input_path = tmp_path / "source.parquet"
    source.write_parquet(input_path)
    output_dir = tmp_path / "nested" / "graph"
    report_path = tmp_path / "reports" / "construction.md"

    result = run_graph_construction_pipeline(input_path, output_dir, report_path)

    assert result.nodes.columns == ["node_id", "station_name"]
    assert result.edges.columns == [
        "edge_id",
        "service",
        "source",
        "target",
        "n_months_observed",
        "first_date",
        "last_date",
    ]
    assert result.edge_observations.columns[:5] == [
        "edge_id",
        "date",
        "service",
        "source",
        "target",
    ]
    for name in ("nodes.parquet", "edges.parquet", "edge_observations.parquet"):
        assert pl.read_parquet(output_dir / name).height > 0
    metadata = json.loads(
        (output_dir / "graph_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["source_row_count"] == 2
    assert metadata["node_count"] == 2
    assert metadata["service_aware_edge_count"] == 2
    report = report_path.read_text(encoding="utf-8")
    assert "Diagnostics de la structure du réseau par service" in report
    assert "Diagnostics temporels" in report
    assert "Diagnostics de qualité des données" in report

    second = export_graph_artifacts(
        construct_graph_data(source, source_dataset_path=input_path),
        tmp_path / "second",
        tmp_path / "second-report.md",
    )
    assert result.nodes.equals(second.nodes)
    assert result.edges.equals(second.edges)
    assert result.edge_observations.equals(second.edge_observations)
    assert result.metadata == second.metadata


def test_empty_input_exports_typed_empty_tables(tmp_path) -> None:
    empty = make_data([])
    result = construct_graph_data(empty)
    assert (
        result.nodes.height
        == result.edges.height
        == result.edge_observations.height
        == 0
    )
    assert result.metadata["minimum_observation_month"] is None
    exported = export_graph_artifacts(
        result, tmp_path / "graph", tmp_path / "report.md"
    )
    assert pl.read_parquet(exported.output_paths["edges"]).schema == result.edges.schema
