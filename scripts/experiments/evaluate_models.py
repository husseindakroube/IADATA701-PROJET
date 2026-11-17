"""Évalue les modèles sélectionnés sur la période test 2025–2026."""
    
from sncf_rail_insight.dataset import load_ml_dataset
from sncf_rail_insight.ml.evaluation import compute_metrics
from sncf_rail_insight.ml.models import (
    BASE_FEATURES,
    EDGE_FEATURES,
    HISTORY_FEATURES,
    TARGET,
    build_model,
)

# Hyperparamètres sélectionnés sur la validation 2024 (MAE minimale).
MODEL_CONFIGS = {
    "Historique": {
        "numeric_features": HISTORY_FEATURES,
        "max_iter": 100,
        "learning_rate": 0.03,
        "max_leaf_nodes": 7,
    },
    "Historique + liaisons": {
        "numeric_features": HISTORY_FEATURES + EDGE_FEATURES,
        "max_iter": 150,
        "learning_rate": 0.05,
        "max_leaf_nodes": 7,
    },
}

def main() -> None:
    """Réentraîne sur 2019–2024 et évalue sur janvier 2025–septembre 2026."""
    data = load_ml_dataset("data/raw/regularite-mensuelle-tgv-aqst.csv")

    train = data.loc[data["date"] < "2025-01-01"]
    test = data.loc[data["date"] >= "2025-01-01"]

    print("=== EVALUATION FINALE 2025-2026 ===")
    print(f"Train : {len(train)} observations")
    print(f"Test  : {len(test)} observations")

    for name, config in MODEL_CONFIGS.items():
        numeric_features = config["numeric_features"]
        columns = BASE_FEATURES + numeric_features

        model = build_model(
            numeric_features=numeric_features,
            max_iter=config["max_iter"],
            learning_rate=config["learning_rate"],
            max_leaf_nodes=config["max_leaf_nodes"],
        )
        model.fit(train[columns], train[TARGET])
        predictions = model.predict(test[columns]).clip(0, 1)

        metrics = compute_metrics(
            y_true=test[TARGET],
            y_pred=predictions,
            sample_weight=test["circulated"],
        )

        print(f"\n{name}")
        print(f"MAE          : {metrics['mae']:.8f}")
        print(f"RMSE         : {metrics['rmse']:.8f}")
        print(f"MAE pondérée : {metrics['weighted_mae']:.8f}")


if __name__ == "__main__":
    main()