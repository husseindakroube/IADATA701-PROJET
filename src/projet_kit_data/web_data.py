'Adaptateurs en lecture seule pour les résultats d’analyse enregistrés par l’équipe.'

import json
import logging
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
KEYS = ["date", "service", "gare_depart", "gare_arrivee"]
FLAGS = [
    "flag_negative_count",
    "flag_sup30_lt_sup60",
    "flag_sup15_lt_sup30",
    "flag_cancellations_gt_planned",
]
LOGGER = logging.getLogger(__name__)


def load_table(relative: str) -> pd.DataFrame:
    'Charge une table du projet et journalise les échecs sans modifier le fichier.'
    path = ROOT / relative
    try:
        frame = (
            pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        )
        LOGGER.debug('Fichier chargé %s : %d lignes', relative, len(frame))
        return frame
    except Exception:
        LOGGER.exception('Impossible de charger le fichier %s', relative)
        raise


def load_json(relative: str) -> dict:
    'Charge les métadonnées enregistrées, sans désérialisation ni entraînement de modèle.'
    result = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    LOGGER.debug('Métadonnées chargées : %s', relative)
    return result


def validate_observations(frame: pd.DataFrame) -> pd.DataFrame:
    'Valide la clé commune avant d’afficher les observations dans l’interface.'
    required = {
        *KEYS,
        *FLAGS,
        "retard_moyen_tous_trains_arrivee",
        "nb_train_prevu",
        "nb_annulation",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Champs absents : {sorted(missing)}")
    if frame[KEYS].isna().any().any() or frame.duplicated(KEYS).any():
        raise ValueError("Clé mensuelle absente ou dupliquée")
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], format="%Y-%m")
    return result


def filter_observations(
    frame: pd.DataFrame, start, end, service=None, departure=None, arrival=None
) -> pd.DataFrame:
    'Applique les mêmes filtres de dates inclusives et de liaisons orientées sur chaque page.'
    mask = frame["date"].between(pd.Timestamp(start), pd.Timestamp(end))
    for column, value in [
        ("service", service),
        ("gare_depart", departure),
        ("gare_arrivee", arrival),
    ]:
        if value is not None:
            mask &= frame[column].eq(value)
    return frame.loc[mask].copy()
