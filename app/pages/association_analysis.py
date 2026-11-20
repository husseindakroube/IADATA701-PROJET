"""Structure du réseau et analyses d'association avec la régularité."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from projet_kit_data.web_data import ROOT
from utils.activity import log_selection
from utils.association_views import (
    CORRELATION_COLUMNS,
    METHOD_LABELS,
    OUTCOME_LABELS,
    PREDICTOR_LABELS,
    QUANTILE_COLUMNS,
    ROBUSTNESS_COLUMNS,
    SCOPES,
    filter_correlations,
    filter_quantiles,
    filter_robustness,
    validate_result_table,
)
from utils.carte import construire_ego_graphe, gares_du_service
from utils.data import network_summary_metrics, table, validate_rankings


PHASE3B_DIR = "data/processed/graph/phase3b"


def _fr_number(value: float, decimals: int = 3) -> str:
    """Formate un nombre selon les conventions françaises d'affichage."""
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def _quantile_pattern_summary(frame: pd.DataFrame) -> tuple[int, int, int, int]:
    """Résume les séquences enregistrées et le chevauchement des intervalles."""
    families = [
        ["Q1", "Q2", "Q3", "Q4"],
        ["Positive Q1", "Positive Q2", "Positive Q3", "Positive Q4"],
    ]
    monotonic = 0
    sequences = 0
    overlaps = 0
    adjacent_pairs = 0
    for _, group in frame.groupby(["service", "predictor", "outcome"]):
        for family in families:
            labels = [label for label in family if label in set(group.group_label)]
            if len(labels) < 2:
                continue
            ordered = group.set_index("group_label").reindex(labels)
            medians = ordered["median"].tolist()
            if all(a <= b for a, b in zip(medians, medians[1:])) or all(
                a >= b for a, b in zip(medians, medians[1:])
            ):
                monotonic += 1
            sequences += 1
            for (_, left), (_, right) in zip(
                ordered.iloc[:-1].iterrows(), ordered.iloc[1:].iterrows()
            ):
                adjacent_pairs += 1
                overlaps += int(max(left.q25, right.q25) <= min(left.q75, right.q75))
    return sequences, monotonic, overlaps, adjacent_pairs


def _load_result(relative: str, required: set[str], label: str) -> pd.DataFrame:
    """Charge une table mise en cache et vérifie les colonnes attendues."""
    loaded = table(relative, required=False)
    if loaded.empty:
        if (ROOT / relative).is_file():
            st.info(f"La table {label} est vide.")
        return loaded
    frame, error = validate_result_table(loaded, required, label)
    if error:
        st.warning(error)
    return frame


def _scope_selector(key: str) -> str:
    return st.selectbox("Périmètre d’analyse", list(SCOPES), key=key)


def _select_label(value: str | None, labels: dict[str, str]) -> str:
    if value is None:
        return "Toutes les valeurs"
    return labels.get(value, value)


def _render_network_structure() -> None:
    """Présente les sorties de structure réseau existantes de Phase 1."""
    st.subheader("Analyse structurelle du réseau TGV")
    st.write(
        "Analyse par théorie des graphes de la structure origine-destination "
        "des services TGV AQST sur l'ensemble de la période 2018-01 → 2026-09. "
        "Chaque gare est un nœud, chaque liaison orientée une arête."
    )
    st.caption(
        "Le graphe décrit les liaisons origine-destination observées dans les "
        "données mensuelles. Il ne permet pas d'établir les itinéraires réels, "
        "les flux de voyageurs, l'infrastructure physique ni une propagation "
        "des retards."
    )

    with st.expander("Comprendre les mesures de centralité", expanded=False):
        st.markdown(
            "**Degré entrant / sortant.** Nombre de liaisons origine-destination "
            "observées qui arrivent à une gare ou en partent dans le graphe. Il "
            "décrit sa connectivité dans ce graphe, sans mesurer son importance "
            "dans le réseau ferroviaire physique.\n\n"
            "**Betweenness Centrality (intermédiarité).** Mesure la position d'une "
            "gare dans les plus courts chemins du graphe OD construit. Elle ne "
            "prouve ni le passage de trains réels par cette gare, ni un volume "
            "de trafic ou un rôle de transit stratégique.\n\n"
            "**PageRank.** Mesure calculée à partir des connexions dirigées du "
            "graphe OD et de la structure des voisins. Une valeur manquante indique "
            "un résultat indisponible, notamment en cas de non-convergence ; elle "
            "ne doit pas être interprétée comme zéro.\n\n"
            "**Closeness (proximité).** Résume les distances dans le graphe OD "
            "construit. Elle ne décrit pas les distances ni l'accessibilité de "
            "l'infrastructure ferroviaire réelle."
        )

    summary = table(
        "data/processed/graph/descriptive/network_summary.parquet", required=False
    )
    if not summary.empty:
        st.markdown("### Vue d'ensemble des deux réseaux")
        for _, row in summary.iterrows():
            with st.container(border=True):
                st.markdown(f"**Réseau {row.service}**")
                colonnes = st.columns(4)
                for index, (libelle, valeur) in enumerate(network_summary_metrics(row)):
                    colonnes[index % 4].metric(libelle, valeur)

    st.divider()
    service = st.selectbox(
        "Choisir un réseau à analyser", ["National", "International"]
    )
    log_selection("network_view", service=service)

    st.markdown("### Explorer une gare et ses connexions directes")
    st.caption(
        "Choisissez une gare pour voir ses liaisons directes. Rouge = départs "
        "de la gare, bleu = arrivées. Taille des voisins proportionnelle à leur betweenness."
    )
    liste_gares = gares_du_service(service)
    if liste_gares:
        default_idx = 0
        for candidat in ["PARIS LYON", "PARIS EST", "LYON PART DIEU"]:
            if candidat in liste_gares:
                default_idx = liste_gares.index(candidat)
                break
        gare_centrale = st.selectbox(
            "Gare centrale",
            liste_gares,
            index=default_idx,
            key=f"ego_gare_{service}",
        )
        log_selection("ego_graphe_view", service=service, gare=gare_centrale)
        st.plotly_chart(construire_ego_graphe(service, gare_centrale), width="stretch")

    path = ROOT / f"data/processed/graph/visualizations/network_{service.lower()}.png"
    if path.is_file():
        with st.expander(
            "Voir aussi la visualisation statique issue de l'analyse graphe"
        ):
            st.image(
                str(path),
                caption=f"Réseau {service} · 2018-01 → 2026-09 · liaisons orientées",
                width="stretch",
            )

    ranking, ranking_warning = validate_rankings(
        table("data/processed/graph/descriptive/node_rankings.parquet", required=False)
    )
    if ranking_warning:
        st.warning(ranking_warning)
    if not ranking.empty:
        ranking_service = ranking.loc[ranking.service.eq(service)]
        if not ranking_service.empty:
            st.markdown("### Classements des gares les plus centrales")
            st.caption(
                "Top des gares pour chaque mesure de centralité calculée sur "
                "l'ensemble de la période. Ces rangs décrivent uniquement le "
                "graphe OD observé et ne démontrent pas un rôle dans les "
                "itinéraires ou le trafic ferroviaire réels."
            )
            classement_affiche = ranking_service.drop(
                columns=["node_id"], errors="ignore"
            ).rename(
                columns={
                    "rank": "Rang",
                    "service": "Service",
                    "ranking_metric": "Mesure",
                    "station_name": "Gare",
                    "value": "Valeur",
                }
            )
            classement_affiche["Mesure"] = classement_affiche["Mesure"].replace(
                {
                    "connectivity_degree": "Degré de connectivité",
                    "betweenness_centrality": "Betweenness Centrality",
                    "pagerank": "PageRank",
                }
            )
            st.dataframe(classement_affiche, hide_index=True, width="stretch")
        else:
            st.info(f"Aucun classement n'est disponible pour le service {service}.")

    nodes = table("data/processed/graph/node_metrics.parquet", required=False)
    if not nodes.empty:
        nodes_s = nodes.loc[nodes.service.eq(service) & nodes.period.eq("overall")]
        if not nodes_s.empty:
            st.markdown("### Métriques détaillées par gare")
            station = st.selectbox(
                "Choisir une gare",
                sorted(nodes_s.station_name.unique()),
                key=f"station_{service}",
            )
            log_selection("station_view", service=service, station=station)
            detail = nodes_s.loc[nodes_s.station_name.eq(station)]
            st.dataframe(detail, hide_index=True, width="stretch")


