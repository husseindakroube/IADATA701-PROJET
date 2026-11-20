"""Tests ciblés des vues Streamlit des résultats Phase 3B."""

import pandas as pd
import pytest

from projet_kit_data.web_data import ROOT, load_table
from utils.association_views import (
    CORRELATION_COLUMNS,
    QUANTILE_COLUMNS,
    ROBUSTNESS_COLUMNS,
    filter_correlations,
    filter_quantiles,
    filter_robustness,
    validate_result_table,
)

PHASE3B = "data/processed/graph/phase3b"


def test_result_table_validation_handles_empty_and_missing_columns():
    empty, empty_message = validate_result_table(
        pd.DataFrame(), CORRELATION_COLUMNS, "Corrélations"
    )
    invalid, invalid_message = validate_result_table(
        pd.DataFrame([{"service": "National"}]),
        CORRELATION_COLUMNS,
        "Corrélations",
    )

    assert empty.empty
    assert empty_message and "vide ou indisponible" in empty_message
    assert invalid.empty
    assert invalid_message and "champs absents" in invalid_message


def test_correlation_filters_match_saved_overall_result():
    frame = load_table(f"{PHASE3B}/correlations.parquet")
    selected = filter_correlations(
        frame,
        "Ensemble (Overall)",
        "spearman",
        "edge_betweenness",
        "retard_moyen_tous_trains_arrivee",
    )

    saved = frame.loc[
        frame.analysis_scope.eq("overall")
        & frame.service.eq("Overall")
        & frame.method.eq("spearman")
        & frame.predictor.eq("edge_betweenness")
        & frame.outcome.eq("retard_moyen_tous_trains_arrivee")
    ]
    assert len(selected) == 1
    assert selected.iloc[0].to_dict() == saved.iloc[0].to_dict()
    assert selected.iloc[0].n_valid == 12907
    assert selected.iloc[0].service == "Overall"


def test_correlation_interpretation_values_match_saved_results():
    frame = load_table(f"{PHASE3B}/correlations.parquet")
    strongest = frame.loc[frame.coefficient.abs().idxmax()]

    assert frame.coefficient.min() == pytest.approx(-0.22721930772560808)
    assert frame.coefficient.max() == pytest.approx(0.18703088627434145)
    assert strongest.service == "International"
    assert strongest.predictor == "edge_betweenness"
    assert strongest.outcome == "cancellation_rate"
    assert strongest.method == "spearman"
    assert strongest.n_valid == 1541


def test_correlation_patterns_support_the_page_synthesis():
    frame = load_table(f"{PHASE3B}/correlations.parquet")
    paired = frame.pivot_table(
        index=["analysis_scope", "service", "predictor", "outcome"],
        columns="method",
        values="coefficient",
    ).dropna()
    winners = frame.loc[
        frame.groupby(["service", "outcome", "method"])["coefficient"].apply(
            lambda values: values.abs().idxmax()
        )
    ]
    service_maxima = frame.loc[
        frame.groupby("service")["coefficient"].apply(
            lambda values: values.abs().idxmax()
        )
    ].set_index("service")

    assert len(frame) == 126
    assert int((paired.pearson * paired.spearman >= 0).sum()) == 57
    assert winners.predictor.eq("edge_betweenness").sum() == 5
    assert len(winners) == 18
    assert service_maxima.loc["International"].coefficient == pytest.approx(
        -0.2272193077
    )
    assert service_maxima.loc["National"].coefficient == pytest.approx(0.1588463071)
    assert service_maxima.loc["Overall"].coefficient == pytest.approx(0.1170636571)


def test_quantile_filter_keeps_original_groups_and_artifact_statistics():
    frame = load_table(f"{PHASE3B}/quantile_comparisons.parquet")
    selected = filter_quantiles(
        frame,
        "International",
        "source_betweenness_centrality",
        "retard_moyen_tous_trains_arrivee",
    )

    assert set(selected.group_label) == {
        "Zero",
        "Positive Q1",
        "Positive Q2",
        "Positive Q3",
        "Positive Q4",
    }
    assert selected.n.nunique() > 1
    assert selected.grouping_strategy.eq("zero_plus_tie_preserving_quantiles").all()
    saved_zero = frame.loc[
        frame.analysis_scope.eq("service")
        & frame.service.eq("International")
        & frame.predictor.eq("source_betweenness_centrality")
        & frame.outcome.eq("retard_moyen_tous_trains_arrivee")
        & frame.group_label.eq("Zero")
    ].iloc[0]
    zero = selected.loc[selected.group_label.eq("Zero")].iloc[0]
    assert zero.n == saved_zero.n
    assert zero["median"] == saved_zero["median"]
    assert zero["q25"] == saved_zero["q25"]
    assert zero["q75"] == saved_zero["q75"]


