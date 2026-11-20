"Fonctions de présentation Streamlit communes aux résultats importés."

import logging

import numpy as np
import pandas as pd
import streamlit as st
from utils.activity import log_action, log_selection

from projet_kit_data.web_data import (
    ROOT,
    filter_observations,
    load_table,
    validate_observations,
)


@st.cache_data(show_spinner=False)
def cached_table(relative: str, modified: int) -> pd.DataFrame:
    "Met un résultat en cache jusqu’à modification de sa date de mise à jour."
    return load_table(relative)


def table(relative: str, required: bool = True) -> pd.DataFrame:
    "Affiche un message compréhensible si un fichier est absent ou illisible."
    try:
        return cached_table(relative, (ROOT / relative).stat().st_mtime_ns)
    except Exception:
        logging.getLogger("projet_kit_data.web").exception(
            "Résultat indisponible : %s", relative
        )
        st.warning(f"Résultat indisponible : {relative}")
        if required:
            st.stop()
        return pd.DataFrame()


def network_summary_metrics(row: pd.Series) -> list[tuple[str, int]]:
    """Renvoie les indicateurs topologiques présents dans une ligne de synthèse."""
    indicateurs = [
        ("node_count", "Gares (nœuds)"),
        ("edge_count", "Liaisons OD orientées"),
        ("weakly_connected_components", "Composantes faiblement connexes"),
        ("strongly_connected_components", "Composantes fortement connexes"),
        ("largest_weak_component", "Gares dans la plus grande composante faible"),
        ("nodes_multiple_incoming", "Gares avec plusieurs liaisons entrantes"),
        ("nodes_multiple_outgoing", "Gares avec plusieurs liaisons sortantes"),
        ("self_loops", "Boucles sur un même nœud"),
    ]
    return [
        (label, int(row[field]))
        for field, label in indicateurs
        if field in row.index and pd.notna(row[field])
    ]


def network_station_counts(
    summary: pd.DataFrame, nodes: pd.DataFrame
) -> tuple[int | None, int | None]:
    """Compte les identifiants de gare distincts et les appartenances par service."""
    gares_distinctes = None
    if (
        not nodes.empty
        and "node_id" in nodes.columns
        and nodes["node_id"].notna().all()
    ):
        gares_distinctes = int(nodes["node_id"].nunique())

    appartenances = None
    if not summary.empty and "node_count" in summary.columns:
        comptes = pd.to_numeric(summary["node_count"], errors="coerce")
        comptes_valides = (
            comptes.notna().all()
            and comptes.ge(0).all()
            and comptes.mod(1).eq(0).all()
            and comptes.ne(float("inf")).all()
        )
        if comptes_valides:
            appartenances = int(comptes.sum())
    return gares_distinctes, appartenances


def validate_rankings(
    rankings: pd.DataFrame,
) -> tuple[pd.DataFrame, str | None]:
    """Valide un classement et signale explicitement ses lignes inutilisables."""
    required = {"service", "ranking_metric", "rank", "station_name", "value"}
    if rankings.empty:
        return rankings.copy(), "Le classement des gares est vide ou indisponible."

    missing = required - set(rankings.columns)
    if missing:
        champs = ", ".join(sorted(missing))
        return (
            pd.DataFrame(),
            f"Le classement des gares ne peut pas être utilisé : champs absents ({champs}).",
        )

    ranks = pd.to_numeric(rankings["rank"], errors="coerce")
    values = pd.to_numeric(rankings["value"], errors="coerce")
    champs_texte_valides = pd.Series(True, index=rankings.index)
    for champ in ("service", "ranking_metric", "station_name"):
        champs_texte_valides &= rankings[champ].map(
            lambda valeur: isinstance(valeur, str) and bool(valeur.strip())
        )

    metriques_valides = rankings["ranking_metric"].isin(
        {"connectivity_degree", "betweenness_centrality", "pagerank"}
    )
    rangs_valides = (
        ranks.notna()
        & ranks.gt(0)
        & ranks.mod(1).eq(0)
        & ranks.ne(float("inf"))
        & ~rankings["rank"].map(lambda valeur: isinstance(valeur, (bool, np.bool_)))
    )
    valeurs_valides = (
        values.notna()
        & values.ne(float("inf"))
        & values.ne(float("-inf"))
        & ~rankings["value"].map(lambda valeur: isinstance(valeur, (bool, np.bool_)))
    )
    valides = champs_texte_valides & metriques_valides & rangs_valides & valeurs_valides
    resultat = rankings.loc[valides].copy()
    resultat["rank"] = ranks.loc[valides].astype("int64")
    resultat["value"] = values.loc[valides]

    nb_invalides = int((~valides).sum())
    if resultat.empty:
        return (
            resultat,
            f"Aucune ligne du classement n'est exploitable; {nb_invalides} ligne(s) "
            "contiennent des champs manquants ou des valeurs invalides.",
        )
    if nb_invalides:
        return (
            resultat,
            f"{nb_invalides} ligne(s) du classement ont été écartées car des champs "
            "requis sont manquants ou invalides.",
        )
    return resultat, None


