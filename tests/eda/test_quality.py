"""Tests unitaires des fonctions de contrôle qualité de l'EDA."""

import pandas as pd
import pytest

from sncf_tgv.eda.quality import (
    check_train_counts,
    check_identifiers,
    count_duplicates,
    get_column_types,
    get_dataset_overview,
    get_missing_values,
    check_durations,
    check_percentages,
    check_comments,
)


def test_dataset_overview() -> None:
    """Vérifie que les dimensions du jeu de données sont correctes."""
    data = pd.DataFrame(
        {
            "gare_depart": ["Paris", "Lyon"],
            "nb_train_prevu": [100, 200],
        }
    )

    result = get_dataset_overview(data)

    assert result["n_rows"] == 2
    assert result["n_columns"] == 2


def test_missing_values() -> None:
    """Vérifie le calcul des valeurs manquantes."""
    data = pd.DataFrame(
        {
            "retard": [10.0, None, 20.0, None],
        }
    )

    result = get_missing_values(data)

    assert result.loc["retard", "missing_count"] == 2
    assert result.loc["retard", "missing_percentage"] == pytest.approx(50.0)


def test_missing_values_empty_dataset() -> None:
    """Vérifie le comportement avec un jeu de données vide."""
    data = pd.DataFrame(columns=["retard"])

    result = get_missing_values(data)

    assert result.loc["retard", "missing_count"] == 0
    assert result.loc["retard", "missing_percentage"] == 0.0


def test_duplicates() -> None:
    """Vérifie la détection des lignes dupliquées."""
    data = pd.DataFrame(
        {
            "gare_depart": ["Paris", "Paris", "Lyon"],
        }
    )

    assert count_duplicates(data) == 1


def test_duplicates_with_subset() -> None:
    """Vérifie la détection selon une clé métier."""
    data = pd.DataFrame(
        {
            "date": ["2026-01", "2026-01", "2026-02"],
            "gare_depart": ["Paris", "Paris", "Paris"],
            "nb_train_prevu": [100, 120, 130],
        }
    )

    result = count_duplicates(
        data,
        subset=["date", "gare_depart"],
    )

    assert result == 1


def test_column_types() -> None:
    """Vérifie l'identification des types de colonnes."""
    data = pd.DataFrame(
        {
            "nb_train_prevu": pd.Series([100, 200, 300], dtype="int64"),
            "retard": pd.Series([None, None, 20.0], dtype="float64"),
        }
    )

    result = get_column_types(data)

    assert result.loc[0, "column"] == "nb_train_prevu"
    assert result.loc[0, "dtype"] == "int64"
    assert result.loc[1, "column"] == "retard"
    assert result.loc[1, "dtype"] == "float64"


def test_identifiers_valid_data() -> None:
    """Vérifie que des identifiants valides ne produisent aucune anomalie."""
    data = pd.DataFrame(
        {
            "date": ["2026-01", "2026-02"],
            "service": ["National", "National"],
            "gare_depart": ["PARIS", "SEOUL"],
            "gare_arrivee": ["LYON", "BUSAN"],
        }
    )

    result = check_identifiers(data)

    assert result["nombre_anomalies"].sum() == 0


def test_identifiers_invalid_values() -> None:
    """Détecte une date invalide et un nom de gare vide."""
    data = pd.DataFrame(
        {
            "date": ["2026-13"],
            "service": ["National"],
            "gare_depart": ["   "],
            "gare_arrivee": ["LYON"],
        }
    )

    result = check_identifiers(data)
    anomalies = result.set_index("regle")["nombre_anomalies"]

    assert anomalies["date_invalide"] == 1
    assert anomalies["gare_depart_manquant"] == 1


def test_identifiers_duplicate_key() -> None:
    """Détecte deux observations portant la même clé métier."""
    data = pd.DataFrame(
        {
            "date": ["2026-01", "2026-01"],
            "service": ["National", "National"],
            "gare_depart": ["PARIS", "PARIS"],
            "gare_arrivee": ["LYON", "LYON"],
        }
    )

    result = check_identifiers(data)
    anomalies = result.set_index("regle")["nombre_anomalies"]

    assert anomalies["doublon_metier"] == 1


def test_train_counts_valid() -> None:
    """Vérifie qu'une observation cohérente ne génère aucune anomalie."""
    data = pd.DataFrame(
        {
            "nb_train_prevu": [100],
            "nb_annulation": [5],
            "nb_train_depart_retard": [10],
            "nb_train_retard_arrivee": [20],
            "nb_train_retard_sup_15": [15],
            "nb_train_retard_sup_30": [8],
            "nb_train_retard_sup_60": [3],
        }
    )

    result = check_train_counts(data)

    assert result["nombre_anomalies"].sum() == 0


def test_train_counts_invalid() -> None:
    """Détecte des annulations et des comptages incohérents."""
    data = pd.DataFrame(
        {
            "nb_train_prevu": [100],
            "nb_annulation": [120],
            "nb_train_depart_retard": [-2],
            "nb_train_retard_arrivee": [110],
            "nb_train_retard_sup_15": [15],
            "nb_train_retard_sup_30": [8],
            "nb_train_retard_sup_60": [12],
        }
    )

    result = check_train_counts(data)
    anomalies = result.set_index("regle")["nombre_anomalies"]

    assert anomalies["annulations_excessives"] == 1
    assert anomalies["comptage_negatif"] == 1
    assert anomalies["seuil_60_superieur_30"] == 1


