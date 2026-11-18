from pathlib import Path
import streamlit as st


def load_css():
    # Retrouver les feuilles de style depuis le dossier app.
    BASE_PATH = Path(__file__).resolve().parent.parent
    COLORSTYLE_FILE = BASE_PATH / "styles" / "colors.css"
    CSSSPAGE_FILE = BASE_PATH / "styles" / "page-principal.css"
    CSSBARRE_FILE = BASE_PATH / "styles" / "barre-navigation.css"

    # Charger la palette puis les composants dans un ordre de cascade stable.
    css = (
    COLORSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSSPAGE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSBARRE_FILE.read_text(encoding="utf-8")
)
    # Injecter les règles CSS sans ajouter de contenu visible.
    st.html(f"<style>{css}</style>")