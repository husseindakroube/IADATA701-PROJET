'Exploration des liaisons et analyse structurelle du réseau TGV.'

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.activity import log_selection
from utils.carte import (
    afficher_bandeau_clusters,
    afficher_legende_taux,
    afficher_panneau_liaison,
    charger_coordonnees_gares,
    charger_liaisons_detail,
    charger_sncf_mensuel,
    construire_carte,
    construire_ego_graphe,
    gares_du_service,
    libelle_liaison,
    LIBELLES_CLUSTERS,
)
from utils.data import filters, observations, report, scope_metrics, table
from projet_kit_data.web_data import ROOT


st.caption("EXPLORER LES SERVICES TGV")
st.title("Une liaison, mois après mois")
st.write(
    "Explorez les 130 liaisons orientées du réseau sur une carte interactive, "
    "suivez l'évolution des retards et annulations d'une liaison précise, "
    "ou analysez la structure globale du réseau à travers les centralités."
)

carte_onglet, routes, comparer, network = st.tabs([
    "Carte interactive", "Explorer une liaison", "Comparer deux liaisons",
    "Comprendre le réseau",
])


# =============================================================================
# Onglet 1 — Carte interactive
# =============================================================================
with carte_onglet:
    st.subheader("Carte des 130 liaisons TGV orientées")
    st.caption(
        "Les liaisons sont colorées par cluster (profils calculés sur la période "
        "d'apprentissage 2019-01 → 2024-05) ou par taux de retard observé. "
        "Les prédictions affichées proviennent du modèle A retenu dans le notebook 05."
    )

    liaisons_detail = charger_liaisons_detail()
    coords = charger_coordonnees_gares()
    sncf_mensuel = charger_sncf_mensuel()
    moyenne_reseau = liaisons_detail["taux_retard_observe_global"].mean()

    afficher_bandeau_clusters(liaisons_detail)
    st.divider()

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        services = ["Tous"] + sorted(liaisons_detail["service"].dropna().unique().tolist())
        service_choisi = st.selectbox("Service", services, key="carte_service")
    with col_f2:
        gares_dep = ["Toutes"] + sorted(liaisons_detail["gare_depart"].unique().tolist())
        gare_dep = st.selectbox("Gare de départ", gares_dep, key="carte_dep")
    with col_f3:
        gares_arr = ["Toutes"] + sorted(liaisons_detail["gare_arrivee"].unique().tolist())
        gare_arr = st.selectbox("Gare d'arrivée", gares_arr, key="carte_arr")
    with col_f4:
        clusters_opts = ["Tous"] + [
            f"Cluster {c} — {LIBELLES_CLUSTERS[c]}" for c in sorted(LIBELLES_CLUSTERS)
        ]
        cluster_choisi = st.selectbox("Cluster", clusters_opts, key="carte_cluster")

    col_mode, col_tel = st.columns([3, 1])
    with col_mode:
        mode_couleur = st.radio(
            "Colorer la carte par", options=["Cluster", "Taux de retard"],
            horizontal=True, key="carte_mode",
        )
        mode_code = "cluster" if mode_couleur == "Cluster" else "taux"

    lf = liaisons_detail.copy()
    if service_choisi != "Tous":
        lf = lf[lf["service"] == service_choisi]
    if gare_dep != "Toutes":
        lf = lf[lf["gare_depart"] == gare_dep]
    if gare_arr != "Toutes":
        lf = lf[lf["gare_arrivee"] == gare_arr]
    if cluster_choisi != "Tous":
        num_c = int(cluster_choisi.split(" ")[1])
        lf = lf[lf["cluster"] == num_c]

    with col_tel:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.download_button(
            label="Télécharger la sélection (CSV)",
            data=lf.to_csv(index=False).encode("utf-8-sig"),
            file_name="liaisons_selection.csv", mime="text/csv",
            width="stretch", disabled=lf.empty,
        )

    st.caption(
        f"**{len(lf)} liaison{'s' if len(lf) > 1 else ''}** sur {len(liaisons_detail)} "
        "après application des filtres."
    )

    if mode_code == "taux":
        afficher_legende_taux()

    if "carte_liaison_courante" not in st.session_state:
        st.session_state["carte_liaison_courante"] = "(aucune sélection)"

    options = ["(aucune sélection)"] + [
        libelle_liaison(l) for _, l in lf.sort_values(["gare_depart", "gare_arrivee"]).iterrows()
    ]
    if st.session_state["carte_liaison_courante"] not in options:
        st.session_state["carte_liaison_courante"] = "(aucune sélection)"
    idx_def = options.index(st.session_state["carte_liaison_courante"])

    col_sel, col_reset = st.columns([5, 1])
    with col_sel:
        choix = st.selectbox(
            "Choisir une liaison", options, index=idx_def, key="carte_selectbox_liaison"
        )
    with col_reset:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Réinitialiser", width="stretch",
                     disabled=(choix == "(aucune sélection)"),
                     help="Revient à la vue d'ensemble"):
            st.session_state["carte_liaison_courante"] = "(aucune sélection)"
            st.rerun()
    st.session_state["carte_liaison_courante"] = choix

    liaison_sel = None
    if choix != "(aucune sélection)":
        dep, arr = choix.split(" → ")
        m = liaisons_detail[(liaisons_detail["gare_depart"] == dep)
                            & (liaisons_detail["gare_arrivee"] == arr)]
        if not m.empty:
            liaison_sel = m.iloc[0].to_dict()
            log_selection("carte_route_view", route=choix)

    gares_actives = set(lf["gare_depart"].unique()) | set(lf["gare_arrivee"].unique())
    coords_filtrees = coords[coords["gare"].isin(gares_actives)]

    col_carte, col_panneau = st.columns([2, 1])
    with col_carte:
        from streamlit_folium import st_folium
        carte_folium = construire_carte(lf, coords_filtrees, liaison_sel, mode_couleur=mode_code)
        retour = st_folium(
            carte_folium, width=None, height=560,
            returned_objects=["last_object_clicked_tooltip"],
            key=f"carte_principale_{mode_code}",
        )
        if retour and retour.get("last_object_clicked_tooltip"):
            tooltip = retour["last_object_clicked_tooltip"]
            if " → " in tooltip and tooltip != choix:
                st.session_state["carte_liaison_courante"] = tooltip
                st.rerun()

    with col_panneau:
        if liaison_sel is None:
            st.info("Sélectionnez une liaison dans la liste ou cliquez sur une ligne "
                    "de la carte pour voir ses caractéristiques.")
            st.markdown("### Vue d'ensemble")
            moy_f = lf["taux_retard_observe_global"].mean() if not lf.empty else 0
            st.metric("Liaisons visibles", len(lf))
            st.metric("Gares concernées", len(coords_filtrees))
            st.metric(
                "Taux de retard moyen de la sélection",
                f"{moy_f * 100:.1f} %",
                f"{(moy_f - moyenne_reseau) * 100:+.1f} pts vs réseau" if moy_f != 0 else None,
            )
            if not lf.empty:
                st.markdown("**Top 3 des plus en retard**")
                for _, r in lf.nlargest(3, "taux_retard_observe_global").iterrows():
                    st.markdown(f"- {r['gare_depart']} → {r['gare_arrivee']} : "
                                f"**{r['taux_retard_observe_global'] * 100:.1f} %**")
                st.markdown("**Top 3 des plus ponctuelles**")
                for _, r in lf.nsmallest(3, "taux_retard_observe_global").iterrows():
                    st.markdown(f"- {r['gare_depart']} → {r['gare_arrivee']} : "
                                f"**{r['taux_retard_observe_global'] * 100:.1f} %**")
        else:
            st.markdown(f"### {libelle_liaison(liaison_sel)}")
            afficher_panneau_liaison(liaison_sel, moyenne_reseau, liaisons_detail, sncf_mensuel)

    st.caption(
        "Les prédictions utilisent le modèle A (HistGradientBoostingRegressor) retenu "
        "après correction de la fuite temporelle, période test 2025-07 → 2026-09. "
        "Les causes de retard sont des pourcentages moyens pondérés par le nombre de retards."
    )


