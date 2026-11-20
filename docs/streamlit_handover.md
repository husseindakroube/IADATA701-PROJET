# Streamlit data handover

## Project context

The research question is: « Dans quelle mesure la structure du réseau TGV est-elle associée à la régularité des liaisons ? » The graph analysis package prepares the graph, centrality, descriptive and association results. This repository currently contains no Streamlit application and has no Streamlit dependency. The handover below uses artifacts verified in the repository; it does not require rerunning upstream analysis.

## Official datasets

| Path | Grain and key | Important fields | Recommended use |
| --- | --- | --- | --- |
| `data/processed/research_dataset.parquet` | One month × service × OD liaison; unique key `(date, service, gare_depart, gare_arrivee)` | `date` (`YYYY-MM` string), `service`, `edge_id`, `source`, `target`, origin/destination names, operational indicators, `cancellation_rate`, `cancellation_rate_valid`, graph metrics, quality flags | Primary source for monthly operational and association views. It has 12,907 rows and 56 columns. |
| `data/processed/graph/nodes.parquet` | One station identity; unique `node_id` | `node_id`, `station_name` | Name mapping for network topology. There are 59 distinct station IDs shared across services. |
| `data/processed/graph/edges.parquet` | One service-aware directed OD edge; unique `edge_id` | `edge_id`, `service`, `source`, `target`, `n_months_observed`, `first_date`, `last_date` | Overall network topology. |
| `data/processed/graph/node_metrics.parquet` | One period × service × station; unique `(period, service, node_id)`; 6,385 rows × 13 columns | `period`, `service`, `node_id`, `station_name`, degree, betweenness, closeness and PageRank fields | Supplementary station metrics. Filter `period = "overall"` for overall node attributes; monthly rows are available when a metric is missing from the research dataset. |
| `data/processed/graph/edge_metrics.parquet` | One period × service × directed edge; unique `(period, service, edge_id)`; 13,053 rows × 24 columns | `period`, `service`, `edge_id`, `source`, `target`, `edge_betweenness` and source/target metrics | Supplementary liaison metrics. Filter `period = "overall"` for overall edge attributes; use monthly rows only for missing research-dataset metrics. |
| `data/processed/graph/descriptive/monthly_summary.parquet` | One month × service; unique `(period, service)` | `node_count`, `edge_count`, `mean_degree`, `max_pagerank`, `max_betweenness`, edge betweenness summaries | Monthly topology and metric trends. |

`data/processed/sncf.parquet` is the 30-column ETL output used upstream. `data/processed/graph/edge_observations.parquet` is a construction input. Its 33 columns and all 12,907 keyed records match a subset of `research_dataset.parquet`; neither should be loaded as a second primary dashboard dataset.

## Analysis tables

Phase 3A outputs in `data/processed/graph/descriptive/`:

- `network_summary.parquet` (2 × 9): service-level node, edge and connectivity counts.
- `monthly_summary.parquet` (210 × 10): service-month topology and metric summaries.
- `node_rankings.parquet` (113 × 6): station leaders by service and metric; ties are retained.
- `edge_rankings.parquet` (52 × 7): high edge-betweenness liaisons with readable origin and destination names. It has no rank column; preserve equal values when displaying cutoffs.
- `operational_summary.parquet` (2 × 31): descriptive operational statistics by service.
- `quality_flag_summary.parquet` (2 × 6): optional quality overview.
- `node_metric_summary.parquet` (2 × 82): wide supplementary summary; prefer `node_metrics.parquet` or `node_rankings.parquet` for interactive views.

Phase 3B outputs in `data/processed/graph/phase3b/`:

- `correlations.parquet` (126 × 8): unique key `(analysis_scope, service, predictor, outcome, method)`; coefficient, raw exploratory `p_value`, and `n_valid`.
- `quantile_comparisons.parquet` (270 × 13): centrality group, grouping strategy, sample size, median, mean, standard deviation, quartiles and IQR.
- `robustness_comparisons.parquet` (42 × 10): complete versus sensitivity coefficients and effective sample sizes for the primary outcome.

## Visualizations

All current figure paths are listed below. The PNGs are report-ready snapshots; in the app, reconstruct figures from the corresponding Parquet data when users need filters or hover details.

