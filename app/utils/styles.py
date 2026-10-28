from pathlib import Path
import streamlit as st


def load_css():
    BASE_PATH = Path(__file__).resolve().parent.parent
    COLORSTYLE_FILE = BASE_PATH / "styles" / "colors.css"
    CSSSTYLE_FILE = BASE_PATH / "styles" / "style.css"
    CSSNAVBAR_FILE = BASE_PATH / "styles" / "navbar.css"

    css = (
    COLORSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSNAVBAR_FILE.read_text(encoding="utf-8")
)
    st.html(f"<style>{css}</style>")