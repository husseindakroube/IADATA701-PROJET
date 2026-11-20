"""Synthèses descriptives de la topologie, des métriques et des résultats opérationnels du graphe SNCF."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import polars as pl

from projet_kit_data.graph.presentation import (
    METRIC_PRESENTATION,
    format_metric_value,
)

GRAPH_DIR = Path("data/processed/graph")
DEFAULT_RESEARCH_PATH = Path("data/processed/research_dataset.parquet")
DEFAULT_NODE_METRICS_PATH = GRAPH_DIR / "node_metrics.parquet"
DEFAULT_EDGE_METRICS_PATH = GRAPH_DIR / "edge_metrics.parquet"
DEFAULT_NODES_PATH = GRAPH_DIR / "nodes.parquet"
DEFAULT_EDGES_PATH = GRAPH_DIR / "edges.parquet"
DEFAULT_CONSTRUCTION_METADATA_PATH = GRAPH_DIR / "graph_metadata.json"
DEFAULT_OUTPUT_DIR = GRAPH_DIR / "descriptive"
DEFAULT_REPORT_PATH = Path("data/reports/graph/research_report.md")
NODE_METRICS = (
    "in_degree",
    "out_degree",
    "degree",
    "in_degree_centrality",
    "out_degree_centrality",
    "betweenness_centrality",
    "in_closeness",
    "out_closeness",
    "pagerank",
)
OUTCOMES = (
    "retard_moyen_tous_trains_arrivee",
    "cancellation_rate",
    "retard_moyen_arrivee",
)


@dataclass
class DescriptiveResult:
    """Tables produites par l’analyse descriptive.

    :ivar network_summary: Topologie globale par service.
    :ivar node_metric_summary: Statistiques de distribution des métriques globales des nœuds.
    :ivar node_rankings: Tables globales des gares les mieux classées.
    :ivar edge_rankings: Tables globales des liaisons orientées les mieux classées.
    :ivar monthly_summary: Synthèses mensuelles/service de la topologie et de certaines métriques.
    :ivar operational_summary: Statistiques de distribution des résultats opérationnels par service.
    :ivar quality_flag_summary: Nombre d’indicateurs de qualité booléens existants par service.
    :ivar metadata: Sources d’entrée et configuration de l’analyse.
    :ivar output_paths: Chemins écrits par le pipeline fondé sur des fichiers.
    """

    network_summary: pl.DataFrame
    node_metric_summary: pl.DataFrame
    node_rankings: pl.DataFrame
    edge_rankings: pl.DataFrame
    monthly_summary: pl.DataFrame
    operational_summary: pl.DataFrame
    quality_flag_summary: pl.DataFrame
    metadata: dict[str, Any]
    output_paths: dict[str, Path] = field(default_factory=dict)


def _check_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            f"{label} ne contient pas les colonnes suivantes : {', '.join(sorted(missing))}"
        )


def _stats_by_group(
    frame: pl.DataFrame, group: str, columns: tuple[str, ...]
) -> pl.DataFrame:
    expressions: list[pl.Expr] = []
    for column in columns:
        expressions.extend(
            [
                pl.col(column).count().alias(f"{column}_count"),
                pl.col(column).null_count().alias(f"{column}_missing"),
                pl.col(column).mean().alias(f"{column}_mean"),
                pl.col(column).std().alias(f"{column}_std"),
                pl.col(column).median().alias(f"{column}_median"),
                pl.col(column).quantile(0.25).alias(f"{column}_q25"),
                pl.col(column).quantile(0.75).alias(f"{column}_q75"),
                pl.col(column).min().alias(f"{column}_min"),
                pl.col(column).max().alias(f"{column}_max"),
            ]
        )
    return frame.group_by(group).agg(expressions).sort(group)


def _markdown_table(frame: pl.DataFrame) -> str:
    columns = frame.columns
    rows = frame.to_dicts()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values = ["" if row[column] is None else str(row[column]) for column in columns]
        lines.append(
            "| " + " | ".join(value.replace("|", "\\|") for value in values) + " |"
        )
    return "\n".join(lines)


def build_descriptive_summaries(
    research_data: pl.DataFrame,
    node_metrics: pl.DataFrame,
    edge_metrics: pl.DataFrame,
    nodes: pl.DataFrame,
    edges: pl.DataFrame,
    construction_metadata: dict[str, Any] | None = None,
    top_n: int = 10,
) -> DescriptiveResult:
    """Construire des tables descriptives réutilisables à partir des artefacts existants.

    Les métriques de graphe existantes sont synthétisées telles quelles ; cette
    fonction ne les recalcule pas. Les nombres de composantes du réseau sont
    dérivés de la table d’arêtes orientées existante uniquement pour vérifier
    et décrire la topologie.

    :param research_data: Jeu de recherche mensuel.
    :type research_data: polars.DataFrame
    :param node_metrics: Métriques globales et mensuelles des nœuds.
    :type node_metrics: polars.DataFrame
    :param edge_metrics: Métriques globales et mensuelles des arêtes.
    :type edge_metrics: polars.DataFrame
    :param nodes: Correspondance entre identifiants de nœud et noms de gare.
    :type nodes: polars.DataFrame
    :param edges: Arêtes orientées globales tenant compte du service.
    :type edges: polars.DataFrame
    :param construction_metadata: Métadonnées de construction d’origine facultatives pour
        vérifier les nombres liés à la topologie.
    :type construction_metadata: dict[str, Any] | None
    :param top_n: Nombre de gares/liaisons par classement et par service.
    :type top_n: int
    :returns: Tables descriptives et métadonnées de provenance.
    :rtype: DescriptiveResult
    :raises TypeError: Si une entrée n’est pas un DataFrame Polars.
    :raises ValueError: Si des champs requis sont absents ou si top_n est invalide.
    """
    frames = (research_data, node_metrics, edge_metrics, nodes, edges)
    if any(not isinstance(frame, pl.DataFrame) for frame in frames):
        raise TypeError(
            "Toutes les entrées tabulaires doivent être des DataFrame Polars"
        )
    if top_n < 1:
        raise ValueError("top_n doit être positif")
    _check_columns(
        research_data,
        {"date", "service", "gare_depart", "gare_arrivee", *OUTCOMES},
        "research_data",
    )
    _check_columns(
        node_metrics,
        {"period", "service", "node_id", "station_name", *NODE_METRICS},
        "node_metrics",
    )
    _check_columns(
        edge_metrics,
        {"period", "service", "edge_id", "source", "target", "edge_betweenness"},
        "edge_metrics",
    )
    _check_columns(nodes, {"node_id", "station_name"}, "nodes")
    _check_columns(edges, {"edge_id", "service", "source", "target"}, "edges")

    topology_rows: list[dict[str, Any]] = []
    for service in sorted(edges["service"].unique().to_list()):
        service_edges = edges.filter(pl.col("service") == service)
        graph = nx.DiGraph()
        graph.add_edges_from(service_edges.select("source", "target").iter_rows())
        components = list(nx.weakly_connected_components(graph))
        topology_rows.append(
            {
                "service": service,
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "weakly_connected_components": len(components),
                "strongly_connected_components": nx.number_strongly_connected_components(
                    graph
                ),
                "largest_weak_component": max(
                    (len(component) for component in components), default=0
                ),
                "nodes_multiple_incoming": sum(
                    degree > 1 for _, degree in graph.in_degree()
                ),
                "nodes_multiple_outgoing": sum(
                    degree > 1 for _, degree in graph.out_degree()
                ),
                "self_loops": nx.number_of_selfloops(graph),
            }
        )
    network_summary = pl.DataFrame(topology_rows)
    if construction_metadata:
        metadata_counts = construction_metadata.get(
            "network_diagnostics_by_service", {}
        )
        for row in topology_rows:
            reported = metadata_counts.get(row["service"])
            if reported and (
                reported.get("nodes") != row["node_count"]
                or reported.get("edges") != row["edge_count"]
            ):
                raise ValueError(
                    f"Incohérence entre les métadonnées de construction et la topologie pour {row['service']}"
                )

    overall_nodes = node_metrics.filter(pl.col("period") == "overall")
    overall_edges = edge_metrics.filter(pl.col("period") == "overall")
    node_metric_summary = _stats_by_group(overall_nodes, "service", NODE_METRICS)
    centrality_zero_shares = {}
    for service in sorted(overall_nodes["service"].unique().to_list()):
        service_nodes = overall_nodes.filter(pl.col("service") == service)
        centrality_zero_shares[service] = {
            metric: (
                float((service_nodes[metric] == 0).sum() / service_nodes.height)
                if service_nodes.height
                else 0.0
            )
            for metric in ("betweenness_centrality", "pagerank")
        }
    ranking_frames: list[pl.DataFrame] = []
    for service in sorted(overall_nodes["service"].unique().to_list()):
        for metric, label in (
            ("degree", "connectivity_degree"),
            ("betweenness_centrality", "betweenness_centrality"),
            ("pagerank", "pagerank"),
        ):
            precision = METRIC_PRESENTATION[metric].precision
            candidates = overall_nodes.filter(
                (pl.col("service") == service) & (pl.col(metric) > 0)
            ).with_columns(pl.col(metric).round(precision).alias("_display_value"))
            ranking = (
                candidates.with_columns(
                    pl.col("_display_value")
                    .rank(method="dense", descending=True)
                    .cast(pl.UInt32)
                    .alias("rank")
                )
                .filter(pl.col("rank") <= top_n)
                .select(
                    "rank",
                    pl.lit(service).alias("service"),
                    pl.lit(label).alias("ranking_metric"),
                    "node_id",
                    "station_name",
                    pl.col(metric).cast(pl.Float64).alias("value"),
                )
            )
            ranking_frames.append(ranking)
    node_rankings = (
        pl.concat(ranking_frames).sort(
            "service", "ranking_metric", "rank", "station_name"
        )
        if ranking_frames
        else pl.DataFrame()
    )
    edge_candidates = (
        overall_edges.filter(pl.col("edge_betweenness") > 0)
        .with_columns(
            pl.col("edge_betweenness")
            .round(METRIC_PRESENTATION["edge_betweenness"].precision)
            .alias("_display_value")
        )
        .with_columns(
            pl.col("_display_value")
            .rank(method="dense", descending=True)
            .over("service")
            .alias("_rank")
        )
        .filter(pl.col("_rank") <= top_n)
    )
    edge_rankings = (
        edge_candidates.join(nodes, left_on="source", right_on="node_id", how="left")
        .rename({"station_name": "origin_name"})
        .join(nodes, left_on="target", right_on="node_id", how="left")
        .rename({"station_name": "destination_name"})
        .sort("service", "_rank", "origin_name", "destination_name")
        .select(
            "service",
            "edge_id",
            "source",
            "origin_name",
            "target",
            "destination_name",
            "edge_betweenness",
        )
    )

    monthly_nodes = node_metrics.filter(pl.col("period") != "overall")
    monthly_edges = edge_metrics.filter(pl.col("period") != "overall")
    monthly_node_summary = monthly_nodes.group_by("period", "service").agg(
        pl.col("node_id").n_unique().alias("node_count"),
        pl.col("degree").mean().alias("mean_degree"),
        pl.col("pagerank").max().alias("max_pagerank"),
        pl.col("betweenness_centrality").max().alias("max_betweenness"),
        pl.col("betweenness_centrality").median().alias("median_betweenness"),
    )
    monthly_edge_summary = monthly_edges.group_by("period", "service").agg(
        pl.col("edge_id").n_unique().alias("edge_count"),
        pl.col("edge_betweenness").mean().alias("mean_edge_betweenness"),
        pl.col("edge_betweenness").max().alias("max_edge_betweenness"),
    )
    monthly_summary = monthly_node_summary.join(
        monthly_edge_summary, on=["period", "service"], how="full", coalesce=True
    ).sort("service", "period")
    operational_summary = _stats_by_group(research_data, "service", OUTCOMES)
    outlier_expressions = []
    for column in OUTCOMES:
        q1, q3 = pl.col(column).quantile(0.25), pl.col(column).quantile(0.75)
        iqr = q3 - q1
        outlier_expressions.append(
            ((pl.col(column) < q1 - 1.5 * iqr) | (pl.col(column) > q3 + 1.5 * iqr))
            .fill_null(False)
            .sum()
            .alias(f"{column}_iqr_outlier_count")
        )
    outliers = research_data.group_by("service").agg(outlier_expressions)
    operational_summary = operational_summary.join(outliers, on="service", how="left")
    flag_columns = [
        column
        for column in research_data.columns
        if column.startswith("flag_") and research_data.schema[column] == pl.Boolean
    ]
    quality_flag_summary = (
        research_data.group_by("service").agg(
            [
                pl.col(column).fill_null(False).sum().alias(column)
                for column in flag_columns
            ]
        )
        if flag_columns
        else pl.DataFrame(
            {"service": sorted(research_data["service"].unique().to_list())}
        )
    )
    metadata = {
        "observation_count": research_data.height,
        "date_coverage": {
            "min": research_data["date"].min() if research_data.height else None,
            "max": research_data["date"].max() if research_data.height else None,
        },
        "services": sorted(research_data["service"].unique().to_list()),
        "overall_graphs": topology_rows,
        "overall_node_metric_rows": overall_nodes.height,
        "overall_edge_metric_rows": overall_edges.height,
        "centrality_zero_shares": centrality_zero_shares,
        "monthly_graph_count": monthly_summary.height,
        "metric_columns": {"node": list(NODE_METRICS), "edge": ["edge_betweenness"]},
        "outlier_definition": "Règle de Tukey à 1,5 × IQR, à visée descriptive uniquement ; les observations ne sont pas supprimées.",
        "limitations": [
            "Les liaisons OD ne correspondent pas nécessairement à des itinéraires de train ni à des segments physiques de voie.",
            "La centralité ne mesure ni le trafic voyageurs, ni la fréquence des trains, ni la propagation des retards.",
            "Les métriques globales du graphe sont distinctes des métriques et des résultats mensuels.",
        ],
    }
    return DescriptiveResult(
        network_summary,
        node_metric_summary,
        node_rankings,
        edge_rankings,
        monthly_summary,
        operational_summary,
        quality_flag_summary,
        metadata,
    )


def _write_report(result: DescriptiveResult, path: Path) -> None:
    """Maintenir une synthèse de recherche en français dans le rapport unifié.

    Le contenu rédigé hors du passage balisé est conservé.
    """
    begin = "<!-- BEGIN GENERATED DESCRIPTIVE CONTENT -->"
    end = "<!-- END GENERATED DESCRIPTIVE CONTENT -->"
    image_dir = "../../processed/graph/visualizations"
    topology = result.network_summary.select(
        pl.col("service").alias("Service"),
        pl.col("node_count").alias("Gares"),
        pl.col("edge_count").alias("Liaisons dirigées"),
        pl.col("weakly_connected_components").alias("Composantes faiblement connexes"),
        pl.col("strongly_connected_components").alias("Composantes fortement connexes"),
        pl.col("largest_weak_component").alias(
            "Nœuds dans la plus grande composante faible"
        ),
    )

    metric_labels = {
        "connectivity_degree": METRIC_PRESENTATION["degree"].label,
        "betweenness_centrality": METRIC_PRESENTATION["betweenness_centrality"].label,
        "pagerank": METRIC_PRESENTATION["pagerank"].label,
    }
    leaders: list[dict[str, Any]] = []
    for row in result.node_rankings.filter(pl.col("rank") == 1).to_dicts():
        leaders.append(
            {
                "Service": row["service"],
                "Mesure": metric_labels.get(
                    row["ranking_metric"], row["ranking_metric"]
                ),
                "Gare": row["station_name"],
                "Valeur": f"{row['value']:.4f}"
                if row["value"] < 1
                else f"{row['value']:.0f}",
            }
        )
    leader_table = (
        pl.DataFrame(leaders)
        if leaders
        else pl.DataFrame(
            schema={
                "Service": pl.String,
                "Mesure": pl.String,
                "Gare": pl.String,
                "Valeur": pl.String,
            }
        )
    )
    leader_patterns = []
    for service in ("National", "International"):
        service_leaders = result.node_rankings.filter(
            (pl.col("service") == service) & (pl.col("rank") == 1)
        )
        if service_leaders.height:
            shared_names = (
                service_leaders.group_by("station_name")
                .len()
                .sort("len", descending=True)
            )
            if shared_names.height and shared_names["len"][0] == 3:
                leader_patterns.append(
                    f"{service} : {shared_names['station_name'][0]} arrive en tête des trois mesures"
                )
            else:
                metric_names = "; ".join(
                    f"{metric_labels[row['ranking_metric']]} : {row['station_name']}"
                    for row in service_leaders.to_dicts()
                )
                leader_patterns.append(f"{service} : {metric_names}")
    zero_shares = result.metadata.get("centrality_zero_shares", {})
    zero_text = "; ".join(
        f"{service}, {METRIC_PRESENTATION['betweenness_centrality'].label} : "
        f"{100 * values['betweenness_centrality']:.1f}% de valeurs égales à zéro"
        for service, values in zero_shares.items()
    )

    edge_notes: list[str] = []
    for service in ("National", "International"):
        ranked = result.edge_rankings.filter(pl.col("service") == service)
        if ranked.height == 0:
            continue
        maximum = ranked["edge_betweenness"].max()
        precision = METRIC_PRESENTATION["edge_betweenness"].precision
        leaders_for_service = ranked.filter(
            pl.col("edge_betweenness").round(precision) == round(maximum, precision)
        )
        examples = leaders_for_service.head(2).to_dicts()
        names = "; ".join(
            f"{row['origin_name']} → {row['destination_name']}" for row in examples
        )
        edge_notes.append(
            f"{service} : {leaders_for_service.height} liaison(s) partagent le maximum"
            + (
                f" ({format_metric_value('edge_betweenness', maximum)}); exemples : {names}."
                if names
                else "."
            )
        )

    outcome_rows = []
    for row in result.operational_summary.to_dicts():
        for label, stem in (
            (
                "Retard moyen tous trains à l’arrivée (min)",
                "retard_moyen_tous_trains_arrivee",
            ),
            ("Retard moyen des trains retardés (min)", "retard_moyen_arrivee"),
            ("Taux d’annulation (part)", "cancellation_rate"),
        ):
            mean = row[f"{stem}_mean"]
            median = row[f"{stem}_median"]
            outcome_rows.append(
                {
                    "Service": row["service"],
                    "Indicateur": label,
                    "N valide / manquant": f"{row[f'{stem}_count']} / {row[f'{stem}_missing']}",
                    "Médiane": "—" if median is None else f"{median:.2f}",
                    "Moyenne complète": "—" if mean is None else f"{mean:.2f}",
                }
            )
    outcomes = pl.DataFrame(outcome_rows)
    outcome_by_service = {
        row["service"]: row for row in result.operational_summary.to_dicts()
    }
    national_outcomes = outcome_by_service.get("National")
    international_outcomes = outcome_by_service.get("International")
    if national_outcomes and international_outcomes:

        def french_decimal(value: float | None) -> str:
            return "—" if value is None else f"{value:.2f}".replace(".", ",")

        operational_pattern = (
            "Les médianes sont de "
            f"{french_decimal(national_outcomes['retard_moyen_tous_trains_arrivee_median'])} contre "
            f"{french_decimal(international_outcomes['retard_moyen_tous_trains_arrivee_median'])} min pour le retard moyen tous trains, et de "
            f"{french_decimal(national_outcomes['retard_moyen_arrivee_median'])} contre "
            f"{french_decimal(international_outcomes['retard_moyen_arrivee_median'])} min parmi les trains retardés (National puis International)."
        )
    else:
        operational_pattern = (
            "Les médianes par indicateur et service figurent dans le tableau."
        )

    display_counts = result.metadata.get("operational_chart_counts", {})
    primary_by_service = display_counts.get("primary_below_minus_15_by_service", {})
    primary_excluded_breakdown = ", ".join(
        f"{service} {primary_by_service.get(service, 0)}"
        for service in ("National", "International")
    )
    delayed_by_service = display_counts.get("delayed_above_120_by_service", {})
    cancellation_above_zoom = display_counts.get("cancellation_above_010")
    cancellation_missing = display_counts.get("cancellation_missing")

    international = result.monthly_summary.filter(
        pl.col("service") == "International"
    ).sort("period")
    intl_rows = international.to_dicts()
    transition_text = "La série mensuelle est descriptive; aucun changement n’est attribué à une cause."
    if intl_rows:
        month_map = {row["period"]: row for row in intl_rows}
        july = month_map.get("2025-07")
        october = month_map.get("2025-10")
        if july and october:
            july_following = [month_map.get(f"2025-0{month}") for month in (8, 9)]
            oct_following = [
                month_map.get(f"2025-{month:02d}") for month in range(11, 13)
            ]
            july_persistent = all(
                row
                and row["node_count"] == july["node_count"]
                and row["edge_count"] == july["edge_count"]
                for row in july_following
            )
            october_persistent = all(
                row
                and row["node_count"] == october["node_count"]
                and row["edge_count"] == october["edge_count"]
                for row in oct_following
            )
            latest = intl_rows[-1]
            transition_text = (
                f"International : en juillet 2025, le graphe passe à {july['node_count']} gares et {july['edge_count']} liaisons dirigées"
                + (" jusqu’en septembre." if july_persistent else ".")
                + f" En octobre 2025, il passe à {october['node_count']} gares et {october['edge_count']} liaisons dirigées"
                + (
                    f"; cette configuration persiste jusqu’à {latest['period']}."
                    if october_persistent and latest["period"] >= "2025-12"
                    else "."
                )
            )

    def component_phrase(count: int, connectivity: str) -> str:
        if count == 1:
            return f"une composante {connectivity}"
        return f"{count} composantes {connectivity}s"

    topology_text = "; ".join(
        f"Le graphe {row['service']} comprend "
        f"{component_phrase(row['weakly_connected_components'], 'faiblement connexe')} et "
        f"{component_phrase(row['strongly_connected_components'], 'fortement connexe')}"
        for row in result.network_summary.to_dicts()
    ).replace("; Le graphe", "; le graphe")
    content = [
        "## 2. Structure du réseau",
        "",
        "### Couverture et connexité",
        "",
        "Nous commençons par comparer les graphes de liaisons origine-destination observées pour les deux services. Le réseau National couvre davantage de gares et de liaisons; le tableau précise aussi comment chaque graphe se répartit en composantes faiblement et fortement connexes.",
        "",
        _markdown_table(topology),
        "",
        f"{topology_text}.",
        "",
        "Dans un graphe orienté, une composante faiblement connexe relie les nœuds si l’on ignore le sens des arcs; une composante fortement connexe exige des chemins orientés dans les deux sens entre ses nœuds. Le réseau National forme une seule composante faible et une seule composante forte. Le réseau International compte trois composantes faibles, dont la plus grande réunit 11 gares, et trois composantes fortes. Ces chiffres décrivent les OD présentes dans les données, pas l’ensemble de l’infrastructure ferroviaire.",
        "",
        f"![Réseau National]({image_dir}/network_national.png)",
        "",
        f"![Réseau International]({image_dir}/network_international.png)",
        "",
        "### Importance des gares",
        "",
        "Le degré compte les relations entrantes et sortantes ; la betweenness centrality et PageRank décrivent d’autres positions dans le graphe orienté. Ces mesures aident à repérer les gares centrales dans les OD observées, mais ne mesurent ni le nombre de voyageurs ni la fréquence des trains.",
        "",
        f"![Distributions des degrés]({image_dir}/degree_distributions.png)",
        "",
        f"![Distributions de centralité]({image_dir}/node_centrality_distributions.png)",
        "",
        f"![Gares en tête par mesure]({image_dir}/leading_station_rankings.png)",
        "",
        _markdown_table(leader_table),
        "",
        "Dans les deux services, Paris Lyon est en tête des trois mesures présentées. La distribution de Betweenness centrality comprend toutefois une forte part de zéros : "
        + zero_text
        + ". La position dominante de quelques gares ne signifie pas que toutes les gares jouent le même rôle topologique; elle ne permet pas non plus de conclure à un rôle opérationnel causal.",
        "",
        "### Importance des liaisons OD",
        "",
        "L’intermédiarité des arêtes (edge betweenness) indique la fréquence avec laquelle une arête intervient dans les plus courts chemins du graphe orienté. La distribution montre des valeurs concentrées près du bas de l’échelle et quelques valeurs plus élevées.",
        "",
        f"![Distribution de l’intermédiarité des arêtes]({image_dir}/edge_betweenness_distribution.png)",
        "",
        "**Valeurs observées.** " + " ".join(edge_notes),
        "",
        "Plusieurs liaisons partagent les valeurs maximales, notamment 20 liaisons International. Cette mesure d’intermédiarité des arêtes décrit une position dans le graphe ; elle ne représente ni le trafic ni un volume de passagers. Les ex æquo sont conservés dans le tableau de classement.",
        "",
        "## 3. Évolution temporelle",
        "",
        "La série mensuelle permet de voir si la couverture observée reste stable. Les panneaux de centralité représentent les maxima mensuels, et non des moyennes du réseau.",
        "",
        f"![Évolution mensuelle du réseau]({image_dir}/monthly_network_evolution.png)",
        "",
        f"{transition_text} Les changements sont nets dans le graphe International : ils décrivent le contenu des observations à ces dates, mais les données disponibles n’en établissent pas la cause.",
        "",
        "## 4. Régularité opérationnelle",
        "",
        "Après la topologie, nous regardons les retards et les annulations rapportés pour les mêmes liaisons mensuelles. Cette étape décrit les résultats opérationnels avant de les mettre en relation avec les métriques de graphe.",
        "",
        f"![Distributions des indicateurs opérationnels]({image_dir}/operational_outcome_distributions.png)",
        "",
        "Pour rendre les distributions lisibles, le panneau principal sépare les observations sous −15 minutes du retard moyen tous trains; les 16 valeurs de retard moyen des trains retardés supérieures à 120 minutes sont présentées dans un panneau distinct. Ces valeurs restent dans le jeu de recherche et dans les statistiques complètes. Le zoom des taux d’annulation ne remplace pas les valeurs manquantes par zéro.",
        (
            f"Le graphique signale {sum(primary_by_service.values())} retards moyens tous trains sous −15 minutes ({primary_excluded_breakdown}), {sum(delayed_by_service.values())} observations au-dessus de 120 minutes, {cancellation_above_zoom} taux d’annulation au-dessus de 0,10 et {cancellation_missing} taux manquants."
            if primary_by_service and delayed_by_service
            else "Les effectifs hors des panneaux centraux et les valeurs manquantes sont indiqués sur le graphique."
        ),
        "",
        f"{operational_pattern} Les moyennes complètes dépassent les médianes pour ces indicateurs, ce qui montre que les valeurs hautes influencent les moyennes. Pour les annulations, la médiane est proche de 1 % tandis que la moyenne est proche de 4 % dans les deux services. Les 73 taux manquants sont signalés comme invalides lorsque le nombre de trains planifiés ne permet pas de calculer le ratio; ils ne signifient pas zéro annulation.",
        "",
        _markdown_table(outcomes),
        "",
        "La différence des médianes entre services est descriptive. Elle ne permet pas d’attribuer les retards à une gare ou à une liaison. La section suivante examine directement les associations avec les métriques du graphe, sans interpréter ces différences comme une causalité.",
        "",
        "Cette analyse descriptive ne teste pas l’association entre structure du réseau et régularité; cette question est examinée dans la section d’associations qui suit.",
        "",
    ]
    replacement = "\n".join(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = (
            "# Rapport de recherche — Réseau TGV et régularité\n\n"
            "Ce document rassemble les résultats de recherche.\n\n"
            f"{begin}\n{end}\n\n"
            "<!-- Ajouter ici les analyses complémentaires, vérifications de robustesse et la discussion. -->\n"
        )
    if begin in existing and end in existing:
        prefix, remainder = existing.split(begin, maxsplit=1)
        _, suffix = remainder.split(end, maxsplit=1)
        updated = f"{prefix}{begin}\n{replacement}\n{end}{suffix}"
    else:
        updated = f"{existing.rstrip()}\n\n{begin}\n{replacement}\n{end}\n"
    path.write_text(updated, encoding="utf-8")


def run_descriptive_analysis(
    research_data_path: str | os.PathLike[str] = DEFAULT_RESEARCH_PATH,
    node_metrics_path: str | os.PathLike[str] = DEFAULT_NODE_METRICS_PATH,
    edge_metrics_path: str | os.PathLike[str] = DEFAULT_EDGE_METRICS_PATH,
    nodes_path: str | os.PathLike[str] = DEFAULT_NODES_PATH,
    edges_path: str | os.PathLike[str] = DEFAULT_EDGES_PATH,
    construction_metadata_path: str
    | os.PathLike[str] = DEFAULT_CONSTRUCTION_METADATA_PATH,
    output_dir: str | os.PathLike[str] = DEFAULT_OUTPUT_DIR,
    report_path: str | os.PathLike[str] = DEFAULT_REPORT_PATH,
    top_n: int = 10,
) -> DescriptiveResult:
    """Résumer les résultats et artefacts du graphe dans des tables et un rapport.

    :param research_data_path: Chemin du fichier Parquet de recherche.
    :type research_data_path: str | os.PathLike[str]
    :param node_metrics_path: Chemin existant du fichier Parquet des métriques de nœud.
    :type node_metrics_path: str | os.PathLike[str]
    :param edge_metrics_path: Chemin existant du fichier Parquet des métriques d’arête.
    :type edge_metrics_path: str | os.PathLike[str]
    :param nodes_path: Chemin existant du fichier Parquet de correspondance des nœuds.
    :type nodes_path: str | os.PathLike[str]
    :param edges_path: Chemin existant du fichier Parquet des arêtes globales.
    :type edges_path: str | os.PathLike[str]
    :param construction_metadata_path: Chemin existant du fichier JSON des métadonnées de construction.
    :type construction_metadata_path: str | os.PathLike[str]
    :param output_dir: Répertoire de destination des tables descriptives Parquet.
    :type output_dir: str | os.PathLike[str]
    :param report_path: Chemin de destination du rapport Markdown.
    :type report_path: str | os.PathLike[str]
    :param top_n: Nombre de gares/liaisons classées à conserver par service.
    :type top_n: int
    :returns: Tables descriptives, métadonnées et chemins de sortie.
    :rtype: DescriptiveResult
    :raises OSError: Si les entrées ne peuvent pas être lues ou les sorties écrites.
    :raises ValueError: Si les schémas, comptes des métadonnées ou top_n sont invalides.
    """
    input_paths = {
        "research_data": Path(research_data_path),
        "node_metrics": Path(node_metrics_path),
        "edge_metrics": Path(edge_metrics_path),
        "nodes": Path(nodes_path),
        "edges": Path(edges_path),
    }
    construction_metadata = json.loads(
        Path(construction_metadata_path).read_text(encoding="utf-8")
    )
    research_data = pl.read_parquet(input_paths["research_data"])
    result = build_descriptive_summaries(
        research_data,
        pl.read_parquet(input_paths["node_metrics"]),
        pl.read_parquet(input_paths["edge_metrics"]),
        pl.read_parquet(input_paths["nodes"]),
        pl.read_parquet(input_paths["edges"]),
        construction_metadata=construction_metadata,
        top_n=top_n,
    )
    result.metadata["input_paths"] = {
        key: str(path) for key, path in input_paths.items()
    }
    primary_flag = "flag_primary_arrival_delay_below_minus_15"
    primary_visual_extreme = (
        pl.col(primary_flag).fill_null(False)
        if primary_flag in research_data.columns
        else pl.col("retard_moyen_tous_trains_arrivee") < -15
    )
    result.metadata["operational_chart_counts"] = {
        "primary_below_minus_15_by_service": {
            row["service"]: row["count"]
            for row in research_data.filter(primary_visual_extreme)
            .group_by("service")
            .agg(pl.len().alias("count"))
            .to_dicts()
        },
        "delayed_above_120_by_service": {
            row["service"]: row["count"]
            for row in research_data.filter(pl.col("retard_moyen_arrivee") > 120)
            .group_by("service")
            .agg(pl.len().alias("count"))
            .to_dicts()
        },
        "cancellation_above_010": research_data.filter(
            pl.col("cancellation_rate") > 0.1
        ).height,
        "cancellation_missing": research_data["cancellation_rate"].null_count(),
    }
    primary_flag = "flag_primary_arrival_delay_below_minus_15"
    primary_extreme = (
        pl.col(primary_flag).fill_null(False)
        if primary_flag in research_data.columns
        else pl.col("retard_moyen_tous_trains_arrivee") < -15
    )
    result.metadata["operational_chart_counts"] = {
        "primary_below_minus_15_by_service": {
            row["service"]: row["count"]
            for row in research_data.filter(primary_extreme)
            .group_by("service")
            .agg(pl.len().alias("count"))
            .to_dicts()
        },
        "delayed_above_120_by_service": {
            row["service"]: row["count"]
            for row in research_data.filter(pl.col("retard_moyen_arrivee") > 120)
            .group_by("service")
            .agg(pl.len().alias("count"))
            .to_dicts()
        },
        "cancellation_above_010": research_data.filter(
            pl.col("cancellation_rate") > 0.1
        ).height,
        "cancellation_missing": research_data["cancellation_rate"].null_count(),
    }
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    tables = {
        "network_summary": result.network_summary,
        "node_metric_summary": result.node_metric_summary,
        "node_rankings": result.node_rankings,
        "edge_rankings": result.edge_rankings,
        "monthly_summary": result.monthly_summary,
        "operational_summary": result.operational_summary,
        "quality_flag_summary": result.quality_flag_summary,
    }
    result.output_paths = {}
    for name, table in tables.items():
        destination = directory / f"{name}.parquet"
        table.write_parquet(destination)
        result.output_paths[name] = destination
    report_destination = Path(report_path)
    _write_report(result, report_destination)
    result.output_paths["report"] = report_destination
    return result
