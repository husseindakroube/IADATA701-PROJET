"""Agrege toutes les informations utiles par liaison orientee pour la page carte.

Fusionne quatre sources:
- sncf.parquet pour les statistiques observees (duree, causes de retard)
- comparaison_predictions_test.parquet pour les predictions du modele retenu
- clusters_liaisons.csv pour le cluster d'appartenance
- coordonnees_gares.csv pour tracer les lignes et zoomer

Produit data/processed/liaisons_detail.csv avec une ligne par liaison orientee.
"""

from ast import literal_eval
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_PROC = ROOT / "data" / "processed"
DATA_RAW = ROOT / "data" / "raw"

COLS_CAUSES = [
    "prct_cause_externe",
    "prct_cause_infra",
    "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant",
    "prct_cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs",
]


def charger_clusters() -> pd.DataFrame:
    """Charge les clusters et transforme la paire tuple en gares ordonnees."""
    clusters = pd.read_csv(DATA_PROC / "clusters_liaisons.csv")
    paires = clusters["paire"].apply(literal_eval)
    clusters["gare_a"] = paires.apply(lambda t: t[0])
    clusters["gare_b"] = paires.apply(lambda t: t[1])
    return clusters[["gare_a", "gare_b", "cluster"]]


def agreger_observe(sncf: pd.DataFrame) -> pd.DataFrame:
    """Agrege les observations par liaison orientee."""
    sncf = sncf.copy()
    sncf["nb_train_realise"] = sncf["nb_train_prevu"] - sncf["nb_annulation"]
    agg = sncf.groupby(["gare_depart", "gare_arrivee"]).agg(
        duree_moyenne=("duree_moyenne", "mean"),
        nb_train_prevu=("nb_train_prevu", "sum"),
        nb_train_realise=("nb_train_realise", "sum"),
        nb_train_retard_arrivee=("nb_train_retard_arrivee", "sum"),
        nb_observations=("date", "count"),
    ).reset_index()
    agg["taux_retard_observe_global"] = (
        agg["nb_train_retard_arrivee"] / agg["nb_train_realise"]
    )
    # Moyenne des causes ponderee par le nombre de retards du mois
    for col in COLS_CAUSES:
        serie = sncf.groupby(["gare_depart", "gare_arrivee"]).apply(
            lambda g: (g[col] * g["nb_train_retard_arrivee"]).sum()
            / max(g["nb_train_retard_arrivee"].sum(), 1),
            include_groups=False,
        )
        agg[col] = agg.set_index(["gare_depart", "gare_arrivee"]).index.map(serie)
    return agg


def agreger_predictions(pred: pd.DataFrame) -> pd.DataFrame:
    """Moyenne ponderee des predictions du modele A sur la periode test."""
    pred = pred.copy()
    pred["num_a"] = pred["prediction_a"] * pred["circulated"]
    pred["num_obs"] = pred["delay_rate_15"] * pred["circulated"]
    pred["num_naive"] = pred["prediction_naive"] * pred["circulated"]
    agg = pred.groupby(["departure", "arrival"]).agg(
        taux_retard_predit=("num_a", "sum"),
        taux_retard_observe_test=("num_obs", "sum"),
        taux_retard_naif=("num_naive", "sum"),
        circulated_total=("circulated", "sum"),
        service=("service", "first"),
    ).reset_index()
    for col in ["taux_retard_predit", "taux_retard_observe_test", "taux_retard_naif"]:
        agg[col] = agg[col] / agg["circulated_total"]
    agg = agg.drop(columns=["circulated_total"])
    agg = agg.rename(columns={"departure": "gare_depart", "arrival": "gare_arrivee"})
    return agg


def ajouter_cluster(liaisons: pd.DataFrame, clusters: pd.DataFrame) -> pd.DataFrame:
    """Rattache le cluster, en cherchant la paire dans les deux sens."""
    cluster_map: dict[tuple[str, str], int] = {}
    for _, row in clusters.iterrows():
        cluster_map[(row["gare_a"], row["gare_b"])] = row["cluster"]
        cluster_map[(row["gare_b"], row["gare_a"])] = row["cluster"]
    liaisons["cluster"] = liaisons.apply(
        lambda r: cluster_map.get((r["gare_depart"], r["gare_arrivee"])), axis=1
    )
    return liaisons


def main() -> None:
    sncf = pd.read_parquet(DATA_PROC / "sncf.parquet")
    pred = pd.read_parquet(DATA_PROC / "ml" / "comparaison_predictions_test.parquet")
    coords = pd.read_csv(DATA_RAW / "coordonnees_gares.csv")
    clusters = charger_clusters()

    observe = agreger_observe(sncf)
    predit = agreger_predictions(pred)

    liaisons = observe.merge(predit, on=["gare_depart", "gare_arrivee"], how="left")
    liaisons = ajouter_cluster(liaisons, clusters)

    # Rattache les coordonnees de chaque gare
    coords_dep = coords.rename(
        columns={"gare": "gare_depart", "latitude": "lat_depart", "longitude": "lon_depart"}
    )
    coords_arr = coords.rename(
        columns={"gare": "gare_arrivee", "latitude": "lat_arrivee", "longitude": "lon_arrivee"}
    )
    liaisons = liaisons.merge(coords_dep, on="gare_depart", how="left")
    liaisons = liaisons.merge(coords_arr, on="gare_arrivee", how="left")

    manquants = liaisons[liaisons["lat_depart"].isna() | liaisons["lat_arrivee"].isna()]
    if not manquants.empty:
        print("Gares sans coordonnees detectees:")
        print(manquants[["gare_depart", "gare_arrivee"]])

    sortie = DATA_PROC / "liaisons_detail.csv"
    liaisons.to_csv(sortie, index=False)
    print(f"\nEcrit {len(liaisons)} liaisons dans {sortie}")
    print(f"Avec prediction modele A: {liaisons['taux_retard_predit'].notna().sum()}")
    print(f"Avec cluster: {liaisons['cluster'].notna().sum()}")


if __name__ == "__main__":
    main()
