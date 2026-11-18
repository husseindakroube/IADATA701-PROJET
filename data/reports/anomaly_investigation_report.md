# Régularité mensuelle TGV SNCF : investigation des anomalies

## 1. Objectif et méthode

Cette investigation en lecture seule examine les anomalies de l’audit qualité existant. Elle ne modifie ni les observations brutes ni les règles et n’applique aucun nettoyage. Le code de l’audit et son rapport `data_quality_report.txt` ont été examinés ; leurs schémas SNCF, conditions d’anomalie et seuil extrême de `-15` minutes sont réutilisés.

- Entrée : `data\raw\regularite-mensuelle-tgv-aqst.json` (12,907 observations JSON).
- Synthèse existante : `data\reports\data_quality_report.txt` (lecture seule).
- Sortie : `data\reports\anomaly_investigation_report.md`.
- Les pourcentages mensuels utilisent toutes les observations du mois au dénominateur. Les mois sans cas sont omis des tableaux de répartition clairsemés.
- Les témoins d’une comparaison sont les observations des mêmes mois ne satisfaisant pas la condition d’anomalie étudiée. Ils peuvent relever d’une autre anomalie. Les comparaisons sont descriptives et non causales.
- Les listes détaillées contiennent toutes les lignes concernées ; le rapport d’audit d’origine reste inchangé lors de cette investigation.

La période complète contient 12,907 observations sur 105 mois et 26 champs. Les exemples numériques utilisent les valeurs sources enregistrées. Le seuil `-15` est un seuil d’investigation hérité de l’audit, pas une règle de nettoyage proposée.

## 2. Synthèse et répartition mensuelle

Le pourcentage mensuel est le nombre d’observations concernées divisé par l’effectif total du mois.

| Catégorie d’anomalie | Mois | Concernés | Observations du mois | Part mensuelle |
| --- | --- | --- | --- | --- |
| Valeur négative de `nb_train_retard_sup_30` | 2025-01 | 18 | 121 | 14.88% |
| Valeur négative de `nb_train_retard_sup_30` | 2025-02 | 15 | 121 | 12.40% |
| Valeur négative de `nb_train_retard_sup_30` | 2025-03 | 10 | 121 | 8.26% |
| Valeur négative de `retard_moyen_trains_retard_sup15` | 2018-04 | 2 | 130 | 1.54% |
| Valeur négative de `retard_moyen_trains_retard_sup15` | 2018-09 | 2 | 130 | 1.54% |
| Valeur négative de `retard_moyen_trains_retard_sup15` | 2019-02 | 1 | 123 | 0.81% |
| Valeur négative de `retard_moyen_trains_retard_sup15` | 2019-03 | 2 | 123 | 1.63% |
| Valeur négative de `retard_moyen_trains_retard_sup15` | 2019-04 | 1 | 123 | 0.81% |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | 2019-10 | 3 | 123 | 2.44% |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | 2019-11 | 4 | 123 | 3.25% |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | 2019-12 | 3 | 123 | 2.44% |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | 2020-02 | 1 | 123 | 0.81% |
| Valeur extrême de `retard_moyen_tous_trains_depart` | 2019-10 | 2 | 123 | 1.63% |
| Valeur extrême de `retard_moyen_tous_trains_depart` | 2019-11 | 3 | 123 | 2.44% |
| Valeur extrême de `retard_moyen_arrivee` | 2019-11 | 2 | 123 | 1.63% |
| `nb_annulation > nb_train_prevu` | 2020-04 | 50 | 123 | 40.65% |
| `nb_annulation > nb_train_prevu` | 2020-05 | 9 | 123 | 7.32% |
| `nb_annulation > nb_train_prevu` | 2020-06 | 4 | 123 | 3.25% |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | 2025-01 | 118 | 121 | 97.52% |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | 2025-02 | 117 | 121 | 96.69% |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | 2025-03 | 119 | 121 | 98.35% |
| `nb_train_retard_sup_15 < nb_train_retard_sup_30` | 2020-05 | 2 | 123 | 1.63% |
| `nb_train_retard_sup_15 < nb_train_retard_sup_30` | 2025-03 | 1 | 121 | 0.83% |

### Totaux et concentration par catégorie

| Catégorie | Lignes concernées | Liaisons-service distinctes | Effectifs mensuels non nuls |
| --- | --- | --- | --- |
| Valeur négative de `nb_train_retard_sup_30` | 43 | 29 | 2025-01: 18, 2025-02: 15, 2025-03: 10 |
| Valeur négative de `retard_moyen_trains_retard_sup15` | 8 | 6 | 2018-04: 2, 2018-09: 2, 2019-02: 1, 2019-03: 2, 2019-04: 1 |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | 11 | 8 | 2019-10: 3, 2019-11: 4, 2019-12: 3, 2020-02: 1 |
| Valeur extrême de `retard_moyen_tous_trains_depart` | 5 | 3 | 2019-10: 2, 2019-11: 3 |
| Valeur extrême de `retard_moyen_arrivee` | 2 | 2 | 2019-11: 2 |
| `nb_annulation > nb_train_prevu` | 63 | 52 | 2020-04: 50, 2020-05: 9, 2020-06: 4 |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | 354 | 121 | 2025-01: 118, 2025-02: 117, 2025-03: 119 |
| `nb_train_retard_sup_15 < nb_train_retard_sup_30` | 3 | 3 | 2020-05: 2, 2025-03: 1 |

### Distribution complète des retards négatifs de l’audit

La section précédente utilise le seuil extrême inférieur à -15 minutes. Ce tableau complémentaire couvre toutes les valeurs négatives (<0) des champs de retard moyen, sans masquer les négatifs de moindre amplitude. La colonne modérée représente [-15, 0), la colonne extrême les valeurs < -15. `retard_moyen_depart` ne contient aucune valeur négative dans cet état des données.

| Champ | Valeurs négatives | [-15, 0) | < -15 |
| --- | --- | --- | --- |
| retard_moyen_tous_trains_arrivee | 122 | 111 | 11 |
| retard_moyen_tous_trains_depart | 170 | 165 | 5 |
| retard_moyen_arrivee | 2 | 0 | 2 |
| retard_moyen_depart | 0 | 0 | 0 |
| retard_moyen_trains_retard_sup15 | 8 | 8 | 0 |

#### Effectifs mensuels de toutes les valeurs négatives

| Champ | Mois | Lignes négatives | Observations du mois | Part mensuelle |
| --- | --- | --- | --- | --- |
| retard_moyen_tous_trains_arrivee | 2018-04 | 2 | 130 | 1.54% |
| retard_moyen_tous_trains_arrivee | 2018-09 | 2 | 130 | 1.54% |
| retard_moyen_tous_trains_arrivee | 2019-02 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2019-03 | 2 | 123 | 1.63% |
| retard_moyen_tous_trains_arrivee | 2019-04 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2019-05 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2019-07 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2019-10 | 3 | 123 | 2.44% |
| retard_moyen_tous_trains_arrivee | 2019-11 | 4 | 123 | 3.25% |
| retard_moyen_tous_trains_arrivee | 2019-12 | 4 | 123 | 3.25% |
| retard_moyen_tous_trains_arrivee | 2020-01 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2020-02 | 2 | 123 | 1.63% |
| retard_moyen_tous_trains_arrivee | 2020-04 | 7 | 123 | 5.69% |
| retard_moyen_tous_trains_arrivee | 2020-05 | 15 | 123 | 12.20% |
| retard_moyen_tous_trains_arrivee | 2020-06 | 10 | 123 | 8.13% |
| retard_moyen_tous_trains_arrivee | 2020-07 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2020-11 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2020-12 | 3 | 123 | 2.44% |
| retard_moyen_tous_trains_arrivee | 2021-02 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2021-03 | 7 | 121 | 5.79% |
| retard_moyen_tous_trains_arrivee | 2021-04 | 13 | 118 | 11.02% |
| retard_moyen_tous_trains_arrivee | 2021-05 | 4 | 121 | 3.31% |
| retard_moyen_tous_trains_arrivee | 2021-06 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_arrivee | 2021-08 | 4 | 121 | 3.31% |
| retard_moyen_tous_trains_arrivee | 2021-09 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2022-01 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2022-02 | 7 | 121 | 5.79% |
| retard_moyen_tous_trains_arrivee | 2022-08 | 1 | 124 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2022-09 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_arrivee | 2023-05 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2023-07 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2023-08 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2024-01 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2024-02 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2024-05 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2024-08 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_arrivee | 2024-09 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2024-10 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2024-11 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2024-12 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2025-01 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2025-05 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2025-09 | 1 | 135 | 0.74% |
| retard_moyen_tous_trains_arrivee | 2025-10 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2026-03 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2026-04 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_arrivee | 2026-08 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2018-04 | 3 | 130 | 2.31% |
| retard_moyen_tous_trains_depart | 2018-05 | 1 | 130 | 0.77% |
| retard_moyen_tous_trains_depart | 2018-06 | 5 | 130 | 3.85% |
| retard_moyen_tous_trains_depart | 2018-07 | 1 | 130 | 0.77% |
| retard_moyen_tous_trains_depart | 2018-09 | 3 | 130 | 2.31% |
| retard_moyen_tous_trains_depart | 2018-10 | 4 | 130 | 3.08% |
| retard_moyen_tous_trains_depart | 2018-11 | 2 | 130 | 1.54% |
| retard_moyen_tous_trains_depart | 2019-02 | 2 | 123 | 1.63% |
| retard_moyen_tous_trains_depart | 2019-04 | 4 | 123 | 3.25% |
| retard_moyen_tous_trains_depart | 2019-05 | 3 | 123 | 2.44% |
| retard_moyen_tous_trains_depart | 2019-06 | 2 | 123 | 1.63% |
| retard_moyen_tous_trains_depart | 2019-08 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2019-10 | 2 | 123 | 1.63% |
| retard_moyen_tous_trains_depart | 2019-11 | 3 | 123 | 2.44% |
| retard_moyen_tous_trains_depart | 2019-12 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2020-02 | 4 | 123 | 3.25% |
| retard_moyen_tous_trains_depart | 2020-03 | 3 | 123 | 2.44% |
| retard_moyen_tous_trains_depart | 2020-04 | 7 | 123 | 5.69% |
| retard_moyen_tous_trains_depart | 2020-05 | 6 | 123 | 4.88% |
| retard_moyen_tous_trains_depart | 2020-06 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2020-07 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2020-09 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2020-10 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2020-11 | 14 | 123 | 11.38% |
| retard_moyen_tous_trains_depart | 2020-12 | 6 | 123 | 4.88% |
| retard_moyen_tous_trains_depart | 2021-01 | 6 | 121 | 4.96% |
| retard_moyen_tous_trains_depart | 2021-02 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_depart | 2021-03 | 16 | 121 | 13.22% |
| retard_moyen_tous_trains_depart | 2021-04 | 17 | 118 | 14.41% |
| retard_moyen_tous_trains_depart | 2021-05 | 6 | 121 | 4.96% |
| retard_moyen_tous_trains_depart | 2021-08 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_depart | 2021-09 | 3 | 121 | 2.48% |
| retard_moyen_tous_trains_depart | 2021-10 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2021-11 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2021-12 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_depart | 2022-01 | 3 | 121 | 2.48% |
| retard_moyen_tous_trains_depart | 2022-02 | 6 | 121 | 4.96% |
| retard_moyen_tous_trains_depart | 2022-09 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2022-10 | 1 | 123 | 0.81% |
| retard_moyen_tous_trains_depart | 2022-11 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_depart | 2023-02 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_depart | 2023-06 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_depart | 2023-09 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2024-04 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2024-05 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2024-06 | 1 | 119 | 0.84% |
| retard_moyen_tous_trains_depart | 2024-08 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2025-03 | 3 | 121 | 2.48% |
| retard_moyen_tous_trains_depart | 2025-04 | 2 | 121 | 1.65% |
| retard_moyen_tous_trains_depart | 2025-05 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2025-06 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2025-09 | 2 | 135 | 1.48% |
| retard_moyen_tous_trains_depart | 2025-11 | 1 | 121 | 0.83% |
| retard_moyen_tous_trains_depart | 2026-03 | 1 | 121 | 0.83% |
| retard_moyen_arrivee | 2019-11 | 2 | 123 | 1.63% |
| retard_moyen_trains_retard_sup15 | 2018-04 | 2 | 130 | 1.54% |
| retard_moyen_trains_retard_sup15 | 2018-09 | 2 | 130 | 1.54% |
| retard_moyen_trains_retard_sup15 | 2019-02 | 1 | 123 | 0.81% |
| retard_moyen_trains_retard_sup15 | 2019-03 | 2 | 123 | 1.63% |
| retard_moyen_trains_retard_sup15 | 2019-04 | 1 | 123 | 0.81% |
## 3. Valeurs négatives de `nb_train_retard_sup_30`

