from pathlib import Path
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def load_data(file_path: Path) -> pd.DataFrame:
   
    try:
        dataframe = pd.read_csv(
            file_path,
            sep=";",
            encoding="utf-8",
        )

    except FileNotFoundError:
        logger.exception("Fichier de données introuvable: %s", file_path)
        raise

    except (
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ):
        logger.exception("Impossible de lire le fichier CSV: %s", file_path)
        raise

    logger.info(
        "Données chargées avec succès: %s (%d rows, %d columns)",
        file_path,
        dataframe.shape[0],
        dataframe.shape[1],
    )

    return dataframe
