"""Display saved descriptive clusters without fitting any model."""

import streamlit as st
from utils.data import report, table

from projet_kit_data.web_data import ROOT

st.title("Profils des liaisons et clustering")
st.write(
    "Le notebook 04 regroupe les paires de gares selon la durée moyenne et "
    "six pourcentages de causes, standardisés par StandardScaler. KMeans utilise "
    "k=4, random_state=42 et n_init=10 ; le choix de k s'appuie sur la courbe du coude."
)
st.warning(
    "Analyse historique descriptive : les deux directions sont regroupées et "
    "le service n'entre pas dans la clé des labels. Le notebook exclut toute ligne "
    "portant un indicateur de qualité. Ces labels ne sont pas des classes prédictives "
    "validées sans fuite temporelle. Aucun recalcul n'est lancé ici."
)
clusters = table("data/processed/clusters_liaisons.csv")
st.metric("Paires de gares avec un label enregistré", len(clusters))
st.bar_chart(clusters.groupby("cluster").size().rename("Paires de gares"))
st.caption(
    "Les identifiants de cluster ne représentent pas un ordre de qualité. "
    "Le taux de retard n'est pas une variable de ce clustering."
)
cluster = st.selectbox("Cluster", sorted(clusters.cluster.unique()))
st.dataframe(clusters.loc[clusters.cluster.eq(cluster)], hide_index=True)
st.subheader("Figures enregistrées dans le notebook 04")
st.caption(
    "Instantané du notebook : données historiques après exclusion des anomalies, "
    "issues de sncf.parquet. La période exacte et la version de génération des labels "
    "ne sont pas enregistrées dans le CSV ; leur correspondance au snapshot actuel reste à vérifier."
)
for name, title in [("elbow", "Choix de k"), ("pca", "Projection PCA statique")]:
    path = ROOT / f"data/reports/clustering/{name}.png"
    if path.is_file():
        st.image(str(path), caption=title)
text = ROOT / "data/reports/clustering/pca.txt"
if text.is_file():
    st.text(text.read_text(encoding="utf-8"))
st.caption(
    "La projection en deux dimensions ne représente qu'une partie de la variance originale."
)
st.info(
    "À compléter : PCA interactive exportée, stabilité selon l'initialisation, "
    "traçabilité de la période, noms interprétables validés et profils exportés. "
    "Les moyennes de causes et taux du notebook ne sont pas repris comme indicateurs "
    "validés, car leurs dénominateurs ne sont pas harmonisés."
)
report("notebooks/04_ml_non_supervise.ipynb", "Notebook de clustering (source)")
