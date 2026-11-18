"""Construct and export service-aware monthly SNCF route graphs."""

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
_INTERPRETATION_WARNING = (
    "A liaison is an observed origin-destination pair, not necessarily a physical "
    "adjacent railway segment, a consecutive train leg, or a confirmed train "
    "connection. Graph adjacency does not establish train movement or delay propagation."
)


@dataclass
class GraphConstructionResult:
    """Structured output from graph construction.

    :ivar nodes: One row per station with deterministic node identifiers.
    :ivar edges: One row per unique service-aware directed edge.
    :ivar edge_observations: Original monthly records with graph identifiers.
    :ivar excluded_records: Input rows excluded from graph construction and their reasons.
    :ivar graph: Combined directed multigraph, with service-aware edge keys.
    :ivar service_graphs: Overall directed topology for each observed service.
    :ivar metadata: Machine-readable construction metadata.
    :ivar output_paths: Paths written by :func:`export_graph_artifacts`.
    """

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
        raise TypeError("data must be a Polars DataFrame")
    missing = [column for column in GRAPH_KEY_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required graph key columns: {', '.join(missing)}")
    non_string = [
        column for column in GRAPH_KEY_COLUMNS if data.schema[column] != pl.String
    ]
    if non_string:
        raise TypeError(
            "Graph key columns must use Polars String dtype: " + ", ".join(non_string)
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
    """Build deterministic nodes, edges, observations, and NetworkX graphs.

    Invalid graph keys are explicitly recorded in ``excluded_records``. If a
    graph business key occurs more than once, every row in that duplicate group
    is excluded so no source row is chosen arbitrarily. Operational values and
    diagnostic flags do not determine graph-key eligibility.

    :param data: Processed SNCF records. The input is never modified.
    :type data: polars.DataFrame
    :param source_dataset_path: Source path recorded in metadata, or
        ``"<in-memory>"`` when the input has no file source.
    :type source_dataset_path: str | os.PathLike[str]
    :returns: Tables, reusable directed graphs, exclusions, and metadata.
    :rtype: GraphConstructionResult
    :raises TypeError: If ``data`` is not a Polars DataFrame or graph key
        columns are not strings.
    :raises ValueError: If required graph key columns are absent.
    """
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
        "graph_directionality": "directed; combined graph is a MultiDiGraph keyed by edge_id",
        "node_identity_definition": "Exact original station label (gare_depart/gare_arrivee)",
        "edge_identity_definition": "(service, origin station label, destination station label)",
        "identifier_generation_strategy": (
            "First 24 hexadecimal characters of SHA-256 over compact UTF-8 JSON identity tuples; "
            "node IDs use node_<digest>, edge IDs use edge_<digest>."
        ),
        "construction_configuration": {
            "input_rows_with_duplicate_business_keys": "exclude every row in duplicate groups",
            "empty_key_policy": "reject whitespace-only key values; preserve all retained source values",
            "operational_measurement_policy": "preserve nulls, values, and diagnostic flags unchanged",
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
    """Reconstruct a service-specific directed graph for one month.

    :param observations: Monthly edge observations from a construction result or
        the exported ``edge_observations.parquet`` file.
    :type observations: polars.DataFrame
    :param service: Exact service category to select.
    :type service: str
    :param month: Reporting month in ``YYYY-MM`` format.
    :type month: str
    :returns: Directed graph with station labels and original observation
        attributes on each edge.
    :rtype: networkx.DiGraph
    :raises TypeError: If observations is not a Polars DataFrame.
    :raises ValueError: If required columns are missing or the month is invalid.
    """
    if not isinstance(observations, pl.DataFrame):
        raise TypeError("observations must be a Polars DataFrame")
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
        raise ValueError("Missing observation columns: " + ", ".join(missing))
    if not _DATE_PATTERN.fullmatch(month):
        raise ValueError("month must be a valid YYYY-MM calendar month")
    try:
        calendar_date.fromisoformat(f"{month}-01")
    except ValueError as exc:
        raise ValueError("month must be a valid YYYY-MM calendar month") from exc
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
        "# SNCF Graph Construction Report",
        "",
        "## Dataset overview",
        "",
        f"- Source: `{metadata['source_dataset_path']}`",
        f"- Source rows: {metadata['source_row_count']:,}",
        f"- Valid monthly observations: {metadata['valid_monthly_observation_count']:,}",
        f"- Excluded rows: {metadata['excluded_record_count']:,}",
        f"- Excluded reasons: `{json.dumps(metadata['exclusion_reasons_and_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Date coverage: {metadata['minimum_observation_month'] or 'n/a'} to {metadata['maximum_observation_month'] or 'n/a'} ({metadata['distinct_month_count']} distinct months)",
        f"- Services: {', '.join(metadata['service_categories']) or 'none'}",
        f"- Stations: {metadata['node_count']:,}",
        f"- Service-aware directed edges: {metadata['service_aware_edge_count']:,}",
        f"- Monthly observations: {metadata['monthly_observation_count']:,}",
        "",
        "## Network structure diagnostics by service",
        "",
        "All counts refer to each service-specific observed topology. Isolated nodes are zero where a service graph has edges because nodes are introduced from its observed edges.",
        "",
        "| Service | Nodes | Edges | Isolated | Self-loops | Weak components | Strong components | Largest weak component | Multiple incoming | Multiple outgoing |",
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
        "## Temporal diagnostics",
        "",
        f"- Distinct observed months: {temporal['distinct_months']}",
        f"- Gaps in overall monthly coverage: {', '.join(temporal['missing_months']) or 'none'}",
        "",
        "| Month | Observations | Unique edges | New edges vs previous month | No longer observed vs previous month |",
        "|---|---:|---:|---:|---:|",
    ]
    for month, count in temporal["observations_per_month"].items():
        coverage = temporal["edge_coverage_changes"][month]
        lines.append(
            f"| {month} | {count} | {temporal['unique_edges_per_month'][month]} | {coverage['new_edges']} | {coverage['no_longer_observed']} |"
        )
    lines += [
        "",
        "## Data-quality diagnostics",
        "",
        f"- Duplicate business-key records: {metadata['duplicate_business_key_record_count']}",
        f"- Exclusion counts by reason: `{json.dumps(metadata['exclusion_reasons_and_counts'], ensure_ascii=False, sort_keys=True)}`",
        "- Existing diagnostic flags set in the source (these observations remain included when graph keys are valid):",
    ]
    if metadata["flagged_record_counts_in_source"]:
        lines.extend(
            f"  - `{column}`: {count:,}"
            for column, count in metadata["flagged_record_counts_in_source"].items()
        )
    else:
        lines.append("  - No recognized diagnostic flag columns were present.")
    lines += [
        "",
        "## Interpretation and warnings",
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
    """Write the graph tables, metadata JSON, and Markdown report.

    :param result: Structured graph construction output to export.
    :type result: GraphConstructionResult
    :param output_dir: Directory for the three Parquet artifacts and metadata.
    :type output_dir: str | os.PathLike[str]
    :param report_path: Destination for the human-readable Markdown report.
    :type report_path: str | os.PathLike[str]
    :returns: The same result, with ``output_paths`` populated.
    :rtype: GraphConstructionResult
    :raises TypeError: If ``result`` has an unsupported type.
    :raises OSError: If an output directory or artifact cannot be written.
    :raises ValueError: If metadata cannot be serialized as JSON.
    """
    if not isinstance(result, GraphConstructionResult):
        raise TypeError("result must be a GraphConstructionResult")
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
    """Read processed Parquet data and run the complete graph export pipeline.

    :param input_path: Processed SNCF Parquet input path.
    :type input_path: str | os.PathLike[str]
    :param output_dir: Directory for graph Parquet tables and metadata JSON.
    :type output_dir: str | os.PathLike[str]
    :param report_path: Construction report destination.
    :type report_path: str | os.PathLike[str]
    :returns: Graph tables, graph objects, metadata, diagnostics, and output paths.
    :rtype: GraphConstructionResult
    :raises OSError: If the input cannot be read or outputs cannot be written.
    :raises TypeError: If graph key columns have unsupported types.
    :raises ValueError: If graph key columns are missing.
    """
    source_path = Path(input_path)
    data = pl.read_parquet(source_path)
    result = construct_graph_data(data, source_dataset_path=source_path)
    return export_graph_artifacts(
        result, output_dir=output_dir, report_path=report_path
    )