# =============================================================================
# Onglet 2 — Explorer une liaison (vue temporelle détaillée)
# =============================================================================
with routes:
    st.subheader("Suivi mensuel d'une liaison")
    st.write(
        "Explorez l'évolution mois par mois d'une liaison : retards moyens à "
        "l'arrivée, nombre de circulations et annulations, et détail des causes."
    )

    data = filters(observations(), label="Période, service et gares", expanded=True)
    with st.expander("Couverture du périmètre sélectionné"):
        scope_metrics(data)

    labels = data.service + " · " + data.gare_depart + " → " + data.gare_arrivee
    route = st.selectbox("Liaison à explorer", sorted(labels.unique()))
    log_selection("route_view", route=route)
    selected = data.loc[labels.eq(route)].sort_values("date").copy()

    # Bandeau de synthèse de la liaison
    total_prevu = int(selected["nb_train_prevu"].sum())
    total_annul = int(selected["nb_annulation"].sum())
    taux_annul = (total_annul / total_prevu * 100) if total_prevu > 0 else 0
    retard_moy = selected["retard_moyen_tous_trains_arrivee"].mean()
    nb_mois = len(selected)

    with st.container(border=True):
        st.markdown(f"### {selected.iloc[0].gare_depart} → {selected.iloc[0].gare_arrivee}")
        st.caption(
            f"{selected.iloc[0].service} · {nb_mois} mois observés · "
            f"{selected.date.min():%Y-%m} → {selected.date.max():%Y-%m}"
        )
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Trains prévus (total)", f"{total_prevu:,}".replace(",", " "))
        with s2:
            st.metric("Annulations (total)", f"{total_annul:,}".replace(",", " "),
                      f"{taux_annul:.2f} % du prévu")
        with s3:
            st.metric("Retard moyen arrivée", f"{retard_moy:.1f} min")
        with s4:
            st.metric("Mois observés", nb_mois)

    # Courbe retard moyen arrivée
    st.subheader("Retard moyen à l'arrivée (minutes par mois)")
    fig_retard = go.Figure()
    fig_retard.add_trace(go.Scatter(
        x=selected["date"], y=selected["retard_moyen_tous_trains_arrivee"],
        mode="lines+markers", line=dict(color="#C0392B", width=2), marker=dict(size=5),
        hovertemplate="%{x|%b %Y}<br>%{y:.1f} min<extra></extra>",
    ))
    fig_retard.add_hline(
        y=retard_moy, line_dash="dot", line_color="#7F8C8D",
        annotation_text=f"Moyenne {retard_moy:.1f} min",
        annotation_position="top right", annotation_font_size=10,
    )
    fig_retard.update_layout(
        height=300, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title=None, showgrid=False),
        yaxis=dict(title="Minutes", gridcolor="#ECF0F1"),
        plot_bgcolor="#FFFFFF", showlegend=False,
    )
    st.plotly_chart(fig_retard, width="stretch")

    # Courbe circulations prévues + annulations
    st.subheader("Circulations prévues et annulations (nombre de trains)")
    fig_trains = go.Figure()
    fig_trains.add_trace(go.Scatter(
        x=selected["date"], y=selected["nb_train_prevu"],
        mode="lines+markers", name="Trains prévus",
        line=dict(color="#2E86DE", width=2), marker=dict(size=4),
    ))
    fig_trains.add_trace(go.Scatter(
        x=selected["date"], y=selected["nb_annulation"],
        mode="lines+markers", name="Annulations",
        line=dict(color="#E74C3C", width=2), marker=dict(size=4),
    ))
    fig_trains.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(title=None, showgrid=False),
        yaxis=dict(title="Nombre de trains", gridcolor="#ECF0F1"),
        plot_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_trains, width="stretch")

    # Taux d annulation si disponible
    research = table("data/processed/research_dataset.parquet", required=False)
    if not research.empty:
        row = selected.iloc[0]
        cancellation = research.loc[
            research.service.eq(row.service)
            & research.gare_depart.eq(row.gare_depart)
            & research.gare_arrivee.eq(row.gare_arrivee)
            & research.date.isin(selected.date.dt.strftime("%Y-%m"))
        ].sort_values("date")
        if not cancellation.empty:
            st.subheader("Taux d'annulation mensuel (%)")
            fig_canc = go.Figure(data=[go.Scatter(
                x=pd.to_datetime(cancellation["date"]),
                y=cancellation["cancellation_rate"] * 100,
                mode="lines+markers", line=dict(color="#E67E22", width=2),
                marker=dict(size=5),
                hovertemplate="%{x|%b %Y}<br>%{y:.2f} %<extra></extra>",
            )])
            fig_canc.update_layout(
                height=260, margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(title=None, showgrid=False),
                yaxis=dict(title="Part annulée (%)", gridcolor="#ECF0F1"),
                plot_bgcolor="#FFFFFF", showlegend=False,
            )
            st.plotly_chart(fig_canc, width="stretch")

    # Causes de retard
    with st.expander("Causes de retard mois par mois (%)"):
        st.caption(
            "Ces pourcentages indiquent la part de chaque catégorie de cause "
            "dans les retards du mois, telle que renseignée par la SNCF."
        )
        colonnes_causes = ["date"] + [c for c in selected.columns if c.startswith("prct_cause")]
        st.dataframe(selected[colonnes_causes], hide_index=True, width="stretch")

    with st.expander("Observations brutes et commentaires SNCF"):
        st.dataframe(selected, hide_index=True)


