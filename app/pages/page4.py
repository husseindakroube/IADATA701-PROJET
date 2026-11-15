from pathlib import Path

import streamlit as st

st.html("""
<section class="conteneur-video-principal">

    <video
        class="video-arriere-plan"
        autoplay
        muted
        loop
        playsinline
        preload="metadata"
        aria-hidden="true"
    >
        <source
            src="/app/static/sncf.mp4"
            type="video/mp4"
        >
    </video>

</section>
""")

footer_css = (
    Path(__file__).resolve().parent.parent / "styles" / "footer.css"
).read_text(encoding="utf-8")
st.html(f"<style>{footer_css}</style>")

st.html("""
<footer class="pied-de-page" aria-label="Pied de page">
    <div class="grille-pied-de-page">
        <div class="marque-pied-de-page">
            <a class="logo-pied-de-page" href="./">TGVision<span>.</span></a>
            <p class="slogan-pied-de-page">LE RAIL SOUS UN NOUVEAU REGARD</p>
            <p>Comprendre la ponctualité des TGV,<br>un voyage à travers les données.</p>
        </div>

        <nav class="liens-pied-de-page" aria-label="Explorer TGVision">
            <h2>Explorer</h2>
            <a href="./">Accueil</a>
            <a href="./page1">Exploration des données</a>
            <a href="./page2">Analyse du réseau TGV</a>
            <a href="./page3">Prédiction des retards</a>
        </nav>

        <div class="projet-pied-de-page">
            <h2>Un projet, des perspectives</h2>
            <p>Un projet pédagogique réalisé dans le cadre du module IADATA701.
            Découvrez notre démarche et suivez son évolution.</p>
            <a class="bouton-pied-de-page"
               href="https://github.com/husseindakroube/IADATA701-PROJET"
               target="_blank" rel="noopener noreferrer">
                Voir le projet sur GitHub <span aria-hidden="true">↗</span>
            </a>
        </div>
    </div>

    <div class="mentions-pied-de-page">
        <span>TGVision · Projet IADATA701</span>
        <span>Application en cours de développement</span>
        <span>Réalisé avec Python &amp; Streamlit</span>
    </div>
</footer>
""")
