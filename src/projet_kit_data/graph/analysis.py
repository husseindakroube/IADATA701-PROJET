'Prépare les données mensuelles par liaison pour les analyses de recherche ultérieures.'

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
    """Table de recherche préparée et métadonnées de qualité.
    
    :ivar data: Une ligne par observation mensuelle d’origine, service et liaison.
    :ivar metadata: Statistiques d’entrée, de jointure, de couverture et de qualité.
    :ivar output_paths: Chemins écrits par la chaîne de traitement des fichiers."""

    data: pl.DataFrame
    metadata: dict[str, Any]
    output_paths: dict[str, Path] = field(default_factory=dict)


def _require_columns(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} ne contient pas les colonnes requises : {', '.join(missing)}")


def _assert_unique(frame: pl.DataFrame, keys: tuple[str, ...], label: str) -> None:
    if frame.select(pl.struct(list(keys)).n_unique()).item() != frame.height:
        raise ValueError(f"{label} contient des clés dupliquées pour {keys}")


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
    """Joint les observations opérationnelles aux métriques du graphe du même mois.
    
    Toutes les observations et valeurs sources sont conservées. Seules les métriques
    mensuelles sont utilisées ; les lignes ``period="overall"`` sont exclues. Le taux
    d’annulation est calculé si le nombre prévu est positif et si les annulations sont
    comprises entre zéro et ce nombre. Sinon, les comptages sont conservés, le taux
    reste nul et un motif de diagnostic est ajouté.
    
    :param observations: Observations mensuelles des arêtes issues de la construction.
    :type observations: polars.DataFrame
    :param edge_metrics: Métriques globales et mensuelles des arêtes de la phase 1.
    :type edge_metrics: polars.DataFrame
    :param node_metrics: Métriques globales et mensuelles des nœuds de la phase 1.
    :type node_metrics: polars.DataFrame
    :returns: Données de recherche et métadonnées structurées de qualité et de jointure.
    :rtype: ResearchDataResult
    :raises TypeError: Si une entrée n’est pas un DataFrame Polars.
    :raises ValueError: Si les schémas sont invalides, les clés dupliquées ou les identités des arêtes incohérentes."""
    frames = (observations, edge_metrics, node_metrics)
    if any(not isinstance(frame, pl.DataFrame) for frame in frames):
        raise TypeError(
            'observations, edge_metrics et node_metrics doivent être des DataFrames Polars'
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
        raise TypeError('observations.date doit utiliser le type String de Polars')
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
        raise ValueError('La jointure des métriques d’arêtes a modifié le nombre d’observations')
    edge_mismatch = edge_matches.filter(
        (pl.col("source") != pl.col("source_metric"))
        | (pl.col("target") != pl.col("target_metric"))
    ).height
    if edge_mismatch:
        raise ValueError(
            f"{edge_mismatch} lignes de métriques d’arêtes ont des extrémités orientées incohérentes"
        )

    prepared = observations.join(
        monthly_edges.select("date", "service", "edge_id", "edge_betweenness"),
        on=["date", "service", "edge_id"],
        how="left",
        validate="m:1",
    )
    if prepared.height != source_count:
        raise ValueError('La jointure des métriques d’arêtes a modifié le nombre d’observations')
    source_metrics = _monthly_node_metrics(node_metrics, "source")
    target_metrics = _monthly_node_metrics(node_metrics, "target")
    prepared = prepared.join(
        source_metrics, on=["date", "service", "source"], how="left", validate="m:1"
    )
    if prepared.height != source_count:
        raise ValueError('La jointure des nœuds de départ a modifié le nombre d’observations')
    prepared = prepared.join(
        target_metrics, on=["date", "service", "target"], how="left", validate="m:1"
    )
    if prepared.height != source_count:
        raise ValueError('La jointure des nœuds d’arrivée a modifié le nombre d’observations')

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
    _assert_unique(prepared, BUSINESS_KEY, 'jeu de recherche préparé')
    if prepared.height != source_count:
        raise ValueError('La préparation de recherche n’a pas conservé toutes les observations')

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
            "cancellation_rate": 'nb_annulation / nb_train_prevu uniquement si le nombre prévu est positif et les annulations comprises entre zéro et ce nombre',
            "cancellation_rate_valid": 'Validité booléenne de la règle du numérateur et du dénominateur de cancellation_rate',
            "cancellation_rate_invalid_reason": 'Valeur nulle si le taux est valide ; sinon code du motif',
            _EXTREME_DELAY_FLAG: f"{_PRIMARY_DELAY} < -15 minutes ; la valeur d’origine est conservée",
            "arrival_delay_rate": 'non calculé ; dénominateur non établi',
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
            'Le retard principal est conservé, y compris les valeurs négatives ; les valeurs signalées ne sont pas exclues.',
            'Les métriques décrivent la topologie ; elles ne prouvent ni itinéraires de trains ni propagation des retards.',
            'Aucun arrival_delay_rate n’est calculé car son dénominateur n’est pas établi.',
        ],
    }
    return ResearchDataResult(prepared, metadata)


