"""Tests du prétraitement des variables de prédiction."""

import numpy as np
import pandas as pd

from projet_kit_data.ml.models import build_preprocessor


def test_baseline_preprocessing() -> None:
    """Vérifie l'encodage des variables catégorielles."""
    data = pd.DataFrame(
        {
            "service": ["National", "International"],
            "departure": ["PARIS LYON", "RENNES"],
            "arrival": ["RENNES", "PARIS LYON"],
            "month": [1, 2],
        }
    )

    preprocessor = build_preprocessor()
    transformed = preprocessor.fit_transform(data)

    assert transformed.shape == (2, 7)
    assert np.isfinite(transformed).all()


def test_numeric_features_with_missing_values() -> None:
    """Vérifie l'imputation des valeurs numériques manquantes."""
    data = pd.DataFrame(
        {
            "service": ["National", "National"],
            "departure": ["PARIS LYON", "RENNES"],
            "arrival": ["RENNES", "PARIS LYON"],
            "month": [1, 2],
            "edge_volume": [100.0, np.nan],
        }
    )

    preprocessor = build_preprocessor(numeric_features=["edge_volume"])

    transformed = preprocessor.fit_transform(data)

    assert transformed.shape == (2, 8)
    assert np.isfinite(transformed).all()

    # L'indicateur signale l'absence de volume pour la deuxième ligne.
    assert transformed[0, -1] == 0
    assert transformed[1, -1] == 1
