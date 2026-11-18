"""Read saved held-out predictions, never deserialize or retrain a model."""

import pandas as pd
import streamlit as st
from sklearn.metrics import r2_score
from utils.data import report, table

from projet_kit_data.ml.evaluation import compute_metrics
from projet_kit_data.web_data import load_json

st.title("Prédictions et évaluation historique")
st.write(
    "Évaluation historique sur des mois de test réservés. La cible du travail "
    "fourni est nb_train_retard_sup_15 / (nb_train_prevu − nb_annulation). "
    "Elle ne doit pas être confondue avec le taux officiel d'arrivée en retard."
)
st.warning(
    "Le champ >15 min a une applicabilité à confirmer. Ces résultats décrivent "
    "l'expérience existante ; ils ne valident pas encore le protocole demandé. "
    "Ils concernent une liaison et un mois, pas une circulation individuelle."
)
predictions = table("data/processed/ml/comparaison_predictions_test.parquet")
required = {
    "date",
    "service",
    "departure",
    "arrival",
    "circulated",
    "delay_rate_15",
    "prediction_naive",
    "prediction_a",
    "prediction_b",
    "prediction_c",
    "prediction_d",
    "cluster",
}
if not required.issubset(predictions.columns):
    st.error("Schéma de prédictions incompatible avec cette page.")
    st.stop()
predictions["date"] = pd.to_datetime(predictions.date)
if predictions.empty:
    st.info("Aucune observation de test enregistrée.")
    st.stop()
st.caption(
    f"Test chargé : {predictions.date.min():%Y-%m} → "
    f"{predictions.date.max():%Y-%m}, {len(predictions):,} observations. "
    "Les filtres descriptifs des autres pages ne changent pas ce test."
)
with st.expander("Protocole des notebooks 04 et 05"):
    st.write(
        "Entraînement : 2019-01 à 2024-05 ; validation : 2024-06 à 2025-06 ; "
        "test : 2025-07 à 2026-09. Les clusters sont appris jusqu'à 2024-05. "
        "Le graphe utilise l'entraînement pour la validation, puis entraînement + "
        "validation pour le test. Le modèle est choisi sur la MAE pondérée de validation. "
        "Les modèles finaux sont ajustés sur entraînement + validation. "
        "L'historique glissant utilise les mois antérieurs : ce test ne représente "
        "pas une prévision simultanée de tous les mois depuis une date unique."
    )
    st.caption(
        "A : historique + service, gares et mois ; B : A + centralités ; "
        "C : A + cluster ; D : A + centralités + cluster. "
        "Naïf : historique par liaison. Aucun entraînement dans l'application."
    )
models = {
    "Naïf historique": "prediction_naive",
    "A - Baseline": "prediction_a",
    "B - Baseline + graphe": "prediction_b",
    "C - Baseline + cluster": "prediction_c",
    "D - Baseline + graphe + cluster": "prediction_d",
}
try:
    metrics = load_json("data/processed/ml/comparaison_metrics.json")
except (OSError, ValueError):
    metrics = {}
    st.warning("Métriques enregistrées indisponibles ; calcul depuis les prédictions.")
checked_metrics = {}
for name, column in models.items():
    checked = compute_metrics(
        predictions.delay_rate_15, predictions[column], predictions.circulated
    )
    checked["r2"] = r2_score(predictions.delay_rate_15, predictions[column])
    checked_metrics[name] = checked
    if name in metrics and any(
        abs(checked[k] - metrics[name].get(k, float("inf"))) > 1e-8
        for k in checked
    ):
        st.warning(f"Métriques enregistrées incohérentes : {name}.")
display = pd.DataFrame(checked_metrics).T
for column in ["mae", "rmse", "weighted_mae"]:
    display[column] *= 100
st.subheader("Comparaison sur les mêmes observations de test")
st.dataframe(display.rename(columns={
    "mae": "MAE (pp)", "rmse": "RMSE (pp)",
    "weighted_mae": "MAE pondérée (pp)", "r2": "R² (sans unité)",
}))
st.caption("La MAE pondérée utilise les nombres de circulations. R² n'est pas un pourcentage.")
st.subheader("Revoir une prédiction enregistrée")
labels = (
    predictions.service + " · " + predictions.departure + " → " + predictions.arrival
)
route = st.selectbox("Liaison du test", sorted(labels.unique()))
selected = predictions.loc[labels.eq(route)].sort_values("date")
month = st.selectbox("Mois du test", selected.date.dt.strftime("%Y-%m").tolist())
model_name = st.selectbox("Modèle à consulter", list(models)[1:])
model_column = models[model_name]
row = selected.loc[selected.date.dt.strftime("%Y-%m").eq(month)].iloc[0]
cols = st.columns(4)
for col, label, value in zip(
    cols,
    ["Observé (%)", "Modèle (%)", "Naïf (%)", "Erreur absolue modèle (pp)"],
    [
        row.delay_rate_15 * 100,
        row[model_column] * 100,
        row.prediction_naive * 100,
        abs(row.delay_rate_15 - row[model_column]) * 100,
    ],
):
    col.metric(label, f"{value:.2f}")
st.line_chart(
    selected.set_index("date")[["delay_rate_15", model_column, "prediction_naive"]]
    * 100
)
st.caption(
    "Évolution sur les mois de test disponibles — unité : %. "
    "Les performances historiques ne garantissent pas les performances futures."
)
st.subheader("Erreurs par cluster — mêmes mois de test")
errors = predictions[["cluster"]].copy()
for name, column in models.items():
    errors[name] = (predictions.delay_rate_15 - predictions[column]).abs() * 100
summary = errors.groupby("cluster").mean()
summary.insert(0, "Observations", errors.groupby("cluster").size())
st.dataframe(summary)
st.caption("MAE en points de pourcentage ; cluster −1 = paire inconnue. Les identifiants ne classent pas la qualité.")
st.info(
    "À compléter : erreurs par service, stabilité sur plusieurs périodes, "
    "manifeste complet des modèles et horizon opérationnel explicite. "
    "Aucune prévision future ni intervalle proposé."
)
report("notebooks/03_ml_baseline.ipynb", "Notebook de la baseline")
report("notebooks/05_ml_comparaison.ipynb", "Comparaison A/B/C/D (source)")
