'Fonctions de rendu de la carte interactive des liaisons TGV.'

from __future__ import annotations

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from folium.features import DivIcon

import networkx as nx

from projet_kit_data.web_data import load_table


# =============================================================================
# Constantes de style
# =============================================================================

COULEURS_CLUSTERS = {
    0: "#C0392B",
    1: "#E67E22",
    2: "#27AE60",
    3: "#2E86DE",
}

LIBELLES_CLUSTERS = {
    0: "International longue distance",
    1: "Mixte Europe proche",
    2: "France courte distance",
    3: "France longue distance",
}

DESCRIPTIONS_CLUSTERS = {
    0: "Les 8 liaisons internationales les plus longues (Francfort, Stuttgart, "
       "Madrid, Italie). Taux de retard moyen autour de 20 pour cent, les plus "
       "difficiles à prédire du réseau.",
    1: "36 liaisons de durée intermédiaire, mêlant la France et l'Europe proche "
       "(Genève, Lausanne, Zurich, Barcelone). Taux de retard autour de 14 pour cent.",
    2: "48 liaisons courtes principalement nationales, durée moyenne autour de "
       "deux heures. Taux de retard proche de 16 pour cent avec forte variabilité.",
    3: "38 liaisons longues entre grandes villes françaises ou province-province. "
       "Taux de retard autour de 14 pour cent.",
}

CAUSES_LIBELLES = {
    "prct_cause_externe": "Causes externes",
    "prct_cause_infra": "Infrastructure",
    "prct_cause_gestion_trafic": "Gestion du trafic",
    "prct_cause_materiel_roulant": "Matériel roulant",
    "prct_cause_gestion_gare": "Gestion gare",
    "prct_cause_prise_en_charge_voyageurs": "Voyageurs",
}

GRADIENT_TAUX = [
    (0.00, "#1E8449"),
    (0.08, "#27AE60"),
    (0.12, "#F1C40F"),
    (0.17, "#E67E22"),
    (0.25, "#C0392B"),
    (1.00, "#7B241C"),
]


# =============================================================================
# Chargement des données
# =============================================================================

@st.cache_data(show_spinner=False)
def charger_liaisons_detail() -> pd.DataFrame:
    'Charge le fichier agrégé des 130 liaisons orientées.'
    return load_table("data/processed/liaisons_detail.csv")


@st.cache_data(show_spinner=False)
def charger_coordonnees_gares() -> pd.DataFrame:
    'Charge les coordonnées GPS des gares utilisées dans le projet.'
    return load_table("data/raw/coordonnees_gares.csv")


@st.cache_data(show_spinner=False)
def charger_sncf_mensuel() -> pd.DataFrame:
    'Charge les observations mensuelles pour l évolution temporelle.'
    df = load_table("data/processed/sncf.parquet")
    df["date"] = pd.to_datetime(df["date"] + "-01", errors="coerce")
    return df


# =============================================================================
# Utilitaires
# =============================================================================

