from pathlib import Path
import streamlit as st

GLOBAL_Path = Path(__file__).resolve().parent
IMAGES_PATH = GLOBAL_Path.parent.parent / "images"

title_title, Logo_title = st.columns(
    [1, 1.5],
    gap="medium",
    vertical_alignment="center",
)

with Logo_title:
    with st.container(
        horizontal_alignment="right"
    ):
      st.image(
         str(IMAGES_PATH / "TGV_title.gif"),
         width="content",
      )

with title_title:
    st.html(
        """
        <section class="principal">
            <p class="etiquette-principale">
                LE RAIL À TRAVERS LES DONNÉES
            </p>

            <h1 class="titre-principal">TGVision</h1>

            <h2 class="slogan-principal">
                <span class="ligne-slogan">
                  Au-delà des horaires,
                </span>
                <span class="ligne-slogan decalage-slogan">
                  la réalité des voyages.
                </span>
            </h2>

            <p class="description-principale">
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
    '<p class="titre-section">'
    "Bienvenue sur TGVision, une plateforme interactive dédiée à l'analyse de la ponctualité des TGV en France."
    "</p>"
)

st.html('<p class="etiquette-principale">DÉCOUVRIR TGVISION</p>')

with st.container(key="histoire_deroulante"):
    with st.expander("Et si chaque retard racontait une histoire ?", expanded=False):
        st.html(
            """
    <section class="section-histoire">
        <p class="texte-histoire">
            Le train ne relie pas seulement des villes. Il rapproche les personnes et accompagne les moments importants de nos vies.
            <span class="ligne-texte-histoire">
                Chaque jour, des millions de voyageurs parcourent la France en train. Certains se rendent au travail, d’autres retrouvent leurs proches, rentrent chez eux ou partent vers de nouvelles opportunités. Derrière chaque trajet se cachent du temps, des projets et des attentes.
            </span>
        </p>

        <p class="histoire-mise-en-valeur">
            Pourtant, tout ne se passe pas toujours comme prévu.
        </p>

        <p class="texte-histoire">
            Un retard peut faire manquer un rendez-vous important. Un train supprimé peut bouleverser tout un programme. 
            <span class = "histoire-mise-en-valeur ligne-texte-histoire">
                Une correspondance manquée peut transformer une journée ordinaire en une succession d’imprévus.
            </span>
            <span class="ligne-texte-histoire">
                Ces perturbations ont des répercussions bien au-delà des voyageurs. Elles touchent aussi les entreprises et les territoires qui dépendent du réseau ferroviaire. La qualité du service ferroviaire ne se résume donc pas à de simples statistiques de ponctualité. Derrière ces chiffres se trouvent des réalités bien concrètes : du temps, des projets et des moments de vie qui comptent.
            </span>
        </p>
    </section>
    """
        )

st.header("Notre problématique")
st.write("XXXXXXXXXXXXX")

st.info("**I. XXX :** XXXXXXX\n\n**II. XXX :** XXXXXX\n\n**III. XXXXX :** XXXXX ")

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

