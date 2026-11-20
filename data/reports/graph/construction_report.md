# Rapport de construction du graphe SNCF

## Vue d’ensemble du jeu de données

- Source : `data\processed\sncf.parquet`
- Lignes source : 12,907
- Observations mensuelles valides : 12,907
- Lignes exclues : 0
- Motifs d’exclusion : `{}`
- Couverture temporelle : de 2018-01 à 2026-09 (105 mois distincts)
- Services : International, National
- Gares : 59
- Arêtes orientées tenant compte du service : 146
- Observations mensuelles : 12,907

## Diagnostics de la structure du réseau par service

Tous les comptes portent sur la topologie observée propre à chaque service. Les graphes de service contenant des arêtes n’ont aucun nœud isolé, car leurs nœuds sont créés à partir des arêtes observées.

| Service | Nœuds | Arêtes | Nœuds isolés | Boucles | Composantes faibles | Composantes fortes | Plus grande composante faible | Plusieurs arêtes entrantes | Plusieurs arêtes sortantes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| International | 18 | 30 | 0 | 0 | 3 | 3 | 11 | 3 | 3 |
| National | 52 | 116 | 0 | 0 | 1 | 1 | 52 | 15 | 15 |

## Diagnostics temporels

- Mois distincts observés : 105
- Mois manquants dans la couverture globale : aucun

| Mois | Observations | Arêtes uniques | Nouvelles arêtes par rapport au mois précédent | Arêtes qui ne sont plus observées par rapport au mois précédent |
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

## Diagnostics de qualité des données

- Enregistrements dupliqués selon la clé métier : 0
- Nombre d’exclusions par motif : `{}`
- Flags diagnostiques déjà activés dans la source (ces observations restent incluses si les clés du graphe sont valides) :
  - `flag_negative_count`: 43
  - `flag_sup30_lt_sup60`: 354
  - `flag_sup15_lt_sup30`: 3
  - `flag_cancellations_gt_planned`: 63

## Interprétation et avertissements

- Une liaison est une paire origine-destination observée, mais pas nécessairement un segment ferroviaire physiquement adjacent, un tronçon consécutif du trajet d’un train ni une correspondance confirmée. L’adjacence dans le graphe ne prouve ni un déplacement de train ni une propagation des retards.