43 lignes sont concernées, pour 29 liaisons-service distinctes, toutes entre janvier et mars 2025 : 18/121 en janvier (14.88%), 15/121 en février (12.40%) et 10/121 en mars (8.26%). La concentration couvre trois mois, pas seulement janvier.


### Toutes les liaisons et valeurs négatives de `nb_train_retard_sup_30`

#### 2025-01 (18 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_30 | nb_train_retard_sup_15 | nb_train_retard_sup_60 | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-01 | International | LAUSANNE | PARIS LYON | -4 | 15 | 9 | 172 | 10 |
| 2025-01 | National | DIJON VILLE | PARIS LYON | -1 | 47 | 30 | 426 | 4 |
| 2025-01 | National | DOUAI | PARIS NORD | -1 | 21 | 9 | 167 | 2 |
| 2025-01 | National | LE MANS | PARIS MONTPARNASSE | -1 | 51 | 30 | 472 | 5 |
| 2025-01 | National | MARSEILLE ST CHARLES | MARNE LA VALLEE | -2 | 43 | 17 | 296 | 0 |
| 2025-01 | National | LILLE | PARIS NORD | -1 | 49 | 18 | 643 | 4 |
| 2025-01 | National | LYON PART DIEU | LILLE | -44 | 64 | 21 | 352 | 0 |
| 2025-01 | National | LYON PART DIEU | MARNE LA VALLEE | -2 | 42 | 18 | 360 | 0 |
| 2025-01 | National | LYON PART DIEU | PARIS LYON | -3 | 43 | 17 | 732 | 3 |
| 2025-01 | National | QUIMPER | PARIS MONTPARNASSE | -1 | 31 | 14 | 281 | 34 |
| 2025-01 | National | STRASBOURG | PARIS EST | -1 | 67 | 30 | 592 | 5 |
| 2025-01 | National | MONTPELLIER | LYON PART DIEU | -1 | 23 | 10 | 177 | 0 |
| 2025-01 | National | VANNES | PARIS MONTPARNASSE | -1 | 34 | 16 | 302 | 38 |
| 2025-01 | National | ANGERS SAINT LAUD | PARIS MONTPARNASSE | -12 | 49 | 28 | 523 | 7 |
| 2025-01 | National | AVIGNON TGV | PARIS LYON | -5 | 48 | 25 | 469 | 1 |
| 2025-01 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | -1 | 40 | 17 | 263 | 0 |
| 2025-01 | National | LYON PART DIEU | MARSEILLE ST CHARLES | -2 | 75 | 39 | 502 | 0 |
| 2025-01 | National | RENNES | LYON PART DIEU | -2 | 10 | 3 | 94 | 0 |

#### 2025-02 (15 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_30 | nb_train_retard_sup_15 | nb_train_retard_sup_60 | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-02 | National | LE MANS | PARIS MONTPARNASSE | -3 | 24 | 10 | 429 | 1 |
| 2025-02 | National | LYON PART DIEU | MONTPELLIER | -1 | 35 | 16 | 241 | 0 |
| 2025-02 | National | LYON PART DIEU | PARIS LYON | -8 | 39 | 17 | 646 | 2 |
| 2025-02 | National | RENNES | PARIS MONTPARNASSE | -9 | 60 | 24 | 748 | 28 |
| 2025-02 | National | STRASBOURG | PARIS EST | -5 | 62 | 20 | 485 | 3 |
| 2025-02 | International | STUTTGART | PARIS EST | -1 | 14 | 5 | 90 | 2 |
| 2025-02 | National | ANGERS SAINT LAUD | PARIS MONTPARNASSE | -18 | 27 | 13 | 491 | 2 |
| 2025-02 | National | TOURCOING | BORDEAUX ST JEAN | -4 | 2 | 2 | 28 | 1 |
| 2025-02 | National | LYON PART DIEU | MARNE LA VALLEE | -2 | 44 | 19 | 320 | 0 |
| 2025-02 | National | MARSEILLE ST CHARLES | PARIS LYON | -2 | 54 | 32 | 460 | 0 |
| 2025-02 | National | VALENCE ALIXAN TGV | PARIS LYON | -2 | 46 | 20 | 338 | 0 |
| 2025-02 | International | ZURICH | PARIS LYON | -8 | 9 | 6 | 164 | 4 |
| 2025-02 | National | BESANCON FRANCHE COMTE TGV | PARIS LYON | -9 | 8 | 5 | 166 | 0 |
| 2025-02 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | -3 | 62 | 28 | 276 | 3 |
| 2025-02 | National | LAVAL | PARIS MONTPARNASSE | -1 | 16 | 5 | 216 | 5 |

#### 2025-03 (10 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_30 | nb_train_retard_sup_15 | nb_train_retard_sup_60 | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-03 | National | BREST | PARIS MONTPARNASSE | -5 | 17 | 8 | 286 | 2 |
| 2025-03 | National | LYON PART DIEU | LILLE | -11 | 80 | 40 | 343 | 0 |
| 2025-03 | National | TOURCOING | BORDEAUX ST JEAN | -21 | 4 | 2 | 22 | 1 |
| 2025-03 | National | LE MANS | PARIS MONTPARNASSE | -1 | 24 | 13 | 485 | 0 |
| 2025-03 | International | FRANCFORT | PARIS EST | -5 | 19 | 8 | 178 | 5 |
| 2025-03 | National | DIJON VILLE | PARIS LYON | -1 | 27 | 12 | 402 | 1 |
| 2025-03 | National | LYON PART DIEU | PARIS LYON | -1 | 47 | 27 | 729 | 0 |
| 2025-03 | National | QUIMPER | PARIS MONTPARNASSE | -1 | 19 | 10 | 271 | 1 |
| 2025-03 | National | STRASBOURG | PARIS EST | -3 | 66 | 25 | 652 | 7 |
| 2025-03 | National | BESANCON FRANCHE COMTE TGV | PARIS LYON | -3 | 10 | 5 | 175 | 0 |


## 4. Investigation de l’ordre des seuils

La comparaison >30 contre >60 est le contrôle le plus direct des seuils cumulatifs. Le champ >15 comporte une réserve d’applicabilité : le schéma SNCF le réserve aux liaisons en concurrence avec l’avion, mais aucun indicateur d’applicabilité n’est fourni. Les comparaisons >15 contre >30 sont donc des signalements potentiels, pas des violations établies.

### `nb_train_retard_sup_30 < nb_train_retard_sup_60`

354 lignes sont concernées, toutes entre janvier et mars 2025 : 118/121 en janvier (97.52%), 117/121 en février (96.69%) et 119/121 en mars (98.35%). Seules 9 des 363 lignes ne satisfont pas l’inégalité. Les 354 lignes sont détaillées ci-dessous avec les trois indicateurs.


### Toutes les lignes avec inversion >30/<60, y compris janvier 2025