# =============================================================================
# Onglet 3 — Comparer deux liaisons
# =============================================================================
with comparer:
    st.subheader("Comparer deux liaisons côte à côte")
    st.write(
        "Sélectionnez deux liaisons pour superposer leurs caractéristiques, "
        "leur évolution mensuelle et leurs causes de retard."
    )

    liaisons_cmp = charger_liaisons_detail()
    sncf_cmp = charger_sncf_mensuel()
    options_cmp = sorted(
        libelle_liaison(l) for _, l in liaisons_cmp.iterrows()
    )

    cA, cB = st.columns(2)
    with cA:
        choix_A = st.selectbox("Liaison A", options_cmp, index=0, key="cmp_A")
    with cB:
        default_B = 1 if len(options_cmp) > 1 else 0
        choix_B = st.selectbox("Liaison B", options_cmp, index=default_B, key="cmp_B")

    def _get(choix):
        dep, arr = choix.split(" → ")
        m = liaisons_cmp[(liaisons_cmp["gare_depart"] == dep)
                         & (liaisons_cmp["gare_arrivee"] == arr)]
        return m.iloc[0].to_dict() if not m.empty else None

    lA = _get(choix_A)
    lB = _get(choix_B)

    if lA is None or lB is None:
        st.warning("Une des liaisons choisies n'a pas été trouvée.")
    elif choix_A == choix_B:
        st.info("Sélectionnez deux liaisons différentes pour les comparer.")
    else:
        # Tableau comparatif
        def _fmt(v, suf="%", mul=100, nd=1):
            return f"{v * mul:.{nd}f} {suf}" if pd.notna(v) else "N/A"

        comparatif = pd.DataFrame([
            {"Métrique": "Service", "Liaison A": lA["service"], "Liaison B": lB["service"]},
            {"Métrique": "Cluster", "Liaison A": int(lA["cluster"]) if pd.notna(lA["cluster"]) else "?",
             "Liaison B": int(lB["cluster"]) if pd.notna(lB["cluster"]) else "?"},
            {"Métrique": "Durée moyenne", "Liaison A": f"{lA['duree_moyenne']:.0f} min",
             "Liaison B": f"{lB['duree_moyenne']:.0f} min"},
            {"Métrique": "Taux de retard observé",
             "Liaison A": _fmt(lA["taux_retard_observe_global"]),
             "Liaison B": _fmt(lB["taux_retard_observe_global"])},
            {"Métrique": "Taux prédit (modèle A)",
             "Liaison A": _fmt(lA["taux_retard_predit"]),
             "Liaison B": _fmt(lB["taux_retard_predit"])},
            {"Métrique": "Nombre d'observations",
             "Liaison A": int(lA["nb_observations"]),
             "Liaison B": int(lB["nb_observations"])},
        ])
        st.markdown("### Vue comparative")
        st.dataframe(comparatif, hide_index=True, width="stretch")

        # Courbes superposées de l évolution
        st.markdown("### Évolution mensuelle du taux de retard")
        import plotly.graph_objects as go

        def _serie(l):
            s = sncf_cmp[(sncf_cmp["gare_depart"] == l["gare_depart"])
                         & (sncf_cmp["gare_arrivee"] == l["gare_arrivee"])].sort_values("date").copy()
            s["realise"] = s["nb_train_prevu"] - s["nb_annulation"]
            s = s[s["realise"] > 0]
            s["taux"] = s["nb_train_retard_arrivee"] / s["realise"]
            return s

        sA = _serie(lA)
        sB = _serie(lB)
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Scatter(
            x=sA["date"], y=sA["taux"] * 100, mode="lines",
            name=f"A — {lA['gare_depart']} → {lA['gare_arrivee']}",
            line=dict(color="#C0392B", width=2),
        ))
        fig_cmp.add_trace(go.Scatter(
            x=sB["date"], y=sB["taux"] * 100, mode="lines",
            name=f"B — {lB['gare_depart']} → {lB['gare_arrivee']}",
            line=dict(color="#2E86DE", width=2),
        ))
        fig_cmp.update_layout(
            height=320, margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(title=None, showgrid=False),
            yaxis=dict(title="Taux mensuel (%)", gridcolor="#ECF0F1"),
            plot_bgcolor="#FFFFFF",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1),
        )
        st.plotly_chart(fig_cmp, width="stretch")

        # Causes de retard comparées
        st.markdown("### Causes de retard comparées")
        from utils.carte import CAUSES_LIBELLES
        causes_A = {lib: lA[col] for col, lib in CAUSES_LIBELLES.items()
                    if pd.notna(lA[col])}
        causes_B = {lib: lB[col] for col, lib in CAUSES_LIBELLES.items()
                    if pd.notna(lB[col])}
        labels_causes = list(CAUSES_LIBELLES.values())
        fig_causes = go.Figure()
        fig_causes.add_trace(go.Bar(
            name=f"A — {lA['gare_depart']} → {lA['gare_arrivee']}",
            x=labels_causes,
            y=[causes_A.get(l, 0) for l in labels_causes],
            marker=dict(color="#C0392B"),
        ))
        fig_causes.add_trace(go.Bar(
            name=f"B — {lB['gare_depart']} → {lB['gare_arrivee']}",
            x=labels_causes,
            y=[causes_B.get(l, 0) for l in labels_causes],
            marker=dict(color="#2E86DE"),
        ))
        fig_causes.update_layout(
            height=320, margin=dict(l=10, r=10, t=30, b=40),
            barmode="group",
            yaxis=dict(title="Part des retards (%)", gridcolor="#ECF0F1"),
            xaxis=dict(title=None, tickangle=-20),
            plot_bgcolor="#FFFFFF",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1),
        )
        st.plotly_chart(fig_causes, width="stretch")


