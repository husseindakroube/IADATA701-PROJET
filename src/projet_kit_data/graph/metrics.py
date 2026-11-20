"""Calculer les métriques structurelles globales et mensuelles des graphes orientés."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import polars as pl

from projet_kit_data.graph.construction import DEFAULT_OUTPUT_DIR

DEFAULT_NODES_PATH = DEFAULT_OUTPUT_DIR / "nodes.parquet"
DEFAULT_EDGES_PATH = DEFAULT_OUTPUT_DIR / "edges.parquet"
DEFAULT_OBSERVATIONS_PATH = DEFAULT_OUTPUT_DIR / "edge_observations.parquet"
DEFAULT_REPORT_PATH = Path("data/reports/graph/metrics_report.md")
DEFAULT_ALPHA = 0.85
DEFAULT_TOL = 1e-6
DEFAULT_MAX_ITER = 1000
NODE_METRIC_NAMES = (
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
_NODE_SCHEMA = {
    "period": pl.String,
    "service": pl.String,
    "node_id": pl.String,
    "station_name": pl.String,
    "in_degree": pl.UInt32,
    "out_degree": pl.UInt32,
    "degree": pl.UInt32,
    "in_degree_centrality": pl.Float64,
    "out_degree_centrality": pl.Float64,
    "betweenness_centrality": pl.Float64,
    "in_closeness": pl.Float64,
    "out_closeness": pl.Float64,
    "pagerank": pl.Float64,
}
_EDGE_SCHEMA: dict[str, pl.DataType] = {
    "period": pl.String,
    "service": pl.String,
    "edge_id": pl.String,
    "source": pl.String,
    "target": pl.String,
    "edge_betweenness": pl.Float64,
}
for _endpoint in ("source", "target"):
    for _name in NODE_METRIC_NAMES:
        _EDGE_SCHEMA[f"{_endpoint}_{_name}"] = (
            pl.UInt32 if _name in {"in_degree", "out_degree", "degree"} else pl.Float64
        )


@dataclass
class GraphMetricsResult:
    """Tables et diagnostics produits par le pipeline de métriques du graphe.

    :ivar node_metrics: Enregistrements des métriques de nœud globales et mensuelles.
    :ivar edge_metrics: Enregistrements des métriques d’arête globales et mensuelles.
    :ivar metadata: Configuration, schémas d’entrée/sortie et échecs des métriques.
    :ivar output_paths: Chemins écrits par :func:`run_graph_metrics_pipeline`.
    """

    node_metrics: pl.DataFrame
    edge_metrics: pl.DataFrame
    metadata: dict[str, Any]
    output_paths: dict[str, Path] = field(default_factory=dict)


def _validate_artifacts(
    nodes: pl.DataFrame, edges: pl.DataFrame, observations: pl.DataFrame
) -> None:
    requirements = {
        "nodes": ({"node_id", "station_name"}, nodes),
        "edges": ({"edge_id", "service", "source", "target"}, edges),
        "observations": (
            {"edge_id", "date", "service", "source", "target"},
            observations,
        ),
    }
    for label, (required, frame) in requirements.items():
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(
                f"L’artefact {label} ne contient pas les colonnes suivantes : {', '.join(missing)}"
            )
    for label, frame, columns in (
        ("nodes", nodes, ("node_id", "station_name")),
        ("edges", edges, ("edge_id", "service", "source", "target")),
        (
            "observations",
            observations,
            ("edge_id", "date", "service", "source", "target"),
        ),
    ):
        wrong = [column for column in columns if frame.schema[column] != pl.String]
        if wrong:
            raise TypeError(
                f"Les colonnes de clé de l’artefact {label} doivent être de type String : {', '.join(wrong)}"
            )
    if nodes.get_column("node_id").n_unique() != nodes.height:
        raise ValueError("L’artefact nodes contient des valeurs node_id en double")
    if edges.get_column("edge_id").n_unique() != edges.height:
        raise ValueError("L’artefact edges contient des valeurs edge_id en double")
    if (
        edges.select(pl.struct("service", "source", "target").n_unique()).item()
        != edges.height
    ):
        raise ValueError(
            "L’artefact edges contient des identités service/source/target en double"
        )
    if (
        observations.select(
            pl.struct("date", "service", "gare_depart", "gare_arrivee").n_unique()
        ).item()
        != observations.height
    ):
        raise ValueError(
            "Les observations d’arêtes contiennent des clés métier mensuelles en double"
        )
    node_ids = set(nodes.get_column("node_id").to_list())
    if not set(edges.get_column("source").to_list()).issubset(node_ids) or not set(
        edges.get_column("target").to_list()
    ).issubset(node_ids):
        raise ValueError(
            "L’artefact edges fait référence à des identifiants de nœuds absents "
            "de l’artefact nodes"
        )
    edge_ids = set(edges.get_column("edge_id").to_list())
    if not set(observations.get_column("edge_id").to_list()).issubset(edge_ids):
        raise ValueError(
            "Les observations font référence à des identifiants d’arêtes absents "
            "de l’artefact edges"
        )
    edge_pairs = {
        (row["edge_id"], row["service"], row["source"], row["target"])
        for row in edges.iter_rows(named=True)
    }
    if any(
        (row["edge_id"], row["service"], row["source"], row["target"]) not in edge_pairs
        for row in observations.iter_rows(named=True)
    ):
        raise ValueError(
            "Les observations mensuelles ne correspondent pas aux identités des arêtes"
        )


def _calculate_graph_metrics(
    edge_rows: list[dict[str, str]],
    station_names: dict[str, str],
    service: str,
    period: str,
    alpha: float,
    max_iter: int,
    tol: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    graph = nx.DiGraph()
    for edge in edge_rows:
        graph.add_edge(edge["source"], edge["target"], edge_id=edge["edge_id"])
    n_nodes, n_edges = graph.number_of_nodes(), graph.number_of_edges()
    if not n_edges:
        return [], [], None
    in_degree = dict(graph.in_degree())
    out_degree = dict(graph.out_degree())
    denom = n_nodes - 1
    node_values: dict[str, dict[str, Any]] = {}
    betweenness = nx.betweenness_centrality(graph, normalized=True, weight=None)
    in_close = nx.closeness_centrality(graph, distance=None, wf_improved=True)
    out_close = nx.closeness_centrality(
        graph.reverse(copy=False), distance=None, wf_improved=True
    )
    pagerank_error: dict[str, Any] | None = None
    try:
        pagerank = nx.pagerank(
            graph, alpha=alpha, max_iter=max_iter, tol=tol, weight=None
        )
    except nx.PowerIterationFailedConvergence as exc:
        pagerank = {node: None for node in graph}
        pagerank_error = {
            "service": service,
            "period": period,
            "alpha": alpha,
            "max_iter": max_iter,
            "tol": tol,
            "error": str(exc),
        }
    for node in graph:
        node_values[node] = {
            "in_degree": in_degree[node],
            "out_degree": out_degree[node],
            "degree": in_degree[node] + out_degree[node],
            "in_degree_centrality": in_degree[node] / denom if denom > 0 else 0.0,
            "out_degree_centrality": out_degree[node] / denom if denom > 0 else 0.0,
            "betweenness_centrality": betweenness[node],
            "in_closeness": in_close[node],
            "out_closeness": out_close[node],
            "pagerank": pagerank[node],
        }
    node_rows = [
        {
            "period": period,
            "service": service,
            "node_id": node,
            "station_name": station_names[node],
            **metrics,
        }
        for node, metrics in node_values.items()
    ]
    edge_betweenness = nx.edge_betweenness_centrality(
        graph, normalized=True, weight=None
    )
    edge_output = []
    for edge in edge_rows:
        source, target = edge["source"], edge["target"]
        edge_output.append(
            {
                "period": period,
                "service": service,
                "edge_id": edge["edge_id"],
                "source": source,
                "target": target,
                "edge_betweenness": edge_betweenness[(source, target)],
                **{
                    f"source_{name}": value
                    for name, value in node_values[source].items()
                },
                **{
                    f"target_{name}": value
                    for name, value in node_values[target].items()
                },
            }
        )
    return node_rows, edge_output, pagerank_error


def _distribution(frame: pl.DataFrame, column: str) -> dict[str, float | None]:
    if frame.is_empty():
        return {"mean": None, "std": None, "min": None, "median": None, "max": None}
    result = frame.select(
        pl.col(column).mean().alias("mean"),
        pl.col(column).std().alias("std"),
        pl.col(column).min().alias("min"),
        pl.col(column).median().alias("median"),
        pl.col(column).max().alias("max"),
    ).row(0, named=True)
    return {key: value for key, value in result.items()}


def _top_rows(
    frame: pl.DataFrame, metric: str, limit: int = 10
) -> list[dict[str, Any]]:
    return (
        frame.filter(pl.col(metric).is_not_null())
        .sort(metric, descending=True)
        .head(limit)
        .to_dicts()
    )


def _build_report(result: GraphMetricsResult) -> str:
    metadata = result.metadata
    lines = [
        "# Rapport des métriques du graphe",
        "",
        "## Entrées et couverture des calculs",
        "",
        f"- Artefact des nœuds : `{metadata['source_paths']['nodes']}` ({metadata['source_row_counts']['nodes']:,} lignes)",
        f"- Artefact des arêtes : `{metadata['source_paths']['edges']}` ({metadata['source_row_counts']['edges']:,} lignes)",
        f"- Observations mensuelles : `{metadata['source_paths']['observations']}` ({metadata['source_row_counts']['observations']:,} lignes)",
        f"- Services : {', '.join(metadata['services'])}",
        f"- Graphes globaux : {metadata['overall_graph_count']} ; graphes mensuels : {metadata['monthly_graph_count']}",
        f"- Lignes de métriques produites : {result.node_metrics.height:,} pour les nœuds ; {result.edge_metrics.height:,} pour les arêtes",
        "",
        "## Synthèse des graphes globaux par service",
        "",
        "| Service | Nœuds | Arêtes | Degré moyen | PageRank maximal | Betweenness maximal |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for service in metadata["services"]:
        rows = result.node_metrics.filter(
            (pl.col("period") == "overall") & (pl.col("service") == service)
        )
        edge_count = result.edge_metrics.filter(
            (pl.col("period") == "overall") & (pl.col("service") == service)
        ).height
        lines.append(
            f"| {service} | {rows.height} | {edge_count} | {rows['degree'].mean() if rows.height else 0:.4f} | {rows['pagerank'].max() if rows.height and rows['pagerank'].null_count() < rows.height else 'N/D'} | {rows['betweenness_centrality'].max() if rows.height else 'N/D'} |"
        )
    lines += ["", "## Top 10 des gares par service — graphe global", ""]
    for metric in ("in_degree", "out_degree", "betweenness_centrality", "pagerank"):
        lines.extend(
            [f"### {metric}", "", "| Service | Gare | Valeur |", "|---|---|---:|"]
        )
        for service in metadata["services"]:
            for row in _top_rows(
                result.node_metrics.filter(
                    (pl.col("period") == "overall") & (pl.col("service") == service)
                ),
                metric,
            ):
                lines.append(
                    f"| {row['service']} | {row['station_name']} | {row[metric] if row[metric] is not None else 'N/D'} |"
                )
        lines.append("")
    lines += [
        "## Top 10 des arêtes par edge betweenness — graphe global",
        "",
        "| Service | Origine | Destination | Valeur |",
        "|---|---|---|---:|",
    ]
    for service in metadata["services"]:
        for row in _top_rows(
            result.edge_metrics.filter(
                (pl.col("period") == "overall") & (pl.col("service") == service)
            ),
            "edge_betweenness",
        ):
            lines.append(
                f"| {row['service']} | {row['source']} | {row['target']} | {row['edge_betweenness']:.6g} |"
            )
    lines += ["", "## Distributions des métriques", ""]
    for metric in NODE_METRIC_NAMES:
        distribution = metadata["distributions"]["node"][metric]
        ordered_distribution = {
            key: distribution[key] for key in ("mean", "std", "min", "median", "max")
        }
        lines.append(f"- Nœuds du graphe global, `{metric}` : `{ordered_distribution}`")
    edge_distribution = metadata["distributions"]["edge"]["edge_betweenness"]
    ordered_edge_distribution = {
        key: edge_distribution[key] for key in ("mean", "std", "min", "median", "max")
    }
    lines.append(
        f"- Arêtes du graphe global, `edge_betweenness` : `{ordered_edge_distribution}`"
    )
    lines += [
        "",
        "## Évolution mensuelle par service",
        "",
        "| Mois | Service | Nœuds | Arêtes | Degré moyen | PageRank maximal | Betweenness maximal |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in metadata["monthly_graphs"]:
        nodes = result.node_metrics.filter(
            (pl.col("period") == item["period"])
            & (pl.col("service") == item["service"])
        )
        edges = result.edge_metrics.filter(
            (pl.col("period") == item["period"])
            & (pl.col("service") == item["service"])
        )
        max_pr = (
            nodes["pagerank"].max()
            if nodes.height and nodes["pagerank"].null_count() < nodes.height
            else None
        )
        lines.append(
            f"| {item['period']} | {item['service']} | {nodes.height} | {edges.height} | {nodes['degree'].mean() if nodes.height else 0:.4f} | {max_pr if max_pr is not None else 'N/D'} | {nodes['betweenness_centrality'].max() if nodes.height else 'N/D'} |"
        )
    lines += ["", "## Convergence de PageRank et avertissements", ""]
    if metadata["pagerank_convergence_failures"]:
        lines.extend(
            f"- `{failure}`" for failure in metadata["pagerank_convergence_failures"]
        )
    else:
        lines.append(
            "- PageRank a convergé pour chaque graphe calculé par service et période."
        )
    lines += [
        "- En cas de non-convergence, le PageRank est manquant (valeur `None`) pour les nœuds du graphe concerné ; il n’est pas remplacé par zéro.",
        "",
        "## Limites d’interprétation",
        "",
        "- Les métriques sont non pondérées et décrivent les plus courts chemins dans la topologie origine-destination observée ; elles ne représentent ni des itinéraires réels de trains ni des segments physiques de voie.",
        "- Degree compte les liaisons observées distinctes, et non la fréquence des trains ; la centralité ne mesure ni le nombre de voyageurs, ni l’importance opérationnelle, ni la propagation des retards.",
        "- Les valeurs globales résument l’union des arêtes observées sur la période ; les valeurs mensuelles sont calculées séparément à partir des observations du mois correspondant.",
        "- Les services National et International sont calculés séparément.",
        "",
    ]
    return "\n".join(lines)


def run_graph_metrics_pipeline(
    nodes_path: str | os.PathLike[str] = DEFAULT_NODES_PATH,
    edges_path: str | os.PathLike[str] = DEFAULT_EDGES_PATH,
    observations_path: str | os.PathLike[str] = DEFAULT_OBSERVATIONS_PATH,
    output_dir: str | os.PathLike[str] = DEFAULT_OUTPUT_DIR,
    report_path: str | os.PathLike[str] = DEFAULT_REPORT_PATH,
    alpha: float = DEFAULT_ALPHA,
    max_iter: int = DEFAULT_MAX_ITER,
    tol: float = DEFAULT_TOL,
) -> GraphMetricsResult:
    """Calculer et exporter les métriques globales et mensuelles du graphe orienté.

    :param nodes_path: Chemin existant vers ``nodes.parquet`` issu de la construction.
    :type nodes_path: str | os.PathLike[str]
    :param edges_path: Chemin existant vers ``edges.parquet`` issu de la construction.
    :type edges_path: str | os.PathLike[str]
    :param observations_path: Chemin existant du fichier Parquet d’observations mensuelles.
    :type observations_path: str | os.PathLike[str]
    :param output_dir: Répertoire des tables Parquet de métriques et des métadonnées JSON.
    :type output_dir: str | os.PathLike[str]
    :param report_path: Destination du rapport Markdown.
    :type report_path: str | os.PathLike[str]
    :param alpha: Facteur d’amortissement du PageRank dans ``[0, 1]``.
    :type alpha: float
    :param max_iter: Nombre maximal d’itérations PageRank par graphe.
    :type max_iter: int
    :param tol: Tolérance de convergence du PageRank.
    :type tol: float
    :returns: Tables de métriques, métadonnées et chemins écrits.
    :rtype: GraphMetricsResult
    :raises OSError: Si les entrées ne peuvent pas être lues ou les sorties écrites.
    :raises TypeError: Si une entrée n’est pas une table Parquet compatible avec Polars.
    :raises ValueError: Si les paramètres, schémas d’artefacts, clés ou références sont invalides.
    """
    if not 0 <= alpha <= 1:
        raise ValueError("alpha doit être compris entre 0 et 1")
    if max_iter < 1:
        raise ValueError("max_iter doit être positif")
    if tol <= 0:
        raise ValueError("tol doit être positif")
    source_paths = {
        "nodes": Path(nodes_path),
        "edges": Path(edges_path),
        "observations": Path(observations_path),
    }
    nodes, edges, observations = (
        pl.read_parquet(path) for path in source_paths.values()
    )
    _validate_artifacts(nodes, edges, observations)
    name_by_node = dict(nodes.select("node_id", "station_name").iter_rows())
    node_rows: list[dict[str, Any]] = []
    edge_metric_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    services = sorted(edges.get_column("service").unique().to_list())
    overall_graphs: list[dict[str, Any]] = []
    for service in services:
        rows = (
            edges.filter(pl.col("service") == service)
            .select("edge_id", "source", "target")
            .to_dicts()
        )
        n_nodes = len(
            {value for row in rows for value in (row["source"], row["target"])}
        )
        node_values, edge_values, failure = _calculate_graph_metrics(
            rows, name_by_node, service, "overall", alpha, max_iter, tol
        )
        node_rows.extend(node_values)
        edge_metric_rows.extend(edge_values)
        if failure:
            failures.append(failure)
        overall_graphs.append(
            {"service": service, "nodes": n_nodes, "edges": len(rows)}
        )
    monthly_graphs: list[dict[str, Any]] = []
    groups = observations.partition_by(
        ["date", "service"], as_dict=True, maintain_order=False
    )
    for (date, service), frame in sorted(groups.items()):
        rows = frame.select("edge_id", "source", "target").to_dicts()
        period = str(date)
        n_nodes = len(
            {value for row in rows for value in (row["source"], row["target"])}
        )
        node_values, edge_values, failure = _calculate_graph_metrics(
            rows, name_by_node, str(service), period, alpha, max_iter, tol
        )
        node_rows.extend(node_values)
        edge_metric_rows.extend(edge_values)
        if failure:
            failures.append(failure)
        monthly_graphs.append(
            {
                "period": period,
                "service": str(service),
                "nodes": n_nodes,
                "edges": len(rows),
            }
        )
    node_metrics = pl.DataFrame(node_rows, schema=_NODE_SCHEMA)
    edge_metrics = pl.DataFrame(edge_metric_rows, schema=_EDGE_SCHEMA)
    node_key = ["period", "service", "node_id"]
    edge_key = ["period", "service", "edge_id"]
    if (
        node_metrics.select(pl.struct(node_key).n_unique()).item()
        != node_metrics.height
    ):
        raise ValueError(
            "Les métriques de nœuds calculées contiennent des clés en double"
        )
    if (
        edge_metrics.select(pl.struct(edge_key).n_unique()).item()
        != edge_metrics.height
    ):
        raise ValueError(
            "Les métriques d’arêtes calculées contiennent des clés en double"
        )
    metadata: dict[str, Any] = {
        "schema_version": "1.0",
        "source_paths": {key: str(value) for key, value in source_paths.items()},
        "source_row_counts": {
            "nodes": nodes.height,
            "edges": edges.height,
            "observations": observations.height,
        },
        "services": services,
        "overall_graph_count": len(overall_graphs),
        "overall_graphs": overall_graphs,
        "monthly_graph_count": len(monthly_graphs),
        "monthly_graphs": monthly_graphs,
        "observation_period": {
            "min": observations.get_column("date").min()
            if observations.height
            else None,
            "max": observations.get_column("date").max()
            if observations.height
            else None,
        },
        "graph_configuration": {
            "directed": True,
            "weighted": False,
            "self_loops_preserved": True,
        },
        "pagerank_parameters": {
            "alpha": alpha,
            "max_iter": max_iter,
            "tol": tol,
            "dangling": "valeur par défaut de NetworkX (redistribution uniforme)",
        },
        "pagerank_convergence_failures": failures,
        "metric_definitions": {
            "in_degree_centrality": "in_degree / (n_nodes - 1), ou 0 si n_nodes < 2",
            "out_degree_centrality": "out_degree / (n_nodes - 1), ou 0 si n_nodes < 2",
            "betweenness_centrality": "betweenness centrality normalisée de NetworkX pour les plus courts chemins orientés non pondérés",
            "in_closeness": "closeness orientée de NetworkX ; distances entrantes avec correction tenant compte des nœuds accessibles",
            "out_closeness": "closeness orientée de NetworkX sur le graphe inversé ; distances sortantes avec correction tenant compte des nœuds accessibles",
            "edge_betweenness": "edge betweenness normalisée de NetworkX pour les plus courts chemins orientés non pondérés",
        },
        "output_schemas": {
            "node_metrics": {key: str(value) for key, value in _NODE_SCHEMA.items()},
            "edge_metrics": {key: str(value) for key, value in _EDGE_SCHEMA.items()},
        },
        "unique_keys": {"node_metrics": node_key, "edge_metrics": edge_key},
        "software_versions": {"networkx": nx.__version__, "polars": pl.__version__},
        "warnings": [
            "Les chemins OD observés ne prouvent ni les itinéraires réels des trains ni une propagation des retards.",
            "Degree décrit la topologie des liaisons distinctes, pas la fréquence des trains ; PageRank ne mesure pas le flux de voyageurs.",
        ],
    }
    node_overall = node_metrics.filter(pl.col("period") == "overall")
    edge_overall = edge_metrics.filter(pl.col("period") == "overall")
    metadata["distributions"] = {
        "node": {
            metric: _distribution(node_overall, metric) for metric in NODE_METRIC_NAMES
        },
        "edge": {"edge_betweenness": _distribution(edge_overall, "edge_betweenness")},
    }
    destination = Path(output_dir)
    report_destination = Path(report_path)
    destination.mkdir(parents=True, exist_ok=True)
    report_destination.parent.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "node_metrics": destination / "node_metrics.parquet",
        "edge_metrics": destination / "edge_metrics.parquet",
        "metadata": destination / "metrics_metadata.json",
        "report": report_destination,
    }
    node_metrics.write_parquet(output_paths["node_metrics"])
    edge_metrics.write_parquet(output_paths["edge_metrics"])
    output_paths["metadata"].write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = GraphMetricsResult(node_metrics, edge_metrics, metadata, output_paths)
    output_paths["report"].write_text(_build_report(result), encoding="utf-8")
    return result