#### 2025-01 (118 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-01 | International | FRANCFORT | PARIS EST | 27 | 0 | 18 |
| 2025-01 | International | GENEVE | PARIS LYON | 19 | 0 | 13 |
| 2025-01 | International | LAUSANNE | PARIS LYON | 15 | -4 | 9 |
| 2025-01 | International | ZURICH | PARIS LYON | 18 | 0 | 10 |
| 2025-01 | National | ANGOULEME | PARIS MONTPARNASSE | 28 | 0 | 10 |
| 2025-01 | National | DIJON VILLE | PARIS LYON | 47 | -1 | 30 |
| 2025-01 | National | DOUAI | PARIS NORD | 21 | -1 | 9 |
| 2025-01 | National | DUNKERQUE | PARIS NORD | 22 | 0 | 8 |
| 2025-01 | National | GRENOBLE | PARIS LYON | 27 | 0 | 12 |
| 2025-01 | National | LAVAL | PARIS MONTPARNASSE | 18 | 0 | 10 |
| 2025-01 | National | LILLE | LYON PART DIEU | 73 | 0 | 42 |
| 2025-01 | National | MARNE LA VALLEE | MARSEILLE ST CHARLES | 59 | 0 | 31 |
| 2025-01 | National | MARSEILLE ST CHARLES | LILLE | 41 | 0 | 13 |
| 2025-01 | National | MARSEILLE ST CHARLES | LYON PART DIEU | 38 | 0 | 18 |
| 2025-01 | National | MARSEILLE ST CHARLES | PARIS LYON | 58 | 0 | 28 |
| 2025-01 | National | NANTES | PARIS MONTPARNASSE | 74 | 1 | 50 |
| 2025-01 | National | PARIS EST | NANCY | 9 | 0 | 3 |
| 2025-01 | National | PARIS LYON | BESANCON FRANCHE COMTE TGV | 18 | 0 | 12 |
| 2025-01 | National | PARIS LYON | LYON PART DIEU | 48 | 0 | 24 |
| 2025-01 | National | PARIS LYON | PERPIGNAN | 21 | 0 | 11 |
| 2025-01 | National | PARIS MONTPARNASSE | LA ROCHELLE VILLE | 11 | 0 | 4 |
| 2025-01 | National | PARIS MONTPARNASSE | LAVAL | 18 | 0 | 9 |
| 2025-01 | National | PARIS MONTPARNASSE | QUIMPER | 15 | 0 | 8 |
| 2025-01 | National | PARIS NORD | DOUAI | 9 | 0 | 6 |
| 2025-01 | National | REIMS | PARIS EST | 3 | 0 | 2 |
| 2025-01 | National | SAINT ETIENNE CHATEAUCREUX | PARIS LYON | 7 | 0 | 2 |
| 2025-01 | National | ST MALO | PARIS MONTPARNASSE | 6 | 0 | 2 |
| 2025-01 | National | TOULON | PARIS LYON | 41 | 0 | 29 |
| 2025-01 | International | ITALIE | PARIS LYON | 5 | 0 | 1 |
| 2025-01 | National | AIX EN PROVENCE TGV | PARIS LYON | 57 | 0 | 31 |
| 2025-01 | National | BORDEAUX ST JEAN | PARIS MONTPARNASSE | 132 | 0 | 69 |
| 2025-01 | National | LA ROCHELLE VILLE | PARIS MONTPARNASSE | 17 | 0 | 3 |
| 2025-01 | National | LE MANS | PARIS MONTPARNASSE | 51 | -1 | 30 |
| 2025-01 | National | MARSEILLE ST CHARLES | MARNE LA VALLEE | 43 | -2 | 17 |
| 2025-01 | National | METZ | PARIS EST | 15 | 0 | 7 |
| 2025-01 | National | MULHOUSE VILLE | PARIS LYON | 37 | 0 | 25 |
| 2025-01 | National | NIMES | PARIS LYON | 23 | 0 | 10 |
| 2025-01 | National | PARIS LYON | CHAMBERY CHALLES LES EAUX | 49 | 0 | 21 |
| 2025-01 | National | PARIS LYON | DIJON VILLE | 42 | 0 | 22 |
| 2025-01 | National | PARIS LYON | LE CREUSOT MONTCEAU MONTCHANIN | 13 | 0 | 9 |
| 2025-01 | National | PARIS LYON | TOULON | 37 | 0 | 20 |
| 2025-01 | National | PARIS MONTPARNASSE | ST PIERRE DES CORPS | 30 | 0 | 11 |
| 2025-01 | National | PARIS NORD | ARRAS | 29 | 0 | 18 |
| 2025-01 | National | PARIS NORD | LILLE | 41 | 0 | 20 |
| 2025-01 | National | PERPIGNAN | PARIS LYON | 23 | 0 | 13 |
| 2025-01 | International | PARIS LYON | LAUSANNE | 31 | 0 | 10 |
| 2025-01 | International | PARIS LYON | ZURICH | 26 | 0 | 17 |
| 2025-01 | International | STUTTGART | PARIS EST | 22 | 0 | 9 |
| 2025-01 | National | ARRAS | PARIS NORD | 58 | 0 | 22 |
| 2025-01 | National | BESANCON FRANCHE COMTE TGV | PARIS LYON | 20 | 0 | 14 |
| 2025-01 | National | BORDEAUX ST JEAN | TOURCOING | 6 | 0 | 6 |
| 2025-01 | National | LE CREUSOT MONTCEAU MONTCHANIN | PARIS LYON | 14 | 0 | 8 |
| 2025-01 | National | LILLE | MARSEILLE ST CHARLES | 50 | 0 | 24 |
| 2025-01 | National | LILLE | PARIS NORD | 49 | -1 | 18 |
| 2025-01 | National | LYON PART DIEU | LILLE | 64 | -44 | 21 |
| 2025-01 | National | LYON PART DIEU | MARNE LA VALLEE | 42 | -2 | 18 |
| 2025-01 | National | LYON PART DIEU | PARIS LYON | 43 | -3 | 17 |
| 2025-01 | National | MACON LOCHE | PARIS LYON | 31 | 0 | 13 |
| 2025-01 | National | MARNE LA VALLEE | LYON PART DIEU | 78 | 0 | 45 |
| 2025-01 | National | NANTES | STRASBOURG | 10 | 0 | 3 |
| 2025-01 | National | PARIS LYON | AIX EN PROVENCE TGV | 49 | 0 | 25 |
| 2025-01 | National | PARIS LYON | ANNECY | 23 | 0 | 9 |
| 2025-01 | National | PARIS LYON | MACON LOCHE | 16 | 0 | 5 |
| 2025-01 | National | PARIS MONTPARNASSE | ANGERS SAINT LAUD | 47 | 0 | 12 |
| 2025-01 | National | PARIS MONTPARNASSE | ST MALO | 6 | 0 | 3 |
| 2025-01 | National | PARIS MONTPARNASSE | TOURS | 9 | 0 | 5 |
| 2025-01 | National | QUIMPER | PARIS MONTPARNASSE | 31 | -1 | 14 |
| 2025-01 | National | RENNES | PARIS MONTPARNASSE | 84 | 0 | 38 |
| 2025-01 | National | ST PIERRE DES CORPS | PARIS MONTPARNASSE | 27 | 0 | 3 |
| 2025-01 | National | STRASBOURG | NANTES | 4 | 0 | 2 |
| 2025-01 | National | STRASBOURG | PARIS EST | 67 | -1 | 30 |
| 2025-01 | National | TOULOUSE MATABIAU | PARIS MONTPARNASSE | 34 | 1 | 22 |
| 2025-01 | International | BARCELONA | PARIS LYON | 10 | 0 | 7 |
| 2025-01 | International | PARIS EST | FRANCFORT | 36 | 0 | 18 |
| 2025-01 | International | PARIS EST | STUTTGART | 23 | 0 | 13 |
| 2025-01 | International | PARIS LYON | BARCELONA | 7 | 0 | 2 |
| 2025-01 | National | BREST | PARIS MONTPARNASSE | 30 | 0 | 13 |
| 2025-01 | National | LYON PART DIEU | RENNES | 6 | 0 | 4 |
| 2025-01 | National | MONTPELLIER | LYON PART DIEU | 23 | -1 | 10 |
| 2025-01 | National | MONTPELLIER | PARIS LYON | 23 | 0 | 10 |
| 2025-01 | National | NICE VILLE | PARIS LYON | 34 | 0 | 23 |
| 2025-01 | National | PARIS LYON | MONTPELLIER | 14 | 0 | 10 |
| 2025-01 | National | PARIS LYON | NICE VILLE | 37 | 0 | 23 |
| 2025-01 | National | PARIS LYON | NIMES | 9 | 0 | 5 |
| 2025-01 | National | PARIS MONTPARNASSE | BREST | 22 | 0 | 8 |
| 2025-01 | National | PARIS MONTPARNASSE | LE MANS | 28 | 0 | 13 |
| 2025-01 | National | PARIS MONTPARNASSE | POITIERS | 40 | 0 | 16 |
| 2025-01 | National | PARIS MONTPARNASSE | RENNES | 65 | 0 | 30 |
| 2025-01 | National | PARIS MONTPARNASSE | TOULOUSE MATABIAU | 28 | 0 | 19 |
| 2025-01 | National | PARIS MONTPARNASSE | VANNES | 23 | 0 | 10 |
| 2025-01 | National | VALENCE ALIXAN TGV | PARIS LYON | 39 | 1 | 22 |
| 2025-01 | National | VANNES | PARIS MONTPARNASSE | 34 | -1 | 16 |
| 2025-01 | International | PARIS LYON | GENEVE | 39 | 0 | 13 |
| 2025-01 | National | ANGERS SAINT LAUD | PARIS MONTPARNASSE | 49 | -12 | 28 |
| 2025-01 | National | ANNECY | PARIS LYON | 17 | 0 | 7 |
| 2025-01 | National | AVIGNON TGV | PARIS LYON | 48 | -5 | 25 |
| 2025-01 | National | BELLEGARDE (AIN) | PARIS LYON | 27 | 0 | 19 |
| 2025-01 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | 40 | -1 | 17 |
| 2025-01 | National | LYON PART DIEU | MARSEILLE ST CHARLES | 75 | -2 | 39 |
| 2025-01 | National | LYON PART DIEU | MONTPELLIER | 42 | 0 | 22 |
| 2025-01 | National | MARSEILLE ST CHARLES | TOURCOING | 5 | 0 | 3 |
| 2025-01 | National | NANCY | PARIS EST | 12 | 0 | 4 |
| 2025-01 | National | PARIS EST | METZ | 12 | 0 | 7 |
| 2025-01 | National | PARIS EST | REIMS | 8 | 0 | 2 |
| 2025-01 | National | PARIS EST | STRASBOURG | 41 | 1 | 16 |
| 2025-01 | National | PARIS LYON | AVIGNON TGV | 41 | 0 | 18 |
| 2025-01 | National | PARIS LYON | BELLEGARDE (AIN) | 43 | 0 | 21 |
| 2025-01 | National | PARIS LYON | GRENOBLE | 21 | 0 | 13 |
| 2025-01 | National | PARIS LYON | MARSEILLE ST CHARLES | 52 | 0 | 26 |
| 2025-01 | National | PARIS LYON | MULHOUSE VILLE | 46 | 0 | 26 |
| 2025-01 | National | PARIS LYON | SAINT ETIENNE CHATEAUCREUX | 10 | 0 | 4 |
| 2025-01 | National | PARIS LYON | VALENCE ALIXAN TGV | 34 | 0 | 18 |
| 2025-01 | National | PARIS MONTPARNASSE | ANGOULEME | 34 | 0 | 15 |
| 2025-01 | National | PARIS MONTPARNASSE | BORDEAUX ST JEAN | 124 | 0 | 55 |
| 2025-01 | National | PARIS MONTPARNASSE | NANTES | 64 | 0 | 24 |
| 2025-01 | National | PARIS NORD | DUNKERQUE | 21 | 0 | 10 |
| 2025-01 | National | POITIERS | PARIS MONTPARNASSE | 38 | 0 | 12 |
| 2025-01 | National | RENNES | LYON PART DIEU | 10 | -2 | 3 |

