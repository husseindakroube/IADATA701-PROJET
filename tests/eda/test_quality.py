"""Tests unitaires des fonctions de contrôle qualité de l'EDA."""

import pandas as pd
import pytest

from sncf_tgv.eda.quality import (
    check_identifiers,
    count_duplicates,
    get_column_types,
    get_dataset_overview,
    get_missing_values,
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
