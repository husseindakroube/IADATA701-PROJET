from pathlib import Path

import streamlit as st

BASE_PATH = Path(__file__).resolve().parent
IMAGES_PATH = BASE_PATH.parent / "images"
VIDEO_PATH = BASE_PATH.parent / "videos"
CSS_FILE = BASE_PATH / "styles" / "sidebar.css"

st.html(CSS_FILE)

st.set_page_config(
    page_title="RailInsight | SNCF TGV",
    page_icon=str(IMAGES_PATH / "TGV_icon.png"),
    layout="wide",
)

pages = [
    st.Page("pages/main.py", title="Accueil", icon=":material/home:", default=True),
    st.Page("pages/page1.py", title="XXXXXXXX", icon=":material/dashboard:"),
    st.Page("pages/page2.py", title="XXXXXXX", icon=":material/analytics:"),
    st.Page("pages/page3.py", title="XXXXXXXX", icon=":material/train:"),
]

pg = st.navigation(pages, position="hidden")

with st.sidebar:
    st.markdown("## 🚄 TGVision")
    st.caption("LE RAIL À TRAVERS LES DONNÉES")

    st.divider()

    st.caption("NAVIGATION")

    for page in pages:
        st.page_link(page)

    st.divider()
    st.caption("SNCF TGV · Data Analytics")
    with st.expander("🎬 Découvrez la SNCF", expanded=False):
        st.video(VIDEO_PATH / "Le groupe SNCF en bref.mp4")
        st.html("""
             <p class="siderbar-line">
                Découvrez le groupe SNCF et son rôle
                <span class= "siderbar-offset">
                  dans la mobilité en France.
                </span>
             </p>
             """)

pg.run()