#### 2025-02 (117 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-02 | International | PARIS LYON | BARCELONA | 3 | 0 | 2 |
| 2025-02 | International | PARIS LYON | ZURICH | 19 | 0 | 8 |
| 2025-02 | National | ARRAS | PARIS NORD | 31 | 0 | 6 |
| 2025-02 | National | BORDEAUX ST JEAN | TOURCOING | 6 | 0 | 3 |
| 2025-02 | National | LE CREUSOT MONTCEAU MONTCHANIN | PARIS LYON | 9 | 0 | 5 |
| 2025-02 | National | LE MANS | PARIS MONTPARNASSE | 24 | -3 | 10 |
| 2025-02 | National | LYON PART DIEU | MONTPELLIER | 35 | -1 | 16 |
| 2025-02 | National | MARSEILLE ST CHARLES | LILLE | 37 | 0 | 15 |
| 2025-02 | National | MARSEILLE ST CHARLES | MARNE LA VALLEE | 39 | 0 | 22 |
| 2025-02 | National | MULHOUSE VILLE | PARIS LYON | 17 | 0 | 12 |
| 2025-02 | National | PARIS EST | STRASBOURG | 48 | 0 | 23 |
| 2025-02 | National | PARIS LYON | ANNECY | 17 | 0 | 8 |
| 2025-02 | National | PARIS LYON | BESANCON FRANCHE COMTE TGV | 8 | 0 | 6 |
| 2025-02 | National | PARIS LYON | LYON PART DIEU | 38 | 0 | 18 |
| 2025-02 | National | PARIS LYON | PERPIGNAN | 16 | 0 | 10 |
| 2025-02 | National | PARIS MONTPARNASSE | ANGERS SAINT LAUD | 19 | 0 | 11 |
| 2025-02 | National | PARIS MONTPARNASSE | LAVAL | 9 | 0 | 3 |
| 2025-02 | National | PARIS NORD | DOUAI | 6 | 0 | 2 |
| 2025-02 | International | BARCELONA | PARIS LYON | 6 | 0 | 2 |
| 2025-02 | International | PARIS EST | FRANCFORT | 25 | 0 | 7 |
| 2025-02 | National | ANGOULEME | PARIS MONTPARNASSE | 20 | 1 | 9 |
| 2025-02 | National | ANNECY | PARIS LYON | 26 | 0 | 14 |
| 2025-02 | National | GRENOBLE | PARIS LYON | 38 | 0 | 21 |
| 2025-02 | National | LYON PART DIEU | PARIS LYON | 39 | -8 | 17 |
| 2025-02 | National | LYON PART DIEU | RENNES | 8 | 0 | 3 |
| 2025-02 | National | MARNE LA VALLEE | LYON PART DIEU | 72 | 0 | 25 |
| 2025-02 | National | NICE VILLE | PARIS LYON | 40 | 0 | 23 |
| 2025-02 | National | NIMES | PARIS LYON | 27 | 0 | 13 |
| 2025-02 | National | PARIS LYON | BELLEGARDE (AIN) | 31 | 0 | 16 |
| 2025-02 | National | PARIS LYON | MARSEILLE ST CHARLES | 51 | 0 | 30 |
| 2025-02 | National | PARIS LYON | MONTPELLIER | 11 | 0 | 5 |
| 2025-02 | National | PARIS LYON | VALENCE ALIXAN TGV | 20 | 0 | 8 |
| 2025-02 | National | PARIS MONTPARNASSE | ANGOULEME | 22 | 0 | 10 |
| 2025-02 | National | PARIS MONTPARNASSE | QUIMPER | 40 | 0 | 24 |
| 2025-02 | National | PARIS MONTPARNASSE | RENNES | 34 | 0 | 8 |
| 2025-02 | National | PARIS MONTPARNASSE | VANNES | 53 | 0 | 30 |
| 2025-02 | National | PARIS NORD | LILLE | 24 | 0 | 12 |
| 2025-02 | National | RENNES | LYON PART DIEU | 10 | 0 | 4 |
| 2025-02 | National | RENNES | PARIS MONTPARNASSE | 60 | -9 | 24 |
| 2025-02 | National | SAINT ETIENNE CHATEAUCREUX | PARIS LYON | 8 | 0 | 1 |
| 2025-02 | National | STRASBOURG | PARIS EST | 62 | -5 | 20 |
| 2025-02 | National | TOURS | PARIS MONTPARNASSE | 7 | 0 | 3 |
| 2025-02 | International | FRANCFORT | PARIS EST | 22 | 0 | 8 |
| 2025-02 | International | LAUSANNE | PARIS LYON | 9 | 0 | 5 |
| 2025-02 | International | PARIS LYON | LAUSANNE | 8 | 0 | 4 |
| 2025-02 | International | STUTTGART | PARIS EST | 14 | -1 | 5 |
| 2025-02 | National | ANGERS SAINT LAUD | PARIS MONTPARNASSE | 27 | -18 | 13 |
| 2025-02 | National | BREST | PARIS MONTPARNASSE | 23 | 0 | 11 |
| 2025-02 | National | DIJON VILLE | PARIS LYON | 20 | 0 | 12 |
| 2025-02 | National | DOUAI | PARIS NORD | 8 | 0 | 3 |
| 2025-02 | National | LA ROCHELLE VILLE | PARIS MONTPARNASSE | 7 | 0 | 2 |
| 2025-02 | National | LILLE | MARSEILLE ST CHARLES | 51 | 0 | 21 |
| 2025-02 | National | MARSEILLE ST CHARLES | LYON PART DIEU | 39 | 0 | 16 |
| 2025-02 | National | MARSEILLE ST CHARLES | TOURCOING | 3 | 0 | 2 |
| 2025-02 | National | METZ | PARIS EST | 28 | 0 | 11 |
| 2025-02 | National | PARIS EST | REIMS | 10 | 0 | 5 |
| 2025-02 | National | PARIS LYON | GRENOBLE | 37 | 0 | 21 |
| 2025-02 | National | PARIS LYON | MULHOUSE VILLE | 29 | 0 | 20 |
| 2025-02 | National | PARIS LYON | NICE VILLE | 27 | 0 | 12 |
| 2025-02 | National | PARIS LYON | NIMES | 11 | 0 | 5 |
| 2025-02 | National | PARIS LYON | TOULON | 30 | 0 | 19 |
| 2025-02 | National | PARIS MONTPARNASSE | BORDEAUX ST JEAN | 64 | 0 | 28 |
| 2025-02 | National | PARIS MONTPARNASSE | NANTES | 23 | 0 | 12 |
| 2025-02 | National | PARIS MONTPARNASSE | ST PIERRE DES CORPS | 19 | 0 | 7 |
| 2025-02 | National | PARIS MONTPARNASSE | TOULOUSE MATABIAU | 17 | 0 | 9 |
| 2025-02 | National | PARIS MONTPARNASSE | TOURS | 8 | 0 | 4 |
| 2025-02 | National | PARIS NORD | ARRAS | 17 | 0 | 11 |
| 2025-02 | National | TOULOUSE MATABIAU | PARIS MONTPARNASSE | 20 | 0 | 9 |
| 2025-02 | National | TOURCOING | BORDEAUX ST JEAN | 2 | -4 | 2 |
| 2025-02 | National | VANNES | PARIS MONTPARNASSE | 36 | 0 | 17 |
| 2025-02 | International | GENEVE | PARIS LYON | 16 | 0 | 10 |
| 2025-02 | International | ITALIE | PARIS LYON | 10 | 0 | 6 |
| 2025-02 | International | PARIS EST | STUTTGART | 22 | 0 | 10 |
| 2025-02 | International | PARIS LYON | GENEVE | 25 | 0 | 13 |
| 2025-02 | National | BELLEGARDE (AIN) | PARIS LYON | 22 | 0 | 12 |
| 2025-02 | National | BORDEAUX ST JEAN | PARIS MONTPARNASSE | 75 | 0 | 27 |
| 2025-02 | National | DUNKERQUE | PARIS NORD | 12 | 0 | 3 |
| 2025-02 | National | LILLE | LYON PART DIEU | 67 | 0 | 23 |
| 2025-02 | National | LILLE | PARIS NORD | 26 | 0 | 6 |
| 2025-02 | National | LYON PART DIEU | LILLE | 61 | 0 | 19 |
| 2025-02 | National | LYON PART DIEU | MARNE LA VALLEE | 44 | -2 | 19 |
| 2025-02 | National | LYON PART DIEU | MARSEILLE ST CHARLES | 70 | 0 | 26 |
| 2025-02 | National | MARNE LA VALLEE | MARSEILLE ST CHARLES | 59 | 0 | 25 |
| 2025-02 | National | MARSEILLE ST CHARLES | PARIS LYON | 54 | -2 | 32 |
| 2025-02 | National | MONTPELLIER | LYON PART DIEU | 12 | 0 | 7 |
| 2025-02 | National | NANCY | PARIS EST | 15 | 0 | 8 |
| 2025-02 | National | NANTES | PARIS MONTPARNASSE | 35 | 0 | 21 |
| 2025-02 | National | PARIS EST | METZ | 22 | 0 | 12 |
| 2025-02 | National | PARIS EST | NANCY | 14 | 0 | 6 |
| 2025-02 | National | PARIS LYON | AIX EN PROVENCE TGV | 54 | 0 | 35 |
| 2025-02 | National | PARIS LYON | AVIGNON TGV | 40 | 0 | 27 |
| 2025-02 | National | PARIS LYON | CHAMBERY CHALLES LES EAUX | 35 | 0 | 14 |
| 2025-02 | National | PARIS LYON | DIJON VILLE | 21 | 0 | 13 |
| 2025-02 | National | PARIS LYON | LE CREUSOT MONTCEAU MONTCHANIN | 10 | 0 | 4 |
| 2025-02 | National | PARIS MONTPARNASSE | LE MANS | 16 | 0 | 7 |
| 2025-02 | National | PARIS NORD | DUNKERQUE | 8 | 0 | 3 |
| 2025-02 | National | PERPIGNAN | PARIS LYON | 25 | 0 | 12 |
| 2025-02 | National | ST MALO | PARIS MONTPARNASSE | 6 | 0 | 2 |
| 2025-02 | National | VALENCE ALIXAN TGV | PARIS LYON | 46 | -2 | 20 |
| 2025-02 | International | ZURICH | PARIS LYON | 9 | -8 | 6 |
| 2025-02 | National | AIX EN PROVENCE TGV | PARIS LYON | 48 | 0 | 33 |
| 2025-02 | National | AVIGNON TGV | PARIS LYON | 43 | 0 | 27 |
| 2025-02 | National | BESANCON FRANCHE COMTE TGV | PARIS LYON | 8 | -9 | 5 |
| 2025-02 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | 62 | -3 | 28 |
| 2025-02 | National | LAVAL | PARIS MONTPARNASSE | 16 | -1 | 5 |
| 2025-02 | National | MACON LOCHE | PARIS LYON | 38 | 0 | 22 |
| 2025-02 | National | MONTPELLIER | PARIS LYON | 27 | 0 | 13 |
| 2025-02 | National | PARIS LYON | MACON LOCHE | 10 | 0 | 5 |
| 2025-02 | National | PARIS LYON | SAINT ETIENNE CHATEAUCREUX | 7 | 0 | 4 |
| 2025-02 | National | PARIS MONTPARNASSE | BREST | 12 | 0 | 5 |
| 2025-02 | National | PARIS MONTPARNASSE | LA ROCHELLE VILLE | 14 | 0 | 5 |
| 2025-02 | National | PARIS MONTPARNASSE | POITIERS | 28 | 0 | 12 |
| 2025-02 | National | POITIERS | PARIS MONTPARNASSE | 20 | 0 | 5 |
| 2025-02 | National | QUIMPER | PARIS MONTPARNASSE | 34 | 1 | 17 |
| 2025-02 | National | REIMS | PARIS EST | 11 | 0 | 7 |
| 2025-02 | National | ST PIERRE DES CORPS | PARIS MONTPARNASSE | 18 | 0 | 9 |
| 2025-02 | National | TOULON | PARIS LYON | 46 | 0 | 29 |

