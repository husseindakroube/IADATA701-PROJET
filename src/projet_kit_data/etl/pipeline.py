"Orchestre la préparation ETL locale des données SNCF."

from __future__ import annotations

import os
from pathlib import Path

import polars as pl

from projet_kit_data.etl import cleaning, preprocessing
from projet_kit_data.ingestion import sncf_api

DEFAULT_PROCESSED_DATA_PATH = Path("data/processed/sncf.parquet")


def run_etl_pipeline(
    raw_data_path: str | os.PathLike[str] = sncf_api.DEFAULT_RAW_DATA_PATH,
) -> pl.DataFrame:
    """Charge, type et annote les données brutes SNCF locales.

    Appelle successivement les modules d’acquisition, de prétraitement et de contrôle
    qualité. Ne télécharge pas les données, ne lance pas l’audit, ne modifie pas le
    fichier brut et ne corrige ni ne supprime les observations anormales.

    :param raw_data_path: JSON brut existant ; chemin du module d’acquisition par défaut.
    :type raw_data_path: str | os.PathLike[str]
    :returns: Table Polars typée avec les indicateurs de diagnostic existants.
    :rtype: polars.DataFrame
    :raises OSError: Si le fichier brut est illisible.
    :raises json.JSONDecodeError: Si le JSON brut est invalide.
    :raises TypeError: Si les observations ou valeurs intermédiaires ont un type incompatible.
    :raises ValueError: Si la structure JSON, le schéma canonique ou les valeurs sont invalides."""
    records = sncf_api.load_raw_data(path=Path(raw_data_path))
    typed_data = preprocessing.preprocess_data(records)
    return cleaning.clean_data(typed_data)


def run_and_save_etl(
    raw_data_path: str | os.PathLike[str] = sncf_api.DEFAULT_RAW_DATA_PATH,
    output_path: str | os.PathLike[str] = DEFAULT_PROCESSED_DATA_PATH,
) -> pl.DataFrame:
    """Exécute la chaîne ETL locale et enregistre son résultat au format Parquet.

    La chaîne charge le JSON brut, prépare la table canonique typée et ajoute les
    indicateurs qualité. Crée le dossier de sortie si nécessaire, écrit la table sans
    transformation supplémentaire et renvoie cette même table.

    :param raw_data_path: JSON brut existant ; chemin du module d’acquisition par défaut.
    :type raw_data_path: str | os.PathLike[str]
    :param output_path: Destination Parquet ; ``data/processed/sncf.parquet`` par défaut.
    :type output_path: str | os.PathLike[str]
    :returns: Table Polars traitée et enregistrée.
    :rtype: polars.DataFrame
    :raises OSError: Si la lecture de la source ou la création du dossier ou fichier échoue.
    :raises json.JSONDecodeError: Si le JSON brut est invalide.
    :raises TypeError: Si les observations ou valeurs intermédiaires ont un type incompatible.
    :raises ValueError: Si le schéma est incorrect ou une valeur ne peut pas être convertie."""
    processed_data = run_etl_pipeline(raw_data_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    processed_data.write_parquet(destination)
    return processed_data