# =============================================================================
# Onglet 4 — Comprendre le réseau (analyse structurelle)
# =============================================================================
with network:
    st.subheader("Analyse structurelle du réseau TGV")
    st.write(
        "Analyse par théorie des graphes de la structure origine-destination "
        "des services TGV AQST sur l'ensemble de la période 2018-01 → 2026-09. "
        "Chaque gare est un nœud, chaque liaison orientée une arête."
    )

    # Encadré pédagogique sur les centralités
    with st.expander("Comprendre les mesures de centralité", expanded=False):
        st.markdown(
            "**Degré entrant / sortant.** Nombre de liaisons arrivant ou partant "
            "d'une gare. Un degré élevé signifie une gare très connectée.\n\n"
            "**Betweenness (intermédiarité).** Nombre de plus courts chemins "
            "du réseau qui passent par cette gare. Les gares à forte betweenness "
            "sont des hubs de transit stratégiques.\n\n"
            "**PageRank.** Score d'importance qui tient compte de l'importance "
            "des voisins. Une gare connectée à des hubs reçoit un meilleur score "
            "qu'une gare connectée à des terminus isolés.\n\n"
            "**Closeness (proximité).** Inverse de la distance moyenne à toutes "
            "les autres gares. Mesure l'accessibilité globale depuis cette gare."
        )

    # Bandeau de métriques réseau
    summary = table(
        "data/processed/graph/descriptive/network_summary.parquet", required=False
    )
    if not summary.empty:
        st.markdown("### Vue d'ensemble des deux réseaux")
        for _, row in summary.iterrows():
            with st.container(border=True):
                st.markdown(f"**Réseau {row.service}**")
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Gares", int(row.node_count))
                with m2:
                    st.metric("Liaisons orientées", int(row.edge_count))
                with m3:
                    if "density" in row.index and pd.notna(row.density):
                        st.metric("Densité", f"{row.density:.3f}")
                    else:
                        st.metric("Densité", "N/A")
                with m4:
                    if "diameter" in row.index and pd.notna(row.diameter):
                        st.metric("Diamètre", int(row.diameter))
                    else:
                        st.metric("Diamètre", "N/A")

    st.divider()

    # Sélection du service
    service = st.selectbox("Choisir un réseau à analyser", ["National", "International"])
    log_selection("network_view", service=service)

    # Ego-graphe centré sur une gare
    st.markdown("### Explorer une gare et ses connexions directes")
    st.caption(
        "Choisissez une gare pour voir ses liaisons directes. Rouge = départs "
        "de la gare, bleu = arrivées. Taille des voisins proportionnelle à leur betweenness."
    )
    liste_gares = gares_du_service(service)
    if liste_gares:
        # Sélection par défaut : Paris Lyon pour National, Paris Lyon pour Internat
        default_idx = 0
        for candidat in ["PARIS LYON", "PARIS EST", "LYON PART DIEU"]:
            if candidat in liste_gares:
                default_idx = liste_gares.index(candidat)
                break
        gare_centrale = st.selectbox(
            "Gare centrale", liste_gares, index=default_idx,
            key=f"ego_gare_{service}",
        )
        log_selection("ego_graphe_view", service=service, gare=gare_centrale)
        fig_ego = construire_ego_graphe(service, gare_centrale)
        st.plotly_chart(fig_ego, width="stretch")

    # Visualisation statique en complément
    path = ROOT / f"data/processed/graph/visualizations/network_{service.lower()}.png"
    if path.is_file():
        with st.expander("Voir aussi la visualisation statique issue de l'analyse graphe"):
            st.image(
                str(path),
                caption=f"Réseau {service} · 2018-01 → 2026-09 · liaisons orientées",
                width="stretch",
            )

    # Classements de centralité
    ranking = table(
        "data/processed/graph/descriptive/node_rankings.parquet", required=False
    )
    if not ranking.empty:
        ranking_service = ranking.loc[ranking.service.eq(service)]
        if not ranking_service.empty:
            st.markdown("### Classements des gares les plus centrales")
            st.caption(
                "Top des gares pour chaque mesure de centralité calculée sur "
                "l'ensemble de la période."
            )
            st.dataframe(ranking_service, hide_index=True, width="stretch")

    # Détails d une gare
    nodes = table("data/processed/graph/node_metrics.parquet", required=False)
    if not nodes.empty:
        nodes_s = nodes.loc[nodes.service.eq(service) & nodes.period.eq("overall")]
        if not nodes_s.empty:
            st.markdown("### Métriques détaillées par gare")
            station = st.selectbox(
                "Choisir une gare", sorted(nodes_s.station_name.unique()),
                key=f"station_{service}",
            )
            log_selection("station_view", service=service, station=station)
            detail = nodes_s.loc[nodes_s.station_name.eq(station)]
            st.dataframe(detail, hide_index=True, width="stretch")

    report("data/reports/graph/research_report.md", "Rapport réseau complet")