def test_train_counts_decimal_values() -> None:
    """Détecte un comptage contenant une valeur décimale."""
    data = pd.DataFrame(
        {
            "nb_train_prevu": [100.5],
            "nb_annulation": [5],
            "nb_train_depart_retard": [10],
            "nb_train_retard_arrivee": [20],
            "nb_train_retard_sup_15": [15],
            "nb_train_retard_sup_30": [8],
            "nb_train_retard_sup_60": [3],
        }
    )

    result = check_train_counts(data)
    anomalies = result.set_index("regle")["nombre_anomalies"]

    assert anomalies["comptage_non_entier"] == 1


def test_train_counts_missing_column() -> None:
    """Vérifie la détection d'une colonne obligatoire absente."""
    data = pd.DataFrame({"nb_train_prevu": [100]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        check_train_counts(data)


def test_durations_valid() -> None:
    """Vérifie des durées et retards moyens cohérents."""
    data = pd.DataFrame(
        {
            "duree_moyenne": [150],
            "retard_moyen_depart": [12.5],
            "retard_moyen_tous_trains_depart": [3.2],
            "retard_moyen_arrivee": [25.0],
            "retard_moyen_tous_trains_arrivee": [6.1],
            "retard_moyen_trains_retard_sup15": [32.0],
        }
    )

    result = check_durations(data)

    assert result["nombre_anomalies"].sum() == 0


def test_durations_invalid() -> None:
    """Détecte une durée de trajet invalide et un retard négatif."""
    data = pd.DataFrame(
        {
            "duree_moyenne": [-10],
            "retard_moyen_depart": [-5.0],
            "retard_moyen_tous_trains_depart": [2.0],
            "retard_moyen_arrivee": [20.0],
            "retard_moyen_tous_trains_arrivee": [4.0],
            "retard_moyen_trains_retard_sup15": [25.0],
        }
    )

    result = check_durations(data)
    anomalies = result.set_index("regle")["nombre_anomalies"]

    assert anomalies["trajet_duree_invalide"] == 1
    assert anomalies["moyenne_trains_retardes_negative"] == 1


def test_durations_missing_column() -> None:
    """Vérifie la détection d'une colonne obligatoire absente."""
    data = pd.DataFrame({"duree_moyenne": [120]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        check_durations(data)


def test_percentages_valid() -> None:
    """Vérifie une répartition valide des causes de retard."""
    data = pd.DataFrame(
        {
            "prct_cause_externe": [30.0],
            "prct_cause_infra": [25.0],
            "prct_cause_gestion_trafic": [15.0],
            "prct_cause_materiel_roulant": [20.0],
            "prct_cause_gestion_gare": [5.0],
            "prct_cause_prise_en_charge_voyageurs": [5.0],
        }
    )

    result = check_percentages(data)

    assert result["nombre_anomalies"].sum() == 0


def test_percentages_invalid_bounds() -> None:
    """Détecte les pourcentages hors des bornes autorisées."""
    data = pd.DataFrame(
        {
            "prct_cause_externe": [-10.0],
            "prct_cause_infra": [110.0],
            "prct_cause_gestion_trafic": [0.0],
            "prct_cause_materiel_roulant": [0.0],
            "prct_cause_gestion_gare": [0.0],
            "prct_cause_prise_en_charge_voyageurs": [0.0],
        }
    )

    result = check_percentages(data)
    anomalies = result.set_index("regle")["nombre_anomalies"]

    assert anomalies["pourcentage_negatif"] == 1
    assert anomalies["pourcentage_superieur_100"] == 1


def test_percentages_invalid_sum() -> None:
    """Détecte une somme des causes éloignée de 100 %."""
    data = pd.DataFrame(
        {
            "prct_cause_externe": [20.0],
            "prct_cause_infra": [20.0],
            "prct_cause_gestion_trafic": [10.0],
            "prct_cause_materiel_roulant": [10.0],
            "prct_cause_gestion_gare": [5.0],
            "prct_cause_prise_en_charge_voyageurs": [5.0],
        }
    )

    result = check_percentages(data)
    anomalies = result.set_index("regle")["nombre_anomalies"]

    assert anomalies["somme_causes_differente_100"] == 1


def test_percentages_missing_column() -> None:
    """Vérifie la détection d'une colonne obligatoire absente."""
    data = pd.DataFrame({"prct_cause_externe": [30.0]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        check_percentages(data)


def test_comments_valid() -> None:
    """Vérifie le comptage des commentaires renseignés."""
    data = pd.DataFrame(
        {
            "commentaire_annulation": ["Grève", "Travaux"],
            "commentaire_retards_depart": ["Incident", "Météo"],
            "commentaires_retard_arrivee": ["Panne", "Signalisation"],
        }
    )

    result = check_comments(data)

    assert result["nb_renseignes"].tolist() == [2, 2, 2]
    assert result["nb_manquants"].sum() == 0
    assert result["nb_vides"].sum() == 0


def test_comments_missing_and_empty() -> None:
    """Distingue les commentaires manquants et les textes vides."""
    data = pd.DataFrame(
        {
            "commentaire_annulation": [None, "", "  ", "Grève"],
            "commentaire_retards_depart": ["Météo", None, None, None],
            "commentaires_retard_arrivee": [None, "Panne", "", "Signalisation"],
        }
    )

    result = check_comments(data).set_index("colonne")

    assert result.loc["commentaire_annulation", "nb_manquants"] == 1
    assert result.loc["commentaire_annulation", "nb_vides"] == 2
    assert result.loc["commentaire_annulation", "nb_renseignes"] == 1
    assert result.loc["commentaire_annulation", "pourcentage_renseignes"] == 25.0


def test_comments_missing_column() -> None:
    """Vérifie qu'une colonne de commentaires absente est signalée."""
    data = pd.DataFrame({"commentaire_annulation": ["Grève"]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        check_comments(data)
