"""Comparaison des familles de variables sur la validation 2024."""

import pandas as pd

from sncf_rail_insight.dataset import load_ml_dataset
from sncf_rail_insight.ml.evaluation import compute_metrics
from sncf_rail_insight.ml.models import (
    BASE_FEATURES,
    EDGE_FEATURES,
    GRAPH_FEATURES,
    HISTORY_FEATURES,
    TARGET,
    build_model,
)

# Caractéristiques des gares : structurelles ou pondérées
STRUCTURAL_FEATURES = [
    feature
    for feature in GRAPH_FEATURES
    if not ("strength" in feature or "weighted_pagerank" in feature)
]

WEIGHTED_FEATURES = [
    feature for feature in GRAPH_FEATURES if feature not in STRUCTURAL_FEATURES
]

# Configurations comparées avec les mêmes hyperparamètres
FEATURE_SETS = {
    "Baseline": [],
    "Centralites structurelles": STRUCTURAL_FEATURES,
    "Centralites ponderees": WEIGHTED_FEATURES,
    "Liaisons": EDGE_FEATURES,
    "Reseau complet": GRAPH_FEATURES + EDGE_FEATURES,
    "Historique": HISTORY_FEATURES,
    "Historique + liaisons": HISTORY_FEATURES + EDGE_FEATURES,
}


def main() -> None:
    """Entraîne les configurations et compare leurs performances."""
    data = load_ml_dataset("data/raw/regularite-mensuelle-tgv-aqst.csv")

    train = data.loc[data["date"] < "2024-01-01"]
    validation = data.loc[
        (data["date"] >= "2024-01-01") & (data["date"] < "2025-01-01")
    ]

    y_train = train[TARGET]
    y_validation = validation[TARGET]

    results = []

    for name, numeric_features in FEATURE_SETS.items():
        columns = BASE_FEATURES + numeric_features

        model = build_model(numeric_features=numeric_features)
        model.fit(train[columns], y_train)

        predictions = model.predict(validation[columns]).clip(0, 1)

        results.append(
            {
                "model": name,
                **compute_metrics(
                    y_true=y_validation,
                    y_pred=predictions,
                    sample_weight=validation["circulated"],
                ),
            }
        )

    # Comparaison globale
    metrics = pd.DataFrame(results).sort_values("mae").set_index("model")

    print("=== ETUDE D'ABLATION - VALIDATION 2024 ===")
    print(metrics.round(6).to_string())


if __name__ == "__main__":
    main()