def _render_correlations() -> None:
    st.subheader("Associations entre métriques du réseau et régularité")
    st.markdown("### Pourquoi cette analyse ?")
    st.write(
        "Cette première lecture repère les indicateurs de structure les plus liés "
        "aux retards ou aux annulations, puis vérifie si le profil est similaire "
        "dans les périmètres National et International."
    )
    frame = _load_result(
        f"{PHASE3B_DIR}/correlations.parquet", CORRELATION_COLUMNS, "Corrélations"
    )
    if frame.empty:
        return

    strongest_by_service = frame.loc[
        frame.groupby("service")["coefficient"].apply(
            lambda values: values.abs().idxmax()
        )
    ].set_index("service")
    paired = frame.pivot_table(
        index=["analysis_scope", "service", "predictor", "outcome"],
        columns="method",
        values="coefficient",
    ).dropna()
    same_direction = int((paired["pearson"] * paired["spearman"] >= 0).sum())
    winners = frame.loc[
        frame.groupby(["service", "outcome", "method"])["coefficient"].apply(
            lambda values: values.abs().idxmax()
        )
    ]
    edge_wins = int(winners.predictor.eq("edge_betweenness").sum())

    st.markdown("### Principaux enseignements")
    st.write(
        f"Les 126 coefficients vont de {_fr_number(frame['coefficient'].min())} "
        f"à {_fr_number(frame['coefficient'].max())}; leur valeur absolue reste "
        f"inférieure ou égale à {_fr_number(frame['coefficient'].abs().max())}. "
        f"La Betweenness des arêtes est l'indicateur le plus souvent associé au "
        f"coefficient le plus marqué dans une combinaison service–résultat–méthode "
        f"({edge_wins} cas sur {len(winners)}), mais elle ne domine pas tous les "
        "périmètres."
    )
    international = strongest_by_service.loc["International"]
    national = strongest_by_service.loc["National"]
    overall = strongest_by_service.loc["Overall"]
    strongest_positive = frame.loc[frame["coefficient"].idxmax()]
    international_n = f"{int(international.n_valid):,}".replace(",", " ")
    st.write(
        f"Le maximum absolu concerne le périmètre International : la Betweenness "
        f"des arêtes est associée à un taux d'annulation plus faible dans les "
        f"observations classées par Spearman (r = "
        f"{_fr_number(international.coefficient)}, n = {international_n}). "
        f"La plus forte association positive est aussi internationale : "
        f"{PREDICTOR_LABELS[strongest_positive.predictor]} et "
        f"{OUTCOME_LABELS[strongest_positive.outcome]} "
        f"(r = {_fr_number(strongest_positive.coefficient)}); les liaisons "
        "associées à une Betweenness plus élevée tendent aussi à avoir un retard "
        "moyen plus élevé parmi les trains retardés. Ces deux profils sont les "
        "plus visibles, mais leur amplitude reste limitée. "
        f"Les maxima propres aux autres périmètres sont différents : en National, "
        f"le degré du nœud d'arrivée est associé positivement au retard moyen de "
        f"tous les trains (r = {_fr_number(national.coefficient)}); en Overall, "
        f"le PageRank du nœud d'arrivée présente la plus forte association avec "
        f"ce même résultat (r = {_fr_number(overall.coefficient)})."
    )
    st.caption(
        "Les associations avec le taux d'annulation sont presque nulles en "
        "Overall et en National (|r| maximal : environ 0,03 dans chaque périmètre), "
        "alors qu'elles sont plus visibles en International. La topologie ne rend "
        "donc compte que d'une part limitée des différences de régularité."
    )
    st.caption(
        f"Pearson et Spearman donnent le même sens dans {same_direction} des "
        f"{len(paired)} comparaisons appariées. Ils servent ici de lectures "
        "complémentaires : tendance linéaire pour Pearson, classement monotone "
        "pour Spearman. Cette première synthèse est prolongée par les quantiles, "
        "qui examinent les distributions entre groupes, puis par la sensibilité, "
        "qui vérifie la stabilité des coefficients. Une valeur de p faible ne "
        "transforme pas un coefficient de faible amplitude en relation forte."
    )

    colonnes = st.columns(4)
    with colonnes[0]:
        scope = _scope_selector("correlations_scope")
    with colonnes[1]:
        method = st.selectbox(
            "Méthode de corrélation",
            list(METHOD_LABELS),
            format_func=METHOD_LABELS.get,
            key="correlations_method",
        )
    with colonnes[2]:
        predictors = [None, *PREDICTOR_LABELS]
        predictor = st.selectbox(
            "Métrique du réseau",
            predictors,
            format_func=lambda value: _select_label(value, PREDICTOR_LABELS),
            key="correlations_predictor",
        )
    with colonnes[3]:
        outcomes = [None, *OUTCOME_LABELS]
        outcome = st.selectbox(
            "Indicateur opérationnel",
            outcomes,
            format_func=lambda value: _select_label(value, OUTCOME_LABELS),
            key="correlations_outcome",
        )

    selected = filter_correlations(frame, scope, method, predictor, outcome)
    log_selection(
        "correlation_filters",
        scope=scope,
        method=method,
        predictor=predictor or "all",
        outcome=outcome or "all",
    )
    if selected.empty:
        st.info("Aucun résultat ne correspond à ces filtres.")
        return

    st.markdown("### Explorer les résultats filtrés")
    st.write(
        "Le signe indique le sens de l'association et sa valeur absolue, son "
        "amplitude. La taille d'échantillon aide à situer chaque estimation. "
        "La p-value brute est fournie à titre exploratoire; elle ne mesure pas "
        "l'importance pratique de l'association."
    )
    st.caption(
        "Coefficients calculés sur la période complète 2018-01 → 2026-09. "
        "Overall regroupe les deux services; ce n'est pas un troisième service."
    )
    pivot = selected.pivot(index="predictor", columns="outcome", values="coefficient")
    predictor_order = [value for value in PREDICTOR_LABELS if value in pivot.index]
    outcome_order = [value for value in OUTCOME_LABELS if value in pivot.columns]
    pivot = pivot.reindex(index=predictor_order, columns=outcome_order)
    details = selected.set_index(["predictor", "outcome"])
    customdata = []
    for metric in predictor_order:
        row = []
        for indicator in outcome_order:
            value = details.loc[(metric, indicator)]
            row.append([value["n_valid"], value["p_value"]])
        customdata.append(row)
    figure = go.Figure(
        go.Heatmap(
            z=pivot.to_numpy(),
            x=[OUTCOME_LABELS[value] for value in outcome_order],
            y=[PREDICTOR_LABELS[value] for value in predictor_order],
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale="RdBu",
            customdata=customdata,
            colorbar=dict(title="Coefficient"),
            hovertemplate=(
                "%{y}<br>%{x}<br>Coefficient : %{z:.4f}"
                "<br>Taille de l'échantillon : %{customdata[0]}"
                "<br>p-value brute exploratoire : %{customdata[1]:.3g}<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title="Coefficients de corrélation",
        xaxis_title="Indicateur opérationnel",
        yaxis_title="Métrique du réseau",
        height=max(430, 48 * len(predictor_order) + 170),
        margin=dict(l=20, r=20, t=65, b=120),
    )
    st.plotly_chart(figure, width="stretch")

    details_frame = selected[
        ["predictor", "outcome", "coefficient", "n_valid", "p_value"]
    ].rename(
        columns={
            "predictor": "Métrique du réseau",
            "outcome": "Indicateur opérationnel",
            "coefficient": "Coefficient",
            "n_valid": "Taille de l'échantillon",
            "p_value": "p-value brute (exploratoire)",
        }
    )
    details_frame["Métrique du réseau"] = details_frame["Métrique du réseau"].map(
        PREDICTOR_LABELS
    )
    details_frame["Indicateur opérationnel"] = details_frame[
        "Indicateur opérationnel"
    ].map(OUTCOME_LABELS)
    st.dataframe(details_frame, hide_index=True, width="stretch")
    st.caption(
        "Les p-values sont brutes, exploratoires et non corrigées pour les "
        "comparaisons multiples. Elles ne démontrent pas de causalité."
    )
    strongest_selected = selected.loc[selected["coefficient"].abs().idxmax()]
    selected_n = f"{int(strongest_selected.n_valid):,}".replace(",", " ")
    st.markdown("### Lecture de la sélection")
    st.write(
        f"Dans les résultats affichés, l'association la plus marquée relie "
        f"{PREDICTOR_LABELS[strongest_selected.predictor]} à "
        f"{OUTCOME_LABELS[strongest_selected.outcome]} : "
        f"{METHOD_LABELS[strongest_selected.method]} = "
        f"{_fr_number(strongest_selected.coefficient)}, pour le périmètre "
        f"{strongest_selected.service} (n = {selected_n}). Ce résultat situe la "
        "relation la plus visible dans les filtres choisis; "
        "les coefficients de l'ensemble restent de faible amplitude et ne "
        "décrivent pas un mécanisme causal."
    )
    st.caption(
        "Les p-values sont brutes, non corrigées pour les comparaisons multiples. "
        "Les observations mensuelles d'une même liaison sont répétées; les "
        "liaisons OD ne mesurent ni les itinéraires réels ni les flux de voyageurs."
    )
    if "cancellation_rate" in selected.outcome.unique():
        st.caption(
            "Les 73 taux d'annulation invalides ou manquants ne sont pas remplacés "
            "par zéro; seuls les taux valides contribuent aux calculs concernés."
        )


def _render_quantiles() -> None:
    st.subheader("Indicateurs opérationnels par groupes de métriques réseau")
    st.markdown("### Pourquoi cette analyse ?")
    st.write(
        "Une corrélation résume l'association par un seul nombre. Cette vue "
        "complémentaire compare les indicateurs opérationnels entre des groupes "
        "d'observations classés selon une métrique du réseau. Elle aide à voir si "
        "les niveaux typiques de retard ou d'annulation diffèrent selon la "
        "position structurelle associée à une liaison."
    )
    st.markdown("### Comment ça fonctionne ?")
    st.write(
        "Les observations sont triées selon la métrique du réseau. Q1 correspond "
        "aux valeurs les plus basses et Q4 aux plus élevées; Q2 et Q3 se situent "
        "entre les deux. Ce sont des groupes de la métrique explicative, pas des "
        "quartiles du retard. Les valeurs ex æquo ne sont pas séparées, donc les "
        "effectifs peuvent différer. Pour la Betweenness Centrality de départ et "
        "d'arrivée, les valeurs exactement égales à zéro sont séparées dans le "
        "groupe `Zero` si leur part atteint 5 %; les valeurs positives sont "
        "ensuite réparties entre `Positive Q1` et `Positive Q4`."
    )
    st.caption(
        "`n` est l'effectif valide du groupe; la médiane est sa valeur centrale, "
        "la moyenne est la moyenne arithmétique et `std` mesure la dispersion "
        "autour de cette moyenne. Dans le tableau, Q1 et Q3 sont les quartiles de "
        "l'indicateur opérationnel à l'intérieur du groupe, et non les bornes "
        "utilisées pour former les groupes de la métrique du réseau. `IQR` = "
        "Q3 − Q1."
    )
    frame = _load_result(
        f"{PHASE3B_DIR}/quantile_comparisons.parquet",
        QUANTILE_COLUMNS,
        "Comparaisons par quantiles",
    )
    if frame.empty:
        return

    sequences, monotonic, overlaps, adjacent_pairs = _quantile_pattern_summary(frame)
    st.markdown("### Ce que révèlent les groupes")
    st.write(
        f"La comparaison complète porte sur {sequences} séquences de groupes : "
        f"{sequences - monotonic} présentent des médianes irrégulières et "
        f"{monotonic} évoluent de façon monotone. Dans l'exemple Overall, les "
        f"médianes du retard moyen de tous les trains selon la Betweenness des "
        f"arêtes sont 6,79, 4,62, 8,71 puis 5,73 minutes (Q1 à Q4). Une "
        "importance structurelle plus élevée ne correspond donc pas à une hausse "
        "ou une baisse régulière du retard dans cet exemple."
    )
    st.write(
        f"Les intervalles Q1–Q3 se chevauchent dans {overlaps} des "
        f"{adjacent_pairs} comparaisons entre groupes voisins. Les différences "
        "de médiane coexistent donc souvent avec des distributions centrales "
        "largement communes. Les quatre profils monotones apparaissent tous dans "
        "le périmètre International : par exemple, le taux d'annulation médian "
        "diminue de 2,25 % à 0,45 % entre Q1 et Q4 de Betweenness des arêtes; "
        "pour la Betweenness Centrality positive de départ, le retard médian de "
        "tous les trains diminue de 8,86 à 5,23 minutes entre les groupes "
        "positifs extrêmes. Ces gradients restent descriptifs et leurs "
        "intervalles se chevauchent. Cette lecture "
        "complète les corrélations : elle montre les formes irrégulières que "
        "résume mal un seul coefficient."
    )

    colonnes = st.columns(3)
    with colonnes[0]:
        scope = _scope_selector("quantiles_scope")
    with colonnes[1]:
        predictor = st.selectbox(
            "Métrique du réseau",
            list(PREDICTOR_LABELS),
            format_func=PREDICTOR_LABELS.get,
            key="quantiles_predictor",
        )
    with colonnes[2]:
        outcome = st.selectbox(
            "Indicateur opérationnel",
            list(OUTCOME_LABELS),
            format_func=OUTCOME_LABELS.get,
            key="quantiles_outcome",
        )

    selected = filter_quantiles(frame, scope, predictor, outcome)
    log_selection("quantile_filters", scope=scope, predictor=predictor, outcome=outcome)
    if selected.empty:
        st.info("Aucun groupe ne correspond à ces filtres.")
        return

    strategy = selected.grouping_strategy.iloc[0]
    strategy_labels = {
        "tie_preserving_quantiles": "Quantiles conservant les ex æquo",
        "zero_plus_tie_preserving_quantiles": (
            "Groupe Zero séparé, puis quantiles positifs conservant les ex æquo"
        ),
    }
    st.caption(
        f"Méthode : {strategy_labels.get(strategy, strategy)}. Les ex æquo restent "
        "ensemble; les tailles de groupe peuvent donc différer. Les groupes et "
        "statistiques affichés proviennent de la table enregistrée."
    )
    if outcome == "cancellation_rate":
        st.caption(
            "Seuls les taux d'annulation valides contribuent aux résumés; les "
            "valeurs manquantes ne sont pas remplacées par zéro."
        )

    st.markdown("### Lire le profil sélectionné")
    st.write(
        "Le point du graphique représente la médiane; la barre verticale va de "
        "Q1 à Q3 et couvre la moitié centrale des observations. La médiane est "
        "moins sensible que la moyenne aux valeurs extrêmes. Comparez aussi la "
        "longueur des intervalles et l'effectif `n` : ils montrent si un écart "
        "entre médianes s'accompagne d'une dispersion ou d'une précision différente."
    )

    group_order = [
        "Zero",
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Positive Q1",
        "Positive Q2",
        "Positive Q3",
        "Positive Q4",
    ]
    selected = selected.assign(
        _order=selected.group_label.map(
            {label: index for index, label in enumerate(group_order)}
        )
    ).sort_values("_order")
    figure = go.Figure(
        go.Scatter(
            x=selected.group_label,
            y=selected["median"],
            mode="markers+lines+text",
            text=[f"n = {count:,}".replace(",", " ") for count in selected["n"]],
            textposition="top center",
            error_y=dict(
                type="data",
                symmetric=False,
                array=(selected["q75"] - selected["median"]).tolist(),
                arrayminus=(selected["median"] - selected["q25"]).tolist(),
                visible=True,
            ),
            customdata=selected[["n", "mean", "q25", "q75", "iqr"]].to_numpy(),
            hovertemplate=(
                "Groupe : %{x}<br>Médiane : %{y:.4f}"
                "<br>n : %{customdata[0]}<br>Moyenne : %{customdata[1]:.4f}"
                "<br>Q1 : %{customdata[2]:.4f}<br>Q3 : %{customdata[3]:.4f}"
                "<br>IQR : %{customdata[4]:.4f}<extra></extra>"
            ),
            marker=dict(size=10),
            line=dict(color="#2E86DE"),
        )
    )
    figure.update_layout(
        title=f"Médiane et intervalle Q1–Q3 — {OUTCOME_LABELS[outcome]}",
        xaxis_title="Groupe de métrique du réseau",
        yaxis_title=OUTCOME_LABELS[outcome],
        height=440,
        margin=dict(l=20, r=20, t=65, b=50),
    )
    st.plotly_chart(figure, width="stretch")

    summary = selected[
        [
            "group_label",
            "grouping_strategy",
            "n",
            "median",
            "mean",
            "std",
            "q25",
            "q75",
            "iqr",
        ]
    ].rename(
        columns={
            "group_label": "Groupe",
            "grouping_strategy": "Méthode de regroupement",
            "n": "Taille de l'échantillon",
            "median": "Médiane",
            "mean": "Moyenne",
            "std": "Écart-type",
            "q25": "Q1",
            "q75": "Q3",
            "iqr": "IQR",
        }
    )
    summary["Méthode de regroupement"] = summary["Méthode de regroupement"].map(
        strategy_labels
    )
    st.dataframe(summary, hide_index=True, width="stretch")
    medians = selected["median"].tolist()
    if all(left <= right for left, right in zip(medians, medians[1:])):
        progression = "augmente ou reste stable d'un groupe au suivant"
    elif all(left >= right for left, right in zip(medians, medians[1:])):
        progression = "diminue ou reste stable d'un groupe au suivant"
    else:
        progression = "évolue de façon irrégulière entre les groupes"
    lowest = selected.loc[selected["median"].idxmin()]
    highest = selected.loc[selected["median"].idxmax()]
    min_group_n = f"{int(selected['n'].min()):,}".replace(",", " ")
    max_group_n = f"{int(selected['n'].max()):,}".replace(",", " ")
    selected_overlaps = sum(
        max(left.q25, right.q25) <= min(left.q75, right.q75)
        for (_, left), (_, right) in zip(
            selected.iloc[:-1].iterrows(), selected.iloc[1:].iterrows()
        )
    )
    adjacent_selected = max(len(selected) - 1, 0)
    st.markdown("### Interprétation de cette sélection")
    st.write(
        f"Pour cette sélection, les médianes vont de "
        f"{_fr_number(lowest['median'], 2)} ({lowest['group_label']}) à "
        f"{_fr_number(highest['median'], 2)} ({highest['group_label']}); leur "
        f"évolution {progression}. Les effectifs des groupes vont de "
        f"{min_group_n} à {max_group_n}. Les intervalles centraux se chevauchent "
        f"pour {selected_overlaps} des {adjacent_selected} paires voisines. "
        "L'écart des médianes indique donc un profil à examiner, et non à lui seul "
        "une séparation nette entre les groupes."
    )
    st.caption(
        "Ces résumés sont descriptifs et dépendent du regroupement sélectionné; "
        "les tailles de groupe peuvent varier pour conserver les ex æquo."
    )


def _render_robustness() -> None:
    st.subheader("Stabilité des corrélations du résultat principal")
    st.markdown("### Question examinée")
    st.write(
        "Les associations repérées précédemment dépendent-elles fortement des "
        "retards moyens très négatifs ? La comparaison vérifie si les coefficients "
        "du résultat principal restent similaires quand les valeurs inférieures "
        "à −15 minutes sont exclues de ce seul calcul."
    )
    st.caption(
        "Les observations restent dans le jeu de recherche. Seul le calcul de "
        "sensibilité les écarte; l'artefact compare les coefficients et les "
        "effectifs, sans p-value."
    )
    frame = _load_result(
        f"{PHASE3B_DIR}/robustness_comparisons.parquet",
        ROBUSTNESS_COLUMNS,
        "Comparaisons de robustesse",
    )
    if frame.empty:
        return

    differences_all = frame["coefficient_difference"].abs()
    largest_all = frame.loc[differences_all.idxmax()]
    sign_changes_all = frame.loc[
        frame["full_coefficient"] * frame["sensitivity_coefficient"] < 0
    ]
    st.markdown("### Principaux enseignements")
    st.write(
        f"La différence absolue médiane est de {_fr_number(differences_all.median(), 4)}; "
        f"{int((differences_all <= 0.01).sum())} des {len(frame)} coefficients "
        "varient de 0,01 au plus. La plus forte variation concerne le PageRank "
        f"du nœud de départ en National (Pearson) : "
        f"{_fr_number(largest_all.full_coefficient)} à "
        f"{_fr_number(largest_all.sensitivity_coefficient)}. L'association "
        "négative se renforce, mais reste d'amplitude limitée."
    )
    if not sign_changes_all.empty:
        change = sign_changes_all.iloc[0]
        st.write(
            f"Un seul coefficient change de signe : en International, la "
            f"Betweenness Centrality du nœud d'arrivée passe de "
            f"{_fr_number(change.full_coefficient, 4)} à "
            f"{_fr_number(change.sensitivity_coefficient, 4)}; les deux valeurs "
            "restent proches de zéro, donc le changement de signe ne révèle pas "
            "une association marquée. Au total, 11 observations sont écartées "
            "pour ce test : 10 National et 1 International."
        )
    st.caption(
        "Cette vérification porte uniquement sur l'indicateur principal et le "
        "seuil de −15 minutes; elle renseigne sur cette sensibilité précise, pas "
        "sur toutes les formes possibles de robustesse."
    )

    colonnes = st.columns(3)
    with colonnes[0]:
        scope = _scope_selector("robustness_scope")
    with colonnes[1]:
        predictor = st.selectbox(
            "Métrique du réseau",
            [None, *PREDICTOR_LABELS],
            format_func=lambda value: _select_label(value, PREDICTOR_LABELS),
            key="robustness_predictor",
        )
    with colonnes[2]:
        method = st.selectbox(
            "Méthode de corrélation",
            list(METHOD_LABELS),
            format_func=METHOD_LABELS.get,
            key="robustness_method",
        )

    selected = filter_robustness(frame, scope, method, predictor)
    log_selection(
        "robustness_filters",
        scope=scope,
        method=method,
        predictor=predictor or "all",
    )
    if selected.empty:
        st.info("Aucun résultat ne correspond à ces filtres.")
        return

    st.markdown("### Comparer les résultats filtrés")
    st.write(
        "Chaque point compare le coefficient de la période complète à celui de "
        "la sensibilité. La diagonale indique qu'ils sont égaux; un point proche signifie que "
        "le coefficient a peu changé. Examinez aussi sa direction, sa magnitude "
        "et les deux effectifs indiqués dans le tableau."
    )
    x_values = selected["full_coefficient"]
    y_values = selected["sensitivity_coefficient"]
    minimum = min(x_values.min(), y_values.min())
    maximum = max(x_values.max(), y_values.max())
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[minimum, maximum],
            y=[minimum, maximum],
            mode="lines",
            name="Égalité des coefficients",
            line=dict(color="#7F8C8D", dash="dash"),
            hoverinfo="skip",
        )
    )
    for metric in selected.predictor.drop_duplicates():
        points = selected.loc[selected.predictor.eq(metric)]
        figure.add_trace(
            go.Scatter(
                x=points["full_coefficient"],
                y=points["sensitivity_coefficient"],
                mode="markers",
                name=PREDICTOR_LABELS.get(metric, metric),
                customdata=points[
                    ["coefficient_difference", "full_n_valid", "sensitivity_n_valid"]
                ],
                hovertemplate=(
                    f"{PREDICTOR_LABELS.get(metric, metric)}"
                    "<br>Coefficient — période complète : %{x:.4f}"
                    "<br>Coefficient de sensibilité : %{y:.4f}"
                    "<br>Différence : %{customdata[0]:.4f}"
                    "<br>Effectif — période complète : %{customdata[1]}"
                    "<br>n sensibilité : %{customdata[2]}<extra></extra>"
                ),
                marker=dict(size=11),
            )
        )
    figure.update_layout(
        title="Coefficient sur la période complète et en analyse de sensibilité",
        xaxis_title="Coefficient — période complète",
        yaxis_title="Coefficient — analyse de sensibilité",
        height=470,
        margin=dict(l=20, r=20, t=65, b=50),
    )
    st.plotly_chart(figure, width="stretch")

    summary = selected[
        [
            "predictor",
            "outcome",
            "full_coefficient",
            "sensitivity_coefficient",
            "coefficient_difference",
            "full_n_valid",
            "sensitivity_n_valid",
        ]
    ].rename(
        columns={
            "predictor": "Métrique du réseau",
            "outcome": "Indicateur opérationnel",
            "full_coefficient": "Coefficient — période complète",
            "sensitivity_coefficient": "Coefficient — sensibilité",
            "coefficient_difference": "Différence (sensibilité − complet)",
            "full_n_valid": "Effectif — période complète",
            "sensitivity_n_valid": "Effectif — sensibilité",
        }
    )
    summary["Métrique du réseau"] = summary["Métrique du réseau"].map(PREDICTOR_LABELS)
    summary["Indicateur opérationnel"] = summary["Indicateur opérationnel"].map(
        OUTCOME_LABELS
    )
    st.dataframe(summary, hide_index=True, width="stretch")
    differences = frame["coefficient_difference"].abs()
    largest_change = frame.loc[differences.idxmax()]
    sign_changes = frame.loc[
        frame["full_coefficient"] * frame["sensitivity_coefficient"] < 0
    ]
    sample_counts = frame[
        ["service", "full_n_valid", "sensitivity_n_valid"]
    ].drop_duplicates()
    exclusions = ", ".join(
        f"{row.service} : {int(row.full_n_valid - row.sensitivity_n_valid)}"
        for row in sample_counts.itertuples(index=False)
    )
    largest_full_n = f"{int(largest_change.full_n_valid):,}".replace(",", " ")
    largest_sensitivity_n = f"{int(largest_change.sensitivity_n_valid):,}".replace(
        ",", " "
    )
    st.markdown("### Lecture de la sélection")
    conclusion = (
        f"Sur les {len(frame)} comparaisons enregistrées, la différence absolue "
        f"médiane est {_fr_number(differences.median(), 4)}. La plus grande "
        f"différence est {_fr_number(differences.max(), 4)} pour "
        f"{PREDICTOR_LABELS[largest_change.predictor]} ({largest_change.service}, "
        f"{METHOD_LABELS[largest_change.method]}), avec un coefficient qui passe "
        f"de {_fr_number(largest_change.full_coefficient, 3)} à "
        f"{_fr_number(largest_change.sensitivity_coefficient, 3)} "
        f"(n = {largest_full_n} puis {largest_sensitivity_n}). Les observations "
        f"écartées du calcul de sensibilité sont réparties ainsi : {exclusions}. "
    )
    if sign_changes.empty:
        conclusion += "Aucun coefficient ne change de signe. "
    else:
        change = sign_changes.iloc[0]
        conclusion += (
            f"Un coefficient change de signe : {change.service}, "
            f"{PREDICTOR_LABELS[change.predictor]}, "
            f"{METHOD_LABELS[change.method]}, "
            f"de {_fr_number(change.full_coefficient, 4)} à "
            f"{_fr_number(change.sensitivity_coefficient, 4)}; les deux valeurs "
            "restent proches de zéro. "
        )
    st.write(
        conclusion + " Cette sélection permet de voir si le constat général se "
        "maintient pour le périmètre et la méthode choisis."
    )
    st.markdown("### À retenir sur le lien entre structure et régularité")
    st.write(
        "Les corrélations montrent des liens statistiques de faible amplitude, "
        "avec un profil particulièrement visible entre Betweenness des arêtes et "
        "taux d'annulation en International, tandis que les indicateurs les plus "
        "associés diffèrent selon le service et le résultat. Les quantiles "
        "confirment qu'il n'existe pas de progression uniforme : 59 des 63 "
        "séquences de médianes sont irrégulières, et les intervalles centraux "
        "chevauchent souvent. Enfin, les coefficients changent peu dans la plupart "
        "des cas après l'exclusion ciblée des retards extrêmes. Ensemble, ces "
        "résultats suggèrent que la topologie apporte une information partielle et "
        "dépendante du périmètre sur la régularité; d'autres facteurs opérationnels "
        "ou contextuels pourraient également compter, sans être mesurés ici."
    )


