
"""Export des prédictions pour analyser les performances des modèles."""

from pathlib import Path

import pandas as pd

from sncf_rail_insight.dataset import load_ml_dataset
from sncf_rail_insight.ml.models import (
    BASE_FEATURES,
    EDGE_FEATURES,
    HISTORY_FEATURES,
    TARGET,
    build_model,
)

DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.csv")
OUTPUT_PATH = Path("data/processed/predictions.csv")

MODEL_CONFIGS = {
    "historical": {
        "features": HISTORY_FEATURES,
        "max_iter": 100,
        "learning_rate": 0.03,
        "max_leaf_nodes": 7,
    },
    "graph": {
        "features": HISTORY_FEATURES + EDGE_FEATURES,
        "max_iter": 150,
        "learning_rate": 0.05,
        "max_leaf_nodes": 7,
    },
}

def analyze_monthly_errors(predictions: pd.DataFrame) -> pd.DataFrame:
    """Calcule les performances mensuelles des deux modèles."""
    monthly = (
        predictions.groupby("date")
        .agg(
            observations=("actual", "size"),
            actual_rate=("actual", "mean"),
            mae_historical=("error_historical", "mean"),
            mae_graph=("error_graph", "mean"),
        )
        .reset_index()
    )

    # Valeur positive = amélioration apportée par le graphe.
    monthly["mae_gain"] = (
        monthly["mae_historical"] - monthly["mae_graph"]
    )

    return monthly

def analyze_route_errors(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compare les erreurs des modèles pour chaque liaison orientée."""
    routes = (
        predictions.groupby(["departure", "arrival"])
        .agg(
            observations=("actual", "size"),
            circulated=("circulated", "sum"),
            actual_rate=("actual", "mean"),
            mae_historical=("error_historical", "mean"),
            mae_graph=("error_graph", "mean"),
        )
        .reset_index()
    )

    routes["mae_gain"] = (
        routes["mae_historical"] - routes["mae_graph"]
    )

    return routes.sort_values("mae_gain", ascending=False)


def inspect_routes(predictions: pd.DataFrame) -> None:
    """Affiche les prédictions mensuelles de quelques liaisons."""
    routes = [
        ("PARIS EST", "STUTTGART"),
        ("PARIS LYON", "ITALIE"),
        ("LYON PART DIEU", "LILLE"),
    ]

    for departure, arrival in routes:
        subset = predictions.loc[
            (predictions["departure"] == departure)
            & (predictions["arrival"] == arrival),
            [
                "date",
                "service",
                "actual",
                "pred_historical",
                "pred_graph",
            ],
        ].sort_values("date")

        print(f"\n=== {departure} -> {arrival} ===")
        print(subset.to_string(index=False))

def analyze_errors_by_delay_level(predictions: pd.DataFrame) -> pd.DataFrame:
    """Analyse les erreurs selon le taux de retard réellement observé."""
    data = predictions.copy()

    data["delay_level"] = pd.cut(
        data["actual"],
        bins=[-0.001, 0.1, 0.2, 0.3, 0.5, 1.0],
        labels=["0-10 %", "10-20 %", "20-30 %", "30-50 %", "50-100 %"],
    )

    data["bias_historical"] = data["pred_historical"] - data["actual"]
    data["bias_graph"] = data["pred_graph"] - data["actual"]

    results = (
        data.groupby("delay_level", observed=True)
        .agg(
            observations=("actual", "size"),
            actual_rate=("actual", "mean"),
            mae_historical=("error_historical", "mean"),
            mae_graph=("error_graph", "mean"),
            bias_historical=("bias_historical", "mean"),
            bias_graph=("bias_graph", "mean"),
        )
        .reset_index()
    )

    results["mae_gain"] = (
        results["mae_historical"] - results["mae_graph"]
    )

    return results

def main() -> None:
    """Entraîne les modèles finaux et exporte leurs prédictions."""
    data = load_ml_dataset(DATA_PATH)

    train = data.loc[data["date"] < "2025-01-01"]
    test = data.loc[data["date"] >= "2025-01-01"]

    predictions = test[
        ["date", "service", "departure", "arrival", "circulated"]
    ].copy()

    predictions["actual"] = test[TARGET]

    for name, config in MODEL_CONFIGS.items():
        features = BASE_FEATURES + config["features"]

        model = build_model(
            numeric_features=config["features"],
            max_iter=config["max_iter"],
            learning_rate=config["learning_rate"],
            max_leaf_nodes=config["max_leaf_nodes"],
        )

        model.fit(train[features], train[TARGET])
        predictions[f"pred_{name}"] = model.predict(test[features])

        predictions[f"error_{name}"] = (
            predictions["actual"] - predictions[f"pred_{name}"]
        ).abs()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(OUTPUT_PATH, index=False)

    print("=== EXPORT DES PREDICTIONS ===")
    print(f"Train : {len(train)} observations")
    print(f"Test : {len(test)} observations")
    print(f"Fichier : {OUTPUT_PATH}")

    print("\n=== MAE PAR MODELE ===")
    for name in MODEL_CONFIGS:
        mae = predictions[f"error_{name}"].mean()
        print(f"{name}: {mae:.8f}")

    print("\n=== APERCU ===")
    print(predictions.head().to_string(index=False))

    monthly = analyze_monthly_errors(predictions)

    monthly_path = Path("data/processed/monthly_errors.csv")
    monthly.to_csv(monthly_path, index=False)

    print("\n=== PERFORMANCES MENSUELLES ===")
    print(monthly.to_string(index=False))

    print(
        "\nMois où le graphe améliore la MAE :",
        (monthly["mae_gain"] > 0).sum(),
        "/",
        len(monthly),
    )

    routes = analyze_route_errors(predictions)

    routes_path = Path("data/processed/route_errors.csv")
    routes.to_csv(routes_path, index=False)

    print("\n=== TOP 10 DES LIAISONS LES PLUS AMELIOREES ===")
    print(routes.head(10).to_string(index=False))

    print("\n=== TOP 10 DES LIAISONS LES PLUS DEGRADEES ===")
    print(routes.tail(10).to_string(index=False))

    print(
        "\nLiaisons où le graphe améliore la MAE :",
        (routes["mae_gain"] > 0).sum(),
        "/",
        len(routes),
    )

    inspect_routes(predictions)

    delay_levels = analyze_errors_by_delay_level(predictions)

    delay_levels.to_csv(
        "data/processed/delay_level_errors.csv",
        index=False,
    )

    print("\n=== ERREURS PAR NIVEAU DE RETARD ===")
    print(delay_levels.to_string(index=False))


if __name__ == "__main__":
    main()
