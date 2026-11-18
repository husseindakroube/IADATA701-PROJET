
"""Comparaison de différentes caractéristiques historiques de ponctualité."""

import pandas as pd

from sncf_rail_insight.dataset import load_ml_dataset
from sncf_rail_insight.ml.evaluation import compute_metrics
from sncf_rail_insight.ml.models import (
    BASE_FEATURES,
    EDGE_FEATURES,
    HISTORY_FEATURES,
    TARGET,
    build_model,
)

DATA_PATH = "data/raw/regularite-mensuelle-tgv-aqst.csv"

FEATURE_SETS = {
    "Historique + liaisons": HISTORY_FEATURES + EDGE_FEATURES,
    "Avec taux recent": HISTORY_FEATURES + EDGE_FEATURES + [
        "recent_delay_rate_15"
    ],
    "Avec taux recent + tendance": HISTORY_FEATURES + EDGE_FEATURES + [
        "recent_delay_rate_15",
        "delay_rate_trend_15",
    ],
}

def main() -> None:
    """Compare les variables historiques sur la validation 2024."""
    data = load_ml_dataset(DATA_PATH, recent_window_months=3)

    train = data.loc[data["date"] < "2024-01-01"]
    validation = data.loc[
        (data["date"] >= "2024-01-01")
        & (data["date"] < "2025-01-01")
    ]

    results = []

    for name, numeric_features in FEATURE_SETS.items():
        features = BASE_FEATURES + numeric_features

        model = build_model(
            numeric_features=numeric_features,
            max_iter=150,
            learning_rate=0.05,
            max_leaf_nodes=7,
        )

        model.fit(train[features], train[TARGET])
        predictions = model.predict(validation[features])

        metrics = compute_metrics(
            validation[TARGET],
            predictions,
            sample_weight=validation["circulated"],
        )

        results.append({"model": name, **metrics})

    results_df = pd.DataFrame(results).sort_values("mae")

    print("=== COMPARAISON DES VARIABLES HISTORIQUES ===")
    print(f"Train : {len(train)} observations")
    print(f"Validation : {len(validation)} observations")
    print(results_df.to_string(index=False))

    print("\n=== BASELINES NAÏVES ===")
    baseline_features = {
        "Naïf 12 mois": "historical_delay_rate_15",
        "Naïf 3 mois": "recent_delay_rate_15",
    }

    # Repli calculé uniquement sur l'entraînement si une liaison ne possède pas de taux historique.
    fallback_rate = train["late_15"].sum() / train["circulated"].sum()

    for name, feature in baseline_features.items():
        predictions = validation[feature].fillna(fallback_rate)

        metrics = compute_metrics(
            validation[TARGET],
            predictions,
            sample_weight=validation["circulated"],
        )

        print(
            f"{name:15s} | "
            f"MAE : {metrics['mae']:.6f} | "
            f"RMSE : {metrics['rmse']:.6f} | "
            f"MAE pondérée : {metrics['weighted_mae']:.6f}"
        )


if __name__ == "__main__":
    main()
