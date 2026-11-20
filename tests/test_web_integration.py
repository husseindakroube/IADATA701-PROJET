"Tests de non-régression des limites d’intégration et des prédictions enregistrées."

import sys

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from projet_kit_data.ml.evaluation import compute_metrics
from projet_kit_data.web_data import (
    ROOT,
    filter_observations,
    load_json,
    load_table,
    validate_observations,
)

sys.path.insert(0, str(ROOT / "app"))


def test_direction_service_and_inclusive_dates():
    frame = validate_observations(load_table("data/processed/sncf.parquet"))
    row = frame.iloc[0]
    selected = filter_observations(
        frame, row.date, row.date, row.service, row.gare_depart, row.gare_arrivee
    )
    assert len(selected) == 1
    assert selected.iloc[0].gare_depart == row.gare_depart
    assert filter_observations(frame, "1900-01-01", "1900-02-01").empty


def test_duplicate_keys_are_not_silently_aggregated():
    frame = load_table("data/processed/sncf.parquet")
    with pytest.raises(ValueError, match="dupliquée"):
        validate_observations(pd.concat([frame, frame.iloc[:1]]))


def test_saved_metrics_match_same_test_rows():
    frame = load_table("data/processed/ml/baseline_predictions_test.parquet")
    saved = load_json("data/processed/ml/baseline_metrics.json")
    for name, col in [
        ("Naïf historique", "prediction_naive"),
        ("HistGradientBoosting final", "prediction_ml"),
    ]:
        actual = compute_metrics(frame.delay_rate_15, frame[col], frame.circulated)
        for metric in actual:
            assert np.isclose(actual[metric], saved[name][metric], rtol=1e-8)


@pytest.mark.parametrize(
    "page",
    [
        "main.py",
        "data_quality.py",
        "routes_network.py",
        "clusters.py",
        "predictions.py",
        "conclusions.py",
    ],
)
def test_all_pages_render(page):
    app = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    if page != "main.py":
        app.switch_page(f"pages/{page}").run()
    assert not app.exception


def test_map_selected_route_displays_details_and_monthly_evolution():
    app = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    app.switch_page("pages/routes_network.py").run()
    choice = app.selectbox(key="carte_selectbox_liaison")
    choice.select(choice.options[1]).run()
    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert "Durée moyenne" in metrics
    assert "Taux prédit (modèle A)" in metrics
    assert metrics["Durée moyenne"] != "N/A"
    assert any("Causes de retard moyennes" in item.value for item in app.markdown)


def test_ego_graph_has_separate_directional_curves_and_station_legend():
    from utils.carte import construire_ego_graphe

    fig = construire_ego_graphe("National", "ANGERS SAINT LAUD")
    routes = {trace.name: trace for trace in fig.data if trace.mode == "lines+markers"}
    outgoing, incoming = routes["Départs"], routes["Arrivées"]
    assert (outgoing.x[15], outgoing.y[15]) != (incoming.x[15], incoming.y[15])
    assert (outgoing.x[0], outgoing.y[0]) == (incoming.x[30], incoming.y[30])
    assert outgoing.marker.symbol == incoming.marker.symbol == "arrow"
    assert outgoing.marker.angleref == incoming.marker.angleref == "previous"
    stations = [trace for trace in fig.data if trace.mode == "markers"]
    assert len(stations) >= 2
    assert len({trace.marker.color for trace in stations}) == len(stations)
    assert all(trace.name and not trace.text for trace in stations)
    assert fig.layout.legend.x > 1 and fig.layout.legend.y == 1


def test_network_summary_metrics_match_saved_schema():
    from utils.data import network_summary_metrics

    summary = load_table("data/processed/graph/descriptive/network_summary.parquet")
    national = summary.loc[summary.service.eq("National")].iloc[0]
    metrics = dict(network_summary_metrics(national))

    assert metrics["Gares (nœuds)"] == 52
    assert metrics["Liaisons OD orientées"] == 116
    assert metrics["Composantes faiblement connexes"] == 1
    assert metrics["Composantes fortement connexes"] == 1
    assert metrics["Gares avec plusieurs liaisons entrantes"] == 15
    assert "Densité" not in metrics
    assert "Diamètre" not in metrics


def test_network_summary_metrics_skip_absent_optional_fields():
    from utils.data import network_summary_metrics

    metrics = dict(network_summary_metrics(pd.Series({"node_count": 3})))
    assert metrics == {"Gares (nœuds)": 3}


def test_conclusions_distinguishes_stations_from_service_memberships():
    from utils.data import network_station_counts

    summary = load_table("data/processed/graph/descriptive/network_summary.parquet")
    nodes = load_table("data/processed/graph/nodes.parquet")
    assert network_station_counts(summary, nodes) == (59, 70)


def test_centrality_summary_uses_saved_station_ranking():
    from utils.data import ranked_stations

    ranking = load_table("data/processed/graph/descriptive/node_rankings.parquet")
    leaders = ranked_stations(
        ranking,
        service="National",
        metric="betweenness_centrality",
    )
    assert leaders.station_name.tolist() == [
        "PARIS LYON",
        "PARIS MONTPARNASSE",
        "LYON PART DIEU",
    ]
    assert ranked_stations(
        pd.DataFrame(), service="National", metric="betweenness_centrality"
    ).empty


def test_ranking_validation_accepts_valid_rows_and_keeps_order():
    from utils.data import validate_rankings

    rankings = pd.DataFrame(
        [
            {
                "rank": 2,
                "service": "National",
                "ranking_metric": "pagerank",
                "station_name": "GARE B",
                "value": 0.2,
            },
            {
                "rank": 1,
                "service": "National",
                "ranking_metric": "pagerank",
                "station_name": "GARE A",
                "value": 0.5,
            },
        ]
    )
    result, warning = validate_rankings(rankings)
    assert warning is None
    assert result.station_name.tolist() == ["GARE B", "GARE A"]