def _quality_report(result: ResearchDataResult) -> str:
    metadata = result.metadata
    lines = [
        '# Rapport qualité du jeu de recherche',
        "",
        f"- Observations en entrée : {metadata['input_row_counts']['observations']:,}",
        f"- Lignes de métriques mensuelles des arêtes en entrée : {metadata['input_row_counts']['monthly_edge_metrics']:,}",
        f"- Lignes de métriques des nœuds en entrée, globales comprises : {metadata['input_row_counts']['all_node_metrics']:,}",
        f"- Lignes en sortie : {metadata['output_row_count']:,}",
        f"- Colonnes en sortie : {metadata['output_column_count']:,}",
        f"- Couverture temporelle : {metadata['date_coverage']['min']} to {metadata['date_coverage']['max']}",
        f"- Services: {', '.join(metadata['services'])}",
        f"- Clé métier unique `{tuple(BUSINESS_KEY)}`: {metadata['join_validation']['output_business_key_unique']}",
        f"- Métriques globales exclues : {metadata['join_validation']['overall_metrics_excluded']}",
        f"- Effectif conservé après chaque jointure : {metadata['join_validation']['row_count_after_each_join'] == metadata['output_row_count']}",
        f"- Extrémités d’arêtes incohérentes : {metadata['join_validation']['edge_metric_endpoint_mismatches']}",
        "",
        '## Validité du taux d’annulation',
        "",
        f"- Taux valides : {metadata['cancellation_rate_valid_count']:,}",
        f"- Taux absents : {metadata['cancellation_rate_null_count']:,}",
        f"- Motifs d’invalidité : `{json.dumps(metadata['cancellation_rate_invalid_reasons'], ensure_ascii=False)}`",
        "",
        '## Retard principal à l’arrivée',
        "",
        f"- Valeurs négatives conservées : {metadata['negative_primary_outcome_count']:,}",
        f"- Valeurs sous -15 minutes, signalées et conservées : {metadata['extreme_negative_primary_outcome_count']:,}",
        "",
        '## Métriques de graphe manquantes',
        "",
    ]
    lines.extend(
        f"- `{column}`: {count:,}"
        for column, count in metadata["missing_graph_metrics"].items()
    )
    lines += ["", '## Indicateurs qualité', ""]
    lines.extend(
        f"- `{column}`: {count:,}"
        for column, count in metadata["quality_flag_true_counts"].items()
    )
    lines += ["", '## Schéma de sortie', "", '| Colonne | Type Polars |', "|---|---|"]
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
    """Charge les résultats de la phase 1, prépare les données de recherche et les exporte.
    
        :param observations_path: Chemin Parquet des observations mensuelles issues de la construction.
        :type observations_path: str | os.PathLike[str]
        :param edge_metrics_path: Chemin Parquet des métriques d’arêtes de la phase 1.
        :type edge_metrics_path: str | os.PathLike[str]
        :param node_metrics_path: Chemin Parquet des métriques de nœuds de la phase 1.
        :type node_metrics_path: str | os.PathLike[str]
        :param output_path: Destination Parquet des données de recherche.
        :type output_path: str | os.PathLike[str]
        :param metadata_path: Destination du fichier JSON de métadonnées.
        :type metadata_path: str | os.PathLike[str]
        :param report_path: Destination du rapport qualité Markdown.
        :type report_path: str | os.PathLike[str]
        :returns: Données préparées, métadonnées et chemins des fichiers générés.
        :rtype: ResearchDataResult
        :raises OSError: Si les sources ne peuvent pas être lues ou les résultats écrits.
        :raises TypeError: Si les colonnes de clé requises ont un type incompatible.
        :raises ValueError: Si les schémas, clés ou relations de jointure sont invalides.
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
