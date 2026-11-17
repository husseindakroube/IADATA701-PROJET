"""Descriptive summaries of SNCF graph topology, metrics, and outcomes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import polars as pl

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
    """Tables produced by the descriptive analysis.

    :ivar network_summary: Overall topology by service.
    :ivar node_metric_summary: Distribution statistics for overall node metrics.
    :ivar node_rankings: Overall top station tables.
    :ivar edge_rankings: Overall top directed liaison tables.
    :ivar monthly_summary: Month/service topology and selected metric summaries.
    :ivar operational_summary: Outcome distribution statistics by service.
    :ivar quality_flag_summary: Counts of existing Boolean quality flags by service.
    :ivar metadata: Input sources and analysis configuration.
    :ivar output_paths: Paths written by the file-based pipeline.
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
        raise ValueError(f"{label} is missing columns: {', '.join(sorted(missing))}")


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
    """Build reusable descriptive tables from existing Phase 1/2 artifacts.

    Existing graph metrics are summarized as provided; this function does not
    recalculate them. Network component counts are derived from the existing
    directed edge table solely to verify and describe topology.

    :param research_data: Phase 2 monthly research dataset.
    :type research_data: polars.DataFrame
    :param node_metrics: Phase 1 overall and monthly node metrics.
    :type node_metrics: polars.DataFrame
    :param edge_metrics: Phase 1 overall and monthly edge metrics.
    :type edge_metrics: polars.DataFrame
    :param nodes: Phase 1 node identifier/name mapping.
    :type nodes: polars.DataFrame
    :param edges: Phase 1 overall service-aware directed edges.
    :type edges: polars.DataFrame
    :param construction_metadata: Optional original construction metadata for
        cross-checking topology counts.
    :type construction_metadata: dict[str, Any] | None
    :param top_n: Number of stations/routes per ranking and service.
    :type top_n: int
    :returns: Descriptive tables and provenance metadata.
    :rtype: DescriptiveResult
    :raises TypeError: If any input is not a Polars DataFrame.
    :raises ValueError: If required fields are absent or top_n is invalid.
    """
    frames = (research_data, node_metrics, edge_metrics, nodes, edges)
    if any(not isinstance(frame, pl.DataFrame) for frame in frames):
        raise TypeError("all tabular inputs must be Polars DataFrames")
    if top_n < 1:
        raise ValueError("top_n must be positive")
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
                    f"construction metadata topology mismatch for {row['service']}"
                )

    overall_nodes = node_metrics.filter(pl.col("period") == "overall")
    overall_edges = edge_metrics.filter(pl.col("period") == "overall")
    node_metric_summary = _stats_by_group(overall_nodes, "service", NODE_METRICS)
    ranking_frames: list[pl.DataFrame] = []
    for service in sorted(overall_nodes["service"].unique().to_list()):
        for metric, label in (
            ("degree", "connectivity_degree"),
            ("betweenness_centrality", "betweenness_centrality"),
            ("pagerank", "pagerank"),
        ):
            ranking = (
                overall_nodes.filter(pl.col("service") == service)
                .sort(metric, descending=True)
                .head(top_n)
                .select(
                    pl.lit(service).alias("service"),
                    pl.lit(label).alias("ranking_metric"),
                    "node_id",
                    "station_name",
                    pl.col(metric).cast(pl.Float64).alias("value"),
                )
                .with_row_index("rank", offset=1)
            )
            ranking_frames.append(ranking)
    node_rankings = pl.concat(ranking_frames) if ranking_frames else pl.DataFrame()
    edge_rankings = (
        overall_edges.join(nodes, left_on="source", right_on="node_id", how="left")
        .rename({"station_name": "origin_name"})
        .join(nodes, left_on="target", right_on="node_id", how="left")
        .rename({"station_name": "destination_name"})
        .sort("edge_betweenness", descending=True)
        .group_by("service", maintain_order=True)
        .head(top_n)
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
        "monthly_graph_count": monthly_summary.height,
        "metric_columns": {"node": list(NODE_METRICS), "edge": ["edge_betweenness"]},
        "outlier_definition": "Tukey 1.5*IQR, descriptive only; observations are not removed.",
        "limitations": [
            "OD liaisons are not necessarily train itineraries or physical track segments.",
            "Centrality is not passenger traffic, train frequency, or delay propagation.",
            "Overall graph metrics are separate from monthly metrics and outcomes.",
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
    """Maintain the generated descriptive passage in the unified report.

    Human-authored material outside the marked passage is retained so later
    research can extend the report without being overwritten on regeneration.
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
    )
    stations = result.node_rankings.select(
        pl.col("service").alias("Service"),
        pl.when(pl.col("ranking_metric") == "connectivity_degree")
        .then(pl.lit("Degré total"))
        .when(pl.col("ranking_metric") == "betweenness_centrality")
        .then(pl.lit("Intermédiarité"))
        .otherwise(pl.lit("PageRank"))
        .alias("Mesure"),
        pl.col("rank").alias("Rang"),
        pl.col("station_name").alias("Gare"),
        pl.col("value").alias("Valeur"),
    )
    liaisons = result.edge_rankings.select(
        pl.col("service").alias("Service"),
        pl.col("origin_name").alias("Gare d’origine"),
        pl.col("destination_name").alias("Gare de destination"),
        pl.col("edge_betweenness").alias("Intermédiarité de la liaison"),
    )
    outcome_rows = []
    for row in result.operational_summary.to_dicts():
        for label, stem in (
            (
                "Retard moyen, tous les trains (min)",
                "retard_moyen_tous_trains_arrivee",
            ),
            ("Retard moyen des trains retardés (min)", "retard_moyen_arrivee"),
            ("Taux d’annulation (part)", "cancellation_rate"),
        ):
            outcome_rows.append(
                {
                    "Service": row["service"],
                    "Indicateur": label,
                    "N valide": row[f"{stem}_count"],
                    "N manquant": row[f"{stem}_missing"],
                    "Moyenne (données complètes)": row[f"{stem}_mean"],
                    "Médiane": row[f"{stem}_median"],
                    "Minimum": row[f"{stem}_min"],
                    "Maximum": row[f"{stem}_max"],
                }
            )
    outcomes = pl.DataFrame(outcome_rows)
    display_counts = result.metadata.get("operational_chart_counts", {})
    primary_by_service = display_counts.get("primary_below_minus_15_by_service", {})
    delayed_by_service = display_counts.get("delayed_above_120_by_service", {})
    cancellation_above_zoom = display_counts.get("cancellation_above_010")
    cancellation_missing = display_counts.get("cancellation_missing")
    ranges = (
        result.monthly_summary.group_by("service")
        .agg(
            pl.col("node_count").min().alias("min_gare"),
            pl.col("node_count").max().alias("max_gare"),
            pl.col("edge_count").min().alias("min_liaison"),
            pl.col("edge_count").max().alias("max_liaison"),
        )
        .sort("service")
    )
    monthly = result.monthly_summary.filter(
        (pl.col("service") == "International")
        & pl.col("period").str.starts_with("2025-")
    ).sort("period")
    changes: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for row in monthly.to_dicts():
        if previous and (
            row["node_count"] != previous["node_count"]
            or row["edge_count"] != previous["edge_count"]
        ):
            changes.append(
                {
                    "Mois": row["period"],
                    "Gares": row["node_count"],
                    "Liaisons dirigées": row["edge_count"],
                    "Écart de gares": row["node_count"] - previous["node_count"],
                    "Écart de liaisons": row["edge_count"] - previous["edge_count"],
                }
            )
        previous = row
    change_table = (
        pl.DataFrame(changes)
        if changes
        else pl.DataFrame(
            schema={
                "Mois": pl.String,
                "Gares": pl.Int64,
                "Liaisons dirigées": pl.Int64,
                "Écart de gares": pl.Int64,
                "Écart de liaisons": pl.Int64,
            }
        )
    )

    topology_text = ""
    for service in ("National", "International"):
        rows = result.network_summary.filter(pl.col("service") == service)
        if rows.height:
            row = rows.row(0, named=True)
            topology_text += (
                f"{service} : {row['node_count']} gares, {row['edge_count']} liaisons "
                f"et {row['weakly_connected_components']} composante(s) faiblement connexe(s). "
            )
    range_text = [
        f"- {row['service']} : {row['min_gare']}–{row['max_gare']} gares et "
        f"{row['min_liaison']}–{row['max_liaison']} liaisons dirigées observées par mois."
        for row in ranges.to_dicts()
    ]
    content = [
        "## Données et périmètre",
        "",
        f"L’analyse porte sur {result.metadata['observation_count']:,}".replace(
            ",", "\u202f"
        )
        + f" observations mensuelles, du {result.metadata['date_coverage']['min']} au {result.metadata['date_coverage']['max']}, pour les services {', '.join(result.metadata['services'])}. Les métriques de graphe préexistantes sont résumées sans être recalculées.",
        "",
        "## Structure des réseaux",
        "",
        "**Question.** Les réseaux observés présentent-ils la même couverture et la même cohésion selon le service?",
        "",
        f"![Réseau National]({image_dir}/network_national.png)",
        "",
        f"![Réseau International]({image_dir}/network_international.png)",
        "",
        _markdown_table(topology),
        "",
        f"**Observation.** {topology_text}",
        "",
        "**Interprétation.** Les composantes décrivent la connectivité des liaisons origine-destination observées. Elles ne signifient pas que les chemins du graphe sont des itinéraires réellement empruntés.",
        "",
        "**Limite.** Le graphe ne décrit ni l’infrastructure physique ni le volume de trains ou de voyageurs.",
        "",
        "## Degrés et centralité des gares",
        "",
        "**Question.** Comment se répartissent les degrés et les centralités, et quelles gares occupent les premiers rangs?",
        "",
        f"![Répartition des degrés]({image_dir}/degree_distributions.png)",
        "",
        f"![Distributions des centralités]({image_dir}/node_centrality_distributions.png)",
        "",
        f"![Classement des gares]({image_dir}/top10_station_rankings.png)",
        "",
        _markdown_table(stations),
        "",
        "**Observation.** Les degrés comptent des voisins distincts et les graphiques de degrés comparent des proportions. Les distributions de centralité distinguent l’intermédiarité du PageRank et indiquent la proportion de valeurs nulles.",
        "",
        "**Interprétation.** Un rang élevé correspond à une position topologique selon la mesure considérée; les mesures ne sont pas équivalentes.",
        "",
        "**Limite.** Ces indicateurs ne mesurent ni la fréquentation voyageurs ni l’importance commerciale d’une gare.",
        "",
        "## Intermédiarité des liaisons",
        "",
        "**Question.** Quelle est la distribution de la position des liaisons dans les plus courts chemins topologiques?",
        "",
        f"![Intermédiarité des liaisons]({image_dir}/edge_betweenness_distribution.png)",
        "",
        f"![Classement des liaisons]({image_dir}/top10_edge_rankings.png)",
        "",
        _markdown_table(liaisons),
        "",
        "**Observation.** La fonction de répartition empirique est accompagnée d’un histogramme; médiane et 90e percentile sont indiqués par service. Le tableau emploie les noms de gare plutôt que les identifiants machine.",
        "",
        "**Interprétation.** Une valeur élevée signale une position dans les plus courts chemins du graphe construit.",
        "",
        "**Limite.** L’intermédiarité ne représente ni le volume de trains, ni le nombre de passagers, ni l’utilisation physique de la liaison.",
        "",
        "## Évolution mensuelle",
        "",
        "**Question.** Comment évoluent la couverture du réseau et les maxima mensuels de centralité?",
        "",
        f"![Évolution mensuelle]({image_dir}/monthly_network_evolution.png)",
        "",
        "Étendues de la couverture mensuelle observée :",
        "",
        *range_text,
        "",
        "Changements de la topologie Internationale observés en 2025 par rapport au mois précédent :",
        "",
        _markdown_table(change_table)
        if changes
        else "Aucune variation du nombre de gares ou de liaisons n’est observée dans les mois disponibles de 2025.",
        "",
        "**Observation.** Le PageRank maximal et l’intermédiarité maximale sont des maxima mensuels, pas des moyennes. Les annotations 2025 donnent les comptages réellement observés aux mois où ils changent.",
        "",
        "**Interprétation.** Ces évolutions décrivent la couverture topologique des données mensuelles; elles ne démontrent pas une évolution opérationnelle.",
        "",
        "**Limite.** Un maximum peut dépendre d’une seule gare. Les axes ne sont pas resserrés manuellement pour amplifier les variations.",
        "",
        "## Indicateurs opérationnels : description",
        "",
        "**Question.** Quelles distributions présentent les retards moyens et le taux d’annulation observés?",
        "",
        f"![Indicateurs opérationnels]({image_dir}/operational_outcome_distributions.png)",
        "",
        "**Note de visualisation.** L’histogramme central du retard de tous les trains omet les observations signalées sous −15 min; celui des trains retardés sépare les valeurs supérieures à 120 min dans un panneau de queue. Le zoom des taux d’annulation est limité à 0–0,10, tandis que le panneau complet conserve toute la plage valide. Ces choix ne modifient que l’affichage; les valeurs restent dans le jeu de données.",
        (
            f"Les annotations indiquent les effectifs omis des vues centrales (tous trains : {sum(primary_by_service.values())}; trains retardés : {sum(delayed_by_service.values())}) et les taux au-dessus de 0,10 hors du zoom ({cancellation_above_zoom}). Les {cancellation_missing} taux manquants restent manquants."
            if primary_by_service and delayed_by_service
            else "Les effectifs omis des vues centrales, les valeurs hors du zoom et les valeurs manquantes sont indiqués directement sur la figure."
        ),
        "",
        "Le tableau présente des statistiques calculées sur toutes les observations valides, y compris les valeurs absentes des histogrammes centraux.",
        "",
        _markdown_table(outcomes),
        "",
        "**Observation.** Les retards négatifs sont conservés. Les taux d’annulation manquants demeurent manquants et ne sont pas convertis en zéro.",
        "",
        "**Interprétation.** Ces statistiques décrivent les résultats opérationnels par service sans évaluer leur relation aux métriques de graphe.",
        "",
        "**Limite.** Les agrégats liaison-mois ne suffisent pas à attribuer une cause aux retards ou aux annulations.",
        "",
        "## Portée et limites générales",
        "",
        "Aucun test d’association ou modèle explicatif n’est présenté ici. Les constats descriptifs n’établissent ni association ni causalité. Les chemins calculés sur les liaisons OD observées ne représentent pas nécessairement des itinéraires de trains; les centralités ne mesurent ni les flux de voyageurs ni la propagation des retards.",
        "",
    ]
    replacement = "\n".join(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = (
            "# Rapport de recherche — Réseau TGV et régularité\n\n"
            "Ce rapport rassemble les résultats de recherche et sera enrichi au fil du projet. "
            "Le contenu ajouté hors de la section générée est conservé lors des mises à jour.\n\n"
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
    """Summarize existing research and graph artifacts, writing tables/report.

    :param research_data_path: Phase 2 research Parquet path.
    :type research_data_path: str | os.PathLike[str]
    :param node_metrics_path: Existing Phase 1 node metric Parquet path.
    :type node_metrics_path: str | os.PathLike[str]
    :param edge_metrics_path: Existing Phase 1 edge metric Parquet path.
    :type edge_metrics_path: str | os.PathLike[str]
    :param nodes_path: Existing node mapping Parquet path.
    :type nodes_path: str | os.PathLike[str]
    :param edges_path: Existing overall edge Parquet path.
    :type edges_path: str | os.PathLike[str]
    :param construction_metadata_path: Existing construction metadata JSON path.
    :type construction_metadata_path: str | os.PathLike[str]
    :param output_dir: Destination directory for descriptive Parquet tables.
    :type output_dir: str | os.PathLike[str]
    :param report_path: Destination Markdown report path.
    :type report_path: str | os.PathLike[str]
    :param top_n: Number of ranked stations/routes to retain per service.
    :type top_n: int
    :returns: Descriptive tables, metadata, and output paths.
    :rtype: DescriptiveResult
    :raises OSError: If inputs cannot be read or outputs cannot be written.
    :raises ValueError: If schemas, metadata counts, or top_n are invalid.
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
