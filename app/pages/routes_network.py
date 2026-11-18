'Exploration des liaisons et analyse du réseau enregistrée.'

import streamlit as st
from utils.activity import log_selection
from utils.data import filters, observations, report, scope_metrics, table

from projet_kit_data.web_data import ROOT

st.caption("EXPLORER LES SERVICES TGV")
st.title("Une liaison, mois après mois")
st.write(
    "Suivez l'évolution des retards et des annulations d'une liaison, "
    "ou découvrez la place des gares dans le réseau observé."
)
routes, network = st.tabs(["Explorer une liaison", "Comprendre le réseau"])
with routes:
    st.subheader("Choisissez votre périmètre")
    data = filters(observations(), label="Période, service et gares", expanded=True)
    with st.expander("Couverture du périmètre sélectionné"):
        scope_metrics(data)
    labels = data.service + " · " + data.gare_depart + " → " + data.gare_arrivee
    route = st.selectbox("Liaison à explorer", sorted(labels.unique()))
    log_selection("route_view", route=route)
    selected = data.loc[labels.eq(route)].sort_values("date")
    with st.container(border=True):
        st.subheader(
            f"{selected.iloc[0].gare_depart} → {selected.iloc[0].gare_arrivee}"
        )
        st.caption(
            f"{selected.iloc[0].service} · {len(selected)} mois observés · "
            f"{selected.date.min():%Y-%m} → {selected.date.max():%Y-%m}"
        )
    st.caption(
        "Lecture : les retards sont exprimés en minutes. Le taux officiel d'arrivée "
        "n'est pas affiché, car son dénominateur reste à confirmer."
    )
    st.subheader("Retard moyen à l'arrivée — tous trains (minutes)")
    st.line_chart(selected.set_index("date")[["retard_moyen_tous_trains_arrivee"]])
    st.caption("Valeurs mensuelles publiées ; les valeurs négatives sont conservées.")
    st.subheader("Circulations prévues et annulations (nombre de trains)")
    st.line_chart(selected.set_index("date")[["nb_train_prevu", "nb_annulation"]])
    research = table("data/processed/research_dataset.parquet", required=False)
    if not research.empty:
        row = selected.iloc[0]
        cancellation = research.loc[
            research.service.eq(row.service)
            & research.gare_depart.eq(row.gare_depart)
            & research.gare_arrivee.eq(row.gare_arrivee)
            & research.date.isin(selected.date.dt.strftime("%Y-%m"))
        ].sort_values("date")
        st.subheader("Annulations / circulations prévues (%)")
        st.line_chart(cancellation.set_index("date")[["cancellation_rate"]] * 100)
        st.caption(
            "Ratio fourni par la préparation de recherche. Les dénominateurs "
            "invalides restent indisponibles ; aucun taux global n'est déduit."
        )
    with st.expander("Causes enregistrées, mois par mois (%)"):
        st.caption(
            "Pas de moyenne des pourcentages : population et dénominateur "
            "des causes non confirmés. Les valeurs manquantes sont conservées."
        )
        st.dataframe(
            selected[["date", *[c for c in selected if c.startswith("prct_cause")]]],
            hide_index=True,
        )
    with st.expander("Observations et commentaires sources"):
        st.dataframe(selected, hide_index=True)
    st.info(
        "Non fourni sous une forme conforme : classement par taux d'arrivée "
        "avec seuil de volume, comparaison à un groupe de référence et carte géographique."
    )
with network:
    st.subheader("Les gares et leurs relations de service")
    st.caption(
        "Périmètre fixe : 2018-01 → 2026-09. Les choix de l'onglet liaison "
        "ne modifient pas ces graphes et centralités pré-calculés."
    )
    st.write(
        "Ce graphe représente les relations de service origine–destination AQST. "
        "Il ne restitue pas les voies ferrées, les arrêts intermédiaires ou les correspondances."
    )
    summary = table(
        "data/processed/graph/descriptive/network_summary.parquet", required=False
    )
    if not summary.empty:
        st.dataframe(summary, hide_index=True)
    service = st.selectbox("Réseau pré-calculé", ["National", "International"])
    log_selection("network_view", service=service)
    path = ROOT / f"data/processed/graph/visualizations/network_{service.lower()}.png"
    if path.is_file():
        st.image(
            str(path), caption=f"{service} · 2018-01 → 2026-09 · liaisons orientées"
        )
    else:
        st.info("Illustration complémentaire absente.")
    nodes = table("data/processed/graph/node_metrics.parquet", required=False)
    if not nodes.empty:
        nodes = nodes.loc[nodes.service.eq(service) & nodes.period.eq("overall")]
        station = st.selectbox(
            "Détails d'une gare", sorted(nodes.station_name.unique())
        )
        log_selection("station_view", service=service, station=station)
        st.dataframe(nodes.loc[nodes.station_name.eq(station)], hide_index=True)
    ranking = table(
        "data/processed/graph/descriptive/node_rankings.parquet", required=False
    )
    if not ranking.empty:
        st.subheader("Classements de centralité déjà calculés")
        st.dataframe(ranking.loc[ranking.service.eq(service)], hide_index=True)
    report("data/reports/graph/research_report.md", "Rapport réseau complet")
    st.info(
        "À compléter : analyse validée des liens centralité–ponctualité et "
        "du rôle de la durée. Les centralités ne démontrent pas une causalité."
    )
