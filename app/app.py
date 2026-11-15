from base64 import b64encode
from html import escape
from pathlib import Path

import streamlit as st
from utils.styles import load_css

BASE_PATH = Path(__file__).resolve().parent
IMAGES_PATH = BASE_PATH.parent / "images"
AUDIT_PATH = BASE_PATH.parent / "audit"

st.set_page_config(
    page_title="TGVISION | SNCF TGV",
    page_icon=str(IMAGES_PATH / "TGV_icon.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()

pages = [
    st.Page(
        "pages/main.py",
        title="Accueil",
        default=True
    ),
    st.Page(
        "pages/page1.py",
        title="Exploration des données"
    ),
    st.Page(
        "pages/page2.py",
        title="Analyse du réseau TGV"
    ),
    st.Page(
        "pages/page3.py",
        title="Prédiction des retards"
    ),
    st.Page(
        "pages/page4.py",
        title="A PROPRE"
    ),
]

pg = st.navigation(pages, position="hidden")

liens_navigation_mobile = []
for page in pages:
    page_active = page.url_path == pg.url_path
    classe_lien = "lien-navigation"
    if page_active:
        classe_lien += " lien-navigation-active"
    attribut_page_courante = ' aria-current="page"' if page_active else ""
    adresse_page = f"./{page.url_path}" if page.url_path else "./"
    liens_navigation_mobile.append(
        f'<a class="{classe_lien}" href="{escape(adresse_page, quote=True)}"{attribut_page_courante}>'
        f'{escape(page.title)}</a>'
    )

logo_mobile = b64encode((IMAGES_PATH / "SNCF_logo.png").read_bytes()).decode("ascii")
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


with st.container(key="audio-arriere-plan"):
    st.audio(
        AUDIT_PATH / "just keep tootin.mp3",
        format="audio/mpeg",
        autoplay=True,
        loop=True
    )

st.html("""
<script>
(() => {
    const KEY = "tgvision_audio_time";

    function initializeAudio() {
        const audio = document.querySelector(
            ".st-key-audio-arriere-plan audio"
        );

        if (!audio) return false;
        if (audio.dataset.tgvisionReady) return true;

        audio.dataset.tgvisionReady = "true";

        const savedTime = Number(
            sessionStorage.getItem(KEY) || 0
        );

        function restore() {
            if (
                Number.isFinite(savedTime) &&
                savedTime > 0 &&
                Number.isFinite(audio.duration)
            ) {
                audio.currentTime = Math.min(
                    savedTime,
                    Math.max(0, audio.duration - 0.1)
                );
            }
        }

        if (audio.readyState >= 1) {
            restore();
        } else {
            audio.addEventListener(
                "loadedmetadata",
                restore,
                { once: true }
            );
        }

        function save() {
            sessionStorage.setItem(
                KEY,
                String(audio.currentTime)
            );
        }

        audio.addEventListener("timeupdate", save);
        window.addEventListener("pagehide", save);

        return true;
    }

    if (!initializeAudio()) {
        const observer = new MutationObserver(() => {
            if (initializeAudio()) {
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
})();
</script>
""", unsafe_allow_javascript=True)

pg.run()
