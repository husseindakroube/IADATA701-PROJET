'Profils des 4 clusters de liaisons TGV issus du clustering non supervisé.'

from ast import literal_eval

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from utils.activity import log_selection
from utils.data import table


# =============================================================================
# Constantes de style, alignées avec la page Liaisons et réseau
# =============================================================================

COULEURS_CLUSTERS = {
    0: "#C0392B",  # rouge
    1: "#E67E22",  # orange
    2: "#27AE60",  # vert
    3: "#2E86DE",  # bleu
}

LIBELLES_CLUSTERS = {
    0: "International longue distance",
    1: "Mixte Europe proche",
    2: "France courte distance",
    3: "France longue distance",
}

CAUSES_LIBELLES = {
    "prct_cause_externe": "Causes externes",
    "prct_cause_infra": "Infrastructure",
    "prct_cause_gestion_trafic": "Gestion du trafic",
    "prct_cause_materiel_roulant": "Matériel roulant",
    "prct_cause_gestion_gare": "Gestion gare",
    "prct_cause_prise_en_charge_voyageurs": "Voyageurs",
}


# =============================================================================
# En-tête
# =============================================================================

st.caption("TYPOLOGIE DES LIAISONS TGV")
st.title("Quatre profils de liaisons par clustering non supervisé")
st.write(
    "Les 65 paires de gares du réseau ont été regroupées par K-Means (k=4) "
    "sur sept variables standardisées : la durée moyenne du trajet et "
    "les six parts moyennes des causes de retard. Le choix de k=4 est validé "
    "par la méthode du coude et par la cohérence métier des groupes obtenus."
)


# =============================================================================
# Chargement
# =============================================================================

clusters_liaisons = table("data/processed/clusters_liaisons.csv")
profils = table("data/processed/ml/clusters_profils.parquet", required=False)
resume = table("data/processed/ml/clusters_resume.parquet", required=False)


# =============================================================================
# Bandeau des 4 clusters
# =============================================================================

if not resume.empty:
    st.subheader("Les 4 profils en synthèse")
    cols_bandeau = st.columns(4)
    for i, row in resume.iterrows():
        cid = int(row["cluster"])
        couleur = COULEURS_CLUSTERS.get(cid, "#95A5A6")
        libelle = LIBELLES_CLUSTERS.get(cid, f"Cluster {cid}")
        with cols_bandeau[cid]:
            st.markdown(
                f'<div style="border-left:5px solid {couleur};padding:12px 16px;'
                f'background:#FAFAFA;border-radius:4px;height:100%;">'
                f'<div style="font-size:12px;color:#7F8C8D;text-transform:uppercase;'
                f'letter-spacing:0.5px;">Cluster {cid}</div>'
                f'<div style="font-size:15px;font-weight:600;color:#2C3E50;'
                f'margin:4px 0 10px 0;">{libelle}</div>'
                f'<div style="font-size:13px;color:#34495E;line-height:1.7;">'
                f'<b>{int(row["nombre_paires"])}</b> paires de gares<br>'
                f'<b>{int(row["nombre_trains"]):,}</b> trains observés<br>'
                f'<b>{row["duree_moyenne"]:.0f} min</b> durée moyenne<br>'
                f'<b>{row["taux_retard_15_pct"]:.1f} %</b> taux de retard >15 min'
                f'</div></div>'.replace(",", " "),
                unsafe_allow_html=True,
            )
    st.divider()


# =============================================================================
# Comparaison visuelle des profils
# =============================================================================

st.subheader("Comparer les profils des 4 clusters")
st.caption(
    "Parts moyennes des causes de retard dans chaque cluster, utilisées comme "
    "variables de regroupement par K-Means. Les barres regroupées font ressortir "
    "les signatures caractéristiques de chaque profil."
)

if not resume.empty:
    fig_profils = go.Figure()
    for col, lib in CAUSES_LIBELLES.items():
        fig_profils.add_trace(go.Bar(
            name=lib,
            x=[f"Cluster {int(c)}" for c in resume["cluster"]],
            y=resume[col].values,
            text=[f"{v:.1f}" for v in resume[col].values],
            textposition="outside",
            textfont=dict(size=10),
        ))
    fig_profils.update_layout(
        barmode="group",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title="Part moyenne (%)", gridcolor="#ECF0F1"),
        xaxis=dict(title=None),
        plot_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                    xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_profils, width="stretch")


# =============================================================================
# Projection PCA interactive
# =============================================================================

st.subheader("Visualisation PCA des 65 paires")
st.caption(
    "Projection en deux dimensions des 65 paires via analyse en composantes "
    "principales. Chaque point est une paire de gares, coloré par son cluster. "
    "Survolez un point pour voir les deux gares."
)

