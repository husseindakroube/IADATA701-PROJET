"""Chargement et préparation des données pour la prédiction des retards."""

from pathlib import Path

import pandas as pd

from projet_kit_data.ml.temporal import build_temporal_graph_dataset
from projet_kit_data.preprocessing import prepare_graph_data


def load_ml_dataset(
    csv_path: str | Path,
    window_months: int = 12,
) -> pd.DataFrame:
    """Construit le dataset ML à partir du CSV SNCF.

    Args:
        csv_path: Chemin du fichier CSV.
        window_months: Fenêtre historique utilisée pour les variables.

    Returns:
        Observations enrichies avec une cible valide et le mois
        de circulation.
    """
    raw_data = pd.read_csv(csv_path, sep=";")
    data = prepare_graph_data(raw_data)
    data = build_temporal_graph_dataset(data, window_months=window_months)

    data["month"] = data["date"].dt.month

    return data.loc[data["valid_target"]].copy()
