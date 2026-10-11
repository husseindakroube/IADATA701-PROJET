import streamlit as st
from pathlib import Path

IMAGES_PATH = Path(__file__).resolve().parent.parent / "images"
CSS_FILE = Path(__file__).resolve().parent / "styles" / "style.css"

st.html(CSS_FILE)

st.set_page_config(
    page_title="RailInsight | SNCF TGV",
    page_icon=str(IMAGES_PATH / "TGV_icon.png"),
    layout="wide",
)
col_logo, col_title = st.columns(
    [2, 6],
    gap="small",
    vertical_alignment="center",
)

with col_logo:
    st.image(
        str(IMAGES_PATH / "TGV_title.png"),
        width=190,
    )
with col_title:
    st.html(
        '<h1 class="hero-title">TGVision</h1>'
    )
    st.html(
        '<p class="hero-subtitle">'
        'La ponctualité ferroviaire sous un nouvel angle.'
        '</p>'
    )

st.html(
    '<p class="section-title">'
    "Bienvenue sur RailInsight, une plateforme interactive dédiée à l'analyse de la ponctualité des TGV en France."
    '</p>'
)