def test_default_quantile_pattern_is_irregular_in_saved_results():
    frame = load_table(f"{PHASE3B}/quantile_comparisons.parquet")
    selected = (
        filter_quantiles(
            frame,
            "Ensemble (Overall)",
            "edge_betweenness",
            "retard_moyen_tous_trains_arrivee",
        )
        .set_index("group_label")
        .loc[["Q1", "Q2", "Q3", "Q4"]]
    )

    assert selected["median"].tolist() == pytest.approx(
        [6.790929928, 4.624158109, 8.7078430555, 5.7332918804972515]
    )
    assert selected["n"].tolist() == [3357, 5726, 596, 3228]


def test_quantile_synthesis_counts_irregular_medians_and_overlapping_iqrs():
    frame = load_table(f"{PHASE3B}/quantile_comparisons.parquet")
    families = [
        ["Q1", "Q2", "Q3", "Q4"],
        ["Positive Q1", "Positive Q2", "Positive Q3", "Positive Q4"],
    ]
    sequences = monotonic = overlaps = adjacent_pairs = 0

    for _, group in frame.groupby(["service", "predictor", "outcome"]):
        for family in families:
            labels = [label for label in family if label in set(group.group_label)]
            if len(labels) < 2:
                continue
            ordered = group.set_index("group_label").reindex(labels)
            medians = ordered["median"].tolist()
            sequences += 1
            monotonic += int(
                all(a <= b for a, b in zip(medians, medians[1:]))
                or all(a >= b for a, b in zip(medians, medians[1:]))
            )
            for (_, left), (_, right) in zip(
                ordered.iloc[:-1].iterrows(), ordered.iloc[1:].iterrows()
            ):
                adjacent_pairs += 1
                overlaps += int(max(left.q25, right.q25) <= min(left.q75, right.q75))

    assert sequences == 63
    assert monotonic == 4
    assert overlaps == 185
    assert adjacent_pairs == 189


def test_robustness_filter_uses_saved_coefficients_and_sample_sizes():
    frame = load_table(f"{PHASE3B}/robustness_comparisons.parquet")
    selected = filter_robustness(
        frame,
        "International",
        "pearson",
        "target_betweenness_centrality",
    )

    assert len(selected) == 1
    row = selected.iloc[0]
    assert row.outcome == "retard_moyen_tous_trains_arrivee"
    assert row.full_n_valid == 1568
    assert row.sensitivity_n_valid == 1567
    assert row.coefficient_difference == pytest.approx(
        row.sensitivity_coefficient - row.full_coefficient
    )
    assert "p_value" not in selected.columns
    assert not ROBUSTNESS_COLUMNS.intersection({"p_value"})
    assert CORRELATION_COLUMNS.issubset(
        load_table(f"{PHASE3B}/correlations.parquet").columns
    )
    assert QUANTILE_COLUMNS.issubset(
        load_table(f"{PHASE3B}/quantile_comparisons.parquet").columns
    )


def test_robustness_summary_facts_match_saved_results():
    frame = load_table(f"{PHASE3B}/robustness_comparisons.parquet")
    differences = frame.coefficient_difference.abs()
    sign_changes = frame.loc[frame.full_coefficient * frame.sensitivity_coefficient < 0]

    assert differences.median() == pytest.approx(0.0033253871100980825)
    assert differences.max() == pytest.approx(0.05483201286024742)
    assert len(sign_changes) == 1
    assert sign_changes.iloc[0].service == "International"
    assert sign_changes.iloc[0].predictor == "target_betweenness_centrality"
    assert (differences <= 0.01).sum() == 23
    largest = frame.loc[differences.idxmax()]
    assert largest.service == "National"
    assert largest.predictor == "source_pagerank"
    assert largest.full_coefficient == pytest.approx(-0.0518542293)
    assert largest.sensitivity_coefficient == pytest.approx(-0.1066862422)


