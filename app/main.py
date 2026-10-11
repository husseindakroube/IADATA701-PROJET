import streamlit as st
from pathlib import Path

IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"
st.set_page_config(
    page_title="RailInsight | SNCF TGV",
    page_icon=str(IMAGES_DIR / "TGV_icon.png"),
    layout="wide",
)
st.title("Bienvenue sur TGVision|Voyager en TGV")