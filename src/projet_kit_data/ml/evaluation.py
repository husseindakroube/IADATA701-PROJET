"""Métriques d'évaluation des modèles de prédiction des retards."""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> dict[str, float]:
    """Calcule les erreurs de prédiction des taux de retard.

    Args:
        y_true: Taux de retard observés.
        y_pred: Taux de retard prédits.
        sample_weight: Nombre de trains circulés par observation.

    Returns:
        Dictionnaire contenant la MAE, la RMSE et,
        si des poids sont fournis, la MAE pondérée.
    """
    metrics = {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": mean_squared_error(y_true, y_pred) ** 0.5,
    }

    if sample_weight is not None:
        metrics["weighted_mae"] = mean_absolute_error(
            y_true,
            y_pred,
            sample_weight=sample_weight,
        )

    return metrics