def _render_synthesis() -> None:
    """Présente la synthèse des résultats de structure et de régularité."""
    st.subheader("Synthèse de l’analyse du réseau et de la régularité")
    st.write(
        "Cette synthèse répond à la question « Dans quelle mesure la structure "
        "du réseau TGV est-elle associée à la régularité des liaisons ? ». Elle "
        "rassemble les résultats des quatre vues précédentes et porte uniquement "
        "sur l’analyse Structure et régularité."
    )

    st.markdown("### Les principaux enseignements")
    st.markdown(
        "1. **Deux périmètres de réseau distincts.** Le graphe National réunit "
        "52 gares et 116 liaisons OD dirigées dans une composante; le graphe "
        "International compte 18 gares, 30 liaisons et trois composantes.\n"
        "2. **Des associations présentes, mais d’amplitude limitée.** Les 126 "
        "coefficients vont de −0,227 à +0,187; le lien le plus marqué concerne "
        "la Betweenness des arêtes et le taux d’annulation en International.\n"
        "3. **Pas de gradient général selon l’importance structurelle.** 59 des "
        "63 séquences de médianes sont irrégulières et 185 des 189 intervalles "
        "centraux entre groupes voisins se chevauchent.\n"
        "4. **Une lecture globalement stable dans le test choisi.** 23 des 42 "
        "coefficients varient de 0,01 au plus; la différence absolue médiane est "
        "de 0,0033 après l’exclusion ciblée de 11 observations."
    )

    st.markdown("### Organisation du réseau OD observé")
    st.write(
        "Les artefacts décrivent 59 gares distinctes, 146 liaisons OD dirigées "
        "associées à un service et 70 appartenances gare-service. Ce dernier "
        "nombre est supérieur au nombre de gares uniques parce que certaines "
        "gares figurent dans les deux périmètres. Le graphe National forme une "
        "composante fortement et faiblement connexe; le graphe International "
        "comporte trois composantes, dont la plus grande regroupe 11 gares."
    )
    st.write(
        "Paris Lyon arrive en tête des classements de degré, de Betweenness "
        "Centrality et de PageRank dans les deux services. Paris Montparnasse et "
        "Lyon Part Dieu figurent également en tête côté National; Paris Est et "
        "Marseille Saint Charles côté International. Ces classements décrivent "
        "la position des gares dans le graphe OD construit, sans établir leur "
        "rôle dans les itinéraires réels ou les flux de voyageurs."
    )
    st.write(
        "La série mensuelle International présente aussi deux changements "
        "visibles : de juin à juillet 2025, elle passe de 9 à 17 nœuds et de 14 "
        "à 28 arêtes; en octobre, elle passe de 17 à 8 nœuds et de 28 à 12 "
        "arêtes. Ces variations décrivent le graphe OD observé à ces périodes; "
        "les sorties disponibles n’en établissent pas la cause."
    )

    st.markdown("### Ce que les analyses disent du lien avec la régularité")
    st.write(
        "Les corrélations signalent quelques associations distinctes selon le "
        "service et l’indicateur. En International, une Betweenness des arêtes "
        "plus élevée est associée à un taux d’annulation plus faible "
        "(Spearman r = −0,227; n = 1 541); l’association positive la plus forte "
        "relie cette même métrique au retard moyen à l’arrivée des trains "
        "retardés (r = +0,187). En National, le degré du nœud d’arrivée est le "
        "plus associé au retard moyen de tous les trains (r = +0,159), tandis "
        "qu’en Overall, c’est le PageRank du nœud d’arrivée (r = +0,117). Les "
        "taux d’annulation sont presque sans association en Overall et en "
        "National (|r| maximal proche de 0,03). Pearson et Spearman donnent le "
        "même sens dans 57 des 63 comparaisons appariées."
    )
    st.write(
        "Les quantiles complètent cette vue en comparant les distributions "
        "plutôt qu’en les résumant par un coefficient. Pour la Betweenness des "
        "arêtes en Overall, les médianes du retard moyen de tous les trains sont "
        "de 6,79, 4,62, 8,71 et 5,73 minutes des groupes Q1 à Q4 : le retard ne "
        "monte ni ne baisse régulièrement avec cette métrique. Les intervalles "
        "Q1–Q3 se chevauchent dans 185 des 189 comparaisons voisines; cela "
        "n’implique pas que les distributions soient identiques, mais montre "
        "que leurs moitiés centrales se recouvrent souvent. Quelques gradients "
        "monotones apparaissent en International, sans former une règle commune "
        "à tous les indicateurs."
    )
    st.write(
        "La sensibilité exclut uniquement, pour ce calcul, les 11 observations "
        "où le retard moyen de tous les trains à l’arrivée est inférieur à "
        "−15 minutes (10 National et 1 International). La différence absolue "
        "médiane entre coefficients est de 0,0033. Le changement le plus marqué "
        "concerne le PageRank source en National, dont Pearson passe de −0,052 à "
        "−0,107 (différence absolue maximale : 0,0548) : le lien négatif se "
        "renforce, mais son amplitude reste limitée. "
        "Un seul coefficient change de signe, en International pour la "
        "Betweenness Centrality cible; il passe de +0,0093 à −0,0018 et reste "
        "proche de zéro dans les deux cas. La lecture générale varie donc peu "
        "sous ce scénario précis, sans constituer une preuve de robustesse "
        "universelle."
    )

    st.markdown("### Réponse à la question de recherche")
    st.write(
        "La structure du réseau TGV est associée à la régularité dans une "
        "mesure réelle mais limitée et variable selon le service, la métrique et "
        "le résultat opérationnel. L’analyse de graphe décrit une organisation "
        "OD différenciée et met en évidence des gares centrales; les corrélations "
        "repèrent quelques liens, surtout en International, mais leurs amplitudes "
        "restent modestes. Les comparaisons par quantiles montrent que ces liens "
        "ne suivent généralement pas une progression simple, et le test de "
        "sensibilité conserve l’essentiel de cette lecture. La topologie fournit "
        "donc un angle utile pour décrire les relations observées, mais seulement "
        "une partie de l’information associée à la régularité. Des dimensions "
        "opérationnelles ou contextuelles pourraient aussi contribuer à cette "
        "régularité; elles ne sont pas établies par ces analyses."
    )

    st.markdown("### Limites principales")
    st.caption(
        "Le graphe représente des liaisons origine-destination observées, pas "
        "des segments physiques adjacents, des itinéraires confirmés ou des "
        "volumes de voyageurs. Les associations ne démontrent pas de causalité; "
        "les observations mensuelles d’une même liaison sont répétées et les "
        "p-values sont exploratoires. La sensibilité porte uniquement sur le "
        "résultat principal et le seuil de −15 minutes."
    )


