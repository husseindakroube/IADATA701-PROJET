from pathlib import Path
import streamlit as st


def load_stylecss():
    css_dir = Path(__file__).resolve().parent.parent / "styles"

    st.html(css_dir / "style.css")

def load_css():
    css_dir = Path(__file__).resolve().parent.parent / "styles"

    st.html(css_dir / "style.css")
    st.html(css_dir / "sidebar.css")