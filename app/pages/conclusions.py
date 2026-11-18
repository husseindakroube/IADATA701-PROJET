"""Evidence boundaries and reproducibility of the imported work."""

import streamlit as st
from utils.data import report, table

from projet_kit_data.web_data import ROOT

st.title("Conclusions, limites et reproductibilité")
st.subheader("Ce que les résultats permettent de dire")
st.write(
    "Les graphes décrivent des relations de service différentes selon le périmètre "
    "national ou international. La centralité ne représente ni le trafic réel, "
    "ni la propagation des retards, ni une relation causale."
)
summary = table(
    "data/processed/graph/descriptive/network_summary.parquet", required=False
)
if not summary.empty:
    st.caption("Périmètre du rapport réseau : 2018-01 → 2026-09.")
    st.dataframe(summary, hide_index=True)
st.write(
    "L'application présente une baseline naïve et un modèle supervisé issus des "
    "fichiers de test. Ces deux résultats seuls ne permettent pas d'isoler l'apport "
    "du graphe ou du clustering. Les valeurs R² 0,4513 et 0,4595 de la proposition "
    "ne sont donc pas présentées comme une conclusion vérifiée."
)
st.subheader("Limites")
st.markdown(
    "- Données mensuelles sur une partie des services TGV ; pas de risque individuel.\n"
    "- Définitions de certains dénominateurs et seuils encore à confirmer.\n"
    "- Absence de variables externes, notamment météo et grèves.\n"
    "- Profils descriptifs non orientés, groupes parfois petits et services hétérogènes.\n"
    "- Traçabilité et généralisation temporelle des modèles à compléter."
)
st.subheader("Travail restant selon le cahier des charges")
path = ROOT / "docs/INTEGRATION_GAPS.md"
if path.is_file():
    with st.expander("État détaillé de l'intégration", expanded=True):
        st.markdown(path.read_text(encoding="utf-8"))
st.subheader("Documents et code reproductibles")
for relative, label in [
    ("docs/INTEGRATION_GAPS.md", "Liste des manques et correspondance des pages"),
    ("data/reports/data_contract.md", "Contrat des données"),
    ("data/reports/graph/research_report.md", "Rapport de recherche"),
    ("docs/integration_manifest.json", "Empreintes des fichiers importés"),
    ("README.md", "Installation et lancement"),
]:
    report(relative, label)
for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    report(path.relative_to(ROOT).as_posix(), f"Source : {path.name}")
