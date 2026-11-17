# SNCF Graph Construction Handoff

This module exports reusable directed graphs and monthly edge observations for
the Streamlit and Graph Analysis work. It constructs topology only; it does not
calculate centrality, test associations, or interpret delay propagation.

## Model and limitations

- A node is one exact source station label. Its `node_id` is derived from the
  UTF-8 station name using SHA-256; spelling is preserved and labels are never
  fuzzy-matched or normalized.
- An edge points from `gare_depart` to `gare_arrivee`. Direction preserves the
  source route orientation. Reverse routes have a different edge identity.
- The edge identity is `(service, origin station, destination station)`. The
  same station nodes are shared across services, while edge identifiers keep
  services separate. The combined in-memory object is a NetworkX `MultiDiGraph`
  keyed by `edge_id`; `service_graphs` provides a directed topology per service.
- Every eligible source row is kept in `edge_observations.parquet`, so users can
  filter a selected service and month to build a snapshot. Edges and their
  summary dates do not replace these monthly records.

A liaison is an observed origin-destination pair. It is not necessarily a
physical adjacent railway segment, consecutive train leg, or confirmed train
connection. Graph adjacency does not prove actual train movement or delay
propagation.

Null measurements stay null. Existing diagnostic flags and anomalous operational
values do not exclude otherwise valid graph keys. Rows with missing, empty, or
invalid graph keys are reported as exclusions. To ensure unique observation
business keys, every row in a duplicated `(date, service, gare_depart,
gare_arrivee)` group is excluded and counted; no arbitrary duplicate is chosen.

## Run the pipeline

From the repository root:

```powershell
uv run python -c "from projet_kit_data.graph import run_graph_construction_pipeline; result = run_graph_construction_pipeline()"
```

Defaults read `data/processed/sncf.parquet` and write:

```text
data/processed/graph/nodes.parquet
data/processed/graph/edges.parquet
data/processed/graph/edge_observations.parquet
data/processed/graph/graph_metadata.json
data/reports/graph/construction_report.md
```

Paths are configurable:

```python
from projet_kit_data.graph import run_graph_construction_pipeline

result = run_graph_construction_pipeline(
    input_path="data/processed/sncf.parquet",
    output_dir="data/processed/graph",
    report_path="data/reports/graph/construction_report.md",
)
```

For a caller that already has a Polars frame, use
`construct_graph_data(frame)` and optionally `export_graph_artifacts(result)`.
The returned `GraphConstructionResult` exposes the Polars tables, combined
NetworkX graph, per-service graphs, metadata, and output paths.

## Artifact schemas

### `nodes.parquet`

| Column | Polars type | Meaning |
|---|---|---|
| `node_id` | String | Stable `node_<24 hex chars>` identifier |
| `station_name` | String | Exact original station label |

One row represents each unique station label.

### `edges.parquet`

| Column | Polars type | Meaning |
|---|---|---|
| `edge_id` | String | Stable `edge_<24 hex chars>` identifier |
| `service` | String | Original service category |
| `source` | String | Origin `node_id` |
| `target` | String | Destination `node_id` |
| `n_months_observed` | UInt32 | Distinct observed months for the edge |
| `first_date` | String | Earliest `YYYY-MM` observation |
| `last_date` | String | Latest `YYYY-MM` observation |

`(service, source, target)` uniquely identifies an edge. Opposite directions
and different services remain distinct.

### `edge_observations.parquet`

The first five fields are `edge_id` (String), `date` (String, `YYYY-MM`),
`service` (String), `source` (String node ID), and `target` (String node ID).
The current 30-column ETL output produces this exact 33-column table schema:

```text
edge_id: String
date: String
service: String
source: String
target: String
gare_depart: String
gare_arrivee: String
duree_moyenne: Int64
nb_train_prevu: Int64
nb_annulation: Int64
commentaire_annulation: String
nb_train_depart_retard: Int64
retard_moyen_depart: Float64
retard_moyen_tous_trains_depart: Float64
commentaire_retards_depart: String
nb_train_retard_arrivee: Int64
retard_moyen_arrivee: Float64
retard_moyen_tous_trains_arrivee: Float64
commentaires_retard_arrivee: String
nb_train_retard_sup_15: Int64
retard_moyen_trains_retard_sup15: Float64
nb_train_retard_sup_30: Int64
nb_train_retard_sup_60: Int64
prct_cause_externe: Float64
prct_cause_infra: Float64
prct_cause_gestion_trafic: Float64
prct_cause_materiel_roulant: Float64
prct_cause_gestion_gare: Float64
prct_cause_prise_en_charge_voyageurs: Float64
flag_negative_count: Boolean
flag_sup30_lt_sup60: Boolean
flag_sup15_lt_sup30: Boolean
flag_cancellations_gt_planned: Boolean
```

For a compatible input frame, every non-key source column is retained with its
original Polars dtype and values. The source `date` and `service` columns are
also the output date and service fields; they are not duplicated. Extra source
columns, if present, are preserved after the listed fields. The table retains
source route labels, operational measurements, comments, nulls, and diagnostic
flags. One row is one unique monthly business key after explicit exclusions.

`graph_metadata.json` records schema version, source and row counts, exclusion
reasons, graph identities, service categories, date coverage, temporal counts,
service-level directed network diagnostics, flagged source-record counts,
configuration, and interpretation warnings. `construction_report.md` presents
the same key facts for human review, including monthly observations, monthly
unique edge counts and coverage changes, gaps, and weak/strong component
statistics.

## Load and use the artifacts

### Polars

```python
import polars as pl
from projet_kit_data.graph import reconstruct_monthly_graph

base = "data/processed/graph"
nodes = pl.read_parquet(f"{base}/nodes.parquet")
edges = pl.read_parquet(f"{base}/edges.parquet")
observations = pl.read_parquet(f"{base}/edge_observations.parquet")
snapshot = observations.filter(
    (pl.col("service") == "National") & (pl.col("date") == "2025-01")
)
graph = reconstruct_monthly_graph(observations, "National", "2025-01")
```

### Pandas

```python
import pandas as pd

base = "data/processed/graph"
nodes = pd.read_parquet(f"{base}/nodes.parquet")
edges = pd.read_parquet(f"{base}/edges.parquet")
observations = pd.read_parquet(f"{base}/edge_observations.parquet")
snapshot = observations.loc[
    (observations["service"] == "National") & (observations["date"] == "2025-01")
]
```

To use NetworkX from Pandas, join snapshot rows to `nodes` on `source` and
`target`, or load `edge_observations.parquet` with Polars and call
`reconstruct_monthly_graph`. The helper retains station names and original
observation fields as node and edge attributes. For Streamlit, load artifacts
once, use the service/date columns for selectors, filter monthly observations,
and reconstruct the snapshot without parsing the Markdown report. Join future
node metrics on `node_id` and edge metrics on `edge_id`.

The code intentionally does not add future `node_metrics.parquet`,
`edge_metrics.parquet`, analysis summaries, visualizations, or Streamlit pages.