def formater_duree(minutes: float) -> str:
    'Convertit une durée en minutes vers un format lisible.'
    if pd.isna(minutes):
        return "N/A"
    h = int(minutes // 60)
    m = int(round(minutes - h * 60))
    if h == 0:
        return f"{m} min"
    return f"{h} h {m:02d}"


def libelle_liaison(ligne) -> str:
    'Formate une liaison en chaîne lisible.'
    return f"{ligne['gare_depart']} → {ligne['gare_arrivee']}"


def couleur_par_taux(taux: float) -> str:
    'Interpole une couleur sur le gradient vert-rouge pour un taux entre 0 et 1.'
    if pd.isna(taux):
        return "#95A5A6"
    for i in range(len(GRADIENT_TAUX) - 1):
        bas, couleur_bas = GRADIENT_TAUX[i]
        haut, couleur_haut = GRADIENT_TAUX[i + 1]
        if taux <= haut:
            ratio = (taux - bas) / (haut - bas) if haut > bas else 0
            r1, g1, b1 = int(couleur_bas[1:3], 16), int(couleur_bas[3:5], 16), int(couleur_bas[5:7], 16)
            r2, g2, b2 = int(couleur_haut[1:3], 16), int(couleur_haut[3:5], 16), int(couleur_haut[5:7], 16)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            return f"#{r:02X}{g:02X}{b:02X}"
    return GRADIENT_TAUX[-1][1]


# =============================================================================
# Construction de la carte folium
# =============================================================================

def construire_carte(liaisons: pd.DataFrame,
                     coords: pd.DataFrame,
                     liaison_selectionnee: dict | None,
                     mode_couleur: str = "cluster") -> folium.Map:
    'Construit la carte folium avec toutes les liaisons et leurs gares.'
    centre_lat, centre_lon, zoom = 46.6, 4.5, 6
    if liaison_selectionnee is not None:
        centre_lat = (liaison_selectionnee["lat_depart"] + liaison_selectionnee["lat_arrivee"]) / 2
        centre_lon = (liaison_selectionnee["lon_depart"] + liaison_selectionnee["lon_arrivee"]) / 2

    carte = folium.Map(location=[centre_lat, centre_lon], zoom_start=zoom,
                       tiles="OpenStreetMap", control_scale=True)

    for _, ligne in liaisons.iterrows():
        if pd.isna(ligne["lat_depart"]) or pd.isna(ligne["lat_arrivee"]):
            continue
        if mode_couleur == "taux":
            couleur = couleur_par_taux(ligne["taux_retard_observe_global"])
        else:
            cluster = int(ligne["cluster"]) if pd.notna(ligne["cluster"]) else None
            couleur = COULEURS_CLUSTERS.get(cluster, "#95A5A6")
        est_selectionnee = (
            liaison_selectionnee is not None
            and ligne["gare_depart"] == liaison_selectionnee["gare_depart"]
            and ligne["gare_arrivee"] == liaison_selectionnee["gare_arrivee"]
        )
        if est_selectionnee:
            poids, opacite = 6, 1.0
        elif liaison_selectionnee is not None:
            poids, opacite = 1.5, 0.12
        else:
            poids, opacite = 2, 0.55
        folium.PolyLine(
            locations=[[ligne["lat_depart"], ligne["lon_depart"]],
                       [ligne["lat_arrivee"], ligne["lon_arrivee"]]],
            color=couleur, weight=poids, opacity=opacite,
            tooltip=libelle_liaison(ligne),
        ).add_to(carte)

    gares_selection = (
        {liaison_selectionnee["gare_depart"], liaison_selectionnee["gare_arrivee"]}
        if liaison_selectionnee is not None else set()
    )
    for _, gare in coords.iterrows():
        est_dans = gare["gare"] in gares_selection
        if est_dans:
            rayon, bord, remplissage, opacite = 6, "#2C3E50", "#F1C40F", 1.0
        elif liaison_selectionnee is not None:
            rayon, bord, remplissage, opacite = 2, "#7F8C8D", "#FFFFFF", 0.4
        else:
            rayon, bord, remplissage, opacite = 3, "#34495E", "#FFFFFF", 1.0
        folium.CircleMarker(
            location=[gare["latitude"], gare["longitude"]],
            radius=rayon, color=bord, fill=True, fill_color=remplissage,
            fill_opacity=opacite, opacity=opacite, weight=1,
            tooltip=gare["gare"],
        ).add_to(carte)

    if liaison_selectionnee is not None:
        for role, suffixe in [("depart", "Départ"), ("arrivee", "Arrivée")]:
            folium.Marker(
                location=[liaison_selectionnee[f"lat_{role}"],
                          liaison_selectionnee[f"lon_{role}"]],
                icon=DivIcon(
                    icon_size=(140, 20), icon_anchor=(0, -5),
                    html=(
                        f'<div style="font-size:11px;font-weight:600;color:#2C3E50;'
                        f'background:#FFFFFF;padding:1px 6px;border:1px solid #BDC3C7;'
                        f'border-radius:3px;display:inline-block;white-space:nowrap;">'
                        f'{suffixe}: {liaison_selectionnee["gare_" + role]}</div>'
                    ),
                ),
            ).add_to(carte)
        bounds = [
            [liaison_selectionnee["lat_depart"], liaison_selectionnee["lon_depart"]],
            [liaison_selectionnee["lat_arrivee"], liaison_selectionnee["lon_arrivee"]],
        ]
        carte.fit_bounds(bounds, padding=(60, 60))

    return carte


# =============================================================================
# Blocs d affichage
# =============================================================================

def afficher_bandeau_clusters(liaisons: pd.DataFrame) -> None:
    'Bandeau résumant la répartition des clusters en haut de la carte.'
    cols = st.columns(4)
    for cid in sorted(LIBELLES_CLUSTERS):
        sous = liaisons[liaisons["cluster"] == cid]
        nb = len(sous)
        taux = sous["taux_retard_observe_global"].mean() * 100 if nb > 0 else 0
        couleur = COULEURS_CLUSTERS[cid]
        libelle = LIBELLES_CLUSTERS[cid]
        with cols[cid]:
            st.markdown(
                f'<div style="border-left:5px solid {couleur};padding:10px 14px;'
                f'background:#FAFAFA;border-radius:4px;">'
                f'<div style="font-size:12px;color:#7F8C8D;text-transform:uppercase;'
                f'letter-spacing:0.5px;">Cluster {cid}</div>'
                f'<div style="font-size:14px;font-weight:600;color:#2C3E50;margin:4px 0;">{libelle}</div>'
                f'<div style="font-size:12px;color:#34495E;">{nb} liaisons &bull; '
                f'retard moyen <b>{taux:.1f} %</b></div></div>',
                unsafe_allow_html=True,
            )


def afficher_legende_taux() -> None:
    'Petite barre dégradée pour le mode taux.'
    stops = [f"{c[1]} {int(c[0] * 100)}%" for c in GRADIENT_TAUX]
    gradient = f"linear-gradient(to right, {', '.join(stops)})"
    st.markdown(
        f'<div style="margin-bottom:6px;">'
        f'<div style="font-size:12px;color:#7F8C8D;margin-bottom:4px;">'
        f'Taux de retard observé : <b>vert</b> faible &rarr; <b>rouge</b> élevé</div>'
        f'<div style="height:10px;background:{gradient};border-radius:3px;"></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:11px;'
        f'color:#7F8C8D;margin-top:2px;">'
        f'<span>0 %</span><span>8 %</span><span>12 %</span><span>17 %</span>'
        f'<span>25 %</span><span>&gt; 25 %</span></div></div>',
        unsafe_allow_html=True,
    )


def afficher_evolution_temporelle(sncf: pd.DataFrame, liaison: dict, couleur: str) -> None:
    'Trace la courbe d évolution mensuelle du taux de retard de la liaison.'
    sous = sncf[(sncf["gare_depart"] == liaison["gare_depart"])
                & (sncf["gare_arrivee"] == liaison["gare_arrivee"])].sort_values("date").copy()
    if sous.empty:
        return
    sous["realise"] = sous["nb_train_prevu"] - sous["nb_annulation"]
    sous = sous[sous["realise"] > 0]
    sous["taux_mois"] = sous["nb_train_retard_arrivee"] / sous["realise"]
    st.markdown("**Évolution du taux de retard**")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sous["date"], y=sous["taux_mois"] * 100, mode="lines+markers",
        line=dict(color=couleur, width=2), marker=dict(size=5),
        hovertemplate="%{x|%b %Y}<br>%{y:.1f} %<extra></extra>",
    ))
    moyenne = sous["taux_mois"].mean() * 100
    fig.add_hline(y=moyenne, line_dash="dot", line_color="#7F8C8D",
                  annotation_text=f"Moyenne {moyenne:.1f} %",
                  annotation_position="top right", annotation_font_size=10)
    fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(title=None, showgrid=False),
                      yaxis=dict(title="Taux mensuel (%)", gridcolor="#ECF0F1"),
                      plot_bgcolor="#FFFFFF", showlegend=False)
    st.plotly_chart(fig, width="stretch")


