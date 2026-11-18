'Vérifie le routage par gravité, les réexécutions et les enregistrements d’activité.'

import logging

import pytest
from utils import activity

from projet_kit_data.logging_config import configure_logging


@pytest.fixture
def log_directory(tmp_path):
    'Isole les journaux de test et libère ensuite les fichiers ouverts sous Windows.'
    configure_logging(tmp_path)
    yield tmp_path
    logger = logging.getLogger("projet_kit_data")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger._log_directory = None


def test_severity_routing_traceback_and_rerun(log_directory):
    logger = logging.getLogger("projet_kit_data.test")
    original = list(configure_logging(log_directory).handlers)
    assert configure_logging(log_directory).handlers == original
    for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
        logger.log(level, "marker-%s", logging.getLevelName(level))
    try:
        raise ValueError("invalid artifact")
    except ValueError:
        logger.exception("artifact failed")
    debug = (log_directory / "debug.log").read_text(encoding="utf-8")
    error = (log_directory / "error.log").read_text(encoding="utf-8")
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        assert debug.count(f"marker-{level}") == 1
        assert (f"marker-{level}" in error) == (level in ["ERROR", "CRITICAL"])
    assert "Traceback" in error
    assert "ValueError: invalid artifact" in error


def test_actions_deduplicated_per_session_and_downloads_not_deduplicated(log_directory, monkeypatch):
    state = {}
    monkeypatch.setattr(activity.st, "session_state", state)
    activity.log_selection("page_view", page="Qualité")
    activity.log_selection("page_view", page="Qualité")
    activity.log_selection("page_view", page="Prédictions")
    activity.log_action("download", file="rapport.csv")
    activity.log_action("download", file="rapport.csv")
    text = (log_directory / "debug.log").read_text(encoding="utf-8")
    assert text.count("event=page_view") == 2
    assert text.count("event=download") == 2
    assert "Qualité" in text
    assert text.count(f"session={state['_log_session']}") == 4
    assert (log_directory / "error.log").read_text(encoding="utf-8") == ""


def test_rotating_logs_and_new_directory(log_directory):
    logger = configure_logging(log_directory)
    for handler in logger.handlers:
        handler.maxBytes = 100
    logger.error("x" * 200)
    logger.error("another event")
    assert (log_directory / "debug.log.1").exists()
    assert (log_directory / "error.log.1").exists()
    configure_logging(log_directory / "new")
    logger.info("new destination")
    assert "new destination" in (log_directory / "new/debug.log").read_text()


def test_unwritable_destination_preserves_existing_handlers(log_directory, monkeypatch):
    import projet_kit_data.logging_config as config

    original = list(configure_logging(log_directory).handlers)
    real_handler = config.RotatingFileHandler

    def fail_second(path, **kwargs):
        if path.name == "error.log":
            raise PermissionError("read-only")
        return real_handler(path, **kwargs)

    monkeypatch.setattr(config, "RotatingFileHandler", fail_second)
    with pytest.raises(PermissionError):
        configure_logging(log_directory / "unwritable")
    assert logging.getLogger("projet_kit_data").handlers == original
