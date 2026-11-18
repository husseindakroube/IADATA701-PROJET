'Synthèse du projet, réponse à la problématique et ressources de reproductibilité.'

import streamlit as st
from sklearn.metrics import mean_absolute_error, r2_score

from utils.data import table


# =============================================================================
# En-tête
# =============================================================================

st.caption("SYNTHÈSE DU PROJET")
st.title("Conclusions et reproductibilité")
st.write(
    "Synthèse des résultats de TGVision, réponse à la problématique posée "
    "en accueil, et ressources pour reproduire l'ensemble des analyses."
)


# =============================================================================
# Réponse à la problématique
# =============================================================================

st.markdown("## Réponse à la problématique")

st.markdown(
    '<div style="padding:16px 20px;background:#F4F6F7;border-left:4px solid #2C3E50;'
    'border-radius:4px;margin:12px 0 20px 0;font-style:italic;font-size:15px;">'
    "« Dans quelle mesure la structure du réseau TGV est-elle associée à la "
    "régularité des liaisons, et peut-on exploiter cette structure pour "
    "améliorer la prédiction des retards ? »"
    "</div>",
    unsafe_allow_html=True,
)

col_r1, col_r2 = st.columns(2)
with col_r1:
    st.markdown(
        '<div style="padding:16px 20px;background:#D5F5E3;'
        'border-left:4px solid #27AE60;border-radius:4px;height:100%;">'
        '<div style="font-size:12px;letter-spacing:1px;color:#1E8449;'
        'font-weight:600;">PARTIE 1 — ASSOCIATION</div>'
        '<div style="font-size:16px;font-weight:600;margin:6px 0;'
        'color:#1E8449;">Oui, la structure est associée à la régularité.</div>'
        '<div style="font-size:14px;color:#1B4F28;line-height:1.5;">'
        "Le clustering non supervisé fait émerger 4 profils de liaisons "
        "caractérisés par leur durée et leurs causes de retard dominantes. "
        "Les liaisons internationales longues (cluster 0) affichent un taux "
        "de retard de 17,7 %, nettement supérieur aux 8,5 % des liaisons "
        "France courte distance (cluster 2)."
        "</div></div>",
        unsafe_allow_html=True,
    )
with col_r2:
    st.markdown(
        '<div style="padding:16px 20px;background:#FADBD8;'
        'border-left:4px solid #C0392B;border-radius:4px;height:100%;">'
        '<div style="font-size:12px;letter-spacing:1px;color:#922B21;'
        'font-weight:600;">PARTIE 2 — PRÉDICTION</div>'
        '<div style="font-size:16px;font-weight:600;margin:6px 0;'
        'color:#922B21;">Non, l\'exploiter n\'améliore pas significativement la prédiction.</div>'
        '<div style="font-size:14px;color:#641E16;line-height:1.5;">'
        "Les modèles enrichis avec les features de graphe (B), de cluster (C) "
        "ou les deux (D) obtiennent des MAE pondérées quasi identiques au modèle "
        "baseline A (HistGradientBoosting). Les informations opérationnelles "
        "mensuelles suffisent pour atteindre le plafond de performance observé."
        "</div></div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div style="padding:12px 16px;background:#EBF5FB;border-left:4px solid #2E86DE;'
    'border-radius:4px;margin-top:16px;font-size:14px;color:#1F618D;">'
    "<b>Lecture.</b> Ce résultat suggère que la structure du réseau est utile "
    "pour <i>comprendre</i> et <i>typifier</i> les liaisons, mais pas pour "
    "<i>prédire</i> leurs retards mensuels. L'information structurelle est "
    "probablement déjà captée par les variables opérationnelles historiques "
    "présentes dans la baseline."
    "</div>",
    unsafe_allow_html=True,
)


# =============================================================================
# Résultats par pilier
# =============================================================================

st.markdown("## Résultats par pilier")

donnees_qualite = table("data/processed/sncf.parquet", required=False)
summary_reseau = table("data/processed/graph/descriptive/network_summary.parquet", required=False)
clusters = table("data/processed/clusters_liaisons.csv", required=False)
predictions = table("data/processed/ml/comparaison_predictions_test.parquet", required=False)

