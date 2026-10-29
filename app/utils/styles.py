from pathlib import Path
import streamlit as st


def load_css():
    BASE_PATH = Path(__file__).resolve().parent.parent
    COLORSTYLE_FILE = BASE_PATH / "styles" / "colors.css"
    CSSSPAGE_FILE = BASE_PATH / "styles" / "page-principal.css"
    CSSBARRE_FILE = BASE_PATH / "styles" / "barre-navigation.css"
    CSSVIDEO_FILE = BASE_PATH / "styles" / "video-modification.css"

    css = (
    COLORSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSSPAGE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSBARRE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSVIDEO_FILE.read_text(encoding="utf-8")
)
    st.html(f"<style>{css}</style>")