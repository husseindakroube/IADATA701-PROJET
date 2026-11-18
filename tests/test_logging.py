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


def test_map_loading_records_success_and_failure(log_directory, monkeypatch):
    from projet_kit_data import web_data
    from utils.carte import charger_liaisons_detail

    monkeypatch.setattr(web_data, "ROOT", log_directory)
    path = log_directory / "data/processed/liaisons_detail.csv"
    path.parent.mkdir(parents=True)
    path.write_text("gare_depart,gare_arrivee\nA,B\n", encoding="utf-8")
    charger_liaisons_detail.clear()
    try:
        assert len(charger_liaisons_detail()) == 1
        assert "liaisons_detail.csv : 1 lignes" in (log_directory / "debug.log").read_text(encoding="utf-8")
        path.unlink()
        charger_liaisons_detail.clear()
        with pytest.raises(FileNotFoundError):
            charger_liaisons_detail()
        error = (log_directory / "error.log").read_text(encoding="utf-8")
        assert "Impossible de charger le fichier data/processed/liaisons_detail.csv" in error
        assert "FileNotFoundError" in error
    finally:
        charger_liaisons_detail.clear()


def test_map_and_comparison_changes_logged_without_rerun_duplicates(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from projet_kit_data.web_data import ROOT

    events = []
    monkeypatch.setattr(activity, "log_action", lambda event, **details: events.append((event, details)))
    app = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    app.switch_page("pages/routes_network.py").run()
    assert not app.exception
    watched = {"carte_filters", "carte_route_view", "route_comparison"}
    initial = [entry for entry in events if entry[0] in watched]
    assert {entry[0] for entry in initial} == watched
    app.run()
    assert [entry for entry in events if entry[0] in watched] == initial
    app.radio(key="carte_mode").set_value("Taux de retard").run()
    assert not app.exception
    assert [details for event, details in events if event == "carte_filters"][-1]["color_mode"] == "taux"
    selection = app.selectbox(key="cmp_B")
    selection.select(selection.options[-1]).run()
    assert not app.exception
    comparisons = [details for event, details in events if event == "route_comparison"]
    assert len(comparisons) == 2
    assert comparisons[-1]["route_b"] == selection.options[-1]
    assert not any(event == "download" for event, _ in events)
