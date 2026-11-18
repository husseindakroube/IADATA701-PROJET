"Page d accueil de TGVision : présentation du projet, chiffres clés et navigation."

from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

from utils.data import observations, table

GLOBAL_Path = Path(__file__).resolve().parent
IMAGES_PATH = GLOBAL_Path.parent.parent / "images"


# =============================================================================
# En-tête visuel : hero + image
# =============================================================================

title_title, Logo_title = st.columns(
    [1, 1.5],
    gap="medium",
    vertical_alignment="center",
)

with Logo_title:
    with st.container(horizontal_alignment="right"):
        st.image(
            str(IMAGES_PATH / "tgv_inoui_gare_de_lyon.jpg"),
            width="stretch",
        )

with title_title:
    st.html(
        """
        <section class="principal">
            <p class="etiquette-principale">LE RAIL À TRAVERS LES DONNÉES</p>
            <h1 class="titre-principal">TGVision</h1>
            <h2 class="slogan-principal">
                <span class="ligne-slogan">Au-delà des horaires,</span>
                <span class="ligne-slogan decalage-slogan">la réalité des voyages.</span>
            </h2>
            <p class="description-principale">
                La ponctualité ferroviaire sous un nouvel angle
            </p>
        </section>
        """
    )

st.markdown(
    """<div style="height:3px;background:linear-gradient(90deg,#2C7D67,#3E3EC9,#00D4FF);
    border-radius:3px;margin:20px 0;"></div>""",
    unsafe_allow_html=True,
)

st.html(
    '<p class="titre-section">'
    "Bienvenue sur TGVision, une plateforme interactive dédiée à l'analyse "
    "de la ponctualité des TGV en France."
    "</p>"
)


# =============================================================================
# Récit narratif replié
# =============================================================================

st.html('<p class="etiquette-principale">DÉCOUVRIR TGVISION</p>')

with st.container(key="histoire_deroulante"):
    with st.expander("Et si chaque retard racontait une histoire ?", expanded=False):
        st.html(
            """
    <section class="section-histoire">
        <p class="texte-histoire">
            Le train ne relie pas seulement des villes. Il rapproche les personnes et accompagne les moments importants de nos vies.
            <span class="ligne-texte-histoire">
                Chaque jour, des millions de voyageurs parcourent la France en train. Certains se rendent au travail, d'autres retrouvent leurs proches, rentrent chez eux ou partent vers de nouvelles opportunités. Derrière chaque trajet se cachent du temps, des projets et des attentes.
            </span>
        </p>
        <p class="histoire-mise-en-valeur">Pourtant, tout ne se passe pas toujours comme prévu.</p>
        <p class="texte-histoire">
            Un retard peut faire manquer un rendez-vous important. Un train supprimé peut bouleverser tout un programme.
            <span class="histoire-mise-en-valeur ligne-texte-histoire">
                Une correspondance manquée peut transformer une journée ordinaire en une succession d'imprévus.
            </span>
            <span class="ligne-texte-histoire">
                Ces perturbations ont des répercussions bien au-delà des voyageurs. Elles touchent aussi les entreprises et les territoires qui dépendent du réseau ferroviaire. La qualité du service ferroviaire ne se résume donc pas à de simples statistiques de ponctualité. Derrière ces chiffres se trouvent des réalités bien concrètes : du temps, des projets et des moments de vie qui comptent.
            </span>
        </p>
    </section>
    """
        )


# =============================================================================
# Problématique
# =============================================================================

st.header("Notre problématique")
st.write(
    "**Dans quelle mesure la structure du réseau TGV est-elle associée à la "
    "régularité des liaisons, et peut-on exploiter cette structure pour "
    "améliorer la prédiction des retards ?**"
)


# =============================================================================
# Chiffres clés du projet (vue globale, non filtrable)
# =============================================================================

