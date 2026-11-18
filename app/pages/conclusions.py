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
predictions = table("data/processed/ml/comparaison_predictions_test.parquet", required=False)
if not predictions.empty:
    from sklearn.metrics import mean_absolute_error, r2_score

    scores = {}
    for code in ["naive", "a", "b", "c", "d"]:
        scores[code] = (
            mean_absolute_error(predictions.delay_rate_15, predictions[f"prediction_{code}"]) * 100,
            r2_score(predictions.delay_rate_15, predictions[f"prediction_{code}"]),
        )
    best = min("abcd", key=lambda code: scores[code][0])
    st.write(
        f"Sur {len(predictions):,} observations de test, le modèle {best.upper()} "
        f"a la plus faible MAE des variantes A à D : {scores[best][0]:.3f} pp, "
        f"contre {scores['a'][0]:.3f} pp pour A et {scores['naive'][0]:.3f} pp "
        f"pour le naïf historique. Son R² est {scores[best][1]:.4f}, "
        f"contre {scores['naive'][1]:.4f} pour le naïf."
    )
    st.write(
        "Les différences de MAE entre les variantes sont faibles ; le naïf conserve "
        "ici un meilleur R². Ces résultats ne démontrent pas une amélioration générale "
        "grâce au réseau ou aux clusters. La stabilité sur d'autres périodes reste à vérifier. "
        "Ce classement descriptif du test ne remplace pas le choix du modèle sur validation."
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
with st.expander("Crédits photographiques"):
    st.markdown(
        "Photographie de l’accueil : **SNCF TGV inOui Réseau Duplex à Paris Gare de Lyon**, "
        "par [Superalbs / Wikimedia Commons](https://commons.wikimedia.org/wiki/"
        "File:SNCF_TGV_inOui_Reseau_Duplex_at_Paris_Gare_de_Lyon.jpg). "
        "Licence [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). "
        "Version de 1 280 pixels, sans recadrage ni retouche."
    )
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
