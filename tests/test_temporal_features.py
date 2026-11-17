"""Tests des caractéristiques historiques et temporelles."""

import pandas as pd
from pandas.testing import assert_frame_equal

from sncf_rail_insight.ml.historical import (
    compute_historical_delay_features,
)
from sncf_rail_insight.ml.temporal import (
    build_temporal_graph_dataset,
)


def test_historical_delay_rate() -> None:
    """Vérifie le calcul du taux historique pondéré par les circulations."""
    history = pd.DataFrame(
        {
            "departure": ["A", "A"],
            "arrival": ["B", "B"],
            "circulated": [100, 300],
            "late_15": [10, 60],
            "valid_target": [True, True],
        }
    )

    result = compute_historical_delay_features(history)

    assert len(result) == 1
    assert result.iloc[0]["historical_delay_rate_15"] == 70 / 400


def test_current_month_excluded_from_history() -> None:
    """Vérifie que le mois courant n'influence aucune variable historique."""
    months = pd.date_range("2020-01-01", periods=14, freq="MS")

    data = pd.DataFrame(
        {
            "date": months,
            "service": ["National"] * len(months),
            "departure": ["A"] * len(months),
            "arrival": ["B"] * len(months),
            "planned": [100] * len(months),
            "cancelled": [0] * len(months),
            "circulated": [100] * len(months),
            "late_15": [10] * len(months),
            "valid_target": [True] * len(months),
            "delay_rate_15": [0.1] * len(months),
        }
    )

    original = build_temporal_graph_dataset(data, window_months=12)

    # Modifier fortement les données de janvier 2021.
    target_month = pd.Timestamp("2021-01-01")
    modified = data.copy()
    mask = modified["date"] == target_month

    modified.loc[mask, "planned"] = 1000
    modified.loc[mask, "circulated"] = 1000
    modified.loc[mask, "late_15"] = 900
    modified.loc[mask, "delay_rate_15"] = 0.9

    updated = build_temporal_graph_dataset(modified, window_months=12)

    # Exclure les données du mois courant et ne comparer que les
    # caractéristiques calculées à partir de l'historique.
    current_columns = {
        "date",
        "service",
        "departure",
        "arrival",
        "planned",
        "cancelled",
        "circulated",
        "late_15",
        "valid_target",
        "delay_rate_15",
    }

    feature_columns = [
        column
        for column in original.columns
        if column not in current_columns
    ]

    original_features = original.loc[
        original["date"] == target_month, feature_columns
    ].reset_index(drop=True)

    updated_features = updated.loc[
        updated["date"] == target_month, feature_columns
    ].reset_index(drop=True)

    assert_frame_equal(original_features, updated_features)

    # Contrôle explicite du taux historique attendu.
    assert original_features["historical_delay_rate_15"].iloc[0] == 0.1