if not profils.empty:
    features = ["duree_moyenne"] + list(CAUSES_LIBELLES.keys())
    X = profils[features].values
    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    profils_pca = profils[["cluster", "gare_1", "gare_2"]].copy()
    profils_pca["PC1"] = X_pca[:, 0]
    profils_pca["PC2"] = X_pca[:, 1]

    fig_pca = go.Figure()
    for cid in sorted(profils_pca["cluster"].unique()):
        sous = profils_pca[profils_pca["cluster"] == cid]
        fig_pca.add_trace(go.Scatter(
            x=sous["PC1"], y=sous["PC2"], mode="markers",
            name=f"Cluster {int(cid)} — {LIBELLES_CLUSTERS.get(int(cid), '')}",
            marker=dict(
                size=12,
                color=COULEURS_CLUSTERS.get(int(cid), "#95A5A6"),
                line=dict(color="#FFFFFF", width=1.5),
            ),
            hovertext=[f"<b>{g1} ↔ {g2}</b><br>Cluster {int(cid)}"
                       for g1, g2 in zip(sous["gare_1"], sous["gare_2"])],
            hoverinfo="text",
        ))
    fig_pca.update_layout(
        height=480, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(title=f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f} % variance)",
                   gridcolor="#ECF0F1", zerolinecolor="#BDC3C7"),
        yaxis=dict(title=f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f} % variance)",
                   gridcolor="#ECF0F1", zerolinecolor="#BDC3C7"),
        plot_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                    xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_pca, width="stretch")
    st.caption(
        f"Les deux premières composantes expliquent "
        f"{sum(pca.explained_variance_ratio_[:2]) * 100:.1f} % de la variance totale. "
        "La séparation visible entre les groupes confirme la cohérence du partitionnement."
    )


# =============================================================================
# Courbe du coude interactive
# =============================================================================

with st.expander("Choix de k : méthode du coude"):
    if not profils.empty:
        inerties = []
        ks = list(range(2, 11))
        for k in ks:
            km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_scaled)
            inerties.append(km.inertia_)
        fig_elbow = go.Figure()
        fig_elbow.add_trace(go.Scatter(
            x=ks, y=inerties, mode="lines+markers",
            line=dict(color="#2E86DE", width=2), marker=dict(size=8),
        ))
        # Marque k=4
        fig_elbow.add_trace(go.Scatter(
            x=[4], y=[inerties[ks.index(4)]], mode="markers",
            marker=dict(size=14, color="#C0392B",
                        line=dict(color="#FFFFFF", width=2)),
            name="k=4 retenu", showlegend=False,
        ))
        fig_elbow.add_annotation(
            x=4, y=inerties[ks.index(4)],
            text="k=4 retenu", showarrow=True, arrowhead=2,
            ax=30, ay=-30, font=dict(color="#C0392B", size=11),
        )
        fig_elbow.update_layout(
            height=320, margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title="Nombre de clusters k", dtick=1,
                       gridcolor="#ECF0F1"),
            yaxis=dict(title="Inertie intra-cluster", gridcolor="#ECF0F1"),
            plot_bgcolor="#FFFFFF", showlegend=False,
        )
        st.plotly_chart(fig_elbow, width="stretch")
        st.caption(
            "La courbure forme un coude autour de k=4 : au-delà, chaque cluster "
            "ajouté réduit peu l'inertie. Le découpage en 4 groupes offre "
            "le meilleur compromis entre parcimonie et information."
        )


# =============================================================================
# Analyser un cluster en détail
# =============================================================================

st.divider()
st.subheader("Analyser un cluster en détail")

clusters_disponibles = sorted(clusters_liaisons["cluster"].unique())
options_cluster = [
    f"Cluster {int(c)} — {LIBELLES_CLUSTERS.get(int(c), '')}"
    for c in clusters_disponibles
]
choix_cluster = st.selectbox(
    "Choisir un cluster", options_cluster, index=0,
)
cid_choisi = int(choix_cluster.split(" ")[1])
log_selection("cluster_view", cluster=cid_choisi)

# Carte d identité du cluster
if not resume.empty:
    row_c = resume[resume["cluster"] == cid_choisi].iloc[0]
    couleur_c = COULEURS_CLUSTERS.get(cid_choisi, "#95A5A6")
    st.markdown(
        f'<div style="padding:12px 16px;background:{couleur_c};color:white;'
        f'border-radius:6px;margin:12px 0;">'
        f'<b style="font-size:16px;">Cluster {cid_choisi} — '
        f'{LIBELLES_CLUSTERS.get(cid_choisi, "")}</b>'
        f'</div>',
        unsafe_allow_html=True,
    )
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Paires de gares", int(row_c["nombre_paires"]))
    with m2:
        st.metric("Trains observés", f"{int(row_c['nombre_trains']):,}".replace(",", " "))
    with m3:
        st.metric("Durée moyenne", f"{row_c['duree_moyenne']:.0f} min")
    with m4:
        st.metric("Taux de retard >15 min", f"{row_c['taux_retard_15_pct']:.1f} %")

# Liste des paires du cluster
st.markdown("### Paires de gares composant ce cluster")
paires_cluster = clusters_liaisons[clusters_liaisons["cluster"] == cid_choisi].copy()
paires_cluster["paire_formatee"] = paires_cluster["paire"].apply(
    lambda s: " ↔ ".join(literal_eval(s))
)
st.dataframe(
    paires_cluster[["paire_formatee"]].rename(columns={"paire_formatee": "Paire de gares"}),
    hide_index=True, width="stretch",
)

