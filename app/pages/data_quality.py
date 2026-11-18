"Audit qualité des données SNCF avec indicateurs, complétude et pipeline."

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data import filters, observations, report
from projet_kit_data.web_data import FLAGS, KEYS, ROOT


LIBELLES_FLAGS = {
    "flag_negative_count": "Comptage négatif",
    "flag_sup30_lt_sup60": "Retards >30 min inférieurs aux >60 min",
    "flag_sup15_lt_sup30": "Retards >15 min inférieurs aux >30 min",
    "flag_cancellations_gt_planned": "Annulations supérieures aux prévisions",
}


# =============================================================================
# En-tête
# =============================================================================

st.caption("COMPRENDRE LA FIABILITÉ DES DONNÉES")
st.title("Du fichier source aux observations analysées")
st.write(
    "Audit complet des 12 907 observations issues du jeu SNCF AQST. "
    "Les indicateurs de qualité identifient les lignes à vérifier, "
    "sans les corriger ni les supprimer automatiquement."
)


# =============================================================================
# Bilan global (fixe, non filtrable)
# =============================================================================

donnees_completes = observations()
flagged_global = donnees_completes[FLAGS].fillna(False).any(axis=1)
nb_total = len(donnees_completes)
nb_signalees = int(flagged_global.sum())
nb_propres = int((~flagged_global).sum())
part_propre = nb_propres / nb_total * 100

st.caption("BILAN GLOBAL DU DATASET")
c1, c2, c3, c4 = st.columns(4)
with c1, st.container(border=True):
    st.metric("Observations totales", f"{nb_total:,}".replace(",", " "))
    st.caption("Mois × service × gare départ × gare arrivée.")
with c2, st.container(border=True):
    st.metric("Observations signalées", f"{nb_signalees:,}".replace(",", " "))
    st.caption(f"{nb_signalees / nb_total * 100:.2f} % de la base.")
with c3, st.container(border=True):
    st.metric("Observations propres", f"{nb_propres:,}".replace(",", " "))
    st.caption(f"{part_propre:.2f} % sans aucun signalement.")
with c4, st.container(border=True):
    st.metric("Préservation des données", "100 %")
    st.caption("L'ETL conserve toutes les lignes.")

st.divider()


# =============================================================================
# Trois onglets d analyse
# =============================================================================

rules, completeness, lineage = st.tabs(
    ["Signalements de qualité", "Complétude et doublons", "Pipeline et sources"]
)


# -----------------------------------------------------------------------------
# Onglet 1 : Signalements de qualité
# -----------------------------------------------------------------------------
with rules:
    st.subheader("Quatre contrôles automatiques sur les observations")
    st.caption(
        "Chaque règle détecte une incohérence structurelle (retards négatifs, "
        "annulations supérieures aux circulations prévues, ordres de retard "
        "non monotones). Une observation peut déclencher plusieurs contrôles."
    )

    counts = (
        donnees_completes[FLAGS]
        .sum()
        .rename(index=LIBELLES_FLAGS)
        .sort_values(ascending=True)
    )
    fig_flags = go.Figure(
        data=[
            go.Bar(
                y=counts.index,
                x=counts.values,
                orientation="h",
                marker=dict(color="#0077B6"),
                text=[f"{int(v):,}".replace(",", " ") for v in counts.values],
                textposition="outside",
            )
        ]
    )
    fig_flags.update_layout(
        height=260,
        margin=dict(l=10, r=40, t=10, b=10),
        xaxis=dict(title="Nombre d'observations", showgrid=False),
        yaxis=dict(title=None),
        plot_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig_flags, width="stretch")

    st.markdown("### Explorer les observations signalées")
    data = filters(
        donnees_completes,
        label="Affiner le périmètre (période, service, gares)",
        expanded=False,
    )
    flagged = data[FLAGS].fillna(False).any(axis=1)
    nb_vus = int(flagged.sum())
    st.caption(
        f"**{nb_vus:,} observations signalées** dans le périmètre choisi, "
        f"sur {len(data):,} examinées.".replace(",", " ")
    )

    with st.expander("Voir le détail des observations signalées"):
        st.dataframe(data.loc[flagged], hide_index=True)


