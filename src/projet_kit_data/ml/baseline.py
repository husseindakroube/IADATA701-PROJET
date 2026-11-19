"""Préparation d'une baseline supervisée sans indicateurs de graphe.

Les caractéristiques d'un mois t sont calculées exclusivement à partir
des observations des mois antérieurs. Les données SNCF ETL restent intactes.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from projet_kit_data.ml.models import HISTORY_FEATURES

# Une observation correspond à une liaison orientée, un service et un mois.
ROUTE_KEYS = ["service", "departure", "arrival"]
BUSINESS_KEYS = ["date", *ROUTE_KEYS]
ETL_COLUMNS = {
    "date": "date",
    "service": "service",
    "gare_depart": "departure",
    "gare_arrivee": "arrival",
    "nb_train_prevu": "planned",
    "nb_annulation": "cancelled",
    "nb_train_retard_sup_15": "late_15",
}

# Aucune variable mesurée pendant le mois courant ne figure parmi les entrées.
BASELINE_NUMERIC_FEATURES = [
    *HISTORY_FEATURES,
    "historical_circulated",
    "historical_observations",
]
BASELINE_FEATURES = [
    "service",
    "departure",
    "arrival",
    "month",
    *BASELINE_NUMERIC_FEATURES,
]


def prepare_baseline_data(data: pd.DataFrame) -> pd.DataFrame:
    """Adapter les colonnes ETL et calculer la cible sans corriger la source.

    Une cible est valide seulement si les trois comptages sont connus,
    finis, non négatifs, que les annulations ne dépassent pas les prévisions
    et que le nombre de trains retardés ne dépasse pas les circulations.

    Args:
        data: DataFrame produit par l'ETL (`sncf.parquet`).

    Returns:
        Copie normalisée avec `valid_target` et `delay_rate_15`.

    Raises:
        ValueError: Colonnes ou clés manquantes, dates erronées ou doublons.
    """
    missing = sorted(set(ETL_COLUMNS) - set(data.columns))
    if missing:
        raise ValueError(f"Colonnes ETL manquantes : {missing}")

    result = data[list(ETL_COLUMNS)].rename(columns=ETL_COLUMNS).copy()
    if result[list(ROUTE_KEYS)].isna().any().any():
        raise ValueError("Une ou plusieurs clés de liaison sont manquantes.")

    # Accepter le format mensuel YYYY-MM ou une date de premier du mois.
    dates = result["date"]
    if pd.api.types.is_datetime64_any_dtype(dates):
        parsed = pd.to_datetime(dates, errors="coerce")
        if parsed.isna().any() or not parsed.dt.is_month_start.all():
            raise ValueError("Les dates doivent désigner le premier jour du mois.")
    else:
        if not (
            dates.astype("string")
            .str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])")
            .fillna(False)
            .all()
        ):
            raise ValueError("Les dates doivent respecter le format YYYY-MM.")
        parsed = pd.to_datetime(dates, format="%Y-%m", errors="raise")
    result["date"] = parsed

    if result.duplicated(BUSINESS_KEYS).any():
        raise ValueError("Clé métier dupliquée (date, service, départ, arrivée).")

    for column in ("planned", "cancelled", "late_15"):
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result["circulated"] = result["planned"] - result["cancelled"]
    counts = result[["planned", "cancelled", "late_15"]].astype(float)
    finite_counts = pd.Series(
        np.isfinite(counts.to_numpy()).all(axis=1), index=result.index
    )
    result["valid_target"] = (
        finite_counts
        & result["planned"].ge(0)
        & result["cancelled"].ge(0)
        & result["cancelled"].le(result["planned"])
        & result["circulated"].gt(0)
        & result["late_15"].ge(0)
        & result["late_15"].le(result["circulated"])
    ).fillna(False)
    result["delay_rate_15"] = result["late_15"].div(
        result["circulated"].where(result["valid_target"])
    )
    result["month"] = result["date"].dt.month
    return result.sort_values(BUSINESS_KEYS).reset_index(drop=True)


def build_baseline_dataset(data: pd.DataFrame, window_months: int = 12) -> pd.DataFrame:
    """Calculer des prédicteurs historiques sans graphe ni fuite temporelle.

    Pour un mois t, seules les observations valides de [t-W, t[ sont
    agrégées par service, gare de départ et gare d'arrivée. Une liaison
    nouvelle conserve des caractéristiques historiques manquantes.

    Args:
        data: Sortie de `prepare_baseline_data`.
        window_months: Nombre de mois calendaires dans la fenêtre passée.

    Returns:
        Observations à partir du mois W+1, incluant cibles et historique.
    """
    if (
        not isinstance(window_months, int)
        or isinstance(window_months, bool)
        or window_months < 1
    ):
        raise ValueError("window_months doit être un entier strictement positif.")
    needed = set(
        BUSINESS_KEYS
        + ["valid_target", "late_15", "circulated", "delay_rate_15", "month"]
    )
    if not needed.issubset(data.columns):
        missing = sorted(needed - set(data.columns))
        raise ValueError(f"Colonnes ML manquantes : {missing}")
    if data.empty:
        raise ValueError("Le jeu de données ML est vide.")

    first_date = data["date"].min()
    results: list[pd.DataFrame] = []
    for current_date in sorted(data["date"].unique()):
        current_date = pd.Timestamp(current_date)
        start_date = current_date - pd.DateOffset(months=window_months)
        if start_date < first_date:
            continue

        history = data.loc[
            (data["date"] >= start_date)
            & (data["date"] < current_date)
            & data["valid_target"]
        ]
        current = data.loc[data["date"] == current_date].copy()

        aggregates = history.groupby(ROUTE_KEYS, as_index=False).agg(
            historical_late_15=("late_15", "sum"),
            historical_circulated=("circulated", "sum"),
            historical_observations=("date", "size"),
        )
        aggregates["historical_delay_rate_15"] = (
            aggregates["historical_late_15"] / aggregates["historical_circulated"]
        )
        aggregates = aggregates[[*ROUTE_KEYS, *BASELINE_NUMERIC_FEATURES]]
        current = current.merge(
            aggregates, on=ROUTE_KEYS, how="left", validate="many_to_one"
        )
        results.append(current)

    if not results:
        raise ValueError("Historique insuffisant pour construire la baseline.")
    return (
        pd.concat(results, ignore_index=True)
        .sort_values(BUSINESS_KEYS)
        .reset_index(drop=True)
    )


def chronological_split(
    data: pd.DataFrame,
    train_fraction: float = 0.7,
    validation_fraction: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Séparer les mois entiers et ordonnés en train/validation/test.

    La séparation est effectuée seulement sur les lignes dont la cible
    est valide. Aucun mois n'apparaît dans deux partitions.
    """
    if not (0 < train_fraction < 1 and 0 < validation_fraction < 1):
        raise ValueError("Les fractions doivent être comprises entre 0 et 1.")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Il doit rester une période de test.")
    valid = data.loc[data["valid_target"]].copy()
    months = sorted(pd.to_datetime(valid["date"]).unique())
    if len(months) < 3:
        raise ValueError("Au moins trois mois valides sont nécessaires.")
    count_train = max(1, math.floor(len(months) * train_fraction))
    count_validation = max(1, math.floor(len(months) * validation_fraction))
    if count_train + count_validation >= len(months):
        raise ValueError("Nombre de mois insuffisant pour trois partitions.")
    train_months = months[:count_train]
    validation_months = months[count_train : count_train + count_validation]
    test_months = months[count_train + count_validation :]
    return (
        valid.loc[valid["date"].isin(train_months)].copy(),
        valid.loc[valid["date"].isin(validation_months)].copy(),
        valid.loc[valid["date"].isin(test_months)].copy(),
    )


def predict_historical_naive(
    training: pd.DataFrame, observations: pd.DataFrame
) -> np.ndarray:
    """Prédire le taux historique de chaque liaison, sinon la moyenne train.

    Le repli utilise uniquement les données d'entraînement, jamais les
    taux observés en validation ou en test.
    """
    if training.empty or not training["valid_target"].all():
        raise ValueError("L'entraînement doit contenir des cibles valides.")
    global_rate = training["late_15"].sum() / training["circulated"].sum()
    historical = pd.to_numeric(
        observations["historical_delay_rate_15"], errors="coerce"
    )
    return historical.fillna(global_rate).clip(0, 1).to_numpy(dtype=float)