#### 2025-03 (119 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-03 | International | STUTTGART | PARIS EST | 18 | 0 | 9 |
| 2025-03 | National | ANGERS SAINT LAUD | PARIS MONTPARNASSE | 29 | 0 | 16 |
| 2025-03 | National | ANGOULEME | PARIS MONTPARNASSE | 13 | 1 | 7 |
| 2025-03 | National | AVIGNON TGV | PARIS LYON | 59 | 0 | 34 |
| 2025-03 | National | BREST | PARIS MONTPARNASSE | 17 | -5 | 8 |
| 2025-03 | National | LAVAL | PARIS MONTPARNASSE | 10 | 0 | 6 |
| 2025-03 | National | LE CREUSOT MONTCEAU MONTCHANIN | PARIS LYON | 13 | 4 | 6 |
| 2025-03 | National | LILLE | PARIS NORD | 26 | 0 | 12 |
| 2025-03 | National | LYON PART DIEU | LILLE | 80 | -11 | 40 |
| 2025-03 | National | LYON PART DIEU | MARSEILLE ST CHARLES | 63 | 0 | 32 |
| 2025-03 | National | LYON PART DIEU | RENNES | 7 | 0 | 5 |
| 2025-03 | National | MARNE LA VALLEE | MARSEILLE ST CHARLES | 32 | 0 | 17 |
| 2025-03 | National | MARSEILLE ST CHARLES | TOURCOING | 8 | 0 | 6 |
| 2025-03 | National | MONTPELLIER | LYON PART DIEU | 21 | 0 | 9 |
| 2025-03 | National | MONTPELLIER | PARIS LYON | 30 | 0 | 18 |
| 2025-03 | National | PARIS LYON | BESANCON FRANCHE COMTE TGV | 16 | 0 | 9 |
| 2025-03 | National | PARIS LYON | GRENOBLE | 26 | 0 | 13 |
| 2025-03 | National | PARIS LYON | MACON LOCHE | 17 | 0 | 8 |
| 2025-03 | National | PARIS LYON | MARSEILLE ST CHARLES | 41 | 0 | 22 |
| 2025-03 | National | PARIS LYON | MULHOUSE VILLE | 39 | 0 | 18 |
| 2025-03 | National | PARIS LYON | NIMES | 21 | 0 | 12 |
| 2025-03 | National | PARIS LYON | PERPIGNAN | 18 | 0 | 11 |
| 2025-03 | National | PARIS LYON | VALENCE ALIXAN TGV | 34 | 0 | 18 |
| 2025-03 | National | PARIS MONTPARNASSE | ANGERS SAINT LAUD | 18 | 0 | 4 |
| 2025-03 | National | PARIS MONTPARNASSE | BORDEAUX ST JEAN | 52 | 0 | 21 |
| 2025-03 | National | PARIS MONTPARNASSE | BREST | 21 | 0 | 7 |
| 2025-03 | National | PARIS MONTPARNASSE | LE MANS | 16 | 0 | 8 |
| 2025-03 | National | PARIS NORD | DOUAI | 7 | 2 | 4 |
| 2025-03 | National | PERPIGNAN | PARIS LYON | 22 | 0 | 16 |
| 2025-03 | National | POITIERS | PARIS MONTPARNASSE | 23 | 0 | 5 |
| 2025-03 | National | RENNES | LYON PART DIEU | 10 | 0 | 2 |
| 2025-03 | National | TOURCOING | BORDEAUX ST JEAN | 4 | -21 | 2 |
| 2025-03 | National | VALENCE ALIXAN TGV | PARIS LYON | 44 | 0 | 28 |
| 2025-03 | International | PARIS EST | STUTTGART | 21 | 0 | 7 |
| 2025-03 | International | ZURICH | PARIS LYON | 15 | 0 | 10 |
| 2025-03 | National | AIX EN PROVENCE TGV | PARIS LYON | 64 | 0 | 37 |
| 2025-03 | National | LA ROCHELLE VILLE | PARIS MONTPARNASSE | 7 | 0 | 1 |
| 2025-03 | National | LE MANS | PARIS MONTPARNASSE | 24 | -1 | 13 |
| 2025-03 | National | MACON LOCHE | PARIS LYON | 41 | 0 | 18 |
| 2025-03 | National | MARNE LA VALLEE | LYON PART DIEU | 41 | 0 | 14 |
| 2025-03 | National | MARSEILLE ST CHARLES | LILLE | 45 | 0 | 22 |
| 2025-03 | National | MARSEILLE ST CHARLES | LYON PART DIEU | 31 | 0 | 13 |
| 2025-03 | National | MULHOUSE VILLE | PARIS LYON | 23 | 0 | 13 |
| 2025-03 | National | PARIS EST | NANCY | 16 | 0 | 8 |
| 2025-03 | National | PARIS MONTPARNASSE | LAVAL | 14 | 0 | 8 |
| 2025-03 | National | PARIS MONTPARNASSE | RENNES | 47 | 0 | 23 |
| 2025-03 | National | PARIS MONTPARNASSE | ST PIERRE DES CORPS | 21 | 0 | 11 |
| 2025-03 | National | PARIS MONTPARNASSE | TOURS | 8 | 0 | 5 |
| 2025-03 | National | PARIS NORD | DUNKERQUE | 17 | 0 | 9 |
| 2025-03 | National | ST PIERRE DES CORPS | PARIS MONTPARNASSE | 17 | 0 | 6 |
| 2025-03 | National | TOULOUSE MATABIAU | PARIS MONTPARNASSE | 16 | 4 | 11 |
| 2025-03 | International | FRANCFORT | PARIS EST | 19 | -5 | 8 |
| 2025-03 | International | GENEVE | PARIS LYON | 27 | 0 | 19 |
| 2025-03 | International | PARIS EST | FRANCFORT | 31 | 0 | 12 |
| 2025-03 | International | PARIS LYON | BARCELONA | 3 | 0 | 2 |
| 2025-03 | International | PARIS LYON | GENEVE | 26 | 0 | 15 |
| 2025-03 | International | PARIS LYON | ITALIE | 2 | 0 | 2 |
| 2025-03 | National | ARRAS | PARIS NORD | 30 | 0 | 13 |
| 2025-03 | National | DOUAI | PARIS NORD | 8 | 0 | 3 |
| 2025-03 | National | LYON PART DIEU | MONTPELLIER | 45 | 0 | 15 |
| 2025-03 | National | MARSEILLE ST CHARLES | MARNE LA VALLEE | 59 | 0 | 24 |
| 2025-03 | National | METZ | PARIS EST | 48 | 0 | 19 |
| 2025-03 | National | NANTES | PARIS MONTPARNASSE | 34 | 0 | 17 |
| 2025-03 | National | PARIS EST | STRASBOURG | 43 | 1 | 24 |
| 2025-03 | National | PARIS LYON | AVIGNON TGV | 35 | 0 | 20 |
| 2025-03 | National | PARIS LYON | BELLEGARDE (AIN) | 35 | 0 | 20 |
| 2025-03 | National | PARIS LYON | CHAMBERY CHALLES LES EAUX | 24 | 0 | 15 |
| 2025-03 | National | PARIS LYON | DIJON VILLE | 40 | 0 | 22 |
| 2025-03 | National | PARIS LYON | MONTPELLIER | 21 | 0 | 13 |
| 2025-03 | National | PARIS LYON | TOULON | 19 | 0 | 11 |
| 2025-03 | National | PARIS MONTPARNASSE | LA ROCHELLE VILLE | 12 | 0 | 4 |
| 2025-03 | International | PARIS LYON | LAUSANNE | 13 | 0 | 4 |
| 2025-03 | International | PARIS LYON | ZURICH | 20 | 0 | 14 |
| 2025-03 | National | BELLEGARDE (AIN) | PARIS LYON | 29 | 0 | 19 |
| 2025-03 | National | BORDEAUX ST JEAN | TOURCOING | 4 | 0 | 3 |
| 2025-03 | National | DIJON VILLE | PARIS LYON | 27 | -1 | 12 |
| 2025-03 | National | DUNKERQUE | PARIS NORD | 10 | 0 | 5 |
| 2025-03 | National | GRENOBLE | PARIS LYON | 38 | 0 | 20 |
| 2025-03 | National | LILLE | LYON PART DIEU | 36 | 0 | 13 |
| 2025-03 | National | LILLE | MARSEILLE ST CHARLES | 29 | 0 | 16 |
| 2025-03 | National | LYON PART DIEU | MARNE LA VALLEE | 77 | 0 | 31 |
| 2025-03 | National | LYON PART DIEU | PARIS LYON | 47 | -1 | 27 |
| 2025-03 | National | NICE VILLE | PARIS LYON | 32 | 0 | 23 |
| 2025-03 | National | PARIS EST | METZ | 24 | 0 | 9 |
| 2025-03 | National | PARIS EST | REIMS | 10 | 0 | 5 |
| 2025-03 | National | PARIS LYON | AIX EN PROVENCE TGV | 39 | 0 | 18 |
| 2025-03 | National | PARIS LYON | LYON PART DIEU | 50 | 0 | 30 |
| 2025-03 | National | PARIS LYON | NICE VILLE | 13 | 0 | 8 |
| 2025-03 | National | PARIS MONTPARNASSE | ANGOULEME | 18 | 0 | 8 |
| 2025-03 | National | PARIS MONTPARNASSE | POITIERS | 41 | 0 | 11 |
| 2025-03 | National | PARIS MONTPARNASSE | QUIMPER | 21 | 0 | 9 |
| 2025-03 | National | PARIS MONTPARNASSE | ST MALO | 9 | 0 | 5 |
| 2025-03 | National | PARIS MONTPARNASSE | TOULOUSE MATABIAU | 15 | 0 | 9 |
| 2025-03 | National | PARIS MONTPARNASSE | VANNES | 25 | 0 | 12 |
| 2025-03 | National | PARIS NORD | ARRAS | 23 | 1 | 14 |
| 2025-03 | National | QUIMPER | PARIS MONTPARNASSE | 19 | -1 | 10 |
| 2025-03 | National | REIMS | PARIS EST | 8 | 0 | 1 |
| 2025-03 | National | RENNES | PARIS MONTPARNASSE | 50 | 0 | 25 |
| 2025-03 | National | SAINT ETIENNE CHATEAUCREUX | PARIS LYON | 10 | 3 | 6 |
| 2025-03 | National | STRASBOURG | PARIS EST | 66 | -3 | 25 |
| 2025-03 | National | VANNES | PARIS MONTPARNASSE | 23 | 0 | 13 |
| 2025-03 | International | BARCELONA | PARIS LYON | 7 | 0 | 6 |
| 2025-03 | International | ITALIE | PARIS LYON | 9 | 0 | 3 |
| 2025-03 | International | LAUSANNE | PARIS LYON | 10 | 1 | 4 |
| 2025-03 | National | ANNECY | PARIS LYON | 27 | 0 | 12 |
| 2025-03 | National | BESANCON FRANCHE COMTE TGV | PARIS LYON | 10 | -3 | 5 |
| 2025-03 | National | BORDEAUX ST JEAN | PARIS MONTPARNASSE | 66 | 0 | 38 |
| 2025-03 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | 52 | 0 | 22 |
| 2025-03 | National | MARSEILLE ST CHARLES | PARIS LYON | 59 | 0 | 38 |
| 2025-03 | National | NANCY | PARIS EST | 21 | 0 | 12 |
| 2025-03 | National | NANTES | STRASBOURG | 8 | 0 | 4 |
| 2025-03 | National | NIMES | PARIS LYON | 30 | 0 | 18 |
| 2025-03 | National | PARIS LYON | ANNECY | 17 | 0 | 10 |
| 2025-03 | National | PARIS LYON | LE CREUSOT MONTCEAU MONTCHANIN | 10 | 0 | 5 |
| 2025-03 | National | PARIS LYON | SAINT ETIENNE CHATEAUCREUX | 8 | 0 | 5 |
| 2025-03 | National | PARIS MONTPARNASSE | NANTES | 31 | 0 | 13 |
| 2025-03 | National | ST MALO | PARIS MONTPARNASSE | 6 | 0 | 2 |
| 2025-03 | National | STRASBOURG | NANTES | 4 | 0 | 2 |
| 2025-03 | National | TOULON | PARIS LYON | 47 | 0 | 30 |


### `nb_train_retard_sup_15 < nb_train_retard_sup_30`

3 lignes potentielles sont observées : deux en mai 2020 et une en mars 2025. Le champ >15 n’étant pas défini comme universellement applicable, cette relation n’est pas traitée comme un invariant général.


### Toutes les lignes présentant une inversion potentielle >15/<30

#### 2020-05 (2 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2020-05 | National | LILLE | MARSEILLE ST CHARLES | 1 | 3 | 1 |
| 2020-05 | National | MARNE LA VALLEE | MARSEILLE ST CHARLES | 1 | 3 | 1 |

#### 2025-03 (1 observations)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-03 | National | TOURS | PARIS MONTPARNASSE | 2 | 6 | 2 |


## 5. Annulations supérieures aux circulations prévues

63 lignes sont concernées entre avril et juin 2020 : 50 en avril, 9 en mai et 4 en juin. Toutes ont `nb_train_prevu = 0`, avec 1 à 21 annulations. Les comptages de retards au départ/à l’arrivée, >15/>30/>60 et les retards moyens sont tous nuls. Ce profil diffère des témoins des mêmes mois, dont la médiane est 86 trains prévus et 14 annulations.


### Toutes les observations avec annulations supérieures aux prévisions et indicateurs associés

#### 2020-04 (50 observations)

| date | service | gare_depart | gare_arrivee | nb_train_prevu | nb_annulation | nb_train_depart_retard | nb_train_retard_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 | retard_moyen_tous_trains_depart | retard_moyen_tous_trains_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-04 | National | PARIS MONTPARNASSE | ST MALO | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS MONTPARNASSE | TOURS | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | NANTES | STRASBOURG | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS NORD | DOUAI | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | DUNKERQUE | PARIS NORD | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | MARSEILLE ST CHARLES | TOURCOING | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | LYON PART DIEU | MARNE LA VALLEE | 0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | MARNE LA VALLEE | MARSEILLE ST CHARLES | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | MARSEILLE ST CHARLES | MARNE LA VALLEE | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | AIX EN PROVENCE TGV | 0 | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | BELLEGARDE (AIN) | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | GRENOBLE | PARIS LYON | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | PARIS EST | FRANCFORT | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | FRANCFORT | PARIS EST | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | PARIS LYON | GENEVE | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | ST MALO | PARIS MONTPARNASSE | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS NORD | DUNKERQUE | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | ANNECY | PARIS LYON | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | TOULON | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | TOURS | PARIS MONTPARNASSE | 0 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | BORDEAUX ST JEAN | TOURCOING | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | MARNE LA VALLEE | LYON PART DIEU | 0 | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | BELLEGARDE (AIN) | PARIS LYON | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | NICE VILLE | PARIS LYON | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PERPIGNAN | PARIS LYON | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | TOULON | PARIS LYON | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | ITALIE | PARIS LYON | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | LAUSANNE | PARIS LYON | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | BARCELONA | PARIS LYON | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS MONTPARNASSE | LA ROCHELLE VILLE | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | LYON PART DIEU | RENNES | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | LILLE | MARSEILLE ST CHARLES | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | TOURCOING | BORDEAUX ST JEAN | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | CHAMBERY CHALLES LES EAUX | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | PERPIGNAN | 0 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | MADRID | MARSEILLE ST CHARLES | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | MARSEILLE ST CHARLES | MADRID | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | LA ROCHELLE VILLE | PARIS MONTPARNASSE | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | RENNES | LYON PART DIEU | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | STRASBOURG | NANTES | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | MARSEILLE ST CHARLES | LILLE | 0 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | ANNECY | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | GRENOBLE | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | NICE VILLE | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | PARIS LYON | SAINT ETIENNE CHATEAUCREUX | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | National | SAINT ETIENNE CHATEAUCREUX | PARIS LYON | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | GENEVE | PARIS LYON | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | PARIS LYON | ITALIE | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-04 | International | PARIS LYON | LAUSANNE | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

#### 2020-05 (9 observations)

| date | service | gare_depart | gare_arrivee | nb_train_prevu | nb_annulation | nb_train_depart_retard | nb_train_retard_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 | retard_moyen_tous_trains_depart | retard_moyen_tous_trains_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-05 | National | STRASBOURG | NANTES | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | National | SAINT ETIENNE CHATEAUCREUX | PARIS LYON | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | International | MADRID | MARSEILLE ST CHARLES | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | National | BORDEAUX ST JEAN | TOURCOING | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | National | MARSEILLE ST CHARLES | TOURCOING | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | National | PARIS LYON | SAINT ETIENNE CHATEAUCREUX | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | International | MARSEILLE ST CHARLES | MADRID | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | National | NANTES | STRASBOURG | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-05 | National | TOURCOING | BORDEAUX ST JEAN | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

#### 2020-06 (4 observations)

| date | service | gare_depart | gare_arrivee | nb_train_prevu | nb_annulation | nb_train_depart_retard | nb_train_retard_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 | retard_moyen_tous_trains_depart | retard_moyen_tous_trains_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-06 | International | MADRID | MARSEILLE ST CHARLES | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-06 | International | STUTTGART | PARIS EST | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-06 | International | MARSEILLE ST CHARLES | MADRID | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-06 | International | PARIS EST | STUTTGART | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |


## 6. Retards moyens négatifs extrêmes

Le seuil extrême est celui de l’audit : moins de -15 minutes. Il concerne 11 moyennes à l’arrivée de tous les trains, 5 moyennes au départ de tous les trains et 2 moyennes conditionnelles à l’arrivée. Octobre-décembre 2019 regroupe 10 des 11 cas à l’arrivée de tous les trains, les 5 cas au départ et les 2 cas conditionnels. Le cas supplémentaire à l’arrivée date de février 2020.

Les liaisons Nimes → Paris Lyon, Valence Alixan TGV → Paris Lyon et Montpellier → Paris Lyon réapparaissent sur plusieurs mois concernés. Il s’agit de concentrations observées, pas d’une explication des valeurs.


### `retard_moyen_tous_trains_arrivee < -15`

