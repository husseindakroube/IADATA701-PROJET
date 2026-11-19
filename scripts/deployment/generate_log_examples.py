"""Génère des journaux de démonstration sans données d’utilisateur réel."""

import argparse
from pathlib import Path
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

from projet_kit_data.logging_config import configure_logging  # noqa: E402
from utils import activity  # noqa: E402


def generate_examples(directory: Path) -> None:
    """Écrit debug.log et error.log dans un dossier réservé à la démonstration.

    Args:
        directory: Dossier distinct des journaux réels de l'application.

    Les fichiers préexistants sont refusés pour éviter tout écrasement.
    Les erreurs sont simulées et ne signalent pas une panne réelle.
    """
    directory = directory.resolve()
    if directory == ROOT / "logs" or any(
        (directory / name).exists() for name in ("debug.log", "error.log")
    ):
        raise FileExistsError("Utilisez un dossier de démonstration neuf.")
    logger = configure_logging(directory)
    try:
        logger.debug("DEMONSTRATION — données fictives, aucune session réelle")
        with patch.object(
            activity.st, "session_state", {"_log_session": "demo-session"}
        ):
            activity.log_selection("page_view", page="Liaisons et réseau")
            activity.log_selection("page_view", page="Liaisons et réseau")
            activity.log_selection(
                "carte_filters", service="National", color_mode="cluster", routes=2
            )
            activity.log_selection("route_comparison", route_a="A → B", route_b="B → A")
            activity.log_action("download", file="liaisons_selection.csv", routes=2)
        logger.warning("DEMONSTRATION — sélection vide simulée")
        logger.error("DEMONSTRATION — fichier absent simulé : exemple.csv")
        logger.critical("DEMONSTRATION — indisponibilité simulée de la source")
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger._log_directory = None


def main() -> None:
    """Lit le dossier de destination puis génère les deux journaux d'exemple."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    generate_examples(parser.parse_args().directory)


if __name__ == "__main__":
    main()
