"Pied de page commun avec logos locaux et coordonnées des institutions."

from base64 import b64encode
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]


def render_footer() -> None:
    "Affiche le pied de page sans télécharger de ressources pendant l’exécution."
    telecom = b64encode((ROOT / "images/telecom_paris.svg").read_bytes()).decode(
        "ascii"
    )
    sncf = b64encode((ROOT / "images/SNCF_logo.png").read_bytes()).decode("ascii")
    css = (ROOT / "app/styles/footer.css").read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")
    st.html(f"""
        <footer class="tgvision-footer" aria-label="Informations et contacts">
            <div class="tgvision-footer-grid">
                <section class="tgvision-footer-contact">
                    <a class="tgvision-footer-brand" href="./">TGVision</a>
                    <p class="tgvision-footer-tagline">LE RAIL SOUS UN NOUVEAU REGARD</p>
                    <p><strong>Adresse :</strong> Télécom Paris<br>
                        19 place Marguerite Perey · 91120 Palaiseau, France</p>
                    <p><strong>Téléphone de l’accueil :</strong>
                        <a class="tgvision-footer-phone" href="tel:+33175319200">+33 1 75 31 92 00</a></p>
                    <a href="https://www.telecom-paris.fr/fr/ecole/bref/acces-contact"
                       target="_blank" rel="noopener noreferrer">Accès et contact Télécom Paris ↗</a>
                </section>
                <section>
                    <a class="tgvision-footer-logo" href="https://www.telecom-paris.fr/"
                       target="_blank" rel="noopener noreferrer" aria-label="Site de Télécom Paris">
                        <img src="data:image/svg+xml;base64,{telecom}" alt="Télécom Paris" width="108" height="108">
                    </a>
                    <h2>Télécom Paris</h2>
                    <p>Projet académique IADATA701.<br>Explorer, analyser et comprendre les données ferroviaires.</p>
                </section>
                <section>
                    <a class="tgvision-footer-logo" href="https://www.sncf-reseau.com/"
                       target="_blank" rel="noopener noreferrer" aria-label="Site de SNCF Réseau">
                        <img class="tgvision-footer-sncf" src="data:image/png;base64,{sncf}"
                             alt="SNCF Réseau" width="130" height="108">
                    </a>
                    <h2>Données SNCF</h2>
                    <p>Régularité mensuelle TGV AQST.<br>Des données publiques au service de l’analyse.</p>
                </section>
            </div>
            <div class="tgvision-footer-bottom">
                <span>TGVision · Projet étudiant IADATA701</span>
                <a href="https://github.com/husseindakroube/IADATA701-PROJET"
                   target="_blank" rel="noopener noreferrer">Code du projet ↗</a>
            </div>
        </footer>
    """)
