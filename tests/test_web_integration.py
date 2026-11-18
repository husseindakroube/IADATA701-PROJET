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
