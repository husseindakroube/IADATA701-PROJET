"Journaux rotatifs de l’application, communs à l’interface et aux modules de données."

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import RLock

_LOCK = RLock()


def configure_logging(directory: Path | None = None) -> logging.Logger:
    """Crée les journaux de débogage (DEBUG+) et d’erreurs (ERROR+) une seule fois par processus et chemin.

    Les erreurs figurent volontairement dans les deux fichiers. Chacun conserve trois sauvegardes
    de 5 Mio au maximum. Les réexécutions Streamlit réutilisent les gestionnaires existants.
    """
    directory = (directory or Path(__file__).resolve().parents[2] / "logs").resolve()
    logger = logging.getLogger("projet_kit_data")
    with _LOCK:
        if getattr(logger, "_log_directory", None) == directory and logger.handlers:
            return logger
        directory.mkdir(parents=True, exist_ok=True)
        handlers = []
        try:
            for filename, level in [
                ("debug.log", logging.DEBUG),
                ("error.log", logging.ERROR),
            ]:
                handler = RotatingFileHandler(
                    directory / filename,
                    maxBytes=5 * 1024 * 1024,
                    backupCount=3,
                    encoding="utf-8",
                )
                handler.setLevel(level)
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                    )
                )
                handlers.append(handler)
        except OSError:
            for handler in handlers:
                handler.close()
            raise
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        for handler in handlers:
            logger.addHandler(handler)
        logger._log_directory = directory
        logger.info("Journalisation de l’application initialisée")
    return logger
