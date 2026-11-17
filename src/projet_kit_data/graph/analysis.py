"""Prepare monthly liaison-level data for later research analysis."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

GRAPH_DATA_DIR = Path("data/processed/graph")
DEFAULT_OBSERVATIONS_PATH = GRAPH_DATA_DIR / "edge_observations.parquet"
DEFAULT_EDGE_METRICS_PATH = GRAPH_DATA_DIR / "edge_metrics.parquet"
DEFAULT_NODE_METRICS_PATH = GRAPH_DATA_DIR / "node_metrics.parquet"
DEFAULT_OUTPUT_PATH = Path("data/processed/research_dataset.parquet")
DEFAULT_METADATA_PATH = Path("data/processed/research_dataset_metadata.json")
DEFAULT_REPORT_PATH = Path("data/reports/graph/research_data_quality_report.md")
BUSINESS_KEY = ("date", "service", "gare_depart", "gare_arrivee")
_PRIMARY_DELAY = "retard_moyen_tous_trains_arrivee"
_EXTREME_DELAY_FLAG = "flag_primary_arrival_delay_below_minus_15"


@dataclass
class ResearchDataResult:
    """Prepared research table and its quality metadata.

    :ivar data: One row per original monthly service-liaison observation.
    :ivar metadata: Input, join, coverage, and quality statistics.
    :ivar output_paths: Paths written by the file-based pipeline.
    """

    data: pl.DataFrame
    metadata: dict[str, Any]
    output_paths: dict[str, Path] = field(default_factory=dict)


def _require_columns(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def _assert_unique(frame: pl.DataFrame, keys: tuple[str, ...], label: str) -> None:
    if frame.select(pl.struct(list(keys)).n_unique()).item() != frame.height:
        raise ValueError(f"{label} contains duplicate key values for {keys}")


def _monthly_node_metrics(node_metrics: pl.DataFrame, endpoint: str) -> pl.DataFrame:
    monthly = node_metrics.filter(pl.col("period") != "overall")
    fields = [
        column
        for column in monthly.columns
        if column not in {"period", "service", "node_id", "station_name"}
    ]
    return monthly.select(
        pl.col("period").alias("date"),
        "service",
        pl.col("node_id").alias(endpoint),
        *[pl.col(column).alias(f"{endpoint}_{column}") for column in fields],
    )


def prepare_research_dataset(
    observations: pl.DataFrame,
    edge_metrics: pl.DataFrame,
    node_metrics: pl.DataFrame,
) -> ResearchDataResult:
    """Join monthly operation records to matching monthly graph metrics.

    The function preserves every input observation and its original values. It
    uses only monthly graph metrics; ``period="overall"`` rows are excluded.
    Cancellation rate is calculated only when planned trains are positive and
    the cancellation count is nonnegative and no greater than the planned
    count. Invalid cases retain their counts, have a null rate, and receive a
    diagnostic reason.

    :param observations: Existing construction monthly edge observations.
    :type observations: polars.DataFrame
    :param edge_metrics: Overall and monthly edge metrics from Phase 1.
    :type edge_metrics: polars.DataFrame
    :param node_metrics: Overall and monthly node metrics from Phase 1.
    :type node_metrics: polars.DataFrame
    :returns: Research data and machine-readable quality/join metadata.
    :rtype: ResearchDataResult
    :raises TypeError: If any input is not a Polars DataFrame.
    :raises ValueError: If inputs have invalid schemas, duplicate keys, or
        inconsistent graph edge identities.
    """
    frames = (observations, edge_metrics, node_metrics)
    if any(not isinstance(frame, pl.DataFrame) for frame in frames):
        raise TypeError(
            "observations, edge_metrics, and node_metrics must be Polars DataFrames"
        )
    _require_columns(
        observations,
        set(BUSINESS_KEY)
        | {
            "edge_id",
            "source",
            "target",
            "nb_train_prevu",
            "nb_annulation",
            _PRIMARY_DELAY,
        },
        "observations",
    )
    _require_columns(
        edge_metrics,
        {"period", "service", "edge_id", "source", "target", "edge_betweenness"},
        "edge_metrics",
    )
    _require_columns(
        node_metrics,
        {
            "period",
            "service",
            "node_id",
            "in_degree",
            "out_degree",
            "degree",
            "in_degree_centrality",
            "out_degree_centrality",
            "betweenness_centrality",
            "in_closeness",
            "out_closeness",
            "pagerank",
        },
        "node_metrics",
    )
    if observations.schema["date"] != pl.String:
        raise TypeError("observations.date must use Polars String dtype")
    _assert_unique(observations, BUSINESS_KEY, "observations")
    _assert_unique(edge_metrics, ("period", "service", "edge_id"), "edge_metrics")
    _assert_unique(node_metrics, ("period", "service", "node_id"), "node_metrics")

    source_count = observations.height
    monthly_edges = edge_metrics.filter(pl.col("period") != "overall").select(
        "period", "service", "edge_id", "source", "target", "edge_betweenness"
    )
    monthly_edges = monthly_edges.rename({"period": "date"})
    edge_matches = observations.select(
        "date", "service", "edge_id", "source", "target"
    ).join(
        monthly_edges.select("date", "service", "edge_id", "source", "target"),
        on=["date", "service", "edge_id"],
        how="left",
        suffix="_metric",
        validate="m:1",
    )
    if edge_matches.height != source_count:
        raise ValueError("edge metric join changed the observation row count")
    edge_mismatch = edge_matches.filter(
        (pl.col("source") != pl.col("source_metric"))
        | (pl.col("target") != pl.col("target_metric"))
    ).height
    if edge_mismatch:
        raise ValueError(
            f"{edge_mismatch} edge metric rows disagree on directed endpoints"
        )

    prepared = observations.join(
        monthly_edges.select("date", "service", "edge_id", "edge_betweenness"),
        on=["date", "service", "edge_id"],
        how="left",
        validate="m:1",
    )
    if prepared.height != source_count:
        raise ValueError("edge metrics join changed the observation row count")
    source_metrics = _monthly_node_metrics(node_metrics, "source")
    target_metrics = _monthly_node_metrics(node_metrics, "target")
    prepared = prepared.join(
        source_metrics, on=["date", "service", "source"], how="left", validate="m:1"
    )
    if prepared.height != source_count:
        raise ValueError("source node metrics join changed the observation row count")
    prepared = prepared.join(
        target_metrics, on=["date", "service", "target"], how="left", validate="m:1"
    )
    if prepared.height != source_count:
        raise ValueError("target node metrics join changed the observation row count")

    planned = pl.col("nb_train_prevu")
    cancelled = pl.col("nb_annulation")
    rate_valid = (
        planned.is_not_null()
        & cancelled.is_not_null()
        & (planned > 0)
        & (cancelled >= 0)
        & (cancelled <= planned)
    )
    reason = (
        pl.when(planned.is_null())
        .then(pl.lit("missing_planned_count"))
        .when(cancelled.is_null())
        .then(pl.lit("missing_cancellation_count"))
        .when(planned <= 0)
        .then(pl.lit("planned_count_not_positive"))
        .when(cancelled < 0)
        .then(pl.lit("negative_cancellation_count"))
        .when(cancelled > planned)
        .then(pl.lit("cancellations_exceed_planned"))
        .otherwise(None)
    )
    if _EXTREME_DELAY_FLAG not in prepared.columns:
        prepared = prepared.with_columns(
            (pl.col(_PRIMARY_DELAY).is_not_null() & (pl.col(_PRIMARY_DELAY) < -15))
            .fill_null(False)
            .alias(_EXTREME_DELAY_FLAG)
        )
    prepared = prepared.with_columns(
        pl.when(rate_valid)
        .then(cancelled.cast(pl.Float64) / planned.cast(pl.Float64))
        .otherwise(None)
        .cast(pl.Float64)
        .alias("cancellation_rate"),
        rate_valid.fill_null(False).alias("cancellation_rate_valid"),
        reason.alias("cancellation_rate_invalid_reason"),
    )
    _assert_unique(prepared, BUSINESS_KEY, "prepared research dataset")
    if prepared.height != source_count:
        raise ValueError("research preparation did not preserve every observation")

    metric_columns = [
        column
        for column in prepared.columns
        if column == "edge_betweenness" or column.startswith(("source_", "target_"))
    ]
    missing_metrics = {
        column: prepared.get_column(column).null_count() for column in metric_columns
    }
    reason_counts = (
        prepared.group_by("cancellation_rate_invalid_reason")
        .len()
        .filter(pl.col("cancellation_rate_invalid_reason").is_not_null())
        .sort("cancellation_rate_invalid_reason")
        .to_dicts()
    )
    flag_counts = {
        column: prepared.filter(pl.col(column).fill_null(False)).height
        for column in prepared.columns
        if column.startswith("flag_") and prepared.schema[column] == pl.Boolean
    }
    metadata: dict[str, Any] = {
        "schema_version": "1.0",
        "dataset_grain": list(BUSINESS_KEY),
        "input_row_counts": {
            "observations": observations.height,
            "monthly_edge_metrics": monthly_edges.height,
            "all_node_metrics": node_metrics.height,
        },
        "output_row_count": prepared.height,
        "output_column_count": prepared.width,
        "date_coverage": {
            "min": prepared.get_column("date").min() if prepared.height else None,
            "max": prepared.get_column("date").max() if prepared.height else None,
        },
        "services": sorted(prepared.get_column("service").unique().to_list()),
        "input_artifacts": {},
        "join_keys": {
            "edge_metrics": ["date=period", "service", "edge_id"],
            "source_node_metrics": ["date=period", "service", "source=node_id"],
            "target_node_metrics": ["date=period", "service", "target=node_id"],
        },
        "join_validation": {
            "observation_business_key_unique": True,
            "edge_metrics_unique_key": True,
            "node_metrics_unique_key": True,
            "edge_metric_endpoint_mismatches": 0,
            "output_business_key_unique": True,
            "row_count_after_each_join": source_count,
            "overall_metrics_excluded": True,
        },
        "derived_variables": {
            "cancellation_rate": "nb_annulation / nb_train_prevu only when planned > 0 and 0 <= cancellations <= planned",
            "cancellation_rate_valid": "Boolean validity of cancellation_rate denominator/numerator rule",
            "cancellation_rate_invalid_reason": "Null when rate is valid; otherwise a reason code",
            _EXTREME_DELAY_FLAG: f"{_PRIMARY_DELAY} < -15 minutes; original outcome is preserved",
            "arrival_delay_rate": "not calculated; denominator is not established",
        },
        "cancellation_rate_valid_count": prepared.filter(
            pl.col("cancellation_rate_valid")
        ).height,
        "cancellation_rate_null_count": prepared.get_column(
            "cancellation_rate"
        ).null_count(),
        "cancellation_rate_invalid_reasons": reason_counts,
        "negative_primary_outcome_count": prepared.filter(
            pl.col(_PRIMARY_DELAY) < 0
        ).height,
        "extreme_negative_primary_outcome_count": prepared.filter(
            pl.col(_EXTREME_DELAY_FLAG)
        ).height,
        "missing_graph_metrics": missing_metrics,
        "quality_flag_true_counts": flag_counts,
        "output_schema": {
            column: str(dtype) for column, dtype in prepared.schema.items()
        },
        "warnings": [
            "The primary delay outcome is preserved, including negative values; flagged values are not excluded.",
            "Graph metrics are structural topology measures and do not establish train itineraries or delay propagation.",
            "No arrival_delay_rate is calculated because its denominator is not established.",
        ],
    }
    return ResearchDataResult(prepared, metadata)


def _quality_report(result: ResearchDataResult) -> str:
    metadata = result.metadata
    lines = [
        "# Research Dataset Quality Report",
        "",
        f"- Input observation rows: {metadata['input_row_counts']['observations']:,}",
        f"- Input monthly edge metric rows: {metadata['input_row_counts']['monthly_edge_metrics']:,}",
        f"- Input node metric rows (including overall): {metadata['input_row_counts']['all_node_metrics']:,}",
        f"- Output rows: {metadata['output_row_count']:,}",
        f"- Output columns: {metadata['output_column_count']:,}",
        f"- Date coverage: {metadata['date_coverage']['min']} to {metadata['date_coverage']['max']}",
        f"- Services: {', '.join(metadata['services'])}",
        f"- Unique business key `{tuple(BUSINESS_KEY)}`: {metadata['join_validation']['output_business_key_unique']}",
        f"- Overall graph metrics excluded: {metadata['join_validation']['overall_metrics_excluded']}",
        f"- Row count preserved after every join: {metadata['join_validation']['row_count_after_each_join'] == metadata['output_row_count']}",
        f"- Edge endpoint mismatches: {metadata['join_validation']['edge_metric_endpoint_mismatches']}",
        "",
        "## Cancellation rate validity",
        "",
        f"- Valid rates: {metadata['cancellation_rate_valid_count']:,}",
        f"- Null rates: {metadata['cancellation_rate_null_count']:,}",
        f"- Invalid reasons: `{json.dumps(metadata['cancellation_rate_invalid_reasons'], ensure_ascii=False)}`",
        "",
        "## Primary arrival delay",
        "",
        f"- Negative values (preserved): {metadata['negative_primary_outcome_count']:,}",
        f"- Values below -15 minutes (flagged and preserved): {metadata['extreme_negative_primary_outcome_count']:,}",
        "",
        "## Missing graph metrics",
        "",
    ]
    lines.extend(
        f"- `{column}`: {count:,}"
        for column, count in metadata["missing_graph_metrics"].items()
    )
    lines += ["", "## Quality flags", ""]
    lines.extend(
        f"- `{column}`: {count:,}"
        for column, count in metadata["quality_flag_true_counts"].items()
    )
    lines += ["", "## Output schema", "", "| Column | Polars dtype |", "|---|---|"]
    lines.extend(
        f"| `{column}` | {dtype} |"
        for column, dtype in metadata["output_schema"].items()
    )
    lines.append("")
    return "\n".join(lines)


def run_research_data_preparation_pipeline(
    observations_path: str | os.PathLike[str] = DEFAULT_OBSERVATIONS_PATH,
    edge_metrics_path: str | os.PathLike[str] = DEFAULT_EDGE_METRICS_PATH,
    node_metrics_path: str | os.PathLike[str] = DEFAULT_NODE_METRICS_PATH,
    output_path: str | os.PathLike[str] = DEFAULT_OUTPUT_PATH,
    metadata_path: str | os.PathLike[str] = DEFAULT_METADATA_PATH,
    report_path: str | os.PathLike[str] = DEFAULT_REPORT_PATH,
) -> ResearchDataResult:
    """Load Phase 1 artifacts, prepare the research dataset, and export outputs.

    :param observations_path: Monthly construction observation Parquet path.
    :type observations_path: str | os.PathLike[str]
    :param edge_metrics_path: Phase 1 edge metric Parquet path.
    :type edge_metrics_path: str | os.PathLike[str]
    :param node_metrics_path: Phase 1 node metric Parquet path.
    :type node_metrics_path: str | os.PathLike[str]
    :param output_path: Destination research dataset Parquet path.
    :type output_path: str | os.PathLike[str]
    :param metadata_path: Destination metadata JSON path.
    :type metadata_path: str | os.PathLike[str]
    :param report_path: Destination Markdown quality report path.
    :type report_path: str | os.PathLike[str]
    :returns: Prepared data, metadata, and generated artifact paths.
    :rtype: ResearchDataResult
    :raises OSError: If source artifacts cannot be read or outputs written.
    :raises TypeError: If required key columns use unsupported types.
    :raises ValueError: If schemas, keys, or join relationships are invalid.
    """
    input_paths = {
        "observations": Path(observations_path),
        "edge_metrics": Path(edge_metrics_path),
        "node_metrics": Path(node_metrics_path),
    }
    result = prepare_research_dataset(
        pl.read_parquet(input_paths["observations"]),
        pl.read_parquet(input_paths["edge_metrics"]),
        pl.read_parquet(input_paths["node_metrics"]),
    )
    result.metadata["input_artifacts"] = {
        key: str(path) for key, path in input_paths.items()
    }
    destinations = {
        "research_dataset": Path(output_path),
        "metadata": Path(metadata_path),
        "quality_report": Path(report_path),
    }
    for destination in destinations.values():
        destination.parent.mkdir(parents=True, exist_ok=True)
    result.data.write_parquet(destinations["research_dataset"])
    destinations["metadata"].write_text(
        json.dumps(result.metadata, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    destinations["quality_report"].write_text(_quality_report(result), encoding="utf-8")
    result.output_paths = destinations
    return result
