"""Recherche d'hyperparamètres sur la validation chronologique 2024."""

from itertools import product

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

PARAM_GRID = {
    "max_iter": [100, 150, 250],
    "learning_rate": [0.03, 0.05, 0.1],
    "max_leaf_nodes": [7, 15, 31],
}

FEATURE_SETS = {
    "Historique": HISTORY_FEATURES,
    "Historique + liaisons": HISTORY_FEATURES + EDGE_FEATURES,
}


def main() -> None:
    """Compare les configurations sur 2024, sans utiliser le jeu de test."""
    data = load_ml_dataset("data/raw/regularite-mensuelle-tgv-aqst.csv")

    train = data.loc[data["date"] < "2024-01-01"]
    validation = data.loc[
        (data["date"] >= "2024-01-01") & (data["date"] < "2025-01-01")
    ]

    y_train = train[TARGET]
    y_validation = validation[TARGET]

    for name, numeric_features in FEATURE_SETS.items():
        print(f"\n=== OPTIMISATION : {name} ===")
        columns = BASE_FEATURES + numeric_features
        results = []

        for max_iter, learning_rate, max_leaf_nodes in product(
            PARAM_GRID["max_iter"],
            PARAM_GRID["learning_rate"],
            PARAM_GRID["max_leaf_nodes"],
        ):
            model = build_model(
                numeric_features=numeric_features,
                max_iter=max_iter,
                learning_rate=learning_rate,
                max_leaf_nodes=max_leaf_nodes,
            )

            model.fit(train[columns], y_train)
            predictions = model.predict(validation[columns]).clip(0, 1)

            results.append(
                {
                    "max_iter": max_iter,
                    "learning_rate": learning_rate,
                    "max_leaf_nodes": max_leaf_nodes,
                    **compute_metrics(
                        y_true=y_validation,
                        y_pred=predictions,
                        sample_weight=validation["circulated"],
                    ),
                }
            )

        results_df = pd.DataFrame(results).sort_values("mae")

        print("\nTop 5 configurations selon la MAE :")
        print(results_df.head(5).to_string(index=False))

        print("\nMeilleure configuration selon la RMSE :")
        print(results_df.nsmallest(1, "rmse").to_string(index=False))

        print("\nMeilleure configuration selon la MAE pondérée :")
        print(results_df.nsmallest(1, "weighted_mae").to_string(index=False))


if __name__ == "__main__":
    main()
