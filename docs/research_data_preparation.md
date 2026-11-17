# Research Data Preparation

## Purpose and grain

This phase prepares a joinable monthly dataset for the question: *Dans quelle
mesure la structure du réseau TGV est-elle associée à la régularité des
liaisons ?* It does not calculate statistical associations or infer
causality. The grain is one directed liaison, service, and month, uniquely
identified by `(date, service, gare_depart, gare_arrivee)`. The original source
observation and its fields remain in the output.

## Inputs and joins

The pipeline reads the existing Phase 1 artifacts; it does not rerun ETL,
construction, or graph metrics:

| Input | Default path | Join purpose |
|---|---|---|
| Monthly edge observations | `data/processed/graph/edge_observations.parquet` | Operational source values, source/target node IDs, and edge ID |
| Edge metrics | `data/processed/graph/edge_metrics.parquet` | Monthly `edge_betweenness` |
| Node metrics | `data/processed/graph/node_metrics.parquet` | Monthly structural metrics for source and target stations |

Only rows with a month in `period` are eligible for joins. `period="overall"`
is explicitly excluded. Edge metrics are joined by `(date=period, service,
edge_id)` and their stored source/target IDs are checked against the observation.
Node metrics are joined separately by `(date=period, service,
source=node_id)` and `(date=period, service, target=node_id)`. Node values receive
`source_` and `target_` prefixes. Every lookup key is checked for uniqueness,
joins are many-to-one, and the row count is checked after every join. Missing
metrics remain null; they do not remove source observations.

## Operational variables

The primary outcome is `retard_moyen_tous_trains_arrivee`; its source value,
including negative values and nulls, is preserved. The Boolean
`flag_primary_arrival_delay_below_minus_15` marks values below -15 minutes and
does not exclude them. `retard_moyen_arrivee` is retained as a supplementary
severity indicator. Existing source quality flags and operational counts,
threshold counts, cause percentages, and comments are retained unchanged.

`cancellation_rate` is computed as
`nb_annulation / nb_train_prevu` only when `nb_train_prevu > 0` and
`0 <= nb_annulation <= nb_train_prevu`. Otherwise the rate is null, source
counts are preserved, `cancellation_rate_valid` is false, and
`cancellation_rate_invalid_reason` identifies the first failing condition.
Null is never replaced by zero. No `arrival_delay_rate` is calculated because
the denominator for trains actually operated is not established by the
available fields. Threshold-based delay rates and causal variables are not
created.

## Output and reproducibility

From the repository root:

```powershell
uv run python -c "from projet_kit_data.graph.analysis import run_research_data_preparation_pipeline; result = run_research_data_preparation_pipeline()"
```

Outputs are `data/processed/research_dataset.parquet`,
`data/processed/research_dataset_metadata.json`, and
`data/reports/graph/research_data_quality_report.md`. The Parquet contains all
source observation columns plus `edge_betweenness`, source/target-prefixed
monthly node metrics, `flag_primary_arrival_delay_below_minus_15`,
`cancellation_rate`, `cancellation_rate_valid`, and
`cancellation_rate_invalid_reason`. Exact Polars types are recorded in the
metadata and report. Paths are configurable through the public API.

The metadata records grain, row/column counts, month and service coverage,
input paths and row counts, join keys/validation, missing metric counts,
cancellation validity and reason counts, delay anomaly counts, output schema,
and relevant caveats. The Markdown quality report presents the same results for
review. Preserve the Phase 1 construction and metric artifacts as immutable
inputs so the derived dataset can be reproduced.

## Limitations

The SNCF liaison rows describe monthly origin-destination relationships, not
individual train paths or physical track segments. Structural metrics do not
demonstrate actual train movement or delay propagation. Negative mean delays
are retained and flagged rather than interpreted as errors or corrected.
Cancellation rates with zero/nonpositive denominators or inconsistent counts
are unavailable, not zero. The arrival-delay-rate denominator remains
unresolved and that rate is intentionally absent.
