from pathlib import Path

import streamlit as st

GLOBAL_Path = Path(__file__).resolve().parent
IMAGES_PATH = GLOBAL_Path.parent.parent / "images"
CSS_FILE = GLOBAL_Path.parent / "styles" / "style.css"

st.html(CSS_FILE)

st.markdown("""
<style>
    .block-container {
        padding-top: 0rem !important;
    }
</style>
""", unsafe_allow_html=True)

title_title, Logo_title = st.columns(
    [1, 1.4],
    gap="large",
    vertical_alignment="center",
)

with Logo_title:
    st.image(
        str(IMAGES_PATH / "TGV_title.png"),
        width="content",
    )

with title_title:
    st.html(
        """
        <section class="main">
            <p class="main-label">
                LE RAIL À TRAVERS LES DONNÉES
            </p>

            <h1 class="main-title">TGVision</h1>

            <h2 class="main-slogan">
                <span class="slogan-line">
                  Au-delà des horaires,
                </span>
                <span class="slogan-line slogan-offset">
                  la réalité des voyages.
                </span>
            </h2>

            <p class="main-description">
                La ponctualité ferroviaire sous un nouvel angle
            </p>

        </section>
        """
    )

st.markdown(
    """

<div style="
    height: 3px;
    background: linear-gradient(
        90deg,
        #2C7D67,
        #3E3EC9,
        #00D4FF
    );
    border-radius: 3px;
    margin: 20px 0;
"></div>
""",
    unsafe_allow_html=True,
)

st.html(
    '<p class="section-title">'
    "Bienvenue sur TGVision, une plateforme interactive dédiée à l'analyse de la ponctualité des TGV en France."
    "</p>"
)

st.html('<p class="main-label">DÉCOUVRIR TGVISION</p>')

st.markdown(
    """
<style>
.st-key-story_expander [data-testid="stExpander"] summary p {
    font-size: 2rem;
    font-weight: 700;
    color: transparent;
    line-height: 1.3;
    background: linear-gradient(135deg, #c7e9fb, #a6defa, #80d4f9, #5bc9f8, #35bef7);
    background-clip: text;
    -webkit-background-clip: text;
}
</style>
""",
    unsafe_allow_html=True,
)

with st.container(key="story_expander"):
    with st.expander("Et si chaque retard racontait une histoire ?", expanded=False):
        st.html(
            """
    <section class="story-section">
        <p class="story-text">
            Le train ne relie pas seulement des villes. Il rapproche les personnes et accompagne les moments importants de nos vies.
            <span class="story-text-line">
                Chaque jour, des millions de voyageurs parcourent la France en train. Certains se rendent au travail, d’autres retrouvent leurs proches, rentrent chez eux ou partent vers de nouvelles opportunités. Derrière chaque trajet se cachent du temps, des projets et des attentes.
            </span>
        </p>

        <p class="story-highlight">
            Pourtant, tout ne se passe pas toujours comme prévu.
        </p>

        <p class="story-text">
            Un retard peut faire manquer un rendez-vous important. Un train supprimé peut bouleverser tout un programme. 
            <span class = "story-highlight story-text-line">
                Une correspondance manquée peut transformer une journée ordinaire en une succession d’imprévus.
            </span>
            <span class="story-text-line">
                Ces perturbations ont des répercussions bien au-delà des voyageurs. Elles touchent aussi les entreprises et les territoires qui dépendent du réseau ferroviaire. La qualité du service ferroviaire ne se résume donc pas à de simples statistiques de ponctualité. Derrière ces chiffres se trouvent des réalités bien concrètes : du temps, des projets et des moments de vie qui comptent.
            </span>
        </p>
    </section>
    """
        )

st.header("Notre problématique")
st.write("XXXXXXXXXXXXX")

st.info("**I. XXX :** XXXXXXX\n\n**II. XXX :** XXXXXX\n\n**III. XXXXX :** XXXXX ")

st.header("Notre problématique -- ")
st.markdown("XXXX")

col1, col2, col3 = st.columns(3)

with col1, st.container(border=True):
    st.subheader("🚆 XXXXXXX")
    st.write("XXXXXXXX")
    st.page_link(
        "pages/page1.py",
        label="XXXXXXX →",
    )

with col2, st.container(border=True):
    st.subheader("🚉 XXXXXXXX")
    st.write("XXXXXXX")
    st.page_link(
        "pages/page2.py",
        label="XXXXXXX →",
    )

with col3, st.container(border=True):
    st.subheader("🚅 XXXXXXXX")
    st.write("XXXXXX")
    if st.button("Découvrir →", key="page3_button"):
        st.switch_page("pages/page3.py")
