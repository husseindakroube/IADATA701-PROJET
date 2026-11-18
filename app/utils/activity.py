'Journalise les interactions lors des changements de sélection, sans répétition à chaque exécution.'

import json
import logging
from uuid import uuid4

import streamlit as st

LOGGER = logging.getLogger("projet_kit_data.activity")


def log_action(event: str, **details: object) -> None:
    'Enregistre une action avec un identifiant de session anonyme et des valeurs échappées en JSON.'
    if "_log_session" not in st.session_state:
        st.session_state["_log_session"] = uuid4().hex
    LOGGER.info("session=%s event=%s details=%s", st.session_state["_log_session"],
                event, json.dumps(details, ensure_ascii=False, default=str))


def log_selection(event: str, **details: object) -> None:
    'Enregistre la sélection initiale et ses changements dans cette session.'
    state_key = f"_logged_{event}"
    snapshot = json.dumps(details, sort_keys=True, ensure_ascii=False, default=str)
    if st.session_state.get(state_key) != snapshot:
        log_action(event, **details)
        st.session_state[state_key] = snapshot
