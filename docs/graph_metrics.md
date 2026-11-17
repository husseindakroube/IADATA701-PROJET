# Graph Metrics

## Research context

The project asks: *Dans quelle mesure la structure du réseau TGV est-elle
associée à la régularité des liaisons ?* This phase describes observed network
topology so a later research-data step can compare structure with monthly
operational observations. It does not calculate associations or infer causes.

Edges are directed from origin to destination because the liaison is directed.
National and International services are analyzed in separate graphs. Metrics
are initially unweighted: a connection counts once regardless of the number of
trains or any delay/cancellation measurement. An overall graph uses the union
of a service's observed edges over the full dataset. A monthly graph uses only
that service's edges observed in the selected month, and contains no stations
absent from those edges. Consequently, overall and monthly scores are different
snapshots and must not be interchanged.

The graph consists of origin-destination liaisons, not confirmed train
itineraries, transfer connections, or physical track segments. Shortest paths
describe paths in this observed topology only. Centrality does not demonstrate
actual train movement, passenger volume, operational importance, or delay
propagation.

## Metric reference

All calculations use NetworkX directed simple graphs and unweighted shortest
paths. An edge is unique by its construction `edge_id` within a service-period
graph. Degree counts distinct neighbors, not service frequency.

| Metric | Definition and normalization | Interpretation and limitations |
|---|---|---|
| `in_degree` | Number of distinct incoming neighbors. | High values indicate more observed incoming liaison connections. |
| `out_degree` | Number of distinct outgoing neighbors. | High values indicate more observed outgoing liaison connections. |
| `degree` | `in_degree + out_degree`; a self-loop contributes once to each. | Total directed connection count, not traffic volume. |
| `in_degree_centrality` | `in_degree / (n - 1)`; zero when `n < 2`. | Fraction of possible other nodes that link into the node. |
| `out_degree_centrality` | `out_degree / (n - 1)`; zero when `n < 2`. | Fraction of possible other nodes reached directly from the node. |
| `betweenness_centrality` | NetworkX normalized directed betweenness, with unweighted shortest paths and endpoints excluded. For directed graphs the normalization uses ordered node pairs. | High scores indicate a node lies on a larger share of shortest directed paths. Disconnected pairs contribute no paths; this is not evidence of real transfers. |
| `in_closeness` | NetworkX directed closeness on the original graph: distances from nodes that can reach the focal node. Uses the reachable-node correction (`wf_improved=True`). | High values indicate short inbound paths from reachable nodes. Unreachable nodes are excluded from distance sums and the reachability fraction reduces scores. |
| `out_closeness` | Same directed closeness calculation on the reversed graph, giving distances from the focal node to nodes it can reach. Uses the same reachability correction. | High values indicate short outbound reachability. It is not interchangeable with inbound closeness. |
| `pagerank` | NetworkX directed PageRank with `alpha=0.85`, unweighted edges, configurable `max_iter` and `tol`. Dangling nodes use NetworkX's default redistribution according to the personalization vector (uniform when absent). | High values mean a node receives links from nodes with higher PageRank. It is not passenger volume, train frequency, or operational influence. A non-converged graph gets null PageRank for every node and a detailed metadata/report entry; other metrics remain available. |
| `edge_betweenness` | NetworkX normalized directed edge betweenness on unweighted shortest paths. | High values indicate an observed directed liaison appears on more shortest paths. It does not assert a train physically traverses that liaison as one leg. |

Degree centralities use the explicit denominator `n - 1`. Betweenness and
closeness use NetworkX's normalized directed and reachable-node conventions,
respectively. For graphs with one node, normalized degree centralities are zero;
NetworkX returns zero closeness and betweenness. A self-loop remains a directed
edge and contributes to in- and out-degree.

## Data model

The pipeline reads the existing construction outputs and writes
`data/processed/graph/node_metrics.parquet`, `edge_metrics.parquet`, and
`metrics_metadata.json`, plus `data/reports/graph/metrics_report.md`.

### `node_metrics.parquet`

| Column | Type |
|---|---|
| `period` | String: `overall` or `YYYY-MM` |
| `service` | String |
| `node_id` | String |
| `station_name` | String |
| `in_degree`, `out_degree`, `degree` | UInt32 |
| `in_degree_centrality`, `out_degree_centrality` | Float64 |
| `betweenness_centrality`, `in_closeness`, `out_closeness`, `pagerank` | Float64, nullable on PageRank convergence failure |

Unique key: `(period, service, node_id)`.

### `edge_metrics.parquet`

The identity fields are `period` (String), `service` (String), `edge_id`
(String), `source` (String node ID), and `target` (String node ID). They are
followed by `edge_betweenness` (Float64), then the node metric fields prefixed
with `source_` and `target_`. Endpoint fields include in-degree, out-degree,
degree, in/out degree centrality, betweenness, in/out closeness, and PageRank.
Degree fields are UInt32; all other values are Float64, with PageRank nullable
if its graph failed to converge.

Unique key: `(period, service, edge_id)`. Endpoint metrics are taken from the
same service-period graph as their edge. Construction `edge_id` values are
reused; no competing identifier is generated.

The later monthly research dataset should join metrics using `period = date`,
`service`, and `edge_id` (or validate source/target as additional integrity
checks). `period = "overall"` is a separate summary and must not be joined as
though it were a monthly score.

## Run and configure

From the repository root:

```powershell
uv run python -c "from projet_kit_data.graph import run_graph_metrics_pipeline; result = run_graph_metrics_pipeline()"
```

The public API is:

```python
run_graph_metrics_pipeline(
    nodes_path="data/processed/graph/nodes.parquet",
    edges_path="data/processed/graph/edges.parquet",
    observations_path="data/processed/graph/edge_observations.parquet",
    output_dir="data/processed/graph",
    report_path="data/reports/graph/metrics_report.md",
    alpha=0.85,
    max_iter=1000,
    tol=1e-6,
)
```

The returned `GraphMetricsResult` exposes `node_metrics`, `edge_metrics`,
`metadata`, and `output_paths`. Metadata includes per-graph node/edge counts,
metric definitions, software versions, configuration, convergence failures,
schemas, unique keys, and warnings. The report provides overall rankings,
overall metric summaries, monthly coverage and evolution, and interpretation
limitations. Execution does not rerun ETL or graph construction.

For reproducibility, keep input construction artifacts immutable and record the
input paths, NetworkX/Polars versions, and PageRank parameters from metadata.
National and International must remain separate in all downstream joins and
analysis. Any association between these structural metrics and operational
regularity is descriptive evidence, not proof of causality.
