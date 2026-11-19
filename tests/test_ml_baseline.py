"""Tests du modèle supervisé sans graphe et des découpages temporels."""

import numpy as np
import pandas as pd
import pytest

from projet_kit_data.ml.baseline import (
    BASELINE_FEATURES,
    build_baseline_dataset,
    chronological_split,
    predict_historical_naive,
    prepare_baseline_data,
)
from projet_kit_data.ml.models import build_model


def sample_etl(months: int = 18) -> pd.DataFrame:
    """Créer un petit historique synthétique au schéma de l'ETL."""
    dates = pd.date_range("2020-01-01", periods=months, freq="MS")
    return pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m"),
            "service": ["National"] * months,
            "gare_depart": ["PARIS"] * months,
            "gare_arrivee": ["LYON"] * months,
            "nb_train_prevu": [100] * months,
            "nb_annulation": [0] * months,
            "nb_train_retard_sup_15": [10] * months,
        }
    )


def test_validity_preserves_invalid_rows() -> None:
    """Les cibles invalides restent présentes, mais ne sont pas modélisées."""
    data = sample_etl(4)
    data.loc[0, "nb_train_prevu"] = 0
    data.loc[0, "nb_annulation"] = 3
    data.loc[1, "nb_train_retard_sup_15"] = 101
    result = prepare_baseline_data(data)
    assert result["valid_target"].tolist() == [False, False, True, True]
    assert result["delay_rate_15"].isna().sum() == 2
    assert len(result) == 4


def test_preserves_service_identity() -> None:
    """Les observations de services différents ne se confondent pas."""
    data = pd.concat([sample_etl(14), sample_etl(14).assign(service="International")])
    data.loc[data["service"] == "International", "nb_train_retard_sup_15"] = 40
    prepared = prepare_baseline_data(data)
    features = build_baseline_dataset(prepared)
    assert len(features) == 4
    rates = features.loc[features["date"] == pd.Timestamp("2021-01-01")].set_index(
        "service"
    )
    assert rates.loc["National", "historical_delay_rate_15"] == pytest.approx(0.1)
    assert rates.loc["International", "historical_delay_rate_15"] == pytest.approx(0.4)


def test_target_month_never_affects_own_features() -> None:
    """Changer le mois à prédire ne modifie pas ses prédicteurs."""
    prepared = prepare_baseline_data(sample_etl(15))
    original = build_baseline_dataset(prepared)
    changed = prepared.copy()
    month = pd.Timestamp("2021-01-01")
    changed.loc[changed["date"] == month, ["late_15", "delay_rate_15"]] = [90, 0.9]
    updated = build_baseline_dataset(changed)
    current = original.loc[original["date"] == month]
    current_updated = updated.loc[updated["date"] == month]
    pd.testing.assert_frame_equal(
        current[BASELINE_FEATURES].reset_index(drop=True),
        current_updated[BASELINE_FEATURES].reset_index(drop=True),
    )
    assert current["historical_delay_rate_15"].iloc[0] == pytest.approx(0.1)


def test_history_uses_exact_calendar_window() -> None:
    """Une observation vieille de plus de 12 mois ne contribue pas au taux."""
    data = sample_etl(15).drop(index=[1]).reset_index(drop=True)
    data.loc[data["date"] == "2020-01", "nb_train_retard_sup_15"] = 90
    prepared = prepare_baseline_data(data)
    feature = build_baseline_dataset(prepared).loc[
        lambda frame: frame["date"] == pd.Timestamp("2021-02-01")
    ]
    assert feature["historical_delay_rate_15"].iloc[0] == pytest.approx(0.1)


def test_split_months_are_disjoint() -> None:
    """Le test n'utilise aucun mois d'entraînement ou de validation."""
    frame = build_baseline_dataset(prepare_baseline_data(sample_etl(30)))
    train, validation, test = chronological_split(frame)
    assert train["date"].max() < validation["date"].min()
    assert validation["date"].max() < test["date"].min()
    assert len(train) + len(validation) + len(test) == len(frame)


def test_naive_and_model_pipeline() -> None:
    """La baseline historique et le modèle supervisé produisent un taux fini."""
    frame = build_baseline_dataset(prepare_baseline_data(sample_etl(36)))
    train, validation, _ = chronological_split(frame)
    naive = predict_historical_naive(train, validation)
    assert np.isfinite(naive).all()
    assert np.all((0 <= naive) & (naive <= 1))
    model = build_model(
        numeric_features=[
            "historical_delay_rate_15",
            "historical_circulated",
            "historical_observations",
        ],
        max_iter=5,
    )
    model.fit(train[BASELINE_FEATURES], train["delay_rate_15"])
    predictions = model.predict(validation[BASELINE_FEATURES])
    assert np.isfinite(predictions).all()


def test_invalid_dates_and_duplicate_keys_rejected() -> None:
    """Des dates incorrectes et des clés dupliquées ne sont pas acceptées."""
    invalid = sample_etl(4)
    invalid.loc[0, "date"] = "2020-13"
    with pytest.raises(ValueError, match="YYYY-MM"):
        prepare_baseline_data(invalid)
    duplicated = pd.concat([sample_etl(4), sample_etl(4).iloc[[0]]])
    with pytest.raises(ValueError, match="dupliquée"):
        prepare_baseline_data(duplicated)
