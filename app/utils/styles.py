from pathlib import Path
import streamlit as st


def load_css():
    BASE_PATH = Path(__file__).resolve().parent.parent
    COLORSTYLE_FILE = BASE_PATH / "styles" / "colors.css"
    CSSSTYLE_FILE = BASE_PATH / "styles" / "page-principal.css"
    CSSNAVBAR_FILE = BASE_PATH / "styles" / "barre-navigation.css"

    css = (
    COLORSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSNAVBAR_FILE.read_text(encoding="utf-8")
)
    st.html(f"<style>{css}</style>")