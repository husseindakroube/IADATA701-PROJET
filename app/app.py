from base64 import b64encode
from html import escape
from pathlib import Path
import sys
import logging

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st
from utils.styles import load_css
from utils.footer import render_footer

# Résoudre les ressources depuis ce fichier, indépendamment du dossier de lancement.
BASE_PATH = Path(__file__).resolve().parent
IMAGES_PATH = BASE_PATH.parent / "images"
from projet_kit_data.logging_config import configure_logging
from utils.activity import log_selection

try:
    LOGGER = configure_logging()
except OSError:
    logging.getLogger(__name__).exception('Impossible d’initialiser les fichiers de journalisation')
    st.error("Impossible de créer les journaux. Vérifiez les droits du dossier logs/.")
    st.stop()

st.set_page_config(
    page_title="TGVISION | SNCF TGV",
    page_icon=str(IMAGES_PATH / "TGV_icon.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()

# Déclarer les pages communes aux menus de bureau et mobile.
pages = [
    st.Page(
        "pages/main.py",
        title="Accueil",
        default=True
    ),
    st.Page(
        "pages/data_quality.py",
        title="Qualité des données"
    ),
    st.Page(
        "pages/routes_network.py",
        title="Liaisons et réseau"
    ),
    st.Page(
        "pages/clusters.py",
        title="Profils et clusters"
    ),
    st.Page(
        "pages/predictions.py",
        title="Prédictions"
    ),
    st.Page(
        "pages/conclusions.py",
        title="Conclusions"
    ),
]

# Masquer le menu natif pour utiliser les barres de navigation personnalisées.
pg = st.navigation(pages, position="hidden")

# Construire les liens mobiles ; aria-current signale la page active aux lecteurs d’écran.
liens_navigation_mobile = []
for page in pages:
    page_active = page.url_path == pg.url_path
    classe_lien = "lien-navigation"
    if page_active:
        classe_lien += " lien-navigation-active"
    attribut_page_courante = ' aria-current="page"' if page_active else ""
    adresse_page = f"./{page.url_path}" if page.url_path else "./"
    # Échapper les valeurs avant de les insérer dans le HTML.
    liens_navigation_mobile.append(
        f'<a class="{classe_lien}" href="{escape(adresse_page, quote=True)}"{attribut_page_courante}>'
        f'{escape(page.title)}</a>'
    )

# Intégrer le logo au HTML en base64, sans URL de fichier statique.
logo_mobile = b64encode((IMAGES_PATH / "SNCF_logo.png").read_bytes()).decode("ascii")
# La clé fournit un sélecteur CSS st-key ; details/summary gère le menu sans JavaScript.
with st.container(key="barre-navigation-mobile"):
    st.html(f"""
        <nav class="barre-navigation-mobile" aria-label="Navigation principale">
            <a class="marque-navigation-mobile" href="./" aria-label="TGVision — Accueil">
                <img src="data:image/png;base64,{logo_mobile}" alt="SNCF" />
                <span>TGVision</span>
            </a>
            <details class="menu-navigation-mobile">
                <summary>Menu</summary>
                <div class="liens-navigation-mobile">{''.join(liens_navigation_mobile)}</div>
            </details>
        </nav>
    """)

with st.container(key="barre-navigation-haut"):

    # Donner davantage de largeur aux intitulés longs dans la barre de bureau.
    nav_columns = st.columns(
        [0.9, 2.4] + [max(0.9, len(page.title) / 10) for page in pages],
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
            <div class="marque-navigation">
                <div class="titre-navigation">
                    TGVision
                </div>
                <p class="slogan-navigation">
                    LE RAIL SOUS UN NOUVEAU REGARD
                </p>
            </div>
        """)

    for column, page in zip(nav_columns[2:], pages):

        with column:

            is_active = page.url_path == pg.url_path

            link_class = (
                "lien-navigation lien-navigation-active"
                if is_active
                else "lien-navigation"
            )

            href = (
                f"./{page.url_path}"
                if page.url_path
                else "./"
            )

            st.html(
                f'<a class="{link_class}" href="{escape(href, quote=True)}">'
                f'{escape(page.title)}'
                '</a>'
            )


# Afficher la page sélectionnée après les éléments communs de l’application.
log_selection("page_view", page=pg.title)
try:
    pg.run()
    render_footer()
except Exception:
    LOGGER.exception('Échec de l’exécution de la page : %s', pg.title)
    raise