# -----------------------------------------------------------------------------
# Onglet 2 : Complétude et doublons
# -----------------------------------------------------------------------------
with completeness:
    st.subheader("Valeurs manquantes par colonne")
    st.caption(
        "Compte sur l'ensemble des 12 907 observations. "
        "Une valeur manquante n'est pas un zéro : "
        "elle indique l'absence d'information pour ce mois-liaison."
    )

    missing = donnees_completes.isna().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    if missing.empty:
        st.success("Aucune valeur manquante sur l'ensemble du dataset.")
    else:
        part = missing / nb_total * 100
        fig_missing = go.Figure(
            data=[
                go.Bar(
                    y=missing.index[::-1],
                    x=missing.values[::-1],
                    orientation="h",
                    marker=dict(color="#E67E22"),
                    text=[
                        f"{v:,.0f} ({p:.1f} %)".replace(",", " ")
                        for v, p in zip(missing.values[::-1], part.values[::-1])
                    ],
                    textposition="outside",
                )
            ]
        )
        fig_missing.update_layout(
            height=max(300, 24 * len(missing)),
            margin=dict(l=10, r=80, t=10, b=10),
            xaxis=dict(title="Nombre d'observations manquantes", showgrid=False),
            yaxis=dict(title=None),
            plot_bgcolor="#FFFFFF",
        )
        st.plotly_chart(fig_missing, width="stretch")

        with st.expander("Tableau détaillé"):
            tableau = pd.DataFrame(
                {
                    "Valeurs manquantes": missing,
                    "Part des observations (%)": part.round(2),
                }
            )
            st.dataframe(tableau)

    st.markdown("### Unicité de la clé mensuelle")
    nb_doublons = int(donnees_completes.duplicated(KEYS).sum())
    col_k1, col_k2 = st.columns(2)
    with col_k1, st.container(border=True):
        st.metric("Doublons de clé détectés", nb_doublons)
    with col_k2, st.container(border=True):
        st.metric("Clé utilisée", "mois × service × départ × arrivée")
    st.caption(
        "Le chargeur vérifie l'unicité de la clé avant tout affichage. "
        "Un doublon serait un signe d'erreur d'agrégation ou de concaténation."
    )


# -----------------------------------------------------------------------------
# Onglet 3 : Pipeline et sources
# -----------------------------------------------------------------------------
with lineage:
    st.subheader("Pipeline ETL : du fichier source aux observations analysées")
    st.caption(
        "Chaîne de traitement non destructive : chaque étape ajoute de l'information "
        "sans supprimer de ligne, garantissant la traçabilité complète."
    )

    etapes = pd.DataFrame(
        [
            {
                "Étape": "1. Fichier brut SNCF",
                "Observations": f"{nb_total:,}".replace(",", " "),
                "Action": "Téléchargement du CSV AQST depuis l'API data.gouv.fr "
                "(régularité mensuelle TGV).",
            },
            {
                "Étape": "2. Parsing et typage",
                "Observations": f"{nb_total:,}".replace(",", " "),
                "Action": "Lecture via pandas, typage des dates au format mensuel, "
                "normalisation des noms de gares.",
            },
            {
                "Étape": "3. Contrôles de qualité",
                "Observations": f"{nb_total:,}".replace(",", " "),
                "Action": "Ajout de 4 colonnes flag_* identifiant les incohérences "
                "structurelles sans modification des valeurs.",
            },
            {
                "Étape": "4. Sauvegarde parquet",
                "Observations": f"{nb_total:,}".replace(",", " "),
                "Action": "Export vers data/processed/sncf.parquet, format colonnaire "
                "optimisé pour l'analyse et les notebooks.",
            },
        ]
    )
    st.dataframe(etapes, hide_index=True, width="stretch")

    st.markdown("### Ressources de référence")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        report("data/reports/data_contract.md", "Contrat des données (markdown)")
    with col_r2:
        report(
            "data/reports/anomalies_qualite.csv", "Rapport original d'anomalies (CSV)"
        )

    with st.expander("Audit textuel complet du périmètre source"):
        path = ROOT / "data/reports/data_quality_report.txt"
        if path.exists():
            st.text(path.read_text(encoding="utf-8"))
        else:
            st.info("Rapport textuel non disponible.")
