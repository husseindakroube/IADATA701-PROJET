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

st.markdown("""
<style>
    [data-testid="stLogoSpacer"] {
        height: 0 !important;
    }

    [data-testid="stSidebarHeader"] {
        height: 3rem !important;
        margin-bottom: 0 !important;
    }

    [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:

    with st.container(key="sidebar-body"):

        Logo_title, title_title = st.columns(
           [1, 1.8],
           gap=None,
           vertical_alignment="center",
         )

        with Logo_title:
           st.image(
           str(IMAGES_PATH / "SNCF_logo.png"),
           width="content",
    )
        with title_title:
            st.html("""
            <h2 class="main-title" style="font-size: 2.4rem; margin: 0;">TGVision</h2>
            """)

        st.html("""
            <p class="main-label" style = "white-space: nowrap; margin : 0;">
                LE RAIL SOUS UN NOUVEAU REGARD
            </p>
            """
        )

        st.divider()

        st.html("""
            <p class="section-title">
                NAVIGATION
            </p>
        """)

        # for page in pages:
        #     st.page_link(page)

        with st.container(key="sidebar-button"):
             for page in pages:

              if page.url_path == pg.url_path:
                  with st.container(key="active-page"):
                       st.page_link(page)
              else:
                  st.page_link(page)

        st.divider()

        with st.expander("🎬 Découvrez la SNCF", expanded=True):

            st.video(VIDEO_PATH / "Le groupe SNCF en bref.mp4")

            st.html("""
                <p class="sidebar-line">
                    Découvrez le groupe SNCF et son rôle
                    <span class="sidebar-offset">
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
