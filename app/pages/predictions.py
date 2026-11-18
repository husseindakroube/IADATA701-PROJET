'Comparaison des modèles de prédiction du taux de retard et modèle retenu.'

import logging

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import r2_score

from utils.activity import log_selection
from utils.data import table
from projet_kit_data.ml.evaluation import compute_metrics
from projet_kit_data.web_data import load_json

LOGGER = logging.getLogger("projet_kit_data.predictions")


# =============================================================================
# Constantes de style
# =============================================================================

COULEURS_CLUSTERS = {
    0: "#C0392B",
    1: "#E67E22",
    2: "#27AE60",
    3: "#2E86DE",
    -1: "#95A5A6",
}

MODELES = {
    "Naïf historique": "prediction_naive",
    "A — Baseline": "prediction_a",
    "B — Baseline + graphe": "prediction_b",
    "C — Baseline + cluster": "prediction_c",
    "D — Baseline + graphe + cluster": "prediction_d",
}

MODELE_RETENU = "A — Baseline"


# =============================================================================
# En-tête
# =============================================================================

st.caption("ÉVALUATION DES MODÈLES DE PRÉDICTION")
st.title("Prédire le taux de retard des liaisons TGV")
st.write(
    "Comparaison de cinq modèles sur la période de test réservée (juillet 2025 à "
    "septembre 2026). La cible est le **taux de retard supérieur à 15 minutes à "
    "l'arrivée** : nombre de trains en retard >15 min rapporté au nombre de "
    "trains effectivement circulés sur chaque liaison et chaque mois."
)


# =============================================================================
# Chargement et validation des prédictions
# =============================================================================

predictions = table("data/processed/ml/comparaison_predictions_test.parquet")
champs_requis = {
    "date", "service", "departure", "arrival", "circulated", "delay_rate_15",
    "prediction_naive", "prediction_a", "prediction_b", "prediction_c",
    "prediction_d", "cluster",
}
if not champs_requis.issubset(predictions.columns):
    LOGGER.error('Champs absents : %s', sorted(champs_requis - set(predictions.columns)))
    st.error("Schéma des prédictions incompatible avec cette page.")
    st.stop()

predictions["date"] = pd.to_datetime(predictions.date)
if predictions.empty:
    st.info("Aucune observation de test enregistrée.")
    st.stop()


# =============================================================================
# Protocole en expander
# =============================================================================

with st.expander("Protocole expérimental des modèles"):
    st.write(
        "**Découpage temporel.** Entraînement : janvier 2019 à mai 2024. "
        "Validation : juin 2024 à juin 2025. Test : juillet 2025 à septembre 2026. "
        "Les clusters et les centralités du graphe sont appris uniquement sur la "
        "fenêtre d'entraînement pour éviter toute fuite temporelle.\n\n"
        "**Sélection du modèle.** Le modèle final est choisi sur la MAE pondérée "
        "de la fenêtre de validation. Les modèles finaux sont réajustés sur "
        "entraînement + validation avant évaluation sur le test.\n\n"
        "**Cinq modèles comparés.** Naïf historique (moyenne glissante par liaison), "
        "A (baseline HistGradientBoosting avec service, gares, mois, historique), "
        "B (A + centralités de graphe), C (A + cluster d'appartenance), "
        "D (A + centralités + cluster)."
    )


# =============================================================================
# Calcul des métriques pour les 5 modèles
# =============================================================================

try:
    metrics_sauvegardes = load_json("data/processed/ml/comparaison_metrics.json")
except (OSError, ValueError):
    metrics_sauvegardes = {}

metriques = {}
for nom, colonne in MODELES.items():
    m = compute_metrics(predictions.delay_rate_15, predictions[colonne], predictions.circulated)
    m["r2"] = r2_score(predictions.delay_rate_15, predictions[colonne])
    metriques[nom] = m

df_metriques = pd.DataFrame(metriques).T
for col in ["mae", "rmse", "weighted_mae"]:
    df_metriques[col] *= 100


# =============================================================================
# Comparaison visuelle des modèles
# =============================================================================

st.subheader("Comparaison des cinq modèles sur le test")

c1, c2 = st.columns(2)

