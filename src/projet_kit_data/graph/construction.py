"Construit et exporte les graphes mensuels de liaisons SNCF en distinguant les services."

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date as calendar_date
from pathlib import Path
from typing import Any

import networkx as nx
import polars as pl

DEFAULT_INPUT_PATH = Path("data/processed/sncf.parquet")
DEFAULT_OUTPUT_DIR = Path("data/processed/graph")
DEFAULT_REPORT_PATH = Path("data/reports/graph/construction_report.md")
GRAPH_KEY_COLUMNS = ("date", "service", "gare_depart", "gare_arrivee")
FLAG_COLUMNS = (
    "flag_negative_count",
    "flag_sup30_lt_sup60",
    "flag_sup15_lt_sup30",
    "flag_cancellations_gt_planned",
)
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}$")
_INTERPRETATION_WARNING = "Une liaison est une paire origine-destination observée, pas nécessairement un tronçon physique adjacent, une étape consécutive ou une correspondance confirmée. L’adjacence ne prouve ni mouvement réel ni propagation des retards."


@dataclass
class GraphConstructionResult:
    """Résultat structuré de construction du graphe.

    :ivar nodes: Une ligne par gare avec identifiant déterministe.
    :ivar edges: Une ligne par arête orientée unique et par service.
    :ivar edge_observations: Observations mensuelles d’origine avec identifiants du graphe.
    :ivar excluded_records: Lignes exclues de la construction et motifs associés.
    :ivar graph: Multigraphe orienté combiné avec clés d’arêtes distinguant les services.
    :ivar service_graphs: Topologie orientée globale de chaque service observé.
    :ivar metadata: Métadonnées structurées de construction.
    :ivar output_paths: Chemins écrits par :func:`export_graph_artifacts`."""

    nodes: pl.DataFrame
    edges: pl.DataFrame
    edge_observations: pl.DataFrame
    excluded_records: pl.DataFrame
    graph: nx.MultiDiGraph
    service_graphs: dict[str, nx.DiGraph]
    metadata: dict[str, Any]
    output_paths: dict[str, Path] = field(default_factory=dict)


def _stable_id(prefix: str, identity: tuple[str, ...]) -> str:
    payload = json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:24]}"


def _month_sequence(first: str, last: str) -> list[str]:
    start_year, start_month = map(int, first.split("-"))
    end_year, end_month = map(int, last.split("-"))
    months: list[str] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return months