st.caption("ANALYSE DE LA STRUCTURE DU RÉSEAU ET DE LA RÉGULARITÉ")
st.title("Structure et régularité")
st.write(
    "Explorez les résultats enregistrés sur les associations entre les métriques "
    "du réseau et les indicateurs de régularité, ainsi que la structure des "
    "réseaux National et International."
)

with st.expander("Méthode et limites d’interprétation", expanded=False):
    st.markdown(
        "Ces analyses décrivent des associations et ne démontrent pas de lien "
        "causal. Les observations mensuelles d'une même liaison sont répétées; "
        "les p-values classiques doivent donc être interprétées avec prudence. "
        "La taille de l'échantillon est affichée pour chaque résultat et varie "
        "selon les comparaisons.\n\n"
        "Le graphe OD représente les liaisons observées dans les données. Il ne "
        "prouve pas les itinéraires réellement empruntés ni l'adjacence physique "
        "des gares. Les métriques ne mesurent pas les flux de voyageurs et ne "
        "démontrent pas une propagation des retards. Les réseaux National et "
        "International ont des structures et des compositions de liaisons "
        "différentes.\n\n"
        "Les retards moyens négatifs sont conservés dans le jeu de recherche. "
        "L'exclusion des retards inférieurs à −15 minutes concerne uniquement "
        "l'analyse de sensibilité de l'indicateur principal."
    )

structure_tab, correlations_tab, quantiles_tab, robustness_tab, synthesis_tab = st.tabs(
    [
        "Structure du réseau",
        "Corrélations",
        "Comparaison par quantiles",
        "Robustesse",
        "Synthèse",
    ]
)

with structure_tab:
    _render_network_structure()

with correlations_tab:
    _render_correlations()

with quantiles_tab:
    _render_quantiles()

with robustness_tab:
    _render_robustness()

with synthesis_tab:
    _render_synthesis()