with c1:
    st.markdown("**MAE pondérée (points de pourcentage, plus bas = meilleur)**")
    noms = df_metriques.index.tolist()
    valeurs_mae = df_metriques["weighted_mae"].tolist()
    couleurs_mae = [
        "#C0392B" if nom == MODELE_RETENU else "#2E86DE" for nom in noms
    ]
    fig_mae = go.Figure(data=[go.Bar(
        x=noms, y=valeurs_mae, marker=dict(color=couleurs_mae),
        text=[f"{v:.3f}" for v in valeurs_mae], textposition="outside",
    )])
    fig_mae.update_layout(
        height=340, margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(title="MAE pondérée (pp)", gridcolor="#ECF0F1"),
        xaxis=dict(title=None, tickangle=-15),
        plot_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig_mae, width="stretch")

with c2:
    st.markdown("**R² (plus haut = meilleur, 1 = parfait)**")
    valeurs_r2 = df_metriques["r2"].tolist()
    couleurs_r2 = [
        "#C0392B" if nom == MODELE_RETENU else "#2E86DE" for nom in noms
    ]
    fig_r2 = go.Figure(data=[go.Bar(
        x=noms, y=valeurs_r2, marker=dict(color=couleurs_r2),
        text=[f"{v:.3f}" for v in valeurs_r2], textposition="outside",
    )])
    fig_r2.update_layout(
        height=340, margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(title="R²", gridcolor="#ECF0F1"),
        xaxis=dict(title=None, tickangle=-15),
        plot_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig_r2, width="stretch")


# =============================================================================
# Modèle retenu et verdict scientifique
# =============================================================================

st.markdown(
    f'<div style="padding:16px 20px;background:#C0392B;color:white;'
    f'border-radius:8px;margin:16px 0;">'
    f'<div style="font-size:12px;letter-spacing:1px;opacity:0.9;">MODÈLE RETENU</div>'
    f'<div style="font-size:20px;font-weight:600;margin-top:4px;">'
    f'{MODELE_RETENU} (HistGradientBoostingRegressor)</div>'
    f'<div style="font-size:14px;margin-top:8px;opacity:0.95;">'
    f'Meilleure MAE pondérée en validation, performance au même niveau que les '
    f'modèles enrichis en test. Les features structurelles (graphe, clusters) '
    f"n'apportent pas de gain significatif après correction de la fuite temporelle."
    f'</div></div>',
    unsafe_allow_html=True,
)


# =============================================================================
# Détail numérique
# =============================================================================

st.markdown("### Détail des métriques")
st.caption(
    "MAE et RMSE en points de pourcentage sur la cible (rate entre 0 et 1, "
    "exprimée en %). La MAE pondérée utilise le nombre de trains circulés pour "
    "donner plus de poids aux liaisons à fort trafic."
)
st.dataframe(
    df_metriques.rename(columns={
        "mae": "MAE (pp)", "rmse": "RMSE (pp)",
        "weighted_mae": "MAE pondérée (pp)", "r2": "R²",
    }).round(4),
    width="stretch",
)


# =============================================================================
# Erreurs par cluster
# =============================================================================

st.markdown("### Erreurs par cluster de liaisons")
st.caption(
    "Erreur absolue moyenne (MAE) des 5 modèles par cluster. "
    "Mesure à quel point chaque profil de liaisons est difficile à prédire."
)

errors = predictions[["cluster"]].copy()
for nom, colonne in MODELES.items():
    errors[nom] = (predictions.delay_rate_15 - predictions[colonne]).abs() * 100
mae_par_cluster = errors.groupby("cluster").mean()
obs_par_cluster = errors.groupby("cluster").size()

fig_clusters = go.Figure()
for nom in MODELES:
    fig_clusters.add_trace(go.Bar(
        name=nom,
        x=[f"Cluster {int(c) if c != -1 else 'N.C.'}" for c in mae_par_cluster.index],
        y=mae_par_cluster[nom].values,
        text=[f"{v:.2f}" for v in mae_par_cluster[nom].values],
        textposition="outside",
        textfont=dict(size=9),
    ))
fig_clusters.update_layout(
    barmode="group",
    height=360, margin=dict(l=10, r=10, t=10, b=10),
    yaxis=dict(title="MAE (pp)", gridcolor="#ECF0F1"),
    xaxis=dict(title=None),
    plot_bgcolor="#FFFFFF",
    legend=dict(orientation="h", yanchor="bottom", y=-0.3,
                xanchor="center", x=0.5),
)
st.plotly_chart(fig_clusters, width="stretch")

