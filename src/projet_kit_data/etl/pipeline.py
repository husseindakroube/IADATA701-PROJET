"""Orchestrer le flux local de préparation ETL des données SNCF."""

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
    """Charger les données SNCF brutes locales, les typer et les annoter.

    La fonction délègue successivement aux modules existants d’ingestion, de
    prétraitement et de nettoyage. Elle ne télécharge pas les données, ne lance
    pas l’audit, ne modifie pas le fichier brut et ne corrige ni ne supprime
    les enregistrements atypiques.

    :param raw_data_path: Chemin du fichier JSON brut existant. Par défaut,
        chemin des données brutes défini par le module d’ingestion.
    :type raw_data_path: str | os.PathLike[str]
    :returns: DataFrame Polars typé et muni des flags diagnostiques existants.
    :rtype: polars.DataFrame
    :raises OSError: Si le fichier brut ne peut pas être lu.
    :raises json.JSONDecodeError: Si le fichier brut contient un JSON invalide.
    :raises TypeError: Si les enregistrements décodés ou les valeurs
        intermédiaires ont un type non pris en charge.
    :raises ValueError: Si la structure JSON brute, le schéma canonique ou
        les valeurs des champs sont invalides.
    """
    records = sncf_api.load_raw_data(path=Path(raw_data_path))
    typed_data = preprocessing.preprocess_data(records)
    return cleaning.clean_data(typed_data)


def run_and_save_etl(
    raw_data_path: str | os.PathLike[str] = sncf_api.DEFAULT_RAW_DATA_PATH,
    output_path: str | os.PathLike[str] = DEFAULT_PROCESSED_DATA_PATH,
) -> pl.DataFrame:
    """Exécuter le pipeline ETL local et enregistrer sa sortie en Parquet.

    Le pipeline existant charge le JSON brut, prépare le DataFrame typé selon
    le schéma canonique et ajoute les flags diagnostiques. Cette fonction crée
    le répertoire de sortie si nécessaire, écrit le DataFrame sans
    transformation supplémentaire et retourne ce même DataFrame.

    :param raw_data_path: Chemin du fichier JSON brut existant. Par défaut,
        chemin des données brutes défini par le module d’ingestion.
    :type raw_data_path: str | os.PathLike[str]
    :param output_path: Destination Parquet. Par défaut,
        ``data/processed/sncf.parquet``.
    :type output_path: str | os.PathLike[str]
    :returns: DataFrame Polars traité qui a été enregistré.
    :rtype: polars.DataFrame
    :raises OSError: Si les données brutes ne peuvent pas être lues, ou si le
        répertoire de sortie ou le fichier Parquet ne peut pas être créé.
    :raises json.JSONDecodeError: Si le JSON brut est invalide.
    :raises TypeError: Si les enregistrements ou les valeurs intermédiaires
        ont un type non pris en charge.
    :raises ValueError: Si les enregistrements bruts ne correspondent pas au
        schéma canonique ou contiennent des valeurs impossibles à convertir.
    """
    processed_data = run_etl_pipeline(raw_data_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    processed_data.write_parquet(destination)
    return processed_data
