# Research Dataset Quality Report

- Input observation rows: 12,907
- Input monthly edge metric rows: 12,907
- Input node metric rows (including overall): 6,385
- Output rows: 12,907
- Output columns: 56
- Date coverage: 2018-01 to 2026-09
- Services: International, National
- Unique business key `('date', 'service', 'gare_depart', 'gare_arrivee')`: True
- Overall graph metrics excluded: True
- Row count preserved after every join: True
- Edge endpoint mismatches: 0

## Cancellation rate validity

- Valid rates: 12,834
- Null rates: 73
- Invalid reasons: `[{"cancellation_rate_invalid_reason": "planned_count_not_positive", "len": 73}]`

## Primary arrival delay

- Negative values (preserved): 122
- Values below -15 minutes (flagged and preserved): 11

## Missing graph metrics

- `edge_betweenness`: 0
- `source_in_degree`: 0
- `source_out_degree`: 0
- `source_degree`: 0
- `source_in_degree_centrality`: 0
- `source_out_degree_centrality`: 0
- `source_betweenness_centrality`: 0
- `source_in_closeness`: 0
- `source_out_closeness`: 0
- `source_pagerank`: 0
- `target_in_degree`: 0
- `target_out_degree`: 0
- `target_degree`: 0
- `target_in_degree_centrality`: 0
- `target_out_degree_centrality`: 0
- `target_betweenness_centrality`: 0
- `target_in_closeness`: 0
- `target_out_closeness`: 0
- `target_pagerank`: 0

## Quality flags

- `flag_negative_count`: 43
- `flag_sup30_lt_sup60`: 354
- `flag_sup15_lt_sup30`: 3
- `flag_cancellations_gt_planned`: 63
- `flag_primary_arrival_delay_below_minus_15`: 11

## Output schema

| Column | Polars dtype |
|---|---|
| `edge_id` | String |
| `date` | String |
| `service` | String |
| `source` | String |
| `target` | String |
| `gare_depart` | String |
| `gare_arrivee` | String |
| `duree_moyenne` | Int64 |
| `nb_train_prevu` | Int64 |
| `nb_annulation` | Int64 |
| `commentaire_annulation` | String |
| `nb_train_depart_retard` | Int64 |
| `retard_moyen_depart` | Float64 |
| `retard_moyen_tous_trains_depart` | Float64 |
| `commentaire_retards_depart` | String |
| `nb_train_retard_arrivee` | Int64 |
| `retard_moyen_arrivee` | Float64 |
| `retard_moyen_tous_trains_arrivee` | Float64 |
| `commentaires_retard_arrivee` | String |
| `nb_train_retard_sup_15` | Int64 |
| `retard_moyen_trains_retard_sup15` | Float64 |
| `nb_train_retard_sup_30` | Int64 |
| `nb_train_retard_sup_60` | Int64 |
| `prct_cause_externe` | Float64 |
| `prct_cause_infra` | Float64 |
| `prct_cause_gestion_trafic` | Float64 |
| `prct_cause_materiel_roulant` | Float64 |
| `prct_cause_gestion_gare` | Float64 |
| `prct_cause_prise_en_charge_voyageurs` | Float64 |
| `flag_negative_count` | Boolean |
| `flag_sup30_lt_sup60` | Boolean |
| `flag_sup15_lt_sup30` | Boolean |
| `flag_cancellations_gt_planned` | Boolean |
| `edge_betweenness` | Float64 |
| `source_in_degree` | UInt32 |
| `source_out_degree` | UInt32 |
| `source_degree` | UInt32 |
| `source_in_degree_centrality` | Float64 |
| `source_out_degree_centrality` | Float64 |
| `source_betweenness_centrality` | Float64 |
| `source_in_closeness` | Float64 |
| `source_out_closeness` | Float64 |
| `source_pagerank` | Float64 |
| `target_in_degree` | UInt32 |
| `target_out_degree` | UInt32 |
| `target_degree` | UInt32 |
| `target_in_degree_centrality` | Float64 |
| `target_out_degree_centrality` | Float64 |
| `target_betweenness_centrality` | Float64 |
| `target_in_closeness` | Float64 |
| `target_out_closeness` | Float64 |
| `target_pagerank` | Float64 |
| `flag_primary_arrival_delay_below_minus_15` | Boolean |
| `cancellation_rate` | Float64 |
| `cancellation_rate_valid` | Boolean |
| `cancellation_rate_invalid_reason` | String |