st.caption(
    f"Nombre d'observations par cluster : "
    + " · ".join(
        f"**Cluster {int(c) if c != -1 else 'non classé'}** : {int(n):,}".replace(",", " ")
        for c, n in obs_par_cluster.items()
    )
    + "."
)


# =============================================================================
# Explorer une prédiction précise
# =============================================================================

st.divider()
st.subheader("Explorer une prédiction précise")
st.caption(
    "Choisissez une liaison et un modèle pour comparer la prédiction à la "
    "réalité mois par mois sur la période de test."
)

labels = predictions.service + " · " + predictions.departure + " → " + predictions.arrival
labels_options = sorted(labels.unique())

cl1, cl2 = st.columns([3, 2])
with cl1:
    route = st.selectbox("Liaison", labels_options)
with cl2:
    model_name = st.selectbox(
        "Modèle à comparer", [nom for nom in MODELES if nom != "Naïf historique"],
    )
model_column = MODELES[model_name]
log_selection("prediction_view", route=route, model=model_name)

selected = predictions.loc[labels.eq(route)].sort_values("date")
if selected.empty:
    st.info("Aucune donnée pour cette liaison.")
else:
    moy_obs = (selected["delay_rate_15"] * selected["circulated"]).sum() / selected["circulated"].sum()
    moy_pred = (selected[model_column] * selected["circulated"]).sum() / selected["circulated"].sum()
    moy_naif = (selected["prediction_naive"] * selected["circulated"]).sum() / selected["circulated"].sum()
    mae_route = (selected["delay_rate_15"] - selected[model_column]).abs().mean() * 100

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Taux observé (moyenne)", f"{moy_obs * 100:.2f} %")
    with m2:
        st.metric(f"Prédit {model_name.split(' — ')[0]}", f"{moy_pred * 100:.2f} %",
                  f"{(moy_pred - moy_obs) * 100:+.2f} pts vs observé")
    with m3:
        st.metric("Prédit naïf", f"{moy_naif * 100:.2f} %",
                  f"{(moy_naif - moy_obs) * 100:+.2f} pts vs observé")
    with m4:
        st.metric("MAE sur la liaison", f"{mae_route:.2f} pp")

    # Courbe plotly superposée
    fig_route = go.Figure()
    fig_route.add_trace(go.Scatter(
        x=selected["date"], y=selected["delay_rate_15"] * 100,
        mode="lines+markers", name="Observé",
        line=dict(color="#2C3E50", width=2.5), marker=dict(size=6),
    ))
    fig_route.add_trace(go.Scatter(
        x=selected["date"], y=selected[model_column] * 100,
        mode="lines+markers", name=f"Prédit — {model_name.split(' — ')[0]}",
        line=dict(color="#C0392B", width=2, dash="dash"), marker=dict(size=5),
    ))
    fig_route.add_trace(go.Scatter(
        x=selected["date"], y=selected["prediction_naive"] * 100,
        mode="lines+markers", name="Prédit — Naïf",
        line=dict(color="#95A5A6", width=1.5, dash="dot"), marker=dict(size=4),
    ))
    fig_route.update_layout(
        height=360, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(title=None, showgrid=False),
        yaxis=dict(title="Taux de retard >15 min (%)", gridcolor="#ECF0F1"),
        plot_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    st.plotly_chart(fig_route, width="stretch")


# =============================================================================
# Conclusion scientifique
# =============================================================================

st.divider()
st.markdown(
    '<div style="padding:14px 18px;background:#F4F6F7;border-left:4px solid #2E86DE;'
    'border-radius:4px;">'
    "<b>Lecture scientifique.</b> Le modèle A (HistGradientBoosting avec les seules "
    "features opérationnelles de base) obtient des performances au même niveau que "
    "les modèles enrichis par la théorie des graphes ou le clustering. Ce résultat, "
    "observé après correction d'une fuite temporelle initiale, suggère que la "
    "structure du réseau TGV influence peu la prédictibilité des retards à l'horizon "
    "mensuel : les informations opérationnelles mois à mois (volume de trafic, "
    "causes de retard historiques, saisonnalité) suffisent pour atteindre le plafond "
    "de performance observé. La structure est bien associée aux retards, mais pas "
    "de manière à améliorer significativement leur prédiction."
    "</div>",
    unsafe_allow_html=True,
)
