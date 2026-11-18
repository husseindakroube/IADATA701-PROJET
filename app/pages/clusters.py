'Affiche les groupes descriptifs enregistrés sans ajuster de modèle.'

import streamlit as st
from utils.data import report, table
from utils.activity import log_selection

from projet_kit_data.web_data import ROOT

st.title("Profils des liaisons et clustering")
st.write(
    "Le notebook 04 regroupe les paires de gares selon la durée moyenne et "
    "six pourcentages de causes, standardisés par StandardScaler. KMeans utilise "
    "k=4, random_state=42 et n_init=10 ; le choix de k s'appuie sur la courbe du coude."
)
st.warning(
    "Profils historiques appris jusqu’à 2024-05 : les deux directions sont regroupées et "
    "le service n'entre pas dans la clé des labels. Le notebook exclut toute ligne "
    "portant un indicateur de qualité. Les notebooks 04/05 utilisent ces labels sans apprendre sur les mois "
    "de validation ou de test. Aucun recalcul n'est lancé ici."
)
clusters = table("data/processed/clusters_liaisons.csv")
st.metric("Paires de gares avec un label enregistré", len(clusters))
st.bar_chart(clusters.groupby("cluster").size().rename("Paires de gares"))
st.caption(
    "Les identifiants de cluster ne représentent pas un ordre de qualité. "
    "Le taux de retard n'est pas une variable de ce clustering."
)
cluster = st.selectbox("Cluster", sorted(clusters.cluster.unique()))
log_selection("cluster_view", cluster=int(cluster))
st.dataframe(clusters.loc[clusters.cluster.eq(cluster)], hide_index=True)
profiles = table("data/processed/ml/clusters_profils.parquet", required=False)
summary = table("data/processed/ml/clusters_resume.parquet", required=False)
st.subheader("Profils enregistrés sur la période d'apprentissage")
st.caption(
    "Notebook 04 : 2018-01 à 2024-05, 9 414 observations après exclusion des flags "
    "pour les profils. Le taux >15 min utilise séparément les cibles valides du "
    "pipeline ML sur cette période ; les périmètres de qualité sont distincts."
)
if not summary.empty:
    st.dataframe(summary[["cluster", "duree_moyenne", "nombre_paires", "nombre_trains", "taux_retard_15_pct"]], hide_index=True)
    st.bar_chart(summary.set_index("cluster")[["duree_moyenne"]])
    st.caption(
        "Durée : minutes, moyenne des profils de paires. Taux >15 min : "
        "100 × somme des retards >15 min / somme des circulations ; "
        "indicateur historique distinct du taux officiel, non utilisé pour KMeans."
    )
if not profiles.empty:
    st.dataframe(profiles.loc[profiles.cluster.eq(cluster), ["gare_1", "gare_2", "type_liaison", "duree_moyenne"]], hide_index=True)
    with st.expander("Variables sources des profils — réserve sur les causes"):
        st.warning(
            "Les causes sont des moyennes arithmétiques des pourcentages sources. "
            "Leur dénominateur n'est pas confirmé : elles sont présentées comme "
            "variables du clustering, pas comme une répartition globale des retards."
        )
        st.dataframe(profiles.loc[profiles.cluster.eq(cluster)], hide_index=True)
st.subheader("Figures enregistrées dans le notebook 04 mis à jour")
st.caption("Périmètre : profils d'apprentissage jusqu'à 2024-05 ; figures exportées sans exécuter le notebook.")
for name, title in [("elbow", "Choix de k"), ("pca", "Projection PCA statique")]:
    path = ROOT / f"data/reports/clustering/{name}.png"
    if path.is_file():
        st.image(str(path), caption=title)
text = ROOT / "data/reports/clustering/pca.txt"
if text.is_file():
    st.text(text.read_text(encoding="utf-8"))
st.caption("La projection en deux dimensions ne représente qu'une partie de la variance originale.")
st.info(
    "À compléter : PCA interactive exportée, sensibilité aux initialisations, "
    "noms interprétables validés, manifeste de génération et dénominateurs des causes."
)
report("notebooks/04_ml_non_supervise.ipynb", "Notebook de clustering (source)")