def afficher_trajet_retour(liaisons: pd.DataFrame, liaison: dict) -> None:
    'Affiche un bloc avec les métriques du trajet inverse.'
    retour = liaisons[(liaisons["gare_depart"] == liaison["gare_arrivee"])
                      & (liaisons["gare_arrivee"] == liaison["gare_depart"])]
    if retour.empty:
        return
    r = retour.iloc[0]
    taux_a, taux_r = liaison["taux_retard_observe_global"], r["taux_retard_observe_global"]
    if pd.isna(taux_a) or pd.isna(taux_r):
        return
    ecart = (taux_r - taux_a) * 100
    fleche = "monte de" if ecart > 0 else "baisse de"
    couleur_bloc = "#E74C3C" if ecart > 2 else "#27AE60" if ecart < -2 else "#7F8C8D"
    st.markdown(
        f'<div style="margin-top:12px;padding:10px 14px;border:1px solid #ECF0F1;'
        f'border-left:4px solid {couleur_bloc};border-radius:4px;background:#FAFAFA;">'
        f'<div style="font-size:12px;color:#7F8C8D;text-transform:uppercase;'
        f'letter-spacing:0.5px;">Trajet retour</div>'
        f'<div style="font-size:14px;margin-top:4px;color:#2C3E50;">'
        f'{r["gare_depart"]} → {r["gare_arrivee"]} : <b>{taux_r * 100:.1f} %</b> '
        f'<span style="color:{couleur_bloc};">({fleche} {abs(ecart):.1f} pts)</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Graphe interactif du réseau (tous les noms visibles)
# =============================================================================

@st.cache_data(show_spinner=False)
def charger_edges() -> pd.DataFrame:
    'Charge les arêtes du graphe.'
    return load_table("data/processed/graph/edges.parquet")


@st.cache_data(show_spinner=False)
def charger_nodes() -> pd.DataFrame:
    'Charge les nœuds du graphe.'
    return load_table("data/processed/graph/nodes.parquet")


@st.cache_data(show_spinner=False)
def charger_metriques_noeuds() -> pd.DataFrame:
    'Charge les métriques de centralité par nœud.'
    return load_table("data/processed/graph/node_metrics.parquet")


def gares_du_service(service: str) -> list[str]:
    'Retourne la liste triée des gares d un service donné.'
    edges = charger_edges()
    nodes = charger_nodes()
    id_to_name = dict(zip(nodes["node_id"], nodes["station_name"]))
    edges_s = edges[edges["service"] == service].copy()
    gares = set()
    for _, row in edges_s.iterrows():
        src = id_to_name.get(row["source"])
        tgt = id_to_name.get(row["target"])
        if src:
            gares.add(src)
        if tgt:
            gares.add(tgt)
    return sorted(gares)


def construire_ego_graphe(service: str, gare_centrale: str) -> go.Figure:
    'Construit un ego-graphe radial : gare centrale au milieu, voisins en cercle.'
    import math

    edges = charger_edges()
    nodes = charger_nodes()
    metriques = charger_metriques_noeuds()

    metriques_s = metriques[
        (metriques["service"] == service) & (metriques["period"] == "overall")
    ].set_index("station_name")

    edges_s = edges[edges["service"] == service].copy()
    id_to_name = dict(zip(nodes["node_id"], nodes["station_name"]))
    edges_s["source_name"] = edges_s["source"].map(id_to_name)
    edges_s["target_name"] = edges_s["target"].map(id_to_name)
    edges_s = edges_s.dropna(subset=["source_name", "target_name"])

    ego_edges = edges_s[
        (edges_s["source_name"] == gare_centrale)
        | (edges_s["target_name"] == gare_centrale)
    ]
    sortantes = set(ego_edges[ego_edges["source_name"] == gare_centrale]["target_name"])
    entrantes = set(ego_edges[ego_edges["target_name"] == gare_centrale]["source_name"])

    if ego_edges.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Pas de liaison {service} depuis ou vers {gare_centrale}",
            showarrow=False, font=dict(size=14),
        )
        fig.update_layout(height=500, plot_bgcolor="#F8F9FA",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    voisins = sorted(sortantes | entrantes)

    # Layout radial : centre à (0, 0), voisins en cercle à rayon 1
    positions = {gare_centrale: (0.0, 0.0)}
    n = len(voisins)
    for i, nom in enumerate(voisins):
        angle = 2 * math.pi * i / n - math.pi / 2  # commence en haut
        positions[nom] = (math.cos(angle), math.sin(angle))

    # Courbes de Bézier : chaque sens se courbe à sa gauche, séparant l'aller
    # du retour. Les flèches restent au milieu pour être visibles hors des gares.
    fig = go.Figure()
    for destinations, depart, couleur, nom_trace, rang in [
        (sortantes, True, "#C0392B", "Départs", 2000),
        (entrantes, False, "#2E86DE", "Arrivées", 2001),
    ]:
        xs, ys, tailles = [], [], []
        for voisin in voisins:
            if voisin not in destinations:
                continue
            origine, destination = (
                (gare_centrale, voisin) if depart else (voisin, gare_centrale)
            )
            x0, y0 = positions[origine]
            x1, y1 = positions[destination]
            dx, dy = x1 - x0, y1 - y0
            cx = (x0 + x1) / 2 - 0.22 * dy
            cy = (y0 + y1) / 2 + 0.22 * dx
            for i in range(31):
                t = i / 30
                xs.append((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1)
                ys.append((1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1)
                tailles.append(12 if i == 18 else 0)
            xs.append(None)
            ys.append(None)
            tailles.append(0)
        if xs:
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines+markers",
                line=dict(color=couleur, width=2),
                marker=dict(symbol="arrow", angleref="previous",
                            size=tailles, color=couleur),
                hoverinfo="none", name=nom_trace, showlegend=True, legendrank=rang,
            ))

    # Une trace par gare permet une légende nominative et des couleurs stables.
    couleurs_gares = {
        nom: f"hsl({(i * 137.508) % 360:.3f}, 65%, 48%)"
        for i, nom in enumerate(sorted(nodes["station_name"].dropna().unique()))
    }
    for nom in voisins:
        x, y = positions[nom]
        taille = 16
        survol = f"<b>{nom}</b>"
        if nom in metriques_s.index:
            m = metriques_s.loc[nom]
            bet = float(m["betweenness_centrality"])
            taille += math.sqrt(max(bet, 0)) * 30
            survol += (
                f"<br>Degré : {int(m['degree'])}<br>"
                f"Betweenness : {bet:.3f}<br>PageRank : {float(m['pagerank']):.3f}"
            )
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers",
            marker=dict(size=taille, color=couleurs_gares[nom],
                        line=dict(color="#2C3E50", width=1)),
            hovertext=[survol], hoverinfo="text", name=nom, showlegend=True,
        ))

    # Gare centrale
    if gare_centrale in metriques_s.index:
        m_c = metriques_s.loc[gare_centrale]
        hover_c = (f"<b>{gare_centrale}</b><br>Degré : {int(m_c['degree'])}<br>"
                   f"Betweenness : {float(m_c['betweenness_centrality']):.3f}<br>"
                   f"PageRank : {float(m_c['pagerank']):.3f}")
    else:
        hover_c = f"<b>{gare_centrale}</b>"

    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=dict(
            size=70, color="#2C3E50",
            line=dict(color="#1A1A1A", width=2),
        ),
        hovertext=[hover_c], hoverinfo="text",
        name=f"{gare_centrale} (gare centrale)", showlegend=True, legendrank=0,
    ))

    fig.update_layout(
        height=max(600, 140 + 23 * (len(voisins) + 3)),
        margin=dict(l=20, r=330, t=70, b=20),
        xaxis=dict(visible=False, range=[-1.5, 1.5],
                   scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[-1.4, 1.4]),
        plot_bgcolor="#F8F9FA",
        title=dict(
            text=f"<b>{gare_centrale}</b> · {len(sortantes)} destinations, "
                 f"{len(entrantes)} origines",
            x=0.5, xanchor="center", y=0.98, yanchor="top",
            font=dict(size=14),
        ),
        legend=dict(
            orientation="v", yanchor="top", y=1,
            xanchor="left", x=1.02, itemsizing="constant",
            font=dict(size=11),
        ),
    )
    return fig


