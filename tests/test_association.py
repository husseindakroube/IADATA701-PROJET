"""Tests for simplified exploratory graph/regularity associations."""

import numpy as np
import polars as pl

from projet_kit_data.graph.association import (
    PRIMARY_OUTCOME,
    _group_labels,
    build_association_results,
    run_association_analysis_pipeline,
)


def fixture_research_data() -> pl.DataFrame:
    rows = []
    for service in ("National", "International"):
        for cluster in range(4):
            for month in range(16):
                delay = float(cluster * 7 + month / 10)
                if cluster == 0 and month in (0, 1):
                    delay = -20.0 - month
                valid_cancellation = not (cluster == 0 and month == 2)
                rows.append(
                    {
                        "service": service,
                        "date": f"2024-{month + 1:02d}",
                        "gare_depart": f"Origin {cluster}",
                        "gare_arrivee": f"Destination {cluster}",
                        "edge_betweenness": None
                        if cluster == 3 and month == 0
                        else float(cluster + 1) / 100,
                        "source_degree": float(cluster + 1),
                        "target_degree": float(cluster + 1),
                        "source_betweenness_centrality": 0.0
                        if cluster < 2
                        else float(cluster) / 10,
                        "target_betweenness_centrality": 0.0
                        if cluster < 2
                        else float(cluster) / 12,
                        "source_pagerank": float(cluster + 1) / 10,
                        "target_pagerank": float(4 - cluster) / 10,
                        PRIMARY_OUTCOME: delay,
                        "cancellation_rate": 0.01 * cluster
                        if valid_cancellation
                        else None,
                        "cancellation_rate_valid": valid_cancellation,
                        "retard_moyen_arrivee": delay + 5,
                        "flag_primary_arrival_delay_below_minus_15": delay < -15,
                    }
                )
    return pl.DataFrame(rows)


def test_tie_preserving_groups_keep_zero_centrality_separate() -> None:
    values = np.array([0.0] * 4 + [0.1] * 3 + [0.2] * 3 + [0.3] * 3 + [0.4] * 3)

    labels, strategy = _group_labels(values, quantile_count=4, min_positive_size=5)

    assert strategy == "zero_plus_tie_preserving_quantiles"
    assert set(labels[:4]) == {"Zero"}
    assert len(set(labels[4:7])) == 1
    assert len(set(labels[7:10])) == 1
    assert len(set(labels[10:13])) == 1
    assert len(set(labels[13:])) == 1
    assert labels[4] != labels[7]


def test_correlations_use_pairwise_values_and_valid_cancellations() -> None:
    source = fixture_research_data()
    before = source.clone()

    result = build_association_results(source)

    assert source.equals(before)
    primary = result.correlations.filter(
        (pl.col("service") == "National")
        & (pl.col("predictor") == "edge_betweenness")
        & (pl.col("outcome") == PRIMARY_OUTCOME)
    )
    assert set(primary["method"].to_list()) == {"pearson", "spearman"}
    assert primary["n_valid"].unique().to_list() == [63]
    assert primary["coefficient"].null_count() == 0
    assert primary["p_value"].null_count() == 0

    cancellation = result.correlations.filter(
        (pl.col("service") == "National")
        & (pl.col("predictor") == "source_degree")
        & (pl.col("outcome") == "cancellation_rate")
    )
    assert cancellation["n_valid"].unique().to_list() == [63]


def test_centrality_groups_and_service_specific_results_are_preserved() -> None:
    result = build_association_results(fixture_research_data())
    groups = result.quantile_comparisons.filter(
        (pl.col("analysis_scope") == "service")
        & (pl.col("predictor") == "source_betweenness_centrality")
        & (pl.col("outcome") == PRIMARY_OUTCOME)
        & (pl.col("service") == "National")
    )
    assert {"Zero", "Positive"}.issubset(set(groups["group_label"].to_list()))
    assert set(result.correlations["service"].unique().to_list()) == {
        "Overall",
        "National",
        "International",
    }
    assert result.metadata["directed_cluster_count_by_service"] == {
        "National": 4,
        "International": 4,
    }


def test_robustness_compares_full_and_extreme_excluded_correlations() -> None:
    result = build_association_results(fixture_research_data())
    row = result.robustness_comparisons.filter(
        (pl.col("service") == "National")
        & (pl.col("predictor") == "edge_betweenness")
        & (pl.col("method") == "spearman")
    ).row(0, named=True)

    assert row["coefficient_difference"] is not None
    assert row["full_n_valid"] == 63
    assert row["sensitivity_n_valid"] == 61
    assert result.metadata["primary_outcome_extreme_count_below_minus_15"] == 4


def test_pipeline_writes_streamlit_friendly_tables_and_preserves_report_content(
    tmp_path,
) -> None:
    source = tmp_path / "research.parquet"
    report = tmp_path / "research_report.md"
    report.write_text(
        "# Unified report\n\n"
        "<!-- BEGIN GENERATED DESCRIPTIVE CONTENT -->\nPhase 3A content\n"
        "<!-- END GENERATED DESCRIPTIVE CONTENT -->\n\n"
        "Manually maintained content.\n",
        encoding="utf-8",
    )
    report_before = report.read_text(encoding="utf-8")
    fixture_research_data().write_parquet(source)

    result = run_association_analysis_pipeline(
        source,
        output_dir=tmp_path / "results",
        figure_dir=tmp_path / "figures",
        report_path=report,
    )

    assert set(result.output_paths) == {
        "correlations",
        "quantile_comparisons",
        "robustness_comparisons",
        "metadata",
        "edge_betweenness_scatter",
        "target_degree_scatter",
        "edge_betweenness_quantile_groups",
        "primary_spearman_overview",
        "report",
    }
    for name in ("correlations", "quantile_comparisons", "robustness_comparisons"):
        path = result.output_paths[name]
        assert pl.read_parquet(path).schema == getattr(result, name).schema
        assert path.is_file()
    correlation_key = ["analysis_scope", "service", "predictor", "outcome", "method"]
    assert (
        result.correlations.select(correlation_key).n_unique()
        == result.correlations.height
    )
    quantile_key = [
        "analysis_scope",
        "service",
        "predictor",
        "outcome",
        "group_label",
    ]
    assert (
        result.quantile_comparisons.select(quantile_key).n_unique()
        == result.quantile_comparisons.height
    )
    robustness_key = [
        "analysis_scope",
        "service",
        "predictor",
        "outcome",
        "method",
    ]
    assert (
        result.robustness_comparisons.select(robustness_key).n_unique()
        == result.robustness_comparisons.height
    )
    assert result.quantile_comparisons.height > 0
    assert result.robustness_comparisons.height > 0
    assert all(
        path.is_file()
        for key, path in result.output_paths.items()
        if key.endswith(("scatter", "groups", "overview"))
    )

    generated = report.read_text(encoding="utf-8")
    assert "Phase 3A content" in generated
    assert "Manually maintained content." in generated
    assert generated.startswith(report_before)
    assert "Overall est un aperçu descriptif regroupé" in generated
    assert "## 5. Association entre structure du réseau et régularité" in generated
    assert "## 6. Discussion" in generated
    assert "## 7. Conclusion et limites" in generated
    assert "Kruskal" not in generated
    assert "bootstrap" not in generated
    assert "Les p-values brutes restent disponibles" in generated
