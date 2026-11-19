"""Tests unitaires du module comparison."""

import pandas as pd

from projet_kit_data.comparaison import (
    add_cluster_to_dataset,
    format_comparison_table,
    load_cluster_features,
)


def test_load_cluster_features(tmp_path):
    """load_cluster_features lit correctement un CSV de clusters."""
    chemin = tmp_path / "clusters.csv"
    chemin.write_text("paire,cluster\n\"('LYON PART DIEU', 'PARIS LYON')\",0\n")

    clusters = load_cluster_features(chemin)

    assert list(clusters.columns) == ["gare_a", "gare_b", "cluster"]
    assert clusters.loc[0, "gare_a"] == "LYON PART DIEU"
    assert clusters.loc[0, "gare_b"] == "PARIS LYON"
    assert clusters.loc[0, "cluster"] == 0


def test_add_cluster_to_dataset_joint_bien():
    """add_cluster_to_dataset ajoute une colonne cluster via la paire."""
    data = pd.DataFrame(
        {
            "departure": ["PARIS LYON", "LYON PART DIEU"],
            "arrival": ["LYON PART DIEU", "PARIS LYON"],
        }
    )
    clusters = pd.DataFrame(
        {
            "gare_a": ["LYON PART DIEU"],
            "gare_b": ["PARIS LYON"],
            "cluster": [0],
        }
    )

    enrichi = add_cluster_to_dataset(data, clusters)

    assert "cluster" in enrichi.columns
    assert (enrichi["cluster"] == 0).all()


def test_add_cluster_to_dataset_sans_correspondance():
    """Les lignes sans paire correspondante ont une valeur cluster manquante."""
    data = pd.DataFrame(
        {
            "departure": ["PARIS NORD"],
            "arrival": ["BRUXELLES"],
        }
    )
    clusters = pd.DataFrame(
        {
            "gare_a": ["PARIS LYON"],
            "gare_b": ["LYON PART DIEU"],
            "cluster": [0],
        }
    )

    enrichi = add_cluster_to_dataset(data, clusters)
    assert enrichi["cluster"].isna().all()


def test_format_comparison_table_trie_par_mae():
    """format_comparison_table trie les modèles par MAE croissante."""
    resultats = [
        {"modele": "A", "mae": 3.5, "rmse": 5.0, "modele_entraine": None},
        {"modele": "B", "mae": 2.0, "rmse": 4.0, "modele_entraine": None},
    ]

    tableau = format_comparison_table(resultats)

    assert list(tableau["modele"]) == ["B", "A"]
    assert tableau.loc[0, "mae"] == 2.0


def test_compute_errors_by_group():
    """compute_errors_by_group retourne la MAE par groupe."""
    from projet_kit_data.comparaison import compute_errors_by_group

    # un petit modèle factice qui prédit toujours 0.1
    class FakeModel:
        def predict(self, X):
            return [0.1] * len(X)

    test = pd.DataFrame(
        {
            "feature_1": [1, 2, 3, 4],
            "target": [0.1, 0.2, 0.3, 0.1],
            "groupe": ["A", "A", "B", "B"],
        }
    )

    mae = compute_errors_by_group(FakeModel(), test, ["feature_1"], "target", "groupe")

    assert mae.loc["A"] == 5.0
    assert mae.loc["B"] == 10.0


def test_add_graph_features_ajoute_colonnes():
    """add_graph_features ajoute 10 colonnes de graphe au DataFrame."""
    from projet_kit_data.comparaison import add_graph_features

    data = pd.DataFrame(
        {
            "departure": ["A", "B", "A", "C"],
            "arrival": ["B", "A", "C", "B"],
        }
    )

    enrichi = add_graph_features(data)

    # 10 nouvelles colonnes attendues (5 features x 2 gares)
    nouvelles_colonnes = [
        "depart_in_degree",
        "depart_out_degree",
        "depart_total_degree",
        "depart_betweenness",
        "depart_pagerank",
        "arrivee_in_degree",
        "arrivee_out_degree",
        "arrivee_total_degree",
        "arrivee_betweenness",
        "arrivee_pagerank",
    ]
    for col in nouvelles_colonnes:
        assert col in enrichi.columns


def test_compute_naive_baseline_calcule_metriques():
    """compute_naive_baseline retourne la MAE et le R² du modèle naïf."""
    from projet_kit_data.comparaison import compute_naive_baseline

    train = pd.DataFrame({"target": [0.1, 0.2, 0.3]})  # moyenne = 0.2
    test = pd.DataFrame({"target": [0.1, 0.2, 0.3]})

    result = compute_naive_baseline(train, test, "target")

    # MAE = (|0.1-0.2| + |0.2-0.2| + |0.3-0.2|) / 3 = 0.0667
    # En points de pourcentage : 6.67
    assert abs(result["mae_pts"] - 6.667) < 0.01
    assert "r2" in result