| Path | Purpose and recommendation |
| --- | --- |
| `data/processed/graph/visualizations/network_national.png` | National overall directed network; Paris Lyon is visually prominent. Static report image is usable, but labels and edges overlap; rebuild interactively from `nodes.parquet` and `edges.parquet`. |
| `data/processed/graph/visualizations/network_international.png` | International overall network; displays its disconnected components. Static report image is usable; an interactive view can identify components and station details. |
| `data/processed/graph/visualizations/degree_distributions.png` | In-degree and out-degree proportions by service. Rebuild if adding service or metric filters. |
| `data/processed/graph/visualizations/node_centrality_distributions.png` | Betweenness and PageRank distributions, including zero shares. Static overview or interactive metric selector. |
| `data/processed/graph/visualizations/leading_station_rankings.png` | Leading stations by Degree, Betweenness and PageRank. Rebuild from `node_rankings.parquet` for selectors. |
| `data/processed/graph/visualizations/edge_betweenness_distribution.png` | Edge-betweenness ECDF and supplementary histogram with median and P90. Useful static context; an interactive view can expose liaison names. |
| `data/processed/graph/visualizations/monthly_network_evolution.png` | Four monthly series; the PageRank and Betweenness lines are monthly maxima. Rebuild from `monthly_summary.parquet`. |
| `data/processed/graph/visualizations/operational_outcome_distributions.png` | Delay distributions, separated high-delay tail, and cancellation-rate full-range/near-zero views. Rebuild from `research_dataset.parquet` for filters. |
| `data/processed/graph/visualizations/phase3b/edge_betweenness_scatter.png` | Primary delay versus edge betweenness, split by service. Rebuild from the research dataset for hover and filters; points overlap. |
| `data/processed/graph/visualizations/phase3b/target_degree_scatter.png` | Primary delay versus target degree, split by service. Rebuild interactively; discrete degrees overlap. |
| `data/processed/graph/visualizations/phase3b/edge_betweenness_quantile_groups.png` | Primary outcome boxplots across tie-preserving edge-betweenness groups. Rebuild for predictor/outcome selectors. |
| `data/processed/graph/visualizations/phase3b/primary_spearman_overview.png` | Spearman overview for the primary outcome across Overall, National and International. A compact static summary; the correlation table is the filterable source of truth. |

The former `top10_edge_rankings.png` and `top10_station_rankings.png` files are absent; they are not dashboard inputs.

## Suggested pages and filters

1. **Overview:** observation period, number of monthly records, network sizes, and service-level median outcomes. Use `network_summary.parquet`, `operational_summary.parquet`, and the research dataset. Filter by service.
2. **Network structure:** directed graph, station metrics and edge rankings. Use `nodes.parquet`, `edges.parquet`, `node_rankings.parquet`, and `edge_rankings.parquet`. Filter by service, station and metric.
3. **Network evolution:** monthly node/edge counts and metric series from `monthly_summary.parquet`. Filter by service and month range. Label PageRank and Betweenness as monthly maxima.
4. **Operational regularity:** delay and valid cancellation distributions or monthly/liaison summaries from `research_dataset.parquet`. Filter by service, month, origin, destination and outcome.
5. **Structure and regularity:** correlations, centrality-group summaries and sensitivity comparison from the Phase 3B tables. Filter by service/scope, predictor, outcome and method. For row-level scatter plots, use the research dataset rather than joining the metrics tables.

## Joining rules

- Monthly operational and association views use `research_dataset.parquet` directly. It already contains the monthly outcomes and associated graph metrics; do not rejoin `node_metrics.parquet` or `edge_metrics.parquet` for these views.
- For topology, connect `edges.source` and `edges.target` separately to `nodes.node_id`; retain `service` when filtering edges.
- Only if an overall node metric is needed as a network-node attribute, use `data/processed/graph/node_metrics.parquet`, filter `period = "overall"`, and join on `(service, node_id)`. For an overall edge attribute, use `data/processed/graph/edge_metrics.parquet`, filter `period = "overall"`, and join on `(service, edge_id)`.
- For a monthly graph metric missing from the research dataset, match `date = period`, `service`, and `edge_id` for edges, or `date = period`, `service`, and `node_id` for nodes. Do not join on station or edge ID alone across services or periods.
- Use `monthly_summary.parquet` rather than rebuilding monthly topology metrics in the app.

## Missing values and interpretation

- `cancellation_rate` is usable only when `cancellation_rate_valid` is true. There are 73 invalid/missing rates; the metadata identifies a non-positive planned-train denominator. Never replace these with zero.
- Keep negative delay values. The 11 primary outcomes below −15 minutes are excluded only from the sensitivity comparison, not from the research dataset.
- `date` is a month string (`YYYY-MM`), not a day-level date.
- Overall results pool both services and are descriptive. National and International have different route compositions and graph structures.
- Monthly rows for a liaison are repeated observations. Pearson/Spearman p-values are exploratory, not definitive evidence. Correlation does not imply causation. OD liaisons are not necessarily adjacent rail segments or confirmed itineraries; centrality is not passenger traffic and does not establish delay propagation.

## Responsibility boundary

Graph Analysis owns graph construction, centrality, descriptive summaries, correlation calculations, tie-preserving group assignment, and the extreme-delay sensitivity calculation. Streamlit should load the verified outputs, filter and display them, and reconstruct interactive figures where useful. It should not recalculate graph metrics, redefine cancellation validity, replace missing rates with zero, or present ordinary p-values as confirmatory.
