'Audit qualité avec indicateurs dédiés et détails progressifs.'

import pandas as pd
import streamlit as st
from utils.activity import log_action
from utils.data import filters, observations, report, table

from projet_kit_data.web_data import FLAGS, KEYS, ROOT

st.caption("COMPRENDRE LA FIABILITÉ DES DONNÉES")
st.title("Du fichier source aux observations analysées")
st.write(
    "Repérez les observations à examiner et comprenez les choix de préparation. "
    "Les indicateurs de qualité signalent des points à vérifier ; ils ne corrigent "
    "ni ne suppriment automatiquement les données."
)
all_data = observations()
summary = st.container()
data = filters(all_data, label="Affiner le périmètre de l'audit", expanded=False)
flagged = data[FLAGS].fillna(False).any(axis=1)
with summary:
    st.caption("BILAN DU PÉRIMÈTRE SÉLECTIONNÉ")
    a, b, c, d = st.columns(4)
    with a, st.container(border=True):
        st.metric("Observations examinées", f"{len(data):,}")
    with b, st.container(border=True):
        st.metric("Observations signalées", f"{int(flagged.sum()):,}")
        st.caption("Chaque observation est comptée une seule fois.")
    with c, st.container(border=True):
        st.metric("Sans les quatre signalements", f"{int((~flagged).sum()):,}")
        st.caption("Cela ne garantit pas l'absence d'autres problèmes.")
    with d, st.container(border=True):
        st.metric("Lignes supprimées par l'ETL", "0")
        st.caption("Le prétraitement fourni conserve toutes les lignes.")

rules, completeness, lineage = st.tabs(
    ["Signalements de qualité", "Complétude et doublons", "Préparation et sources"]
)
with rules:
    st.subheader("Quels contrôles ont été déclenchés ?")
    labels = {
        "flag_negative_count": "Comptage négatif",
        "flag_sup30_lt_sup60": "Retards >30 min inférieurs aux >60 min",
        "flag_sup15_lt_sup30": "Retards >15 min inférieurs aux >30 min",
        "flag_cancellations_gt_planned": "Annulations supérieures aux prévisions",
    }
    chart, explanation = st.columns([2, 1], gap="large")
    with chart:
        counts = data[FLAGS].sum().rename(index=labels).rename("Observations")
        st.bar_chart(counts, horizontal=True, color="#0077B6")
    with explanation, st.container(border=True):
        st.markdown("**Comment lire ces contrôles**")
        st.write(
            "Une ligne peut déclencher plusieurs règles : les barres ne doivent "
            "pas être additionnées pour obtenir le nombre d'observations signalées."
        )
        st.caption("Le champ >15 min a un périmètre d'applicabilité à confirmer.")
    with st.expander("Examiner les observations signalées et les champs techniques"):
        st.dataframe(data.loc[flagged], hide_index=True)
    st.download_button(
        "Télécharger les signalements de ce périmètre",
        data.loc[flagged].to_csv(index=False).encode("utf-8-sig"),
        "anomalies_perimetre.csv",
        "text/csv",
        on_click=log_action, args=("download",),
        kwargs={"file": "anomalies_perimetre.csv", "observations": int(flagged.sum())},
    )
with completeness:
    st.subheader("Quelles informations manquent ?")
    st.caption(
        "Comptages sur le périmètre sélectionné ; une valeur manquante n'est pas un zéro."
    )
    missing = data.isna().sum().rename("Valeurs manquantes").to_frame()
    missing["Part des observations (%)"] = (
        missing["Valeurs manquantes"] / len(data) * 100
    )
    st.dataframe(missing.sort_values("Valeurs manquantes", ascending=False))
    st.metric(
        "Doublons de clé dans le fichier chargé", int(data.duplicated(KEYS).sum())
    )
    st.caption(
        "Clé : mois × service × départ × arrivée. Le chargeur contrôle cette "
        "clé avant l'affichage ; l'audit source est disponible dans l'onglet suivant."
    )
with lineage:
    st.subheader("Ce qui est conservé à chaque étape")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Étape": "ETL fourni",
                    "Observations restantes": len(all_data),
                    "Explication": "Aucune suppression ; indicateurs de qualité conservés",
                },
                {
                    "Étape": "Filtres d'affichage",
                    "Observations restantes": len(data),
                    "Explication": "Période, service et liaison sélectionnés",
                },
            ]
        ),
        hide_index=True,
    )
    with st.expander("Audit original — périmètre complet"):
        path = ROOT / "data/reports/data_quality_report.txt"
        if path.exists():
            st.text(path.read_text(encoding="utf-8"))
        st.dataframe(table("data/reports/anomalies_qualite.csv", required=False))
    report("data/reports/anomalies_qualite.csv", "Télécharger le rapport original")
    report("data/reports/data_contract.md", "Télécharger le contrat des données")
    st.info(
        "À compléter : validation des dénominateurs et seuils SNCF, dictionnaire "
        "avec disponibilité à la prédiction, bilan comparable avant/après exclusions."
    )
