# Descriptive Network Analysis and Visualizations

Phase 3A summarizes existing Phase 1 graph metrics and Phase 2 operational
observations. It does not recalculate metrics, join structural and operational
outcomes for inferential comparisons, or perform correlations, tests, or
regression. National and International are reported separately.

## Run

From the repository root:

```powershell
uv run python -c "from projet_kit_data.graph.descriptive import run_descriptive_analysis; result = run_descriptive_analysis()"
uv run python -c "from projet_kit_data.graph.visualization import run_visualization_pipeline; paths = run_visualization_pipeline()"
```

Descriptive tables are written to `data/processed/graph/descriptive/`; figures
are written to `data/processed/graph/visualizations/`; the narrative report is
maintained in `data/reports/graph/research_report.md`. The generator replaces
only its marked descriptive section, preserving other report content.

## Descriptive table outputs

- `network_summary.parquet`: one row per service; overall node/edge counts,
  weak/strong component counts, largest weak component, multiple in/out degree
  node counts, and self-loops. Components are computed from the existing
  directed edge table and checked against construction metadata.
- `node_metric_summary.parquet`: one row per service and the overall node
  metric distributions (non-null count, missing count, mean, standard
  deviation, median, 25th/75th percentiles, minimum, maximum).
- `node_rankings.parquet`: up to ten rows per service and ranking measure
  (`connectivity_degree`, `betweenness_centrality`, `pagerank`), with rank,
  station ID, station name, and value.
- `edge_rankings.parquet`: up to ten overall directed liaison rows per service
  by edge betweenness, with edge ID and readable origin/destination names.
- `monthly_summary.parquet`: one row per month/service with observed node and
  edge counts, mean degree, maximum PageRank, maximum/median node betweenness,
  and mean/maximum edge betweenness.
- `operational_summary.parquet`: outcome distribution summaries per service
  for all-train mean arrival delay, cancellation rate, and mean arrival delay
  among delayed trains. It also reports missing counts and descriptive Tukey
  1.5-IQR outlier counts. Outlier counts do not filter or alter observations.
- `quality_flag_summary.parquet`: counts of existing Boolean `flag_*` values by
  service.

Node and edge ranking values use the Phase 1 full-period (`period="overall"`)
metrics. Monthly summaries use only monthly metric rows. Operational outcome
summaries use the Phase 2 monthly research dataset and are not mixed with
overall graph metrics.

### Output schemas

All tables are Parquet files. Identifier, station, service, period, and metric
name fields are strings; numeric summaries are numeric columns and can contain
nulls where the source metrics are missing.

| File | Rows | Columns and types |
| --- | --- | --- |
| `network_summary.parquet` | 1 per service | `service` (String); `node_count`, `edge_count`, `weakly_connected_components`, `strongly_connected_components`, `largest_weak_component`, `nodes_multiple_incoming`, `nodes_multiple_outgoing`, `self_loops` (Int64) |
| `node_metric_summary.parquet` | 1 per service | `service` (String); for each node metric: `*_count` and `*_missing` (UInt32), and `*_mean`, `*_std`, `*_median`, `*_q25`, `*_q75`, `*_min`, `*_max` (numeric; degree extrema retain integer type) |
| `node_rankings.parquet` | Up to 10 per service and ranking measure | `rank` (UInt32), `service`, `ranking_metric`, `node_id`, `station_name` (String), `value` (Float64) |
| `edge_rankings.parquet` | Up to 10 per service | `service`, `edge_id`, `source`, `origin_name`, `target`, `destination_name` (String), `edge_betweenness` (Float64) |
| `monthly_summary.parquet` | 1 per month/service | `period`, `service` (String); `node_count`, `edge_count` (UInt32); mean/max metric summaries (Float64) |
| `operational_summary.parquet` | 1 per service | `service` (String); each outcome's count, missing, and outlier count (UInt32), plus summary statistics (Float64) |
| `quality_flag_summary.parquet` | 1 per service | `service` (String); one UInt32 count for each existing Boolean quality flag |

The exact monthly-summary and outcome field names are recorded in their
Parquet schemas. They are derived from the existing Phase 1/2 source column
names and do not redefine those source measures.

## Charts

Generated PNGs are:

- `network_national.png`, `network_international.png`: full directed OD graphs;
  reciprocal directions curve separately, International weak components are
  arranged independently, and node size represents overall node betweenness.
- `degree_distributions.png`: grouped, normalized in-degree/out-degree bars;
  each panel shows integer degree values and the service node count.
- `node_centrality_distributions.png`: separate empirical CDFs for node
  betweenness and PageRank, with zero-valued proportions in the legend.
- `top10_station_rankings.png`: readable station labels for the ten highest
  values of degree, betweenness and PageRank by service.
- `edge_betweenness_distribution.png`: empirical CDF and supplementary
  histogram, annotated with median and 90th percentile.
- `top10_edge_rankings.png`: ten highest-betweenness directed liaisons per
  service, using origin/destination names.
- `monthly_network_evolution.png`: node/edge counts and maximum monthly
  PageRank/betweenness, with 2025 International topology change annotations.
- `operational_outcome_distributions.png`: primary arrival delay, supplementary
  delayed-train arrival delay, and cancellation-rate distributions by service.
  The flagged all-train delays below -15 minutes are omitted from that central
  histogram; delayed-train averages above 120 minutes are separated in a tail
  panel; cancellation rates have a full-range panel and a 0–0.10 zoom. Missing
  cancellation rates remain missing. These display-only exclusions do not
  alter the research Parquet file, and the figure reports the displayed counts.

## Interpretation limits

Degree counts distinct observed OD neighbors, not train frequency or passenger
traffic. Graph paths are not necessarily actual train itineraries or physical
track segments. Centrality is not evidence of delay propagation. Negative
arrival-delay values remain in descriptive summaries and plots; zero and null
cancellation rates remain distinct. These outputs describe distributions and
topology only. Any relationship assessment belongs to Phase 3B and must account
for repeated liaison-month observations and temporal structure.
