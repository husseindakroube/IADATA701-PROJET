"""Comparaison de modèles de prédiction du taux de retard avec différents jeux de features."""

from pathlib import Path
import pandas as pd
from projet_kit_data.ml.models import build_model


def load_cluster_features(path: str | Path) -> pd.DataFrame:
    """Charge la correspondance liaison -> cluster depuis le CSV du notebook 04.

    Args:
        path: chemin vers le CSV des clusters.

    Returns:
        DataFrame indexé par la paire de gares, avec une colonne cluster.
    """
    clusters = pd.read_csv(path)
    # la colonne paire est stockée comme une chaîne, on la décompose en deux colonnes
    clusters[["gare_a", "gare_b"]] = (
        clusters["paire"]
        .str.strip("()")
        .str.replace("'", "", regex=False)
        .str.split(", ", expand=True)
    )
    return clusters[["gare_a", "gare_b", "cluster"]]


def add_cluster_to_dataset(data: pd.DataFrame, clusters: pd.DataFrame) -> pd.DataFrame:
    """Ajoute le numéro de cluster à chaque observation du dataset ML.

    La jointure est faite sur la paire de gares (ordre alphabétique).
    Les observations sans cluster correspondant gardent une valeur NaN.
    """
    enrichi = data.copy()
    enrichi["gare_a"] = enrichi[["departure", "arrival"]].min(axis=1)
    enrichi["gare_b"] = enrichi[["departure", "arrival"]].max(axis=1)

    enrichi = enrichi.merge(clusters, on=["gare_a", "gare_b"], how="left")
    return enrichi.drop(columns=["gare_a", "gare_b"])


def train_and_evaluate(
    train: pd.DataFrame,
    test: pd.DataFrame,
    base_features: list[str],
    extra_features: list[str],
    target: str,
    name: str,
) -> dict:
    """Entraîne un modèle avec le jeu de features fourni et évalue sur le test.

    Args:
        train: observations d'entraînement.
        test: observations de test.
        base_features: variables de base (service, departure, arrival, month).
        extra_features: variables numériques supplémentaires (graphe, cluster, etc.).
        target: nom de la colonne cible.
        name: nom lisible du modèle pour l'affichage.

    Returns:
        Dictionnaire avec le nom, les métriques (MAE, RMSE) et le modèle entraîné.
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    columns = base_features + extra_features
    modele = build_model(numeric_features=extra_features)

    modele.fit(train[columns], train[target])
    predictions = modele.predict(test[columns])

    return {
        "modele": name,
        "mae": mean_absolute_error(test[target], predictions),
        "rmse": mean_squared_error(test[target], predictions) ** 0.5,
        "modele_entraine": modele,
    }


def format_comparison_table(results: list[dict]) -> pd.DataFrame:
    """Formate les résultats des modèles en un tableau comparatif trié par MAE."""
    tableau = pd.DataFrame([
        {"modele": r["modele"], "mae": r["mae"], "rmse": r["rmse"]}
        for r in results
    ])
    return tableau.sort_values("mae").reset_index(drop=True)


def compute_errors_by_group(
    model: object,
    test: pd.DataFrame,
    columns: list[str],
    target: str,
    group_column: str,
) -> pd.Series:
    """Calcule la MAE par groupe (cluster, service, etc.) pour un modèle entraîné.

    Args:
        model: le modèle entraîné.
        test: les données de test.
        columns: les colonnes utilisées pour la prédiction.
        target: le nom de la colonne cible.
        group_column: le nom de la colonne qui définit les groupes.

    Returns:
        Série indexée par le groupe, avec la MAE en points de pourcentage.
    """
    predictions = model.predict(test[columns])
    erreurs = pd.DataFrame({
        "cible": test[target].to_numpy(),
        "prediction": predictions,
        "groupe": test[group_column].to_numpy(),
    })
    erreurs["abs_erreur"] = (erreurs["cible"] - erreurs["prediction"]).abs()
    return (erreurs.groupby("groupe")["abs_erreur"].mean() * 100).round(3)


def add_graph_features(data: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les features de graphe (centralités) aux observations.

    Construit un graphe orienté à partir des paires (departure, arrival)
    uniques, calcule les métriques de centralité par gare, et les ajoute
    en colonnes pour la gare de départ et la gare d'arrivée.

    Args:
        data: DataFrame contenant les colonnes departure et arrival.

    Returns:
        DataFrame enrichi avec 10 nouvelles colonnes (5 features x 2 gares).
    """
    from projet_kit_data.graph.network import build_railway_graph
    from projet_kit_data.graph.centrality import compute_graph_features

    graph_input = data[["departure", "arrival"]].copy()
    graph_input["planned"] = 1

    G = build_railway_graph(graph_input)
    station_features = compute_graph_features(G)

    feature_cols = [
        "in_degree", "out_degree", "total_degree", "betweenness", "pagerank"
    ]

    enrichi = data.copy()
    for feature in feature_cols:
        mapping = dict(zip(station_features["station"], station_features[feature]))
        enrichi[f"depart_{feature}"] = enrichi["departure"].map(mapping)
        enrichi[f"arrivee_{feature}"] = enrichi["arrival"].map(mapping)

    return enrichi


def compute_naive_baseline(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target: str,
) -> dict:
    """Calcule les métriques d'un modèle naïf qui prédit la moyenne du train.

    Args:
        train: observations d'entraînement.
        test: observations de test.
        target: nom de la colonne cible.

    Returns:
        Dictionnaire avec mae_pts (en points de pourcentage) et r2.
    """
    from sklearn.metrics import r2_score

    moyenne_train = train[target].mean()
    predictions = [moyenne_train] * len(test)

    mae_pts = (test[target] - moyenne_train).abs().mean() * 100
    r2 = r2_score(test[target], predictions)

    return {"mae_pts": round(mae_pts, 3), "r2": round(r2, 4)}