from pathlib import Path
import streamlit as st


BASE_PATH = Path(__file__).resolve().parent

IMAGES_PATH = BASE_PATH.parent / "images"
AUDIT_PATH = BASE_PATH.parent / "audit"

COLORSTYLE_FILE = BASE_PATH / "styles" / "colors.css"
CSSSTYLE_FILE = BASE_PATH / "styles" / "style.css"
CSSNAVBAR_FILE = BASE_PATH / "styles" / "navbar.css"


st.set_page_config(
    page_title="RailInsight | SNCF TGV",
    page_icon=str(IMAGES_PATH / "TGV_icon.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)


css = (
    COLORSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSSTYLE_FILE.read_text(encoding="utf-8")
    + "\n"
    + CSSNAVBAR_FILE.read_text(encoding="utf-8")
)

st.html(f"<style>{css}</style>")

pages = [
    st.Page(
        "pages/main.py",
        title="Accueil",
        icon=":material/home:",
        default=True
    ),
    st.Page(
        "pages/page1.py",
        title="XXXXXXXX",
        icon=":material/dashboard:"
    ),
    st.Page(
        "pages/page2.py",
        title="XXXXXXX",
        icon=":material/analytics:"
    ),
    st.Page(
        "pages/page3.py",
        title="XXXXXXXX",
        icon=":material/train:"
    ),
]

pg = st.navigation(pages, position="hidden")


with st.container(key="top-navbar"):

    nav_columns = st.columns(
        [0.9, 2.4, 1.2, 1.2, 1.2, 1.2],
        gap="small",
        vertical_alignment="center"
    )

    with nav_columns[0]:
        st.image(
            str(IMAGES_PATH / "SNCF_logo.png"),
            width=85
        )

    with nav_columns[1]:
        st.html("""
            <div class="navbar-brand">
                <div class="main-title">
                    TGVision
                </div>
                <p class="navbar-slogan">
                    LE RAIL SOUS UN NOUVEAU REGARD
                </p>
            </div>
        """)

    for column, page in zip(nav_columns[2:], pages):

        with column:

            if page.url_path == pg.url_path:
                with st.container(key="top-active"):
                    st.page_link(
                        page,
                        label=page.title,
                        icon="",
                        width="stretch"
                    )
            else:
                st.page_link(
                    page,
                    label=page.title,
                    icon="",
                    width="stretch"
                )


with st.container(key="background-audio"):
    st.audio(
        AUDIT_PATH / "just keep tootin.mp3",
        format="audio/mpeg",
        autoplay=True,
        loop=True
    )

pg.run()
