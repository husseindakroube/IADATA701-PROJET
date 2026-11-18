"Fonctions de présentation Streamlit communes aux résultats importés."

import logging

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