#### 2019-10 (3 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-10 | National | NIMES | PARIS LYON | -90.6308399 | 17.23357143 | 70 | 266 | 12 |
| 2019-10 | National | VALENCE ALIXAN TGV | PARIS LYON | -68.92808399 | 35.32647059 | 68 | 265 | 11 |
| 2019-10 | National | MONTPELLIER | PARIS LYON | -80.85511288 | 45.92142857 | 49 | 263 | 12 |

#### 2019-11 (4 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-11 | National | MONTPELLIER | PARIS LYON | -150.5621142 | -30.5125 | 44 | 227 | 11 |
| 2019-11 | National | VALENCE ALIXAN TGV | PARIS LYON | -71.52882883 | 27.17254902 | 51 | 233 | 11 |
| 2019-11 | National | PARIS LYON | MONTPELLIER | -15.19254743 | 37.22719298 | 19 | 138 | 15 |
| 2019-11 | National | NIMES | PARIS LYON | -151.2910078 | -40.10925926 | 63 | 226 | 11 |

#### 2019-12 (3 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-12 | National | PARIS NORD | LILLE | -15.0986755 | 27.6937037 | 45 | 367 | 65 |
| 2019-12 | National | LYON PART DIEU | MONTPELLIER | -173.0769697 | 35.88111111 | 15 | 75 | 20 |
| 2019-12 | National | STRASBOURG | NANTES | -472.6388889 | 0 | 0 | 10 | 4 |

#### 2020-02 (1 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-02 | International | PARIS EST | FRANCFORT | -163.0419831 | 31.47222222 | 18 | 165 | 7 |


### `retard_moyen_tous_trains_depart < -15`

#### 2019-10 (2 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_depart | retard_moyen_depart | nb_train_depart_retard | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-10 | National | NIMES | PARIS LYON | -92.76830709 | 11.03809524 | 203 | 266 | 12 |
| 2019-10 | National | VALENCE ALIXAN TGV | PARIS LYON | -67.95374016 | 12.70444947 | 221 | 265 | 11 |

#### 2019-11 (3 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_depart | retard_moyen_depart | nb_train_depart_retard | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-11 | National | VALENCE ALIXAN TGV | PARIS LYON | -69.83828829 | 9.356324786 | 195 | 233 | 11 |
| 2019-11 | International | BARCELONA | PARIS LYON | -229.2694444 | 4.466666667 | 6 | 20 | 2 |
| 2019-11 | National | NIMES | PARIS LYON | -112.2620155 | 8.765614035 | 190 | 226 | 11 |


### `retard_moyen_arrivee < -15`

#### 2019-11 (2 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_arrivee | retard_moyen_tous_trains_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-11 | National | MONTPELLIER | PARIS LYON | -30.5125 | -150.5621142 | 44 | 227 | 11 |
| 2019-11 | National | NIMES | PARIS LYON | -40.10925926 | -151.2910078 | 63 | 226 | 11 |


## 7. Valeurs négatives de `retard_moyen_trains_retard_sup15`

L’audit identifie 8 lignes entre avril 2018 et avril 2019 et 6 liaisons-service distinctes. Marseille Saint Charles → Madrid apparaît trois fois. Plusieurs comptages associés `nb_train_retard_sup_15` valent zéro ou un ; l’interprétation exige donc de connaître précisément le dénominateur et le domaine d’application du champ.


### Toutes les observations négatives de `retard_moyen_trains_retard_sup15`

#### 2018-04 (2 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-04 | National | PARIS VAUGIRARD | BORDEAUX ST JEAN | -0.160714286 | 1 | 17.3 | 2 |
| 2018-04 | International | MARSEILLE ST CHARLES | MADRID | -2.714285714 | 0 | 0 | 0 |

#### 2018-09 (2 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-09 | National | RENNES | PARIS VAUGIRARD | -0.32654321 | 0 | 0 | 0 |
| 2018-09 | National | PARIS MONTPARNASSE | ST MALO | -2.404295533 | 1 | 18.875 | 2 |

#### 2019-02 (1 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-02 | International | MARSEILLE ST CHARLES | MADRID | -1.571428571 | 1 | 37 | 1 |

#### 2019-03 (2 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-03 | National | PARIS LYON | DIJON VILLE | -0.351875902 | 13 | 34.63666667 | 15 |
| 2019-03 | International | ZURICH | PARIS LYON | -0.601023392 | 5 | 38.98333333 | 5 |

#### 2019-04 (1 observations)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-04 | International | MARSEILLE ST CHARLES | MADRID | -4 | 0 | 0 | 0 |


## 8. Investigation détaillée de janvier 2025

Janvier 2025 contient 121 observations, dont 18 comptages >30 négatifs et 118 lignes où >30 < >60, soit 97.52% du mois. Les deux motifs se recoupent : les valeurs >15 et >60 des 18 lignes négatives figurent dans le tableau ci-dessous.

### Liaisons avec comptage >30 négatif en janvier 2025

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_30 | nb_train_retard_sup_15 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-01 | International | LAUSANNE | PARIS LYON | -4 | 15 | 9 |
| 2025-01 | National | DIJON VILLE | PARIS LYON | -1 | 47 | 30 |
| 2025-01 | National | DOUAI | PARIS NORD | -1 | 21 | 9 |
| 2025-01 | National | LE MANS | PARIS MONTPARNASSE | -1 | 51 | 30 |
| 2025-01 | National | MARSEILLE ST CHARLES | MARNE LA VALLEE | -2 | 43 | 17 |
| 2025-01 | National | LILLE | PARIS NORD | -1 | 49 | 18 |
| 2025-01 | National | LYON PART DIEU | LILLE | -44 | 64 | 21 |
| 2025-01 | National | LYON PART DIEU | MARNE LA VALLEE | -2 | 42 | 18 |
| 2025-01 | National | LYON PART DIEU | PARIS LYON | -3 | 43 | 17 |
| 2025-01 | National | QUIMPER | PARIS MONTPARNASSE | -1 | 31 | 14 |
| 2025-01 | National | STRASBOURG | PARIS EST | -1 | 67 | 30 |
| 2025-01 | National | MONTPELLIER | LYON PART DIEU | -1 | 23 | 10 |
| 2025-01 | National | VANNES | PARIS MONTPARNASSE | -1 | 34 | 16 |
| 2025-01 | National | ANGERS SAINT LAUD | PARIS MONTPARNASSE | -12 | 49 | 28 |
| 2025-01 | National | AVIGNON TGV | PARIS LYON | -5 | 48 | 25 |
| 2025-01 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | -1 | 40 | 17 |
| 2025-01 | National | LYON PART DIEU | MARSEILLE ST CHARLES | -2 | 75 | 39 |
| 2025-01 | National | RENNES | LYON PART DIEU | -2 | 10 | 3 |