st.subheader("Le projet en chiffres")
st.caption(
    "Source : SNCF — Régularité mensuelle TGV AQST. "
    "Données couvrant janvier 2018 à septembre 2026."
)

donnees = observations()
clusters_liaisons = table("data/processed/clusters_liaisons.csv", required=False)

nb_observations = len(donnees)
nb_gares = pd.concat([donnees.gare_depart, donnees.gare_arrivee]).nunique()
nb_liaisons = len(donnees[["service", "gare_depart", "gare_arrivee"]].drop_duplicates())
nb_mois = donnees.date.nunique()
nb_clusters = clusters_liaisons.cluster.nunique() if not clusters_liaisons.empty else 4

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Observations mensuelles", f"{nb_observations:,}".replace(",", " "))
with c2:
    st.metric("Gares analysées", nb_gares)
with c3:
    st.metric("Liaisons orientées", nb_liaisons)
with c4:
    st.metric("Mois couverts", nb_mois)
with c5:
    st.metric("Profils de liaisons", nb_clusters)


# =============================================================================
# Résultats clés du projet
# =============================================================================

st.subheader("Trois résultats clés")

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1, st.container(border=True):
    st.markdown("**Structure du réseau**")
    st.caption(
        "Analyse par théorie des graphes des 130 liaisons orientées. "
        "Paris Lyon, Lyon Part Dieu et Paris Montparnasse sont les gares de "
        "plus forte centralité, confirmant une topologie en étoile centrée sur Paris."
    )
with col_r2, st.container(border=True):
    st.markdown("**Typologie des liaisons**")
    st.caption(
        "Clustering non supervisé K-Means sur la durée et les causes de retard. "
        "4 profils distincts identifiés, dont un groupe d'internationales longues "
        "(Francfort, Madrid, Italie) nettement moins ponctuelles que la moyenne."
    )
with col_r3, st.container(border=True):
    st.markdown("**Apport prédictif structurel**")
    st.caption(
        "Comparaison de 4 modèles enrichis avec centralités et clusters, "
        "après correction d'une fuite temporelle. Les features structurelles "
        "n'apportent pas de gain significatif par rapport à la baseline HistGradientBoosting."
    )


# =============================================================================
# Navigation par cartes vers les 5 autres pages
# =============================================================================

st.subheader("Explorer le projet")

cards = [
    (
        "🔍",
        "Qualité des données",
        "Audit des 12 907 observations, règles de nettoyage et indicateurs de fiabilité",
        "data_quality",
        "Découvrir →",
    ),
    (
        "🗺️",
        "Liaisons et réseau",
        "Carte interactive des 130 liaisons et analyse structurelle du réseau TGV",
        "routes_network",
        "Explorer la carte →",
    ),
    (
        "👥",
        "Profils et clusters",
        "Exploration des 4 profils de liaisons issus du clustering non supervisé",
        "clusters",
        "Consulter les profils →",
    ),
    (
        "🤖",
        "Prédiction des retards",
        "Comparaison de cinq modèles de machine learning et modèle retenu",
        "predictions",
        "Voir les modèles →",
    ),
    (
        "📊",
        "Conclusions et méthodologie",
        "Synthèse des résultats, limites de l'étude et ressources de reproductibilité",
        "conclusions",
        "Lire la synthèse →",
    ),
]

cards_html = []
for icon, title, description, page, button in cards:
    cards_html.append(
        '<article class="exploration-card">'
        f'<h3><span class="exploration-card-icon" aria-hidden="true">{icon}</span>'
        f"<span>{escape(title)}</span></h3>"
        f"<p>{escape(description)}</p>"
        f'<a class="exploration-card-button" href="./{page}" '
        f'aria-label="{escape(button)} — {escape(title)}">{escape(button)}</a>'
        "</article>"
    )
st.html(
    '<section class="exploration-cards" aria-label="Explorer le projet">'
    + "".join(cards_html)
    + "</section>"
)