p1, p2 = st.columns(2)

with p1, st.container(border=True):
    st.markdown("**🔍 Qualité des données**")
    if not donnees_qualite.empty:
        from projet_kit_data.web_data import FLAGS
        total = len(donnees_qualite)
        flagged = int(donnees_qualite[FLAGS].fillna(False).any(axis=1).sum())
        propres = total - flagged
        st.caption(
            f"**{total:,} observations** traitées par un ETL non destructif, "
            f"**{propres:,} propres** après application de 4 contrôles de "
            f"cohérence. Toutes les lignes sont conservées avec leurs "
            f"indicateurs de qualité pour garantir la traçabilité."
            .replace(",", " ")
        )

with p2, st.container(border=True):
    st.markdown("**🗺️ Structure du réseau**")
    if not summary_reseau.empty:
        total_gares = int(summary_reseau["node_count"].sum())
        total_edges = int(summary_reseau["edge_count"].sum())
        st.caption(
            f"Analyse par théorie des graphes de **{total_gares} gares** et "
            f"**{total_edges} liaisons orientées**. Paris Lyon, Lyon Part Dieu "
            f"et Paris Montparnasse concentrent la betweenness la plus élevée, "
            f"confirmant une topologie en étoile centrée sur Paris avec un hub "
            f"province fort à Lyon."
        )

p3, p4 = st.columns(2)

with p3, st.container(border=True):
    st.markdown("**👥 Typologie des liaisons**")
    if not clusters.empty:
        nb_paires = len(clusters)
        nb_clusters = clusters["cluster"].nunique()
        st.caption(
            f"Clustering K-Means sur {nb_paires} paires de gares, **{nb_clusters} "
            f"profils identifiés** (k choisi par méthode du coude). "
            f"Les groupes distinguent nettement les liaisons internationales, "
            f"les trajets courts France, les longues distances domestiques et "
            f"les liaisons mixtes Europe proche."
        )

with p4, st.container(border=True):
    st.markdown("**🤖 Prédiction retenue**")
    if not predictions.empty:
        mae_a = mean_absolute_error(predictions.delay_rate_15, predictions["prediction_a"]) * 100
        r2_a = r2_score(predictions.delay_rate_15, predictions["prediction_a"])
        st.caption(
            f"Modèle **A (HistGradientBoostingRegressor)** retenu après correction "
            f"d'une fuite temporelle initiale. MAE **{mae_a:.3f} pp**, "
            f"R² **{r2_a:.3f}** sur {len(predictions):,} observations de test. "
            f"Les modèles enrichis B/C/D obtiennent des performances équivalentes."
            .replace(",", " ")
        )


# =============================================================================
# Limites et perspectives
# =============================================================================

st.markdown("## Limites et perspectives")

st.write(
    "Le projet s'est volontairement concentré sur les données publiques SNCF "
    "AQST agrégées au mois. Les limites suivantes ouvrent des pistes "
    "d'amélioration pour une suite industrielle."
)

col_l1, col_l2, col_l3 = st.columns(3)
with col_l1, st.container(border=True):
    st.markdown("**Variables externes**")
    st.caption(
        "L'ajout de données météorologiques, de calendriers de grèves et "
        "d'événements majeurs enrichirait fortement la capacité prédictive, "
        "notamment pour les pics de retard non expliqués par les variables "
        "opérationnelles."
    )
with col_l2, st.container(border=True):
    st.markdown("**Granularité temporelle**")
    st.caption(
        "L'horizon mensuel limite la finesse d'analyse. Un passage au grain "
        "journalier ou à la circulation individuelle permettrait de modéliser "
        "la propagation des retards dans le réseau et d'exploiter plus "
        "finement la structure des graphes."
    )
with col_l3, st.container(border=True):
    st.markdown("**Features structurelles**")
    st.caption(
        "Les centralités utilisées restent statiques sur la période complète. "
        "Des features dynamiques (centralités glissantes, communautés par "
        "trimestre) pourraient apporter le gain prédictif que les variables "
        "statiques n'ont pas révélé."
    )
