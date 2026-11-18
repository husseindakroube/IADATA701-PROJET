
"""Génération des graphiques RailInsight pour le reporting."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("outputs/streamlit")
OUTPUT_DIR = Path("outputs/reporting")


def plot_monthly_mae() -> None:
    """Compare les erreurs mensuelles des deux modèles."""
    data = pd.read_csv(
        DATA_DIR / "monthly_errors.csv",
        parse_dates=["date"],
    )

    fig, ax = plt.subplots(figsize=(11, 5))

    ax.plot(
        data["date"],
        data["mae_historical"] * 100,
        marker="o",
        label="Historique",
    )
    ax.plot(
        data["date"],
        data["mae_graph"] * 100,
        marker="o",
        label="Historique + graphe",
    )

    ax.set_title("Évolution mensuelle de la MAE")
    ax.set_ylabel("MAE (points de pourcentage)")
    ax.set_xlabel("Mois")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "monthly_mae.png", dpi=200)
    plt.close(fig)


def plot_route_predictions(
    departure: str = "PARIS EST",
    arrival: str = "STUTTGART",
) -> None:
    """Compare les prédictions aux retards réels sur une liaison."""
    data = pd.read_csv(
        DATA_DIR / "predictions.csv",
        parse_dates=["date"],
    )

    route = data.loc[
        (data["departure"] == departure)
        & (data["arrival"] == arrival)
    ].sort_values("date")

    if route.empty:
        raise ValueError(f"Liaison introuvable : {departure} -> {arrival}")

    fig, ax = plt.subplots(figsize=(11, 5))

    for column, label in [
        ("actual", "Réel"),
        ("pred_historical", "Historique"),
        ("pred_graph", "Historique + graphe"),
    ]:
        ax.plot(
            route["date"],
            route[column] * 100,
            marker="o",
            label=label,
        )

    ax.set_title(f"Taux de retard : {departure} → {arrival}")
    ax.set_xlabel("Mois")
    ax.set_ylabel("Trains en retard > 15 min (%)")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "stuttgart_predictions.png", dpi=200)
    plt.close(fig)


def plot_route_gains() -> None:
    """Affiche les dix liaisons les plus améliorées par le graphe."""
    data = pd.read_csv(DATA_DIR / "route_errors.csv")

    top = data.nlargest(10, "mae_gain").copy()
    top["route"] = top["departure"] + " → " + top["arrival"]
    top = top.sort_values("mae_gain")

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.barh(top["route"], top["mae_gain"] * 100)

    ax.set_title("Top 10 des liaisons améliorées par le graphe")
    ax.set_xlabel("Réduction de MAE (points de pourcentage)")
    ax.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "route_gains.png", dpi=200)
    plt.close(fig)


def plot_delay_bias() -> None:
    """Compare les biais selon le niveau de retard observé."""
    data = pd.read_csv(DATA_DIR / "delay_level_errors.csv")

    positions = range(len(data))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(
        [x - width / 2 for x in positions],
        data["bias_historical"] * 100,
        width=width,
        label="Historique",
    )
    ax.bar(
        [x + width / 2 for x in positions],
        data["bias_graph"] * 100,
        width=width,
        label="Historique + graphe",
    )

    ax.set_xticks(list(positions), data["delay_level"])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Biais selon le taux de retard réel")
    ax.set_xlabel("Taux de retard réel")
    ax.set_ylabel("Biais moyen (points de pourcentage)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "delay_bias.png", dpi=200)
    plt.close(fig)


def main() -> None:
    """Génère les quatre graphiques à partir des exports CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    plot_monthly_mae()
    plot_route_predictions()
    plot_route_gains()
    plot_delay_bias()

    print("=== GRAPHIQUES GENERES ===")
    for path in sorted(OUTPUT_DIR.glob("*.png")):
        print(path)


if __name__ == "__main__":
    main()