def ranked_stations(
    rankings: pd.DataFrame,
    *,
    service: str,
    metric: str,
    limit: int = 3,
) -> pd.DataFrame:
    """Filtre un classement existant sans recalculer les métriques du graphe."""
    rankings, warning = validate_rankings(rankings)
    if warning:
        return pd.DataFrame()
    return (
        rankings.loc[rankings.service.eq(service) & rankings.ranking_metric.eq(metric)]
        .sort_values("rank")
        .head(limit)
    )


def observations() -> pd.DataFrame:
    "Charge le résultat de l’ETL non destructif de l’équipe."
    try:
        return validate_observations(table("data/processed/sncf.parquet"))
    except (ValueError, TypeError):
        logging.getLogger("projet_kit_data.web").exception(
            "Schéma des observations invalide"
        )
        st.error("Le fichier ne respecte pas le contrat des observations mensuelles.")
        st.stop()


def filters(
    frame: pd.DataFrame,
    *,
    label: str = "Périmètre des données",
    expanded: bool = True,
) -> pd.DataFrame:
    "Conserve les filtres communs aux pages descriptives et leurs options dépendantes."
    if frame.empty:
        st.info("Aucune observation disponible.")
        st.stop()
    state = st.session_state.get("description_filters", {})
    months = sorted(frame["date"].dt.strftime("%Y-%m").unique())
    with st.expander(label, expanded=expanded):
        old = state.get("months", (months[0], months[-1]))
        old = old if all(m in months for m in old) else (months[0], months[-1])
        dates = st.select_slider("Mois inclus", months, value=old)
        narrowed = filter_observations(frame, dates[0], dates[1])
        selected = {}
        columns = st.columns(3)
        for container, col, field_label in zip(
            columns,
            ["service", "gare_depart", "gare_arrivee"],
            ["Service", "Départ", "Arrivée"],
        ):
            choices = [None, *sorted(narrowed[col].dropna().unique())]
            previous = state.get(col)
            with container:
                value = st.selectbox(
                    field_label,
                    choices,
                    index=choices.index(previous) if previous in choices else 0,
                    format_func=lambda x: "Tous" if x is None else x,
                )
            selected[col] = value
            if value is not None:
                narrowed = narrowed[narrowed[col].eq(value)]
        st.session_state["description_filters"] = {"months": dates, **selected}
    log_selection(
        "filters", **st.session_state["description_filters"], observations=len(narrowed)
    )
    if narrowed.empty:
        st.info("Aucune observation pour ces filtres.")
        st.stop()
    st.caption(
        f"Couverture réelle : {narrowed.date.min():%Y-%m} → "
        f"{narrowed.date.max():%Y-%m} · {len(narrowed):,} observations. "
        "Une observation = mois × service × départ × arrivée (sens conservé)."
    )
    return narrowed


def scope_metrics(frame: pd.DataFrame) -> None:
    "Affiche les effectifs définis dans le contrat commun."
    cols = st.columns(3)
    cols[0].metric(
        "Gares", pd.concat([frame.gare_depart, frame.gare_arrivee]).nunique()
    )
    cols[1].metric(
        "Liaisons orientées × service",
        len(frame[["service", "gare_depart", "gare_arrivee"]].drop_duplicates()),
    )
    cols[2].metric("Observations mensuelles", f"{len(frame):,}")


def report(relative: str, label: str) -> None:
    "Propose un rapport existant sans exécuter son analyse."
    path = ROOT / relative
    if path.is_file():
        st.download_button(
            label,
            path.read_bytes(),
            file_name=path.name,
            key=relative,
            on_click=log_action,
            args=("download",),
            kwargs={"file": relative},
        )
    else:
        st.caption(f"Document non fourni : {path.name}")