def afficher_panneau_liaison(ligne: dict, moyenne_reseau: float,
                             liaisons: pd.DataFrame, sncf: pd.DataFrame) -> None:
    'Affiche le panneau détaillé pour la liaison sélectionnée.'
    cluster = int(ligne["cluster"]) if pd.notna(ligne["cluster"]) else None
    couleur = COULEURS_CLUSTERS.get(cluster, "#95A5A6")
    libelle_cluster = LIBELLES_CLUSTERS.get(cluster, "Non classé")

    st.markdown(
        f'<div style="padding:8px 14px;background:{couleur};color:white;'
        f'border-radius:6px;font-weight:600;display:inline-block;margin-bottom:12px;">'
        f'Cluster {cluster if cluster is not None else "?"} — {libelle_cluster}</div>',
        unsafe_allow_html=True,
    )

    taux_obs = ligne["taux_retard_observe_global"]
    taux_predit = ligne["taux_retard_predit"]
    duree = ligne["duree_moyenne"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Durée moyenne", formater_duree(duree))
        st.metric(
            "Taux de retard observé",
            f"{taux_obs * 100:.1f} %" if pd.notna(taux_obs) else "N/A",
            f"{(taux_obs - moyenne_reseau) * 100:+.1f} pts vs réseau" if pd.notna(taux_obs) else None,
        )
    with col2:
        st.metric("Nombre d'observations",
                  int(ligne["nb_observations"]) if pd.notna(ligne["nb_observations"]) else 0)
        st.metric(
            "Taux prédit (modèle A)",
            f"{taux_predit * 100:.1f} %" if pd.notna(taux_predit) else "N/A",
            f"écart {(taux_predit - taux_obs) * 100:+.1f} pts vs observé"
            if pd.notna(taux_predit) and pd.notna(taux_obs) else None,
        )

    afficher_trajet_retour(liaisons, ligne)
    afficher_evolution_temporelle(sncf, ligne, couleur)

    st.markdown("**Causes de retard moyennes**")
    causes = {lib: ligne[col] for col, lib in CAUSES_LIBELLES.items() if pd.notna(ligne[col])}
    if causes:
        fig = go.Figure(data=[go.Bar(
            x=list(causes.values()), y=list(causes.keys()), orientation="h",
            marker=dict(color=couleur),
            text=[f"{v:.1f} %" for v in causes.values()], textposition="outside",
        )])
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10),
                          xaxis=dict(title="Part des retards (%)",
                                     range=[0, max(causes.values()) * 1.25]),
                          yaxis=dict(title=None, autorange="reversed"),
                          plot_bgcolor="#FAFAFA")
        st.plotly_chart(fig, width="stretch")

    desc = DESCRIPTIONS_CLUSTERS.get(cluster, "")
    if pd.notna(taux_obs):
        ecart = (taux_obs - moyenne_reseau) * 100
        position = "au-dessus" if ecart > 0 else "en dessous"
        st.markdown(
            f"**Lecture.** Cette liaison appartient au cluster {cluster} "
            f"({libelle_cluster}). {desc} Son taux de retard se situe {position} "
            f"de la moyenne du réseau de {abs(ecart):.1f} points."
        )
