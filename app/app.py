from pathlib import Path
import streamlit as st

BASE_PATH = Path(__file__).resolve().parent
IMAGES_PATH = BASE_PATH.parent / "images"
VIDEO_PATH = BASE_PATH.parent / "videos"
AUDIT_PATH = BASE_PATH.parent / "audit"
CSSSIDEBAR_FILE = BASE_PATH / "styles" / "sidebar.css"
CSSSTYLE_FILE = BASE_PATH / "styles" / "style.css"

css = (
    CSSSIDEBAR_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSSTYLE_FILE.read_text(encoding="utf-8")
)

st.html(f"<style>{css}</style>")

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
    st.markdown(
        '<h2 class="main-title">🚄 TGVision</h2>', 
         unsafe_allow_html=True
        )
    st.caption("LE RAIL À TRAVERS LES DONNÉES")
    st.divider()
    st.html(
        """
           <p class = "main-label">
              NAVIGATION
           </p>
        """
    )

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

    st.audio(
    AUDIT_PATH / "just keep tootin.mp3",
    format="audio/mpeg",
    autoplay=True,
    loop=True
)

pg.run()
