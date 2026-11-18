"""Regression checks for integration boundaries and saved predictions."""

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
    ["main.py", "data_quality.py", "routes_network.py", "clusters.py", "predictions.py", "conclusions.py"],
)
def test_all_pages_render(page):
    app = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    if page != "main.py":
        app.switch_page(f"pages/{page}").run()
    assert not app.exception


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
    joined = frame.merge(baseline, on=keys, how="outer", validate="one_to_one", indicator=True)
    assert joined["_merge"].eq("both").all()
    assert np.allclose(joined.prediction_a, joined.prediction_ml)
    assert np.allclose(joined.delay_rate_15_x, joined.delay_rate_15_y)
    saved = load_json("data/processed/ml/comparaison_metrics.json")
    for name, col in zip(saved, ["prediction_naive", "prediction_a", "prediction_b", "prediction_c", "prediction_d"]):
        actual = compute_metrics(frame.delay_rate_15, frame[col], frame.circulated)
        actual["r2"] = r2_score(frame.delay_rate_15, frame[col])
        for metric, value in actual.items():
            assert np.isclose(value, saved[name][metric], rtol=1e-8)


def test_cluster_profiles_match_new_labels_and_summary():
    from projet_kit_data.comparaison import load_cluster_features

    labels = load_cluster_features(ROOT / "data/processed/clusters_liaisons.csv")
    profiles = load_table("data/processed/ml/clusters_profils.parquet")
    summary = load_table("data/processed/ml/clusters_resume.parquet")
    joined = labels.merge(profiles, left_on=["gare_a", "gare_b"], right_on=["gare_1", "gare_2"], how="outer", validate="one_to_one", indicator=True)
    assert joined["_merge"].eq("both").all()
    assert joined.cluster_x.eq(joined.cluster_y).all()
    assert profiles.groupby("cluster").size().to_dict() == summary.set_index("cluster").nombre_paires.to_dict()