### Toutes les liaisons avec inversion >30/<60 en janvier 2025

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-01 | International | FRANCFORT | PARIS EST | 27 | 0 | 18 |
| 2025-01 | International | GENEVE | PARIS LYON | 19 | 0 | 13 |
| 2025-01 | International | LAUSANNE | PARIS LYON | 15 | -4 | 9 |
| 2025-01 | International | ZURICH | PARIS LYON | 18 | 0 | 10 |
| 2025-01 | National | ANGOULEME | PARIS MONTPARNASSE | 28 | 0 | 10 |
| 2025-01 | National | DIJON VILLE | PARIS LYON | 47 | -1 | 30 |
| 2025-01 | National | DOUAI | PARIS NORD | 21 | -1 | 9 |
| 2025-01 | National | DUNKERQUE | PARIS NORD | 22 | 0 | 8 |
| 2025-01 | National | GRENOBLE | PARIS LYON | 27 | 0 | 12 |
| 2025-01 | National | LAVAL | PARIS MONTPARNASSE | 18 | 0 | 10 |
| 2025-01 | National | LILLE | LYON PART DIEU | 73 | 0 | 42 |
| 2025-01 | National | MARNE LA VALLEE | MARSEILLE ST CHARLES | 59 | 0 | 31 |
| 2025-01 | National | MARSEILLE ST CHARLES | LILLE | 41 | 0 | 13 |
| 2025-01 | National | MARSEILLE ST CHARLES | LYON PART DIEU | 38 | 0 | 18 |
| 2025-01 | National | MARSEILLE ST CHARLES | PARIS LYON | 58 | 0 | 28 |
| 2025-01 | National | NANTES | PARIS MONTPARNASSE | 74 | 1 | 50 |
| 2025-01 | National | PARIS EST | NANCY | 9 | 0 | 3 |
| 2025-01 | National | PARIS LYON | BESANCON FRANCHE COMTE TGV | 18 | 0 | 12 |
| 2025-01 | National | PARIS LYON | LYON PART DIEU | 48 | 0 | 24 |
| 2025-01 | National | PARIS LYON | PERPIGNAN | 21 | 0 | 11 |
| 2025-01 | National | PARIS MONTPARNASSE | LA ROCHELLE VILLE | 11 | 0 | 4 |
| 2025-01 | National | PARIS MONTPARNASSE | LAVAL | 18 | 0 | 9 |
| 2025-01 | National | PARIS MONTPARNASSE | QUIMPER | 15 | 0 | 8 |
| 2025-01 | National | PARIS NORD | DOUAI | 9 | 0 | 6 |
| 2025-01 | National | REIMS | PARIS EST | 3 | 0 | 2 |
| 2025-01 | National | SAINT ETIENNE CHATEAUCREUX | PARIS LYON | 7 | 0 | 2 |
| 2025-01 | National | ST MALO | PARIS MONTPARNASSE | 6 | 0 | 2 |
| 2025-01 | National | TOULON | PARIS LYON | 41 | 0 | 29 |
| 2025-01 | International | ITALIE | PARIS LYON | 5 | 0 | 1 |
| 2025-01 | National | AIX EN PROVENCE TGV | PARIS LYON | 57 | 0 | 31 |
| 2025-01 | National | BORDEAUX ST JEAN | PARIS MONTPARNASSE | 132 | 0 | 69 |
| 2025-01 | National | LA ROCHELLE VILLE | PARIS MONTPARNASSE | 17 | 0 | 3 |
| 2025-01 | National | LE MANS | PARIS MONTPARNASSE | 51 | -1 | 30 |
| 2025-01 | National | MARSEILLE ST CHARLES | MARNE LA VALLEE | 43 | -2 | 17 |
| 2025-01 | National | METZ | PARIS EST | 15 | 0 | 7 |
| 2025-01 | National | MULHOUSE VILLE | PARIS LYON | 37 | 0 | 25 |
| 2025-01 | National | NIMES | PARIS LYON | 23 | 0 | 10 |
| 2025-01 | National | PARIS LYON | CHAMBERY CHALLES LES EAUX | 49 | 0 | 21 |
| 2025-01 | National | PARIS LYON | DIJON VILLE | 42 | 0 | 22 |
| 2025-01 | National | PARIS LYON | LE CREUSOT MONTCEAU MONTCHANIN | 13 | 0 | 9 |
| 2025-01 | National | PARIS LYON | TOULON | 37 | 0 | 20 |
| 2025-01 | National | PARIS MONTPARNASSE | ST PIERRE DES CORPS | 30 | 0 | 11 |
| 2025-01 | National | PARIS NORD | ARRAS | 29 | 0 | 18 |
| 2025-01 | National | PARIS NORD | LILLE | 41 | 0 | 20 |
| 2025-01 | National | PERPIGNAN | PARIS LYON | 23 | 0 | 13 |
| 2025-01 | International | PARIS LYON | LAUSANNE | 31 | 0 | 10 |
| 2025-01 | International | PARIS LYON | ZURICH | 26 | 0 | 17 |
| 2025-01 | International | STUTTGART | PARIS EST | 22 | 0 | 9 |
| 2025-01 | National | ARRAS | PARIS NORD | 58 | 0 | 22 |
| 2025-01 | National | BESANCON FRANCHE COMTE TGV | PARIS LYON | 20 | 0 | 14 |
| 2025-01 | National | BORDEAUX ST JEAN | TOURCOING | 6 | 0 | 6 |
| 2025-01 | National | LE CREUSOT MONTCEAU MONTCHANIN | PARIS LYON | 14 | 0 | 8 |
| 2025-01 | National | LILLE | MARSEILLE ST CHARLES | 50 | 0 | 24 |
| 2025-01 | National | LILLE | PARIS NORD | 49 | -1 | 18 |
| 2025-01 | National | LYON PART DIEU | LILLE | 64 | -44 | 21 |
| 2025-01 | National | LYON PART DIEU | MARNE LA VALLEE | 42 | -2 | 18 |
| 2025-01 | National | LYON PART DIEU | PARIS LYON | 43 | -3 | 17 |
| 2025-01 | National | MACON LOCHE | PARIS LYON | 31 | 0 | 13 |
| 2025-01 | National | MARNE LA VALLEE | LYON PART DIEU | 78 | 0 | 45 |
| 2025-01 | National | NANTES | STRASBOURG | 10 | 0 | 3 |
| 2025-01 | National | PARIS LYON | AIX EN PROVENCE TGV | 49 | 0 | 25 |
| 2025-01 | National | PARIS LYON | ANNECY | 23 | 0 | 9 |
| 2025-01 | National | PARIS LYON | MACON LOCHE | 16 | 0 | 5 |
| 2025-01 | National | PARIS MONTPARNASSE | ANGERS SAINT LAUD | 47 | 0 | 12 |
| 2025-01 | National | PARIS MONTPARNASSE | ST MALO | 6 | 0 | 3 |
| 2025-01 | National | PARIS MONTPARNASSE | TOURS | 9 | 0 | 5 |
| 2025-01 | National | QUIMPER | PARIS MONTPARNASSE | 31 | -1 | 14 |
| 2025-01 | National | RENNES | PARIS MONTPARNASSE | 84 | 0 | 38 |
| 2025-01 | National | ST PIERRE DES CORPS | PARIS MONTPARNASSE | 27 | 0 | 3 |
| 2025-01 | National | STRASBOURG | NANTES | 4 | 0 | 2 |
| 2025-01 | National | STRASBOURG | PARIS EST | 67 | -1 | 30 |
| 2025-01 | National | TOULOUSE MATABIAU | PARIS MONTPARNASSE | 34 | 1 | 22 |
| 2025-01 | International | BARCELONA | PARIS LYON | 10 | 0 | 7 |
| 2025-01 | International | PARIS EST | FRANCFORT | 36 | 0 | 18 |
| 2025-01 | International | PARIS EST | STUTTGART | 23 | 0 | 13 |
| 2025-01 | International | PARIS LYON | BARCELONA | 7 | 0 | 2 |
| 2025-01 | National | BREST | PARIS MONTPARNASSE | 30 | 0 | 13 |
| 2025-01 | National | LYON PART DIEU | RENNES | 6 | 0 | 4 |
| 2025-01 | National | MONTPELLIER | LYON PART DIEU | 23 | -1 | 10 |
| 2025-01 | National | MONTPELLIER | PARIS LYON | 23 | 0 | 10 |
| 2025-01 | National | NICE VILLE | PARIS LYON | 34 | 0 | 23 |
| 2025-01 | National | PARIS LYON | MONTPELLIER | 14 | 0 | 10 |
| 2025-01 | National | PARIS LYON | NICE VILLE | 37 | 0 | 23 |
| 2025-01 | National | PARIS LYON | NIMES | 9 | 0 | 5 |
| 2025-01 | National | PARIS MONTPARNASSE | BREST | 22 | 0 | 8 |
| 2025-01 | National | PARIS MONTPARNASSE | LE MANS | 28 | 0 | 13 |
| 2025-01 | National | PARIS MONTPARNASSE | POITIERS | 40 | 0 | 16 |
| 2025-01 | National | PARIS MONTPARNASSE | RENNES | 65 | 0 | 30 |
| 2025-01 | National | PARIS MONTPARNASSE | TOULOUSE MATABIAU | 28 | 0 | 19 |
| 2025-01 | National | PARIS MONTPARNASSE | VANNES | 23 | 0 | 10 |
| 2025-01 | National | VALENCE ALIXAN TGV | PARIS LYON | 39 | 1 | 22 |
| 2025-01 | National | VANNES | PARIS MONTPARNASSE | 34 | -1 | 16 |
| 2025-01 | International | PARIS LYON | GENEVE | 39 | 0 | 13 |
| 2025-01 | National | ANGERS SAINT LAUD | PARIS MONTPARNASSE | 49 | -12 | 28 |
| 2025-01 | National | ANNECY | PARIS LYON | 17 | 0 | 7 |
| 2025-01 | National | AVIGNON TGV | PARIS LYON | 48 | -5 | 25 |
| 2025-01 | National | BELLEGARDE (AIN) | PARIS LYON | 27 | 0 | 19 |
| 2025-01 | National | CHAMBERY CHALLES LES EAUX | PARIS LYON | 40 | -1 | 17 |
| 2025-01 | National | LYON PART DIEU | MARSEILLE ST CHARLES | 75 | -2 | 39 |
| 2025-01 | National | LYON PART DIEU | MONTPELLIER | 42 | 0 | 22 |
| 2025-01 | National | MARSEILLE ST CHARLES | TOURCOING | 5 | 0 | 3 |
| 2025-01 | National | NANCY | PARIS EST | 12 | 0 | 4 |
| 2025-01 | National | PARIS EST | METZ | 12 | 0 | 7 |
| 2025-01 | National | PARIS EST | REIMS | 8 | 0 | 2 |
| 2025-01 | National | PARIS EST | STRASBOURG | 41 | 1 | 16 |
| 2025-01 | National | PARIS LYON | AVIGNON TGV | 41 | 0 | 18 |
| 2025-01 | National | PARIS LYON | BELLEGARDE (AIN) | 43 | 0 | 21 |
| 2025-01 | National | PARIS LYON | GRENOBLE | 21 | 0 | 13 |
| 2025-01 | National | PARIS LYON | MARSEILLE ST CHARLES | 52 | 0 | 26 |
| 2025-01 | National | PARIS LYON | MULHOUSE VILLE | 46 | 0 | 26 |
| 2025-01 | National | PARIS LYON | SAINT ETIENNE CHATEAUCREUX | 10 | 0 | 4 |
| 2025-01 | National | PARIS LYON | VALENCE ALIXAN TGV | 34 | 0 | 18 |
| 2025-01 | National | PARIS MONTPARNASSE | ANGOULEME | 34 | 0 | 15 |
| 2025-01 | National | PARIS MONTPARNASSE | BORDEAUX ST JEAN | 124 | 0 | 55 |
| 2025-01 | National | PARIS MONTPARNASSE | NANTES | 64 | 0 | 24 |
| 2025-01 | National | PARIS NORD | DUNKERQUE | 21 | 0 | 10 |
| 2025-01 | National | POITIERS | PARIS MONTPARNASSE | 38 | 0 | 12 |
| 2025-01 | National | RENNES | LYON PART DIEU | 10 | -2 | 3 |


## 9. Investigation détaillée d’avril 2020

Avril regroupe 50 des 63 lignes avec annulations supérieures aux prévisions, soit 50/123 (40.65%) des observations du mois. Les 13 autres sont en mai et juin. Pour les lignes signalées sur ces trois mois, `nb_train_prevu` et les indicateurs/moyennes de retard sont nuls, tandis que `nb_annulation` est positif. Les tableaux précédents détaillent les liaisons et comptages d’avril, ainsi que mai et juin, pour rendre visible la durée de trois mois du phénomène.

Comparaison observée : les témoins d’avril-juin ont une médiane de 86 trains prévus par ligne, contre zéro pour les lignes signalées. La médiane des annulations est 8 dans les lignes signalées, contre 14 chez les témoins. Un total d’annulations positif avec zéro train prévu déclenche le contrôle ; les seules données ne permettent pas de savoir s’il s’agit d’annulations du programme initial, de réductions ultérieures ou d’une autre convention de publication.


## 10. Investigation détaillée d’octobre-décembre 2019

Octobre-décembre 2019 regroupe 10/11 extrêmes à l’arrivée de tous les trains, 5/5 au départ et 2/2 à l’arrivée conditionnelle. Les origines Nimes, Valence Alixan TGV et Montpellier vers Paris Lyon se répètent. Les tableaux détaillent volumes prévus, annulations, trains retardés et autres moyennes pour chaque observation extrême. En novembre 2019, les deux moyennes conditionnelles d’arrivée valent -30.5125 et -40.10925926 avec 44 et 63 trains déclarés retardés ; les moyennes de tous les trains sont -150.5621142 et -151.2910078. Cet écart justifie une vérification des définitions, sans prouver quel champ est erroné.


## 11. Observations anormales et témoins des mêmes mois

Le tableau compare moyennes et médianes de chaque catégorie et de ses témoins mensuels. Un témoin est normal uniquement vis-à-vis de la règle étudiée ; une autre règle peut le signaler. Les écarts de distribution sont descriptifs et ne prouvent aucune causalité.

| Catégorie | Champ | Effectif anormal | Médiane des anomalies | Moyenne des anomalies | Effectif témoin | Médiane témoin | Moyenne témoin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Effectif négatifb_train_retard_sup_30 | nb_train_retard_sup_30 | 43 | -2 | -4.953488372 | 320 | 0 | 0.13125 |
| Effectif négatifb_train_retard_sup_30 | nb_train_retard_sup_15 | 43 | 39 | 36.44186047 | 320 | 22.5 | 26.775 |
| Effectif négatifb_train_retard_sup_30 | nb_train_retard_sup_60 | 43 | 17 | 16.81395349 | 320 | 11 | 13.146875 |
| Effectif négatifb_train_retard_sup_30 | nb_train_prevu | 43 | 338 | 359.627907 | 320 | 238 | 291.078125 |
| Effectif négatifb_train_retard_sup_30 | nb_annulation | 43 | 1 | 4.209302326 | 320 | 0 | 2.525 |
| Effectif négatifb_train_retard_sup_30 | nb_train_depart_retard | 43 | 130 | 138.3488372 | 320 | 33.5 | 63.0375 |
| Effectif négatifb_train_retard_sup_30 | nb_train_retard_arrivee | 43 | 49 | 51.46511628 | 320 | 30 | 36.6375 |
| Valeur négative de retard_moyen_trains_retard_sup15 | retard_moyen_trains_retard_sup15 | 8 | -1.086225981 | -1.516270826 | 621 | 4.696085859 | 5.466786162 |
| Valeur négative de retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | 8 | 1 | 2.625 | 621 | 19 | 21.39935588 |
| Valeur négative de retard_moyen_trains_retard_sup15 | retard_moyen_arrivee | 8 | 18.0875 | 18.349375 | 621 | 30.86747967 | 34.69558973 |
| Valeur négative de retard_moyen_trains_retard_sup15 | nb_train_retard_arrivee | 8 | 1.5 | 3.125 | 621 | 27 | 32.48953301 |
| Extrêmes all-train arrival average | retard_moyen_tous_trains_arrivee | 11 | -90.6308399 | -132.0768229 | 481 | 5.617142857 | 6.353041818 |
| Extrêmes all-train arrival average | retard_moyen_arrivee | 11 | 27.6937037 | 17.02786276 | 481 | 29.96604938 | 32.15674775 |
| Extrêmes all-train arrival average | nb_train_retard_arrivee | 11 | 45 | 40.18181818 | 481 | 26 | 33.20790021 |
| Extrêmes all-train arrival average | nb_train_prevu | 11 | 227 | 203.1818182 | 481 | 193 | 224.4885655 |
| Extrêmes all-train arrival average | nb_annulation | 11 | 11 | 16.27272727 | 481 | 5 | 9.185031185 |
| Extrêmes all-train departure average | retard_moyen_tous_trains_depart | 5 | -92.76830709 | -114.4183591 | 241 | 3.178896473 | 5.414381548 |
| Extrêmes all-train departure average | retard_moyen_depart | 5 | 9.356324786 | 9.26623004 | 241 | 6.097192982 | 10.17749387 |
| Extrêmes all-train departure average | nb_train_depart_retard | 5 | 195 | 163 | 241 | 137 | 159.9211618 |
| Extrêmes all-train departure average | nb_train_prevu | 5 | 233 | 202 | 241 | 213 | 258.4149378 |
| Extrêmes all-train departure average | nb_annulation | 5 | 11 | 9.4 | 241 | 5 | 7.024896266 |
| Extrêmes conditional arrival average | retard_moyen_arrivee | 2 | -35.31087963 | -35.31087963 | 121 | 28.82424242 | 30.87306544 |
| Extrêmes conditional arrival average | retard_moyen_tous_trains_arrivee | 2 | -150.926561 | -150.926561 | 121 | 5.546376812 | 5.453182756 |
| Extrêmes conditional arrival average | nb_train_retard_arrivee | 2 | 53.5 | 53.5 | 121 | 34 | 39.07438017 |
| Extrêmes conditional arrival average | nb_train_prevu | 2 | 226.5 | 226.5 | 121 | 203 | 249.4793388 |
| Extrêmes conditional arrival average | nb_annulation | 2 | 11 | 11 | 121 | 4 | 5.685950413 |
| Cancellations exceed planned | nb_train_prevu | 63 | 0 | 0 | 306 | 86 | 122.0980392 |
| Cancellations exceed planned | nb_annulation | 63 | 8 | 7.698412698 | 306 | 14 | 16.05882353 |
| Cancellations exceed planned | nb_train_depart_retard | 63 | 0 | 0 | 306 | 42 | 68.94117647 |
| Cancellations exceed planned | nb_train_retard_arrivee | 63 | 0 | 0 | 306 | 7 | 11.21568627 |
| Cancellations exceed planned | retard_moyen_tous_trains_arrivee | 63 | 0 | 0 | 306 | 3.179733911 | 4.697902115 |
| >30 count below >60 count | nb_train_retard_sup_30 | 354 | 0 | -0.5367231638 | 9 | 0 | 2.111111111 |
| >30 count below >60 count | nb_train_retard_sup_60 | 354 | 12 | 13.89265537 | 9 | 0 | 1.333333333 |
| >30 count below >60 count | nb_train_retard_sup_15 | 354 | 23.5 | 28.5 | 9 | 2 | 5.111111111 |
| >30 count below >60 count | nb_train_prevu | 354 | 249 | 303.0282486 | 9 | 52 | 148.5555556 |
| >30 count below >60 count | nb_annulation | 354 | 0 | 2.694915254 | 9 | 0 | 3.888888889 |
| >15 count below >30 count | nb_train_retard_sup_15 | 3 | 1 | 1.333333333 | 241 | 9 | 15.49377593 |
| >15 count below >30 count | nb_train_retard_sup_30 | 3 | 3 | 4 | 241 | 0 | 0.9419087137 |
| >15 count below >30 count | nb_train_retard_sup_60 | 3 | 1 | 1.333333333 | 241 | 3 | 6.908713693 |
| >15 count below >30 count | nb_train_prevu | 3 | 76 | 112.3333333 | 241 | 162 | 203.2282158 |
| >15 count below >30 count | nb_annulation | 3 | 13 | 13.33333333 | 241 | 4 | 9.020746888 |