def _validate_input(data: pl.DataFrame) -> None:
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data doit être un DataFrame Polars")
    missing = [column for column in GRAPH_KEY_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(
            f"Colonnes de clé du graphe requises absentes : {', '.join(missing)}"
        )
    non_string = [
        column for column in GRAPH_KEY_COLUMNS if data.schema[column] != pl.String
    ]
    if non_string:
        raise TypeError(
            "Les colonnes de clé du graphe doivent utiliser le type String de Polars : "
            + ", ".join(non_string)
        )


def _network_diagnostics(graphs: dict[str, nx.DiGraph]) -> dict[str, dict[str, int]]:
    diagnostics: dict[str, dict[str, int]] = {}
    for service, graph in sorted(graphs.items()):
        components = list(nx.weakly_connected_components(graph))
        diagnostics[service] = {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "isolated_nodes": len(list(nx.isolates(graph))),
            "self_loops": nx.number_of_selfloops(graph),
            "weakly_connected_components": len(components),
            "strongly_connected_components": nx.number_strongly_connected_components(
                graph
            ),
            "largest_weak_component": max(map(len, components), default=0),
            "nodes_multiple_incoming": sum(
                degree > 1 for _, degree in graph.in_degree()
            ),
            "nodes_multiple_outgoing": sum(
                degree > 1 for _, degree in graph.out_degree()
            ),
        }
    return diagnostics


def _temporal_diagnostics(observations: pl.DataFrame) -> dict[str, Any]:
    if observations.is_empty():
        return {
            "distinct_months": 0,
            "observations_per_month": {},
            "unique_edges_per_month": {},
            "edge_coverage_changes": {},
            "missing_months": [],
        }
    monthly = (
        observations.group_by("date")
        .agg(
            pl.len().alias("observations"),
            pl.col("edge_id").n_unique().alias("unique_edges"),
        )
        .sort("date")
    )
    months = monthly.get_column("date").to_list()
    observations_by_month = dict(
        zip(months, monthly.get_column("observations").to_list(), strict=True)
    )
    edges_by_month = dict(
        zip(months, monthly.get_column("unique_edges").to_list(), strict=True)
    )
    coverage_changes: dict[str, dict[str, int | None]] = {}
    previous: set[str] | None = None
    for month in months:
        current = set(
            observations.filter(pl.col("date") == month).get_column("edge_id").to_list()
        )
        coverage_changes[month] = {
            "new_edges": len(current) if previous is None else len(current - previous),
            "no_longer_observed": 0 if previous is None else len(previous - current),
        }
        previous = current
    all_months = _month_sequence(months[0], months[-1])
    return {
        "distinct_months": len(months),
        "observations_per_month": observations_by_month,
        "unique_edges_per_month": edges_by_month,
        "edge_coverage_changes": coverage_changes,
        "missing_months": [
            month for month in all_months if month not in observations_by_month
        ],
    }


def construct_graph_data(
    data: pl.DataFrame,
    source_dataset_path: str | os.PathLike[str] = "<in-memory>",
) -> GraphConstructionResult:
    """Construit des nœuds, arêtes, observations et graphes NetworkX déterministes.

    Les clés invalides sont enregistrées dans ``excluded_records``. Toutes les lignes
    d’un groupe de clés métier dupliquées sont exclues pour éviter un choix arbitraire.
    Les mesures opérationnelles et indicateurs qualité ne déterminent pas
    l’admissibilité des clés du graphe.

    :param data: Observations SNCF traitées ; l’entrée n’est jamais modifiée.
    :type data: polars.DataFrame
    :param source_dataset_path: Source inscrite dans les métadonnées ; ``"<in-memory>"`` sans fichier source.
    :type source_dataset_path: str | os.PathLike[str]
    :returns: Tables, graphes orientés réutilisables, exclusions et métadonnées.
    :rtype: GraphConstructionResult
    :raises TypeError: Si ``data`` n’est pas un DataFrame Polars ou si les clés ne sont pas des chaînes.
    :raises ValueError: Si une colonne de clé requise est absente."""
    _validate_input(data)
    rows = data.to_dicts()
    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    for row_index, row in enumerate(rows):
        reason: str | None = None
        for column in GRAPH_KEY_COLUMNS:
            value = row[column]
            if value is None:
                reason = f"missing_{column}"
                break
            if not value.strip():
                reason = f"empty_{column}"
                break
        if reason is None:
            month = row["date"]
            if not _DATE_PATTERN.fullmatch(month):
                reason = "invalid_date_format"
            else:
                try:
                    calendar_date.fromisoformat(f"{month}-01")
                except ValueError:
                    reason = "invalid_date_value"
        if reason:
            excluded.append(
                {**row, "_row_index": row_index, "exclusion_reason": reason}
            )
            reason_counts[reason] += 1
        else:
            eligible.append({**row, "_row_index": row_index})

    key_counts = Counter(
        (row["date"], row["service"], row["gare_depart"], row["gare_arrivee"])
        for row in eligible
    )
    duplicate_keys = {key for key, count in key_counts.items() if count > 1}
    retained: list[dict[str, Any]] = []
    duplicate_count = 0
    for row in eligible:
        key = (row["date"], row["service"], row["gare_depart"], row["gare_arrivee"])
        if key in duplicate_keys:
            excluded.append(
                {
                    **{col: row[col] for col in data.columns},
                    "_row_index": row["_row_index"],
                    "exclusion_reason": "duplicate_business_key",
                }
            )
            duplicate_count += 1
        else:
            retained.append(row)
    if duplicate_count:
        reason_counts["duplicate_business_key"] = duplicate_count

    station_names = sorted(
        {row[column] for row in retained for column in ("gare_depart", "gare_arrivee")}
    )
    node_ids = {name: _stable_id("node", (name,)) for name in station_names}
    station_by_node_id = {node_id: name for name, node_id in node_ids.items()}
    nodes = pl.DataFrame(
        {
            "node_id": [node_ids[name] for name in station_names],
            "station_name": station_names,
        },
        schema={"node_id": pl.String, "station_name": pl.String},
    )
    edge_id_by_identity: dict[tuple[str, str, str], str] = {}
    edge_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in retained:
        identity = (
            row["service"],
            node_ids[row["gare_depart"]],
            node_ids[row["gare_arrivee"]],
        )
        edge_groups.setdefault(identity, []).append(row)
        edge_id_by_identity[identity] = _stable_id("edge", identity)

    edge_rows: list[dict[str, Any]] = []
    for (service, source, target), group in sorted(edge_groups.items()):
        observed_dates = sorted({row["date"] for row in group})
        edge_rows.append(
            {
                "edge_id": edge_id_by_identity[(service, source, target)],
                "service": service,
                "source": source,
                "target": target,
                "n_months_observed": len(observed_dates),
                "first_date": observed_dates[0],
                "last_date": observed_dates[-1],
            }
        )
    edges = pl.DataFrame(
        edge_rows,
        schema={
            "edge_id": pl.String,
            "service": pl.String,
            "source": pl.String,
            "target": pl.String,
            "n_months_observed": pl.UInt32,
            "first_date": pl.String,
            "last_date": pl.String,
        },
    )
    observation_rows: list[dict[str, Any]] = []
    for row in retained:
        identity = (
            row["service"],
            node_ids[row["gare_depart"]],
            node_ids[row["gare_arrivee"]],
        )
        observation_rows.append(
            {
                "edge_id": edge_id_by_identity[identity],
                "date": row["date"],
                "service": row["service"],
                "source": identity[1],
                "target": identity[2],
                **{column: row[column] for column in data.columns},
            }
        )
    observation_schema: dict[str, pl.DataType] = {
        "edge_id": pl.String,
        "date": pl.String,
        "service": pl.String,
        "source": pl.String,
        "target": pl.String,
        **data.schema,
    }
    edge_observations = pl.DataFrame(observation_rows, schema=observation_schema)
    excluded_schema = {
        **data.schema,
        "_row_index": pl.UInt32,
        "exclusion_reason": pl.String,
    }
    excluded_frame = pl.DataFrame(excluded, schema=excluded_schema)

    graph = nx.MultiDiGraph()
    for row in nodes.iter_rows(named=True):
        graph.add_node(row["node_id"], station_name=row["station_name"])
    service_graphs: dict[str, nx.DiGraph] = {}
    for edge in edge_rows:
        attrs = {
            "edge_id": edge["edge_id"],
            "service": edge["service"],
            "n_months_observed": edge["n_months_observed"],
            "first_date": edge["first_date"],
            "last_date": edge["last_date"],
        }
        graph.add_edge(edge["source"], edge["target"], key=edge["edge_id"], **attrs)
        service_graph = service_graphs.setdefault(edge["service"], nx.DiGraph())
        service_graph.add_node(
            edge["source"], station_name=station_by_node_id[edge["source"]]
        )
        service_graph.add_node(
            edge["target"], station_name=station_by_node_id[edge["target"]]
        )
        service_graph.add_edge(edge["source"], edge["target"], **attrs)

    temporal = _temporal_diagnostics(edge_observations)
    network = _network_diagnostics(service_graphs)
    flag_counts: dict[str, int] = {}
    for column in FLAG_COLUMNS:
        if column in data.columns:
            flag_counts[column] = data.filter(
                pl.col(column).eq(True).fill_null(False)
            ).height
    valid_dates = edge_observations.get_column("date").to_list()
    metadata: dict[str, Any] = {
        "artifact_schema_version": "1.0",
        "source_dataset_path": str(source_dataset_path),
        "source_row_count": data.height,
        "valid_monthly_observation_count": edge_observations.height,
        "excluded_record_count": excluded_frame.height,
        "exclusion_reasons_and_counts": dict(sorted(reason_counts.items())),
        "duplicate_business_key_record_count": duplicate_count,
        "node_count": nodes.height,
        "service_aware_edge_count": edges.height,
        "monthly_observation_count": edge_observations.height,
        "service_categories": sorted(edges.get_column("service").unique().to_list())
        if edges.height
        else [],
        "minimum_observation_month": min(valid_dates) if valid_dates else None,
        "maximum_observation_month": max(valid_dates) if valid_dates else None,
        "distinct_month_count": temporal["distinct_months"],
        "graph_directionality": "orienté ; le graphe combiné est un MultiDiGraph indexé par edge_id",
        "node_identity_definition": "Libellé exact de la gare source (gare_depart/gare_arrivee)",
        "edge_identity_definition": "(service, libellé de la gare de départ, libellé de la gare d’arrivée)",
        "identifier_generation_strategy": (
            "24 premiers caractères hexadécimaux du SHA-256 des tuples d’identité JSON UTF-8 compacts ; identifiants node_<digest> et edge_<digest>."
        ),
        "construction_configuration": {
            "input_rows_with_duplicate_business_keys": "exclure toutes les lignes des groupes dupliqués",
            "empty_key_policy": "refuser les clés composées uniquement d’espaces ; préserver toutes les valeurs sources retenues",
            "operational_measurement_policy": "conserver les valeurs nulles, valeurs et indicateurs de diagnostic inchangés",
        },
        "exclusion_reasons": dict(sorted(reason_counts.items())),
        "duplicate_business_key_records": duplicate_count,
        "flagged_record_counts_in_source": flag_counts,
        "temporal_diagnostics": temporal,
        "network_diagnostics_by_service": network,
        "warnings": [_INTERPRETATION_WARNING],
    }
    return GraphConstructionResult(
        nodes, edges, edge_observations, excluded_frame, graph, service_graphs, metadata
    )


def reconstruct_monthly_graph(
    observations: pl.DataFrame,
    service: str,
    month: str,
) -> nx.DiGraph:
    """Reconstruit le graphe orienté d’un service pour un mois.

    :param observations: Observations mensuelles issues de la construction ou du fichier ``edge_observations.parquet``.
    :type observations: polars.DataFrame
    :param service: Libellé exact du service à sélectionner.
    :type service: str
    :param month: Mois au format ``YYYY-MM``.
    :type month: str
    :returns: Graphe orienté avec noms des gares et attributs d’origine sur les arêtes.
    :rtype: networkx.DiGraph
    :raises TypeError: Si observations n’est pas un DataFrame Polars.
    :raises ValueError: Si des colonnes requises manquent ou si le mois est invalide."""
    if not isinstance(observations, pl.DataFrame):
        raise TypeError("observations doit être un DataFrame Polars")
    required = {
        "edge_id",
        "date",
        "service",
        "source",
        "target",
        "gare_depart",
        "gare_arrivee",
    }
    missing = sorted(required.difference(observations.columns))
    if missing:
        raise ValueError("Colonnes d’observation absentes : " + ", ".join(missing))
    if not _DATE_PATTERN.fullmatch(month):
        raise ValueError("month doit être un mois calendaire valide au format YYYY-MM")
    try:
        calendar_date.fromisoformat(f"{month}-01")
    except ValueError as exc:
        raise ValueError(
            "month doit être un mois calendaire valide au format YYYY-MM"
        ) from exc
    selected = observations.filter(
        (pl.col("service") == service) & (pl.col("date") == month)
    )
    graph = nx.DiGraph()
    for row in selected.iter_rows(named=True):
        graph.add_node(row["source"], station_name=row["gare_depart"])
        graph.add_node(row["target"], station_name=row["gare_arrivee"])
        graph.add_edge(
            row["source"],
            row["target"],
            **{
                key: value
                for key, value in row.items()
                if key not in {"source", "target"}
            },
        )
    return graph


def _render_report(result: GraphConstructionResult) -> str:
    metadata = result.metadata
    temporal = metadata["temporal_diagnostics"]
    lines = [
        "# Rapport de construction des graphes SNCF",
        "",
        "## Aperçu du jeu de données",
        "",
        f"- Source: `{metadata['source_dataset_path']}`",
        f"- Lignes sources : {metadata['source_row_count']:,}",
        f"- Observations mensuelles valides : {metadata['valid_monthly_observation_count']:,}",
        f"- Lignes exclues : {metadata['excluded_record_count']:,}",
        f"- Motifs d’exclusion : `{json.dumps(metadata['exclusion_reasons_and_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Couverture temporelle : {metadata['minimum_observation_month'] or 'n/a'} to {metadata['maximum_observation_month'] or 'n/a'} ({metadata['distinct_month_count']} mois distincts)",
        f"- Services: {', '.join(metadata['service_categories']) or 'none'}",
        f"- Gares : {metadata['node_count']:,}",
        f"- Arêtes orientées distinguées par service : {metadata['service_aware_edge_count']:,}",
        f"- Observations mensuelles : {metadata['monthly_observation_count']:,}",
        "",
        "## Diagnostics structurels du réseau par service",
        "",
        "Les effectifs décrivent la topologie observée de chaque service. Aucun nœud n’est isolé lorsqu’il existe des arêtes, car les nœuds proviennent des arêtes observées.",
        "",
        "| Service | Nœuds | Arêtes | Isolés | Boucles | Composantes faibles | Composantes fortes | Plus grande composante faible | Entrées multiples | Sorties multiples |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for service, values in metadata["network_diagnostics_by_service"].items():
        lines.append(
            "| {service} | {nodes} | {edges} | {isolated_nodes} | {self_loops} | {weakly_connected_components} | {strongly_connected_components} | {largest_weak_component} | {nodes_multiple_incoming} | {nodes_multiple_outgoing} |".format(
                service=service, **values
            )
        )
    lines += [
        "",
        "## Diagnostics temporels",
        "",
        f"- Mois distincts observés : {temporal['distinct_months']}",
        f"- Lacunes de couverture mensuelle globale : {', '.join(temporal['missing_months']) or 'none'}",
        "",
        "| Mois | Observations | Arêtes uniques | Nouvelles arêtes depuis le mois précédent | Arêtes non observées depuis le mois précédent |",
        "|---|---:|---:|---:|---:|",
    ]
    for month, count in temporal["observations_per_month"].items():
        coverage = temporal["edge_coverage_changes"][month]
        lines.append(
            f"| {month} | {count} | {temporal['unique_edges_per_month'][month]} | {coverage['new_edges']} | {coverage['no_longer_observed']} |"
        )
    lines += [
        "",
        "## Diagnostics de qualité des données",
        "",
        f"- Observations à clé métier dupliquée : {metadata['duplicate_business_key_record_count']}",
        f"- Effectifs exclus par motif : `{json.dumps(metadata['exclusion_reasons_and_counts'], ensure_ascii=False, sort_keys=True)}`",
        "- Indicateurs de diagnostic actifs dans la source ; observations conservées si les clés du graphe sont valides :",
    ]
    if metadata["flagged_record_counts_in_source"]:
        lines.extend(
            f"  - `{column}`: {count:,}"
            for column, count in metadata["flagged_record_counts_in_source"].items()
        )
    else:
        lines.append("  - Aucune colonne d’indicateur reconnue n’était présente.")
    lines += [
        "",
        "## Interprétation et avertissements",
        "",
        f"- {_INTERPRETATION_WARNING}",
        "",
    ]
    return "\n".join(lines)


def export_graph_artifacts(
    result: GraphConstructionResult,
    output_dir: str | os.PathLike[str] = DEFAULT_OUTPUT_DIR,
    report_path: str | os.PathLike[str] = DEFAULT_REPORT_PATH,
) -> GraphConstructionResult:
    """Écrit les tables du graphe, les métadonnées JSON et le rapport Markdown.

    :param result: Résultat structuré de construction à exporter.
    :type result: GraphConstructionResult
    :param output_dir: Dossier des trois tables Parquet et des métadonnées.
    :type output_dir: str | os.PathLike[str]
    :param report_path: Destination du rapport Markdown lisible.
    :type report_path: str | os.PathLike[str]
    :returns: Même résultat avec ``output_paths`` renseigné.
    :rtype: GraphConstructionResult
    :raises TypeError: Si ``result`` a un type incompatible.
    :raises OSError: Si un dossier ou fichier de sortie ne peut pas être écrit.
    :raises ValueError: Si les métadonnées ne sont pas sérialisables en JSON."""
    if not isinstance(result, GraphConstructionResult):
        raise TypeError("result doit être un GraphConstructionResult")
    destination = Path(output_dir)
    report_destination = Path(report_path)
    destination.mkdir(parents=True, exist_ok=True)
    report_destination.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "nodes": destination / "nodes.parquet",
        "edges": destination / "edges.parquet",
        "edge_observations": destination / "edge_observations.parquet",
        "metadata": destination / "graph_metadata.json",
        "report": report_destination,
    }
    result.nodes.write_parquet(paths["nodes"])
    result.edges.write_parquet(paths["edges"])
    result.edge_observations.write_parquet(paths["edge_observations"])
    paths["metadata"].write_text(
        json.dumps(result.metadata, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.output_paths = paths
    return result


def run_graph_construction_pipeline(
    input_path: str | os.PathLike[str] = DEFAULT_INPUT_PATH,
    output_dir: str | os.PathLike[str] = DEFAULT_OUTPUT_DIR,
    report_path: str | os.PathLike[str] = DEFAULT_REPORT_PATH,
) -> GraphConstructionResult:
    """Lit les données Parquet traitées et exécute la chaîne complète d’export du graphe.

    :param input_path: Chemin du fichier Parquet SNCF traité en entrée.
    :type input_path: str | os.PathLike[str]
    :param output_dir: Dossier des tables Parquet du graphe et des métadonnées JSON.
    :type output_dir: str | os.PathLike[str]
    :param report_path: Destination du rapport de construction.
    :type report_path: str | os.PathLike[str]
    :returns: Tables, objets de graphe, métadonnées, diagnostics et chemins de sortie.
    :rtype: GraphConstructionResult
    :raises OSError: Si l’entrée ne peut pas être lue ou les sorties écrites.
    :raises TypeError: Si les colonnes de clé du graphe ont des types incompatibles.
    :raises ValueError: Si les colonnes de clé du graphe sont absentes.
    """
    source_path = Path(input_path)
    data = pl.read_parquet(source_path)
    result = construct_graph_data(data, source_dataset_path=source_path)
    return export_graph_artifacts(
        result, output_dir=output_dir, report_path=report_path
    )
