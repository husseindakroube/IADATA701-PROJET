"""Diagnostic de qualité des données mensuelles SNCF."""

from pathlib import Path

import pandas as pd

from sncf_rail_insight.preprocessing import prepare_graph_data

DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.csv")

ROUTE_COLUMNS = [
    "Date",
    "Service",
    "Gare de départ",
    "Gare d'arrivée",
]


def main() -> None:
    """Présente le dataset et contrôle la cohérence des observations."""
    raw = pd.read_csv(DATA_PATH, sep=";")
    data = prepare_graph_data(raw)

    # Description générale
    stations = pd.concat([data["departure"], data["arrival"]])
    routes = data[["departure", "arrival"]].drop_duplicates()

    print("=== DATASET SNCF ===")
    print(f"Observations : {len(raw)}")
    print(f"Colonnes : {raw.shape[1]}")
    print(f"Période : {data['date'].min():%Y-%m} -> {data['date'].max():%Y-%m}")
    print(f"Services : {data['service'].nunique()}")
    print(f"Gares : {stations.nunique()}")
    print(f"Liaisons orientées : {len(routes)}")

    # Valeurs manquantes et doublons
    missing = raw.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    print("\n=== COMPLETUDE ET DOUBLONS ===")
    print("Valeurs manquantes :")
    print(missing.to_string() if not missing.empty else "Aucune")

    print(f"\nLignes identiques : {raw.duplicated().sum()}")
    print(f"Doublons par mois/service/liaison : {raw.duplicated(ROUTE_COLUMNS).sum()}")

    # Cohérence des comptages de trains
    late_30 = raw["Nombre trains en retard > 30min"]
    late_60 = raw["Nombre trains en retard > 60min"]

    checks = {
        "Circulations prévues nulles": data["planned"] == 0,
        "Circulations prévues négatives": data["planned"] < 0,
        "Annulations négatives": data["cancelled"] < 0,
        "Annulations > circulations prévues": (data["cancelled"] > data["planned"]),
        "Aucun train circulé": data["circulated"] <= 0,
        "Retards > 15 min négatifs": data["late_15"] < 0,
        "Retards > 30 min négatifs": late_30 < 0,
        "Retards > 60 min négatifs": late_60 < 0,
        "Retards > 15 min supérieurs aux trains circulés": (
            data["late_15"] > data["circulated"]
        ),
        "Retards > 30 min supérieurs aux > 15 min": (late_30 > data["late_15"]),
        "Retards > 60 min supérieurs aux > 30 min": (late_60 > late_30),
        "Durées de trajet nulles": data["duration"] == 0,
        "Durées de trajet négatives": data["duration"] < 0,
    }

    print("\n=== CONTROLES DE COHERENCE ===")
    for description, condition in checks.items():
        print(f"{description}: {condition.sum()}")

    # Qualité de la variable cible
    valid = data["valid_target"]

    print("\n=== VARIABLE CIBLE : RETARD > 15 MIN ===")
    print(f"Observations valides : {valid.sum()}")
    print(f"Observations invalides : {(~valid).sum()}")

    delay_rate = data.loc[valid, "delay_rate_15"]

    print(f"Taux moyen de retard : {delay_rate.mean():.2%}")
    print(f"Taux médian de retard : {delay_rate.median():.2%}")
    print(f"Observations avec taux >= 80 % : {(delay_rate >= 0.8).sum()}")

    # Repérer les valeurs anormales sans les corriger
    print("\n=== ANOMALIES > 30 MIN PAR ANNEE ===")
    negative_30 = data.loc[late_30 < 0, "date"].dt.year
    print(negative_30.value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