def test_ranking_validation_handles_empty_and_incomplete_data():
    from utils.data import validate_rankings

    empty, empty_warning = validate_rankings(pd.DataFrame())
    incomplete, incomplete_warning = validate_rankings(
        pd.DataFrame([{"service": "National", "rank": 1}])
    )
    assert empty.empty
    assert empty_warning and "vide ou indisponible" in empty_warning
    assert incomplete.empty
    assert incomplete_warning and "champs absents" in incomplete_warning


def test_ranking_validation_excludes_missing_values_without_zero_imputation():
    from utils.data import validate_rankings

    rankings = pd.DataFrame(
        [
            {
                "rank": 1,
                "service": "National",
                "ranking_metric": "pagerank",
                "station_name": "GARE VALIDE",
                "value": 0.5,
            },
            {
                "rank": float("nan"),
                "service": "National",
                "ranking_metric": "pagerank",
                "station_name": "RANG MANQUANT",
                "value": 0.4,
            },
            {
                "rank": 3,
                "service": "National",
                "ranking_metric": "pagerank",
                "station_name": "VALEUR MANQUANTE",
                "value": float("nan"),
            },
        ]
    )
    result, warning = validate_rankings(rankings)
    assert result.station_name.tolist() == ["GARE VALIDE"]
    assert result.value.tolist() == [0.5]
    assert warning and "2 ligne(s)" in warning


def test_centrality_explanation_limits_od_graph_interpretation():
    source = (ROOT / "app/pages/routes_network.py").read_text(encoding="utf-8")
    assert "Elle ne " in source
    assert "prouve ni le passage de trains réels" in source
    assert "ne doit pas être interprétée comme zéro" in source
    assert "hubs de transit stratégiques" not in source


def test_missing_pagerank_is_shown_as_unavailable(monkeypatch):
    from utils import carte

    monkeypatch.setattr(
        carte,
        "charger_edges",
        lambda: pd.DataFrame([{"service": "National", "source": "a", "target": "b"}]),
    )
    monkeypatch.setattr(
        carte,
        "charger_nodes",
        lambda: pd.DataFrame(
            [
                {"node_id": "a", "station_name": "GARE A"},
                {"node_id": "b", "station_name": "GARE B"},
            ]
        ),
    )
    monkeypatch.setattr(
        carte,
        "charger_metriques_noeuds",
        lambda: pd.DataFrame(
            [
                {
                    "period": "overall",
                    "service": "National",
                    "station_name": station,
                    "degree": 1,
                    "betweenness_centrality": 0.25,
                    "pagerank": float("nan"),
                }
                for station in ["GARE A", "GARE B"]
            ]
        ),
    )

    figure = carte.construire_ego_graphe("National", "GARE A")
    hover_text = " ".join(
        str(text) for trace in figure.data for text in (trace.hovertext or [])
    )
    assert "PageRank : Indisponible" in hover_text
    assert "PageRank : nan" not in hover_text


def test_dependent_route_filters_and_test_month():
    app = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    app.switch_page("pages/routes_network.py").run()
    app.selectbox[0].select("International").run()
    assert not app.exception
    assert app.selectbox[3].options
    app.selectbox[3].select(app.selectbox[3].options[-1]).run()
    assert not app.exception
    app.switch_page("pages/predictions.py").run()
    app.selectbox[0].select(app.selectbox[0].options[-1]).run()
    app.selectbox[1].select(app.selectbox[1].options[-1]).run()
    assert not app.exception


def test_comparison_exports_share_test_rows_and_metrics():
    from sklearn.metrics import r2_score

    frame = load_table("data/processed/ml/comparaison_predictions_test.parquet")
    baseline = load_table("data/processed/ml/baseline_predictions_test.parquet")
    keys = ["date", "service", "departure", "arrival"]
    joined = frame.merge(
        baseline, on=keys, how="outer", validate="one_to_one", indicator=True
    )
    assert joined["_merge"].eq("both").all()
    assert np.allclose(joined.prediction_a, joined.prediction_ml)
    assert np.allclose(joined.delay_rate_15_x, joined.delay_rate_15_y)
    saved = load_json("data/processed/ml/comparaison_metrics.json")
    for name, col in zip(
        saved,
        [
            "prediction_naive",
            "prediction_a",
            "prediction_b",
            "prediction_c",
            "prediction_d",
        ],
    ):
        actual = compute_metrics(frame.delay_rate_15, frame[col], frame.circulated)
        actual["r2"] = r2_score(frame.delay_rate_15, frame[col])
        for metric, value in actual.items():
            assert np.isclose(value, saved[name][metric], rtol=1e-8)


def test_cluster_profiles_match_new_labels_and_summary():
    from projet_kit_data.comparaison import load_cluster_features

    labels = load_cluster_features(ROOT / "data/processed/clusters_liaisons.csv")
    profiles = load_table("data/processed/ml/clusters_profils.parquet")
    summary = load_table("data/processed/ml/clusters_resume.parquet")
    joined = labels.merge(
        profiles,
        left_on=["gare_a", "gare_b"],
        right_on=["gare_1", "gare_2"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    assert joined["_merge"].eq("both").all()
    assert joined.cluster_x.eq(joined.cluster_y).all()
    assert (
        profiles.groupby("cluster").size().to_dict()
        == summary.set_index("cluster").nombre_paires.to_dict()
    )
