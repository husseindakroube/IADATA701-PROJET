from pathlib import Path
import streamlit as st
from utils.data import filters, observations, scope_metrics, table

GLOBAL_Path = Path(__file__).resolve().parent
IMAGES_PATH = GLOBAL_Path.parent.parent / "images"

# Répartir le texte et le visuel d’accueil sur deux colonnes de largeurs différentes.
title_title, Logo_title = st.columns(
    [1, 1.5],
    gap="medium",
    vertical_alignment="center",
)

# Conserver le format GIF pour afficher l’animation du train.
with Logo_title:
    with st.container(
        horizontal_alignment="right"
    ):
      st.image(
         str(IMAGES_PATH / "TGV_title.gif"),
         width="content",
      )

# Les classes HTML reprennent les styles de page-principal.css.
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

# Séparer visuellement la présentation et le contenu détaillé.
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

# Replier le récit au départ ; la clé permet de cibler cet expander dans colors.css.
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
st.write("Dans quelle mesure la structure du réseau TGV est-elle associée à la régularité des liaisons, et peut-on exploiter cette structure pour améliorer la prédiction des retards ?")

# Chaque carte ouvre une page déclarée dans app.py.
st.subheader("Les données du projet")
st.caption("Source : SNCF — Régularité mensuelle TGV AQST. "
           "La date d'extraction n'est pas consignée dans les artefacts fournis.")
data = filters(observations())
scope_metrics(data)
st.info("Le taux global d'arrivée en retard reste à valider : le contrat fourni "
        "ne confirme pas encore son dénominateur. Les annulations mensuelles sont "
        "consultables dans l'exploration des liaisons.")
st.subheader("Trois repères issus des résultats disponibles")
st.write(f"**{data.date.nunique()} mois observés dans le périmètre sélectionné** : "
         "il s'agit d'observations mensuelles, pas d'horaires de trains individuels.")
network = table("data/processed/graph/descriptive/network_summary.parquet", required=False)
if not network.empty:
    for row in network.itertuples():
        st.write(f"**{row.service} : {row.node_count} gares et {row.edge_count} liaisons "
                 "orientées** dans le graphe enregistré (2018-01 → 2026-09). "
                 "Ce périmètre fixe décrit les services AQST, pas l'infrastructure ferroviaire.")

# Les clés distinguent les boutons portant tous le même libellé.
col1, col2, col3 = st.columns(3)

with col1, st.container(border=True):
    st.subheader("Qualité des données")
    st.write("Consulter les anomalies et les règles du prétraitement existant")
    if st.button("Découvrir →", key="data_quality_button"):
            st.switch_page("pages/data_quality.py")

with col2, st.container(border=True):
    st.subheader("Liaisons et réseau")
    st.write("Étude de la structure du réseau ferroviaire et de ses relations avec la régularité des liaisons")
    if st.button("Découvrir →", key="routes_network_button"):
            st.switch_page("pages/routes_network.py")

with col3, st.container(border=True):
    st.subheader("🚅 Prédiction des retards")
    st.write("Comparaison des modèles de machine learning avec et sans caractéristiques du graphe pour évaluer leur apport prédictif")
    if st.button("Découvrir →", key="predictions_button"):
        st.switch_page("pages/predictions.py")

col4, col5 = st.columns(2)
with col4, st.container(border=True):
    st.subheader("Profils et clusters")
    st.write("Explorer les groupes de liaisons déjà calculés")
    st.page_link("pages/clusters.py", label="Consulter les profils →")
with col5, st.container(border=True):
    st.subheader("Conclusions et reproductibilité")
    st.write("Consulter les limites, les sources et les fonctionnalités manquantes")
    st.page_link("pages/conclusions.py", label="Consulter le bilan →")
st.divider()
st.caption("Projet collectif IADATA701 — interface TGVision et analyses de l'équipe. "
           "Les noms et rôles détaillés de l'équipe restent à renseigner.")
st.markdown("[Code du projet](https://github.com/husseindakroube/IADATA701-PROJET)")