### Liaisons-service touchées à plusieurs reprises

Seules les identités de liaisons comptant au moins deux mois ou observations concernés figurent ici ; toutes les observations individuelles sont détaillées plus haut.

| Catégorie | Service | Origine | Destination | Lignes concernées | Mois |
| --- | --- | --- | --- | --- | --- |
| Valeur négative de `nb_train_retard_sup_30` | National | LE MANS | PARIS MONTPARNASSE | 3 | 2025-01, 2025-02, 2025-03 |
| Valeur négative de `nb_train_retard_sup_30` | National | LYON PART DIEU | PARIS LYON | 3 | 2025-01, 2025-02, 2025-03 |
| Valeur négative de `nb_train_retard_sup_30` | National | STRASBOURG | PARIS EST | 3 | 2025-01, 2025-02, 2025-03 |
| Valeur négative de `nb_train_retard_sup_30` | National | DIJON VILLE | PARIS LYON | 2 | 2025-01, 2025-03 |
| Valeur négative de `nb_train_retard_sup_30` | National | LYON PART DIEU | LILLE | 2 | 2025-01, 2025-03 |
| Valeur négative de `retard_moyen_trains_retard_sup15` | International | MARSEILLE ST CHARLES | MADRID | 3 | 2018-04, 2019-02, 2019-04 |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | National | NIMES | PARIS LYON | 2 | 2019-10, 2019-11 |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | National | VALENCE ALIXAN TGV | PARIS LYON | 2 | 2019-10, 2019-11 |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | National | MONTPELLIER | PARIS LYON | 2 | 2019-10, 2019-11 |
| Valeur extrême de `retard_moyen_tous_trains_depart` | National | NIMES | PARIS LYON | 2 | 2019-10, 2019-11 |
| Valeur extrême de `retard_moyen_tous_trains_depart` | National | VALENCE ALIXAN TGV | PARIS LYON | 2 | 2019-10, 2019-11 |
| `nb_annulation > nb_train_prevu` | International | MADRID | MARSEILLE ST CHARLES | 3 | 2020-04, 2020-05, 2020-06 |
| `nb_annulation > nb_train_prevu` | International | MARSEILLE ST CHARLES | MADRID | 3 | 2020-04, 2020-05, 2020-06 |
| `nb_annulation > nb_train_prevu` | National | NANTES | STRASBOURG | 2 | 2020-04, 2020-05 |
| `nb_annulation > nb_train_prevu` | National | MARSEILLE ST CHARLES | TOURCOING | 2 | 2020-04, 2020-05 |
| `nb_annulation > nb_train_prevu` | National | BORDEAUX ST JEAN | TOURCOING | 2 | 2020-04, 2020-05 |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | International | FRANCFORT | PARIS EST | 3 | 2025-01, 2025-02, 2025-03 |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | International | GENEVE | PARIS LYON | 3 | 2025-01, 2025-02, 2025-03 |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | International | LAUSANNE | PARIS LYON | 3 | 2025-01, 2025-02, 2025-03 |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | International | ZURICH | PARIS LYON | 3 | 2025-01, 2025-02, 2025-03 |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | National | ANGOULEME | PARIS MONTPARNASSE | 3 | 2025-01, 2025-02, 2025-03 |

### Comparaisons complémentaires de toutes les moyennes négatives

Les témoins des mêmes mois excluent seulement les observations négatives dans le champ indiqué. Les moyennes et médianes comparent le groupe négatif aux témoins non négatifs des mois concernés.

| Champ négatif | Métrique comparée | Effectif négatif | Médiane des négatifs | Moyenne des négatifs | Effectif témoin | Médiane témoin | Moyenne témoin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retard_moyen_tous_trains_arrivee | retard_moyen_tous_trains_arrivee | 122 | -0.693324561 | -12.90904378 | 5631 | 4.843209877 | 5.665162903 |
| retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | 122 | 20.63333333 | 20.67739421 | 5631 | 32.66481481 | 34.33929148 |
| retard_moyen_tous_trains_arrivee | nb_train_retard_arrivee | 122 | 3 | 8.229508197 | 5631 | 26 | 33.59119162 |
| retard_moyen_tous_trains_arrivee | nb_train_prevu | 122 | 103 | 149.2295082 | 5631 | 222 | 262.9657254 |
| retard_moyen_tous_trains_depart | retard_moyen_tous_trains_depart | 170 | -0.1744964265 | -3.918746841 | 6476 | 2.19259643 | 3.111087393 |
| retard_moyen_tous_trains_depart | retard_moyen_depart | 170 | 3.578787879 | 5.235672401 | 6476 | 9.166666667 | 11.56538853 |
| retard_moyen_tous_trains_depart | nb_train_depart_retard | 170 | 5.5 | 17.75882353 | 6476 | 52 | 85.51219889 |
| retard_moyen_tous_trains_depart | nb_train_prevu | 170 | 97 | 138.5647059 | 6476 | 219 | 258.6897776 |
| retard_moyen_arrivee | retard_moyen_arrivee | 2 | -35.31087963 | -35.31087963 | 121 | 28.82424242 | 30.87306544 |
| retard_moyen_arrivee | retard_moyen_tous_trains_arrivee | 2 | -150.926561 | -150.926561 | 121 | 5.546376812 | 5.453182756 |
| retard_moyen_arrivee | nb_train_retard_arrivee | 2 | 53.5 | 53.5 | 121 | 34 | 39.07438017 |
| retard_moyen_arrivee | nb_train_prevu | 2 | 226.5 | 226.5 | 121 | 203 | 249.4793388 |
| retard_moyen_depart | retard_moyen_depart | 0 | - | - | 0 | - | - |
| retard_moyen_depart | retard_moyen_tous_trains_depart | 0 | - | - | 0 | - | - |
| retard_moyen_depart | nb_train_depart_retard | 0 | - | - | 0 | - | - |
| retard_moyen_depart | nb_train_prevu | 0 | - | - | 0 | - | - |
| retard_moyen_trains_retard_sup15 | retard_moyen_trains_retard_sup15 | 8 | -1.086225981 | -1.516270826 | 621 | 4.696085859 | 5.466786162 |
| retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | 8 | 1 | 2.625 | 621 | 19 | 21.39935588 |
| retard_moyen_trains_retard_sup15 | retard_moyen_arrivee | 8 | 18.0875 | 18.349375 | 621 | 30.86747967 | 34.69558973 |
| retard_moyen_trains_retard_sup15 | nb_train_retard_arrivee | 8 | 1.5 | 3.125 | 621 | 27 | 32.48953301 |
## 12. Résultats, limites et recommandations

### Constats observés

- `nb_train_retard_sup_30` est négatif dans 43 observations, uniquement de janvier à mars 2025. L’anomalie distincte >30/<60 touche 354/363 observations (97.52%) sur ces trois mois ; de nombreux exemples ont >30 nul ou négatif et >60 positif. Ce recoupement indique fortement une incohérence de champ propre à cette période, sans fournir les valeurs de remplacement correctes.
- `nb_train_retard_sup_15 < nb_train_retard_sup_30` apparaît dans trois lignes seulement, en mai 2020 et mars 2025. L’applicabilité limitée de >15 et l’absence d’indicateur dédié ne permettent pas de règle inconditionnelle.
- Les annulations dépassent les prévisions dans 63 observations d’avril à juin 2020, pas seulement en avril. Toutes ont zéro train prévu et zéro indicateur ou moyenne de retard. Ce profil est distinctif, mais peut dépendre des conventions du producteur ; leur définition doit précéder toute règle stricte.
- Les moyennes négatives extrêmes se concentrent sur quelques liaisons en octobre-décembre 2019. Plusieurs lignes combinent une moyenne tous trains très négative, une moyenne positive des trains retardés et des comptages non nuls. Ce signal concret mérite investigation sans prouver une cause précise.
- Huit valeurs négatives de `retard_moyen_trains_retard_sup15` apparaissent en 2018–2019. Plusieurs sont associées à un comptage >15 de zéro ou un : dénominateur et définition sont particulièrement importants.

### Ce que les données actuelles ne permettent pas d’établir

- Le motif >30/<60 de 2025 peut refléter une évolution de publication, une définition différente, une erreur de saisie ou une autre convention. Aucune métadonnée de version du champ ou d’applicabilité ne permet de trancher.
- Les annulations positives avec zéro train prévu d’avril-juin 2020 ne sont pas expliquées : le JSON ne contient ni méthode de comptage ni état de l’horaire de référence.
- Les valeurs seules ne définissent pas le signe et la plage attendus de chaque retard moyen. Une arrivée anticipée peut produire un retard négatif, tandis que les amplitudes extrêmes et agrégats associés posent d’autres questions.
- La comparaison mensuelle ne contrôle ni les horaires propres aux liaisons, ni la composition des trains, ni les définitions de service, ni les changements de calcul en amont.

### Recommandations pour les règles de nettoyage

1. Traiter les comptages négatifs comme des signalements prioritaires. Conserver les 43 comptages >30 négatifs et les 354 lignes >30/<60 dans un ensemble d’investigation explicitement daté. Ne pas remplacer les négatifs par zéro ni déduire de correction sans preuve de la source.
2. Consulter le producteur ou l’historique des modifications pour les définitions >30/>60 de janvier-mars 2025 et les valeurs systématiquement nulles ou négatives. N’envisager une règle ciblée qu’après confirmation de la période du changement.
3. Garder la relation >15 contre >30 conditionnelle jusqu’à confirmation de l’applicabilité par liaison. Ne pas imposer un ordre universel sur la seule base de cet export.
4. Conserver les annulations supérieures aux prévisions en attendant de savoir si `nb_annulation` se réfère à un programme initial et `nb_train_prevu` à un programme réduit ultérieur. Si confirmé, traiter cela comme exception contextuelle ou avertissement, pas comme motif de suppression.
5. Vérifier les lignes de retard d’octobre-décembre 2019 avec les définitions sources ou agrégats amont. Un indicateur de moyenne négative extrême peut alimenter une liste de vérification ; une correction automatique n’est pas encore justifiée.
6. Conserver ce rapport avec l’état des données brutes pour la reproductibilité. Ne pas transformer ces diagnostics en modifications de données à ce stade.

Tous les résultats sont descriptifs. Aucune cause n’est affirmée et aucune valeur brute n’a été modifiée.