def test_navigation_and_network_content_are_migrated():
    app_source = (ROOT / "app/app.py").read_text(encoding="utf-8")
    route_source = (ROOT / "app/pages/routes_network.py").read_text(encoding="utf-8")
    page_source = (ROOT / "app/pages/association_analysis.py").read_text(
        encoding="utf-8"
    )

    page_titles = [
        'title="Accueil"',
        'title="Qualité des données"',
        'title="Liaisons et réseau"',
        'title="Structure et régularité"',
        'title="Profils et clusters"',
        'title="Prédictions"',
        'title="Conclusions"',
    ]
    positions = [app_source.index(title) for title in page_titles]
    assert positions == sorted(positions)
    assert "Comprendre le réseau" not in route_source
    assert '"Carte interactive"' in route_source
    assert '"Explorer une liaison"' in route_source
    assert '"Comparer deux liaisons"' in route_source
    assert '"Structure du réseau"' in page_source
    assert '"Corrélations"' in page_source
    assert '"Comparaison par quantiles"' in page_source
    assert '"Robustesse"' in page_source
    tabs_start = page_source.index("structure_tab, correlations_tab")
    tabs_end = page_source.index("with structure_tab:", tabs_start)
    tab_definition = page_source[tabs_start:tabs_end]
    tab_labels = [
        '"Structure du réseau"',
        '"Corrélations"',
        '"Comparaison par quantiles"',
        '"Robustesse"',
        '"Synthèse"',
    ]
    tab_positions = [tab_definition.index(label) for label in tab_labels]
    assert tab_positions == sorted(tab_positions)
    assert "_render_network_structure()" in page_source
    assert "_render_synthesis()" in page_source
    assert "run_association_analysis_pipeline" not in page_source


def test_synthesis_contains_the_research_answer_and_verified_evidence():
    page_source = (ROOT / "app/pages/association_analysis.py").read_text(
        encoding="utf-8"
    )
    handover = (ROOT / "docs/streamlit_handover.md").read_text(encoding="utf-8")

    assert "_render_synthesis" in page_source
    assert "Réponse à la question de recherche" in page_source
    assert "59 gares distinctes" in page_source
    assert "de 6,79, 4,62, 8,71 et 5,73 minutes" in page_source
    assert "différence absolue médiane" in page_source
    assert "différence absolue maximale : 0,0548" in page_source
    assert "cinq onglets" in handover
    assert "ne remplace pas la page globale **Conclusions**" in handover


def test_synthesis_network_facts_match_saved_graph_artifacts():
    network = load_table("data/processed/graph/descriptive/network_summary.parquet")
    nodes = load_table("data/processed/graph/nodes.parquet")
    edges = load_table("data/processed/graph/edges.parquet")
    rankings = load_table("data/processed/graph/descriptive/node_rankings.parquet")
    monthly = load_table("data/processed/graph/descriptive/monthly_summary.parquet")

    assert nodes.node_id.nunique() == 59
    assert edges.edge_id.nunique() == 146
    assert network.node_count.sum() == 70
    assert network.set_index("service").loc["National", "node_count"] == 52
    assert network.set_index("service").loc["National", "edge_count"] == 116
    international = network.set_index("service").loc["International"]
    assert international.node_count == 18
    assert international.edge_count == 30
    assert international.weakly_connected_components == 3
    assert international.largest_weak_component == 11
    leaders = rankings.loc[
        rankings["rank"].eq(1)
        & rankings.ranking_metric.isin(
            ["connectivity_degree", "betweenness_centrality", "pagerank"]
        )
    ]
    assert (
        leaders.groupby("service")
        .station_name.apply(lambda names: names.eq("PARIS LYON").all())
        .all()
    )

    intl_months = monthly.loc[
        monthly.service.eq("International")
        & monthly.period.isin(["2025-06", "2025-07", "2025-10"])
    ].set_index("period")
    assert intl_months.loc["2025-06", ["node_count", "edge_count"]].tolist() == [9, 14]
    assert intl_months.loc["2025-07", ["node_count", "edge_count"]].tolist() == [17, 28]
    assert intl_months.loc["2025-10", ["node_count", "edge_count"]].tolist() == [8, 12]
