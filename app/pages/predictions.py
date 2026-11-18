"""Read saved held-out predictions, never deserialize or retrain a model."""

import pandas as pd
import streamlit as st
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
predictions = table("data/processed/ml/baseline_predictions_test.parquet")
required = {
    "date",
    "service",
    "departure",
    "arrival",
    "circulated",
    "delay_rate_15",
    "prediction_naive",
    "prediction_ml",
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
with st.expander("Protocole décrit dans le notebook 03"):
    st.write(
        "Entraînement : 2019-01 à 2024-05 ; validation : 2024-06 à 2025-06. "
        "Historique des mois antérieurs, service, gares et mois calendaire. "
        "La baseline naïve utilise l'historique de la liaison. "
        "Ces dates proviennent des sorties enregistrées du notebook ; "
        "un manifeste reliant les fichiers à la version entraînée reste nécessaire."
    )
    st.write(
        "Le module ml/baseline.py contrôle les comptages et la clé métier ; "
        "les transformations historiques sont disponibles dans ml/. "
        "Aucun modèle n'est chargé ou entraîné par cette application."
    )
try:
    metrics = load_json("data/processed/ml/baseline_metrics.json")
except (OSError, ValueError):
    metrics = {}
    st.warning("Fichier de métriques absent ou illisible ; prédictions consultables.")
if metrics:
    display = pd.DataFrame(metrics).T * 100
    st.subheader("Métriques enregistrées — points de pourcentage")
    st.dataframe(
        display.rename(
            columns={
                "mae": "MAE (pp)",
                "rmse": "RMSE (pp)",
                "weighted_mae": "MAE pondérée (pp)",
            }
        )
    )
    for name, column in [
        ("Naïf historique", "prediction_naive"),
        ("HistGradientBoosting final", "prediction_ml"),
    ]:
        checked = compute_metrics(
            predictions.delay_rate_15, predictions[column], predictions.circulated
        )
        if name in metrics and any(
            abs(checked[k] - metrics[name][k]) > 1e-8 for k in checked
        ):
            st.warning(
                f"Les métriques de {name} ne correspondent pas aux prédictions chargées."
            )
    st.caption(
        "La MAE pondérée utilise les nombres de circulations enregistrés. "
        "MAE et RMSE doivent être lues ensemble ; elles peuvent évoluer différemment."
    )
st.subheader("Revoir une prédiction enregistrée")
labels = (
    predictions.service + " · " + predictions.departure + " → " + predictions.arrival
)
route = st.selectbox("Liaison du test", sorted(labels.unique()))
selected = predictions.loc[labels.eq(route)].sort_values("date")
month = st.selectbox("Mois du test", selected.date.dt.strftime("%Y-%m").tolist())
row = selected.loc[selected.date.dt.strftime("%Y-%m").eq(month)].iloc[0]
cols = st.columns(4)
for col, label, value in zip(
    cols,
    ["Observé (%)", "Modèle (%)", "Naïf (%)", "Erreur absolue modèle (pp)"],
    [
        row.delay_rate_15 * 100,
        row.prediction_ml * 100,
        row.prediction_naive * 100,
        abs(row.delay_rate_15 - row.prediction_ml) * 100,
    ],
):
    col.metric(label, f"{value:.2f}")
st.line_chart(
    selected.set_index("date")[["delay_rate_15", "prediction_ml", "prediction_naive"]]
    * 100
)
st.caption(
    "Évolution sur les mois de test disponibles — unité : %. "
    "Les performances historiques ne garantissent pas les performances futures."
)
st.info(
    "À compléter : comparaison A/B/C/D sur les mêmes observations, R² harmonisé, "
    "audit de fuite temporelle des enrichissements, erreurs par service/cluster "
    "avec effectifs et validation de stabilité. Aucune prévision future ni intervalle proposé."
)
report("notebooks/03_ml_baseline.ipynb", "Notebook de la baseline")
report(
    "notebooks/05_ml_comparaison.ipynb", "Expériences de comparaison (non harmonisées)"
)
