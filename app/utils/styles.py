"""Chargement des feuilles de style communes à toutes les pages."""

from pathlib import Path
import streamlit as st


def load_css() -> None:
    """Lit les fichiers CSS du projet et les injecte dans la page active."""
    # Retrouver les feuilles de style depuis le dossier app.
    BASE_PATH = Path(__file__).resolve().parent.parent
    COLORSTYLE_FILE = BASE_PATH / "styles" / "colors.css"
    CSSSPAGE_FILE = BASE_PATH / "styles" / "page-principal.css"
    CSSBARRE_FILE = BASE_PATH / "styles" / "barre-navigation.css"
    ANALYSIS_FILE = BASE_PATH / "styles" / "analysis-pages.css"

    # Charger la palette puis les composants dans un ordre de cascade stable.
    css = (
        COLORSTYLE_FILE.read_text(encoding="utf-8")
        + "\n"
        + CSSSPAGE_FILE.read_text(encoding="utf-8")
        + "\n"
        + CSSBARRE_FILE.read_text(encoding="utf-8")
        + "\n"
        + ANALYSIS_FILE.read_text(encoding="utf-8")
    )
    # Injecter les règles CSS sans ajouter de contenu visible.
    st.html(f"<style>{css}</style>")
