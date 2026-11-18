# SNCF Graph Construction Report

## Dataset overview

- Source: `data\processed\sncf.parquet`
- Source rows: 12,907
- Valid monthly observations: 12,907
- Excluded rows: 0
- Excluded reasons: `{}`
- Date coverage: 2018-01 to 2026-09 (105 distinct months)
- Services: International, National
- Stations: 59
- Service-aware directed edges: 146
- Monthly observations: 12,907

## Network structure diagnostics by service

All counts refer to each service-specific observed topology. Isolated nodes are zero where a service graph has edges because nodes are introduced from its observed edges.

| Service | Nodes | Edges | Isolated | Self-loops | Weak components | Strong components | Largest weak component | Multiple incoming | Multiple outgoing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| International | 18 | 30 | 0 | 0 | 3 | 3 | 11 | 3 | 3 |
| National | 52 | 116 | 0 | 0 | 1 | 1 | 52 | 15 | 15 |

## Temporal diagnostics

- Distinct observed months: 105
- Gaps in overall monthly coverage: none

| Month | Observations | Unique edges | New edges vs previous month | No longer observed vs previous month |
|---|---:|---:|---:|---:|
| 2018-01 | 130 | 130 | 130 | 0 |
| 2018-02 | 130 | 130 | 0 | 0 |
| 2018-03 | 130 | 130 | 0 | 0 |
| 2018-04 | 130 | 130 | 0 | 0 |
| 2018-05 | 130 | 130 | 0 | 0 |
| 2018-06 | 130 | 130 | 0 | 0 |
| 2018-07 | 130 | 130 | 0 | 0 |
| 2018-08 | 130 | 130 | 0 | 0 |
| 2018-09 | 130 | 130 | 0 | 0 |
| 2018-10 | 130 | 130 | 0 | 0 |
| 2018-11 | 130 | 130 | 0 | 0 |
| 2018-12 | 130 | 130 | 0 | 0 |
| 2019-01 | 123 | 123 | 0 | 7 |
| 2019-02 | 123 | 123 | 0 | 0 |
| 2019-03 | 123 | 123 | 0 | 0 |
| 2019-04 | 123 | 123 | 0 | 0 |
| 2019-05 | 123 | 123 | 0 | 0 |
| 2019-06 | 123 | 123 | 0 | 0 |
| 2019-07 | 123 | 123 | 0 | 0 |
| 2019-08 | 123 | 123 | 0 | 0 |
| 2019-09 | 123 | 123 | 0 | 0 |
| 2019-10 | 123 | 123 | 0 | 0 |
| 2019-11 | 123 | 123 | 0 | 0 |
| 2019-12 | 123 | 123 | 0 | 0 |
| 2020-01 | 123 | 123 | 0 | 0 |
| 2020-02 | 123 | 123 | 0 | 0 |
| 2020-03 | 123 | 123 | 0 | 0 |
| 2020-04 | 123 | 123 | 0 | 0 |
| 2020-05 | 123 | 123 | 0 | 0 |
| 2020-06 | 123 | 123 | 0 | 0 |
| 2020-07 | 123 | 123 | 0 | 0 |
| 2020-08 | 123 | 123 | 0 | 0 |
| 2020-09 | 123 | 123 | 0 | 0 |
| 2020-10 | 123 | 123 | 0 | 0 |
| 2020-11 | 123 | 123 | 0 | 0 |
| 2020-12 | 123 | 123 | 0 | 0 |
| 2021-01 | 121 | 121 | 0 | 2 |
| 2021-02 | 121 | 121 | 0 | 0 |
| 2021-03 | 121 | 121 | 0 | 0 |
| 2021-04 | 118 | 118 | 0 | 3 |
| 2021-05 | 121 | 121 | 3 | 0 |
| 2021-06 | 121 | 121 | 0 | 0 |
| 2021-07 | 121 | 121 | 0 | 0 |
| 2021-08 | 121 | 121 | 0 | 0 |
| 2021-09 | 121 | 121 | 0 | 0 |
| 2021-10 | 121 | 121 | 0 | 0 |
| 2021-11 | 121 | 121 | 0 | 0 |
| 2021-12 | 121 | 121 | 0 | 0 |
| 2022-01 | 121 | 121 | 0 | 0 |
| 2022-02 | 121 | 121 | 0 | 0 |
| 2022-03 | 121 | 121 | 0 | 0 |
| 2022-04 | 123 | 123 | 2 | 0 |
| 2022-05 | 123 | 123 | 0 | 0 |
| 2022-06 | 121 | 121 | 0 | 2 |
| 2022-07 | 123 | 123 | 2 | 0 |
| 2022-08 | 124 | 124 | 1 | 0 |
| 2022-09 | 123 | 123 | 0 | 1 |
| 2022-10 | 123 | 123 | 0 | 0 |
| 2022-11 | 121 | 121 | 0 | 2 |
| 2022-12 | 123 | 123 | 2 | 0 |
| 2023-01 | 121 | 121 | 0 | 2 |
| 2023-02 | 121 | 121 | 0 | 0 |
| 2023-03 | 121 | 121 | 0 | 0 |
| 2023-04 | 121 | 121 | 0 | 0 |
| 2023-05 | 121 | 121 | 0 | 0 |
| 2023-06 | 121 | 121 | 0 | 0 |
| 2023-07 | 121 | 121 | 0 | 0 |
| 2023-08 | 121 | 121 | 0 | 0 |
| 2023-09 | 121 | 121 | 0 | 0 |
| 2023-10 | 119 | 119 | 0 | 2 |
| 2023-11 | 119 | 119 | 0 | 0 |
| 2023-12 | 119 | 119 | 0 | 0 |
| 2024-01 | 121 | 121 | 2 | 0 |
| 2024-02 | 121 | 121 | 0 | 0 |
| 2024-03 | 121 | 121 | 0 | 0 |
| 2024-04 | 121 | 121 | 0 | 0 |
| 2024-05 | 121 | 121 | 0 | 0 |
| 2024-06 | 119 | 119 | 0 | 2 |
| 2024-07 | 121 | 121 | 2 | 0 |
| 2024-08 | 121 | 121 | 0 | 0 |
| 2024-09 | 121 | 121 | 0 | 0 |
| 2024-10 | 121 | 121 | 0 | 0 |
| 2024-11 | 121 | 121 | 0 | 0 |
| 2024-12 | 121 | 121 | 0 | 0 |
| 2025-01 | 121 | 121 | 0 | 0 |
| 2025-02 | 121 | 121 | 0 | 0 |
| 2025-03 | 121 | 121 | 0 | 0 |
| 2025-04 | 121 | 121 | 0 | 0 |
| 2025-05 | 121 | 121 | 0 | 0 |
| 2025-06 | 121 | 121 | 0 | 0 |
| 2025-07 | 135 | 135 | 14 | 0 |
| 2025-08 | 135 | 135 | 0 | 0 |
| 2025-09 | 135 | 135 | 0 | 0 |
| 2025-10 | 121 | 121 | 2 | 16 |
| 2025-11 | 121 | 121 | 0 | 0 |
| 2025-12 | 121 | 121 | 0 | 0 |
| 2026-01 | 121 | 121 | 0 | 0 |
| 2026-02 | 121 | 121 | 0 | 0 |
| 2026-03 | 121 | 121 | 0 | 0 |
| 2026-04 | 121 | 121 | 0 | 0 |
| 2026-05 | 121 | 121 | 0 | 0 |
| 2026-06 | 121 | 121 | 0 | 0 |
| 2026-07 | 121 | 121 | 0 | 0 |
| 2026-08 | 121 | 121 | 0 | 0 |
| 2026-09 | 121 | 121 | 0 | 0 |

## Data-quality diagnostics

- Duplicate business-key records: 0
- Exclusion counts by reason: `{}`
- Existing diagnostic flags set in the source (these observations remain included when graph keys are valid):
  - `flag_negative_count`: 43
  - `flag_sup30_lt_sup60`: 354
  - `flag_sup15_lt_sup30`: 3
  - `flag_cancellations_gt_planned`: 63

## Interpretation and warnings

- A liaison is an observed origin-destination pair, not necessarily a physical adjacent railway segment, a consecutive train leg, or a confirmed train connection. Graph adjacency does not establish train movement or delay propagation.
