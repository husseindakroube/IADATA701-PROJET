# Régularité mensuelle des TGV SNCF : investigation des anomalies

## 1. Objectif et méthodologie

Cette investigation en lecture seule porte sur les anomalies relevées par l’audit existant de la qualité des données. Elle ne modifie pas les enregistrements bruts, les règles d’audit ni les données. L’implémentation de l’audit et son fichier généré `data_quality_report.txt` ont été consultés ; le présent rapport reprend le schéma SNCF, les prédicats d’anomalie et le seuil de retard extrême de `-15` minutes.

- Entrée : `data\raw\regularite-mensuelle-tgv-aqst.json` (12 907 enregistrements JSON).
- Synthèse d’audit existante : `data\reports\data_quality_report.txt` (lecture seule).
- Sortie : `data\reports\anomaly_investigation_report.md`.
- Les pourcentages mensuels utilisent le nombre total d’enregistrements du mois comme dénominateur. Les mois sans anomalie sont omis des tableaux de distribution peu denses.
- Pour les comparaisons à période identique, les témoins sont les enregistrements des mêmes mois concernés qui ne satisfont pas le prédicat d’anomalie considéré. Ils peuvent satisfaire un autre prédicat ; les comparaisons sont descriptives et non causales.
- Les listes détaillées contiennent toutes les lignes correspondantes ; le rapport d’audit d’origine reste inchangé.

La période complète compte 12 907 enregistrements répartis sur 105 valeurs mensuelles. L’audit identifie 26 champs. Les exemples numériques ci-dessous reprennent les valeurs telles qu’elles sont stockées dans la source. Le seuil `-15` est un seuil d’investigation repris de l’audit, et non une règle de nettoyage proposée.

## 2. Synthèse et distribution mensuelle

Le pourcentage mensuel correspond au nombre d’enregistrements concernés divisé par le nombre total de lignes du mois.

| Catégorie d’anomalie | Mois | Enregistrements concernés | Enregistrements du mois | Part mensuelle |
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

| Catégorie | Lignes concernées | Couples service-liaison distincts | Comptes mensuels non nuls |
| --- | --- | --- | --- |
| Valeur négative de `nb_train_retard_sup_30` | 43 | 29 | 2025-01: 18, 2025-02: 15, 2025-03: 10 |
| Valeur négative de `retard_moyen_trains_retard_sup15` | 8 | 6 | 2018-04: 2, 2018-09: 2, 2019-02: 1, 2019-03: 2, 2019-04: 1 |
| Valeur extrême de `retard_moyen_tous_trains_arrivee` | 11 | 8 | 2019-10: 3, 2019-11: 4, 2019-12: 3, 2020-02: 1 |
| Valeur extrême de `retard_moyen_tous_trains_depart` | 5 | 3 | 2019-10: 2, 2019-11: 3 |
| Valeur extrême de `retard_moyen_arrivee` | 2 | 2 | 2019-11: 2 |
| `nb_annulation > nb_train_prevu` | 63 | 52 | 2020-04: 50, 2020-05: 9, 2020-06: 4 |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | 354 | 121 | 2025-01: 118, 2025-02: 117, 2025-03: 119 |
| `nb_train_retard_sup_15 < nb_train_retard_sup_30` | 3 | 3 | 2020-05: 2, 2025-03: 1 |

### Distribution complète des retards négatifs selon l’audit

La section précédente consacrée aux retards extrêmes applique le seuil d’audit inférieur à -15 minutes. Ce tableau complémentaire couvre toutes les valeurs négatives (<0) des champs de retard moyen audités, afin que les valeurs négatives moins marquées ne soient pas masquées par le seuil extrême. La colonne « modérées » couvre l’intervalle [-15, 0) ; la colonne « extrêmes » correspond à < -15. `retard_moyen_depart` ne comporte aucune valeur négative dans cet instantané.

| Champ | Valeurs négatives | [-15, 0) | < -15 |
| --- | --- | --- | --- |
| retard_moyen_tous_trains_arrivee | 122 | 111 | 11 |
| retard_moyen_tous_trains_depart | 170 | 165 | 5 |
| retard_moyen_arrivee | 2 | 0 | 2 |
| retard_moyen_depart | 0 | 0 | 0 |
| retard_moyen_trains_retard_sup15 | 8 | 8 | 0 |

#### Comptes mensuels de toutes les valeurs négatives

| Champ | Mois | Lignes négatives | Enregistrements du mois | Part mensuelle |
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

43 lignes sont concernées sur 29 couples service-liaison distincts, toutes entre janvier et mars 2025. Janvier en compte 18/121 (14,88 %), février 15/121 (12,40 %) et mars 10/121 (8,26 %). La concentration porte donc sur trois mois, et non sur le seul mois de janvier.


### Toutes les liaisons et valeurs négatives de `nb_train_retard_sup_30`

#### 2025-01 (18 enregistrements)

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

#### 2025-02 (15 enregistrements)

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

#### 2025-03 (10 enregistrements)

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


## 4. Étude de l’ordre des seuils

La comparaison par paires entre >30 et >60 constitue le contrôle le plus direct de l’ordre cumulatif des seuils. Le champ >15 est soumis à une réserve d’applicabilité : selon le schéma SNCF, il concerne les liaisons en concurrence avec l’avion, mais le jeu de données ne contient pas d’indicateur d’applicabilité par liaison. Les résultats >15 versus >30 sont donc des alertes potentielles, et non des violations concluantes.

### `nb_train_retard_sup_30 < nb_train_retard_sup_60`

354 lignes présentent cette relation, toutes entre janvier et mars 2025 : 118/121 en janvier (97,52 %), 117/121 en février (96,69 %) et 119/121 en mars (98,35 %). Seules 9 des 363 lignes de ces trois mois ne satisfont pas l’inégalité. Les 354 lignes sont listées ci-dessous avec les trois indicateurs.


### Toutes les lignes où >30/<60 n’est pas ordonné (dont janvier 2025)

#### 2025-01 (118 enregistrements)

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

#### 2025-02 (117 enregistrements)

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

#### 2025-03 (119 enregistrements)

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

Trois lignes sont potentiellement concernées : deux en mai 2020 et une en mars 2025. Comme l’applicabilité de >15 n’est pas universelle selon la documentation, cette relation n’est pas considérée comme un invariant général.


### Toutes les lignes présentant un ordre potentiellement incohérent entre >15 et >30

#### 2020-05 (2 enregistrements)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2020-05 | National | LILLE | MARSEILLE ST CHARLES | 1 | 3 | 1 |
| 2020-05 | National | MARNE LA VALLEE | MARSEILLE ST CHARLES | 1 | 3 | 1 |

#### 2025-03 (1 enregistrements)

| date | service | gare_depart | gare_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-03 | National | TOURS | PARIS MONTPARNASSE | 2 | 6 | 2 |


## 5. Annulations plus nombreuses que les trains prévus

63 lignes sont concernées entre avril et juin 2020. Elles ne proviennent pas toutes d’avril : 50 sont en avril, 9 en mai et 4 en juin. Pour les 63 lignes, `nb_train_prevu = 0` ; le nombre d’annulations varie de 1 à 21. Les comptes de retards au départ et à l’arrivée, les comptes >15/>30/>60 ainsi que les retards moyens déclarés sont tous nuls. Ce profil diffère de celui des lignes non signalées des mêmes mois, dont la médiane des trains prévus est de 86 et celle des annulations de 14.


### Toutes les lignes où les annulations dépassent les trains prévus et indicateurs associés

#### 2020-04 (50 enregistrements)

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

#### 2020-05 (9 enregistrements)

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

#### 2020-06 (4 enregistrements)

| date | service | gare_depart | gare_arrivee | nb_train_prevu | nb_annulation | nb_train_depart_retard | nb_train_retard_arrivee | nb_train_retard_sup_15 | nb_train_retard_sup_30 | nb_train_retard_sup_60 | retard_moyen_tous_trains_depart | retard_moyen_tous_trains_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-06 | International | MADRID | MARSEILLE ST CHARLES | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-06 | International | STUTTGART | PARIS EST | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-06 | International | MARSEILLE ST CHARLES | MADRID | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020-06 | International | PARIS EST | STUTTGART | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |


## 6. Retards moyens extrêmement négatifs

Le seuil extrême reprend celui de l’audit existant, inférieur à -15 minutes. On compte 11 retards moyens à l’arrivée pour tous les trains sous ce seuil, 5 retards moyens au départ pour tous les trains et 2 retards moyens conditionnels à l’arrivée. La période d’octobre à décembre 2019 comprend 10 des 11 cas à l’arrivée tous trains, les 5 cas au départ tous trains et les 2 cas conditionnels à l’arrivée. Un autre cas à l’arrivée tous trains est observé en février 2020.

Certaines liaisons reviennent à plusieurs mois : Nîmes → Paris Lyon, Valence Alixan TGV → Paris Lyon et Montpellier → Paris Lyon. Il s’agit de concentrations observées, et non d’une explication des valeurs.


### `retard_moyen_tous_trains_arrivee < -15`

#### 2019-10 (3 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-10 | National | NIMES | PARIS LYON | -90.6308399 | 17.23357143 | 70 | 266 | 12 |
| 2019-10 | National | VALENCE ALIXAN TGV | PARIS LYON | -68.92808399 | 35.32647059 | 68 | 265 | 11 |
| 2019-10 | National | MONTPELLIER | PARIS LYON | -80.85511288 | 45.92142857 | 49 | 263 | 12 |

#### 2019-11 (4 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-11 | National | MONTPELLIER | PARIS LYON | -150.5621142 | -30.5125 | 44 | 227 | 11 |
| 2019-11 | National | VALENCE ALIXAN TGV | PARIS LYON | -71.52882883 | 27.17254902 | 51 | 233 | 11 |
| 2019-11 | National | PARIS LYON | MONTPELLIER | -15.19254743 | 37.22719298 | 19 | 138 | 15 |
| 2019-11 | National | NIMES | PARIS LYON | -151.2910078 | -40.10925926 | 63 | 226 | 11 |

#### 2019-12 (3 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-12 | National | PARIS NORD | LILLE | -15.0986755 | 27.6937037 | 45 | 367 | 65 |
| 2019-12 | National | LYON PART DIEU | MONTPELLIER | -173.0769697 | 35.88111111 | 15 | 75 | 20 |
| 2019-12 | National | STRASBOURG | NANTES | -472.6388889 | 0 | 0 | 10 | 4 |

#### 2020-02 (1 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_arrivee | retard_moyen_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-02 | International | PARIS EST | FRANCFORT | -163.0419831 | 31.47222222 | 18 | 165 | 7 |


### `retard_moyen_tous_trains_depart < -15`

#### 2019-10 (2 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_depart | retard_moyen_depart | nb_train_depart_retard | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-10 | National | NIMES | PARIS LYON | -92.76830709 | 11.03809524 | 203 | 266 | 12 |
| 2019-10 | National | VALENCE ALIXAN TGV | PARIS LYON | -67.95374016 | 12.70444947 | 221 | 265 | 11 |

#### 2019-11 (3 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_tous_trains_depart | retard_moyen_depart | nb_train_depart_retard | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-11 | National | VALENCE ALIXAN TGV | PARIS LYON | -69.83828829 | 9.356324786 | 195 | 233 | 11 |
| 2019-11 | International | BARCELONA | PARIS LYON | -229.2694444 | 4.466666667 | 6 | 20 | 2 |
| 2019-11 | National | NIMES | PARIS LYON | -112.2620155 | 8.765614035 | 190 | 226 | 11 |


### `retard_moyen_arrivee < -15`

#### 2019-11 (2 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_arrivee | retard_moyen_tous_trains_arrivee | nb_train_retard_arrivee | nb_train_prevu | nb_annulation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-11 | National | MONTPELLIER | PARIS LYON | -30.5125 | -150.5621142 | 44 | 227 | 11 |
| 2019-11 | National | NIMES | PARIS LYON | -40.10925926 | -151.2910078 | 63 | 226 | 11 |


## 7. Valeurs négatives de `retard_moyen_trains_retard_sup15`

L’audit a identifié 8 lignes entre avril 2018 et avril 2019. Elles concernent 6 couples service-liaison distincts ; Marseille Saint Charles → Madrid apparaît trois fois. Plusieurs valeurs associées de `nb_train_retard_sup_15` sont égales à zéro ou à un. Leur interprétation dépend donc du dénominateur exact du champ et de son applicabilité.


### Toutes les lignes avec une valeur négative de `retard_moyen_trains_retard_sup15`

#### 2018-04 (2 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-04 | National | PARIS VAUGIRARD | BORDEAUX ST JEAN | -0.160714286 | 1 | 17.3 | 2 |
| 2018-04 | International | MARSEILLE ST CHARLES | MADRID | -2.714285714 | 0 | 0 | 0 |

#### 2018-09 (2 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-09 | National | RENNES | PARIS VAUGIRARD | -0.32654321 | 0 | 0 | 0 |
| 2018-09 | National | PARIS MONTPARNASSE | ST MALO | -2.404295533 | 1 | 18.875 | 2 |

#### 2019-02 (1 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-02 | International | MARSEILLE ST CHARLES | MADRID | -1.571428571 | 1 | 37 | 1 |

#### 2019-03 (2 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-03 | National | PARIS LYON | DIJON VILLE | -0.351875902 | 13 | 34.63666667 | 15 |
| 2019-03 | International | ZURICH | PARIS LYON | -0.601023392 | 5 | 38.98333333 | 5 |

#### 2019-04 (1 enregistrements)

| date | service | gare_depart | gare_arrivee | retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | retard_moyen_arrivee | nb_train_retard_arrivee |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-04 | International | MARSEILLE ST CHARLES | MADRID | -4 | 0 | 0 | 0 |


## 8. Étude détaillée de janvier 2025

Janvier 2025 compte 121 enregistrements. On y trouve 18 comptes >30 négatifs et 118 lignes où >30 < >60, soit 97,52 % du mois. Les comptes >30 négatifs font partie du motif d’ordre : les valeurs >15 et >60 correspondantes sont également indiquées dans le tableau ci-dessous.

### Liaisons avec un compte >30 négatif en janvier 2025

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

### Toutes les liaisons de janvier 2025 où >30/<60 n’est pas ordonné

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


## 9. Étude détaillée d’avril 2020

Avril compte 50 des 63 lignes où les annulations dépassent les trains prévus, soit 50/123 (40,65 %) des enregistrements du mois. Les 13 autres lignes sont en mai et en juin. Pour toutes les lignes signalées sur ces trois mois, `nb_train_prevu` et les indicateurs/moyennes de retard sont nuls, tandis que `nb_annulation` est positif. Les liaisons et comptes exacts d’avril figurent dans le tableau des annulations ci-dessus ; les lignes de mai et juin y sont également incluses pour montrer que le motif s’étend sur trois mois.

Comparaison observée : les témoins d’avril à juin ont une médiane de 86 trains prévus par ligne, contre zéro pour les lignes signalées. Leur médiane d’annulations est de 8, contre 14 pour les témoins de la même période. Le contrôle d’audit est déclenché par un nombre positif d’annulations associé à zéro train prévu ; les données seules ne permettent pas d’établir si les annulations concernent l’horaire initial, une réduction ultérieure de l’offre ou une autre convention de déclaration.


## 10. Étude détaillée d’octobre à décembre 2019

La période d’octobre à décembre 2019 représente 10/11 des cas extrêmes à l’arrivée tous trains, 5/5 des cas extrêmes au départ tous trains et 2/2 des cas extrêmes conditionnels à l’arrivée. Les mêmes origines — Nîmes, Valence Alixan TGV et Montpellier — vers Paris Lyon réapparaissent. Les tableaux détaillés ci-dessus indiquent, pour chaque cas extrême, les volumes prévus, les annulations, les comptes de trains retardés et l’autre mesure de retard moyen. En novembre 2019, les deux moyennes conditionnelles à l’arrivée valent -30.5125 et -40.10925926, alors que 44 et 63 trains sont déclarés en retard à l’arrivée ; les moyennes à l’arrivée tous trains de ces lignes sont -150.5621142 et -151.2910078. Cette divergence justifie une vérification des définitions source, sans établir à elle seule quel champ serait erroné.


## 11. Comparaison des lignes anormales et non anormales du même mois

Le tableau présente les médianes et moyennes de chaque catégorie ainsi que celles des témoins du même mois. Un témoin est considéré comme normal uniquement au regard de la catégorie de la ligne ; il peut être signalé par un autre contrôle. Les écarts importants entre distributions sont descriptifs et ne doivent pas être interprétés comme des relations causales.

| Catégorie | Champ | n des anomalies | Médiane des anomalies | Moyenne des anomalies | n des témoins | Médiane des témoins | Moyenne des témoins |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Valeur négative de nb_train_retard_sup_30 | nb_train_retard_sup_30 | 43 | -2 | -4.953488372 | 320 | 0 | 0.13125 |
| Valeur négative de nb_train_retard_sup_30 | nb_train_retard_sup_15 | 43 | 39 | 36.44186047 | 320 | 22.5 | 26.775 |
| Valeur négative de nb_train_retard_sup_30 | nb_train_retard_sup_60 | 43 | 17 | 16.81395349 | 320 | 11 | 13.146875 |
| Valeur négative de nb_train_retard_sup_30 | nb_train_prevu | 43 | 338 | 359.627907 | 320 | 238 | 291.078125 |
| Valeur négative de nb_train_retard_sup_30 | nb_annulation | 43 | 1 | 4.209302326 | 320 | 0 | 2.525 |
| Valeur négative de nb_train_retard_sup_30 | nb_train_depart_retard | 43 | 130 | 138.3488372 | 320 | 33.5 | 63.0375 |
| Valeur négative de nb_train_retard_sup_30 | nb_train_retard_arrivee | 43 | 49 | 51.46511628 | 320 | 30 | 36.6375 |
| Valeur négative de retard_moyen_trains_retard_sup15 | retard_moyen_trains_retard_sup15 | 8 | -1.086225981 | -1.516270826 | 621 | 4.696085859 | 5.466786162 |
| Valeur négative de retard_moyen_trains_retard_sup15 | nb_train_retard_sup_15 | 8 | 1 | 2.625 | 621 | 19 | 21.39935588 |
| Valeur négative de retard_moyen_trains_retard_sup15 | retard_moyen_arrivee | 8 | 18.0875 | 18.349375 | 621 | 30.86747967 | 34.69558973 |
| Valeur négative de retard_moyen_trains_retard_sup15 | nb_train_retard_arrivee | 8 | 1.5 | 3.125 | 621 | 27 | 32.48953301 |
| Moyenne extrême à l’arrivée tous trains | retard_moyen_tous_trains_arrivee | 11 | -90.6308399 | -132.0768229 | 481 | 5.617142857 | 6.353041818 |
| Moyenne extrême à l’arrivée tous trains | retard_moyen_arrivee | 11 | 27.6937037 | 17.02786276 | 481 | 29.96604938 | 32.15674775 |
| Moyenne extrême à l’arrivée tous trains | nb_train_retard_arrivee | 11 | 45 | 40.18181818 | 481 | 26 | 33.20790021 |
| Moyenne extrême à l’arrivée tous trains | nb_train_prevu | 11 | 227 | 203.1818182 | 481 | 193 | 224.4885655 |
| Moyenne extrême à l’arrivée tous trains | nb_annulation | 11 | 11 | 16.27272727 | 481 | 5 | 9.185031185 |
| Moyenne extrême au départ tous trains | retard_moyen_tous_trains_depart | 5 | -92.76830709 | -114.4183591 | 241 | 3.178896473 | 5.414381548 |
| Moyenne extrême au départ tous trains | retard_moyen_depart | 5 | 9.356324786 | 9.26623004 | 241 | 6.097192982 | 10.17749387 |
| Moyenne extrême au départ tous trains | nb_train_depart_retard | 5 | 195 | 163 | 241 | 137 | 159.9211618 |
| Moyenne extrême au départ tous trains | nb_train_prevu | 5 | 233 | 202 | 241 | 213 | 258.4149378 |
| Moyenne extrême au départ tous trains | nb_annulation | 5 | 11 | 9.4 | 241 | 5 | 7.024896266 |
| Moyenne conditionnelle extrême à l’arrivée | retard_moyen_arrivee | 2 | -35.31087963 | -35.31087963 | 121 | 28.82424242 | 30.87306544 |
| Moyenne conditionnelle extrême à l’arrivée | retard_moyen_tous_trains_arrivee | 2 | -150.926561 | -150.926561 | 121 | 5.546376812 | 5.453182756 |
| Moyenne conditionnelle extrême à l’arrivée | nb_train_retard_arrivee | 2 | 53.5 | 53.5 | 121 | 34 | 39.07438017 |
| Moyenne conditionnelle extrême à l’arrivée | nb_train_prevu | 2 | 226.5 | 226.5 | 121 | 203 | 249.4793388 |
| Moyenne conditionnelle extrême à l’arrivée | nb_annulation | 2 | 11 | 11 | 121 | 4 | 5.685950413 |
| Annulations supérieures aux trains prévus | nb_train_prevu | 63 | 0 | 0 | 306 | 86 | 122.0980392 |
| Annulations supérieures aux trains prévus | nb_annulation | 63 | 8 | 7.698412698 | 306 | 14 | 16.05882353 |
| Annulations supérieures aux trains prévus | nb_train_depart_retard | 63 | 0 | 0 | 306 | 42 | 68.94117647 |
| Annulations supérieures aux trains prévus | nb_train_retard_arrivee | 63 | 0 | 0 | 306 | 7 | 11.21568627 |
| Annulations supérieures aux trains prévus | retard_moyen_tous_trains_arrivee | 63 | 0 | 0 | 306 | 3.179733911 | 4.697902115 |
| Compte >30 inférieur au compte >60 | nb_train_retard_sup_30 | 354 | 0 | -0.5367231638 | 9 | 0 | 2.111111111 |
| Compte >30 inférieur au compte >60 | nb_train_retard_sup_60 | 354 | 12 | 13.89265537 | 9 | 0 | 1.333333333 |
| Compte >30 inférieur au compte >60 | nb_train_retard_sup_15 | 354 | 23.5 | 28.5 | 9 | 2 | 5.111111111 |
| Compte >30 inférieur au compte >60 | nb_train_prevu | 354 | 249 | 303.0282486 | 9 | 52 | 148.5555556 |
| Compte >30 inférieur au compte >60 | nb_annulation | 354 | 0 | 2.694915254 | 9 | 0 | 3.888888889 |
| Compte >15 inférieur au compte >30 | nb_train_retard_sup_15 | 3 | 1 | 1.333333333 | 241 | 9 | 15.49377593 |
| Compte >15 inférieur au compte >30 | nb_train_retard_sup_30 | 3 | 3 | 4 | 241 | 0 | 0.9419087137 |
| Compte >15 inférieur au compte >30 | nb_train_retard_sup_60 | 3 | 1 | 1.333333333 | 241 | 3 | 6.908713693 |
| Compte >15 inférieur au compte >30 | nb_train_prevu | 3 | 76 | 112.3333333 | 241 | 162 | 203.2282158 |
| Compte >15 inférieur au compte >30 | nb_annulation | 3 | 13 | 13.33333333 | 241 | 4 | 9.020746888 |

### Couples service-liaison concernés à plusieurs reprises

Seules les liaisons concernées pendant au moins deux mois ou dans au moins deux enregistrements sont présentées ici ; toutes les lignes correspondantes figurent dans les tableaux détaillés précédents.

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

### Comparaisons complémentaires de toutes les moyennes de retard négatives

Ces témoins du même mois excluent uniquement les enregistrements dont la valeur du champ indiqué est négative. Les médianes et moyennes sont présentées pour le groupe des valeurs négatives et celui des témoins non négatifs, pendant les mois où des valeurs négatives sont observées.

| Champ négatif | Métrique comparée | n négatif | Médiane négative | Moyenne négative | n des témoins | Médiane des témoins | Moyenne des témoins |
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
## 12. Résultats, limites et recommandations pour la suite

### Constats observés

- `nb_train_retard_sup_30` est négatif dans 43 enregistrements, uniquement de janvier à mars 2025. L’anomalie distincte >30/<60 concerne 354/363 (97,52 %) des enregistrements de ces trois mois ; dans de nombreux exemples, la valeur du champ >30 est égale à zéro ou négative tandis que >60 est positif. Ce chevauchement constitue un indice fort d’incohérence de champ propre à une période, mais ne permet pas de déterminer les valeurs de remplacement correctes.
- `nb_train_retard_sup_15 < nb_train_retard_sup_30` apparaît dans seulement trois lignes (mai 2020 et mars 2025). Le champ >15 ayant une applicabilité limitée aux liaisons et aucun indicateur d’applicabilité n’étant disponible, une règle inconditionnelle ne serait pas étayée.
- Les annulations dépassent le nombre de trains prévus dans 63 enregistrements d’avril à juin 2020, et non en avril seulement. Chaque ligne signalée présente zéro train prévu et des indicateurs/moyennes de retard égaux à zéro. Ce motif est distinctif dans les données, mais un plan égal à zéro peut coexister avec des annulations selon la convention du producteur ; il faut connaître la sémantique source avant d’imposer une règle.
- Les retards moyens extrêmement négatifs se concentrent sur un petit nombre de liaisons entre octobre et décembre 2019. Dans plusieurs lignes, une moyenne tous trains fortement négative coexiste avec une moyenne positive pour les trains retardés et des comptes non nuls. Il s’agit d’un signal concret de cohérence à examiner, et non de la preuve d’une cause précise.
- Huit valeurs négatives de `retard_moyen_trains_retard_sup15` apparaissent entre 2018 et 2019. Plusieurs sont associées à une valeur de `nb_train_retard_sup_15` égale à zéro ou à un ; le dénominateur exact et la définition du champ sont donc particulièrement importants.

### Ce que les données disponibles ne permettent pas d’établir

- Les données ne permettent pas d’établir si le motif >30/<60 de 2025 reflète un changement de déclaration côté source, une modification de définition du champ, une erreur de saisie ou une autre convention. Ces enregistrements ne contiennent ni version des champs ni métadonnées d’applicabilité.
- Elles n’expliquent pas pourquoi des annulations positives coexistent avec zéro train prévu d’avril à juin 2020 ; les enregistrements JSON ne fournissent ni méthode de calcul des annulations ni instantané des horaires.
- Elles ne permettent pas d’établir le signe ou l’étendue attendus de chaque champ `retard moyen` à partir des seules valeurs. Une marche en avance peut produire des retards négatifs, tandis que les amplitudes extrêmes et les agrégats associés soulèvent d’autres questions.
- Le rapport compare les enregistrements au sein des mois ; il ne contrôle pas les horaires propres aux liaisons, la composition des trains, les définitions des services ou les changements de calcul en amont.

### Recommandations pour la conception de règles de nettoyage

1. Traiter les comptes négatifs comme des indicateurs de validation prioritaires. En particulier, conserver les 43 comptes >30 négatifs et les 354 lignes >30/<60 dans un ensemble d’investigation explicite, délimité dans le temps. Ne pas remplacer les valeurs négatives par zéro ni déduire des comptes corrigés sans source faisant autorité.
2. Interroger le producteur des données ou consulter l’historique des modifications du jeu de données pour connaître les définitions >30 et >60 de janvier à mars 2025 ainsi que les valeurs systématiquement égales à zéro ou négatives de 2025. N’envisager une règle ciblée qu’après confirmation de la date de changement.
3. Conserver la relation >15 versus >30 comme conditionnelle tant que l’applicabilité par liaison n’est pas établie. Ne pas imposer un ordre universel à partir de ce seul jeu de données.
4. Préserver les lignes où les annulations dépassent les trains prévus tant qu’il n’est pas établi si `nb_annulation` se rapporte aux services initialement prévus tandis que `nb_train_prevu` reflète un horaire réduit ultérieur. Si cela est confirmé, représenter le cas par une exception contextuelle ou un avertissement plutôt que supprimer les lignes.
5. Comparer les retards par liaison d’octobre à décembre 2019 à la documentation source ou aux agrégats en amont. Un indicateur fondé sur un seuil de retards moyens extrêmement négatifs pourrait alimenter une file de vérification, mais une règle de correction stricte n’est pas encore justifiée.
6. Conserver ensemble ce rapport d’investigation et l’instantané brut source pour assurer la reproductibilité ; ne pas encore encoder ces conditions diagnostiques sous forme de transformations.

Tous les résultats de ce document sont des constats descriptifs. Aucune cause n’est avancée et aucune valeur brute n’a été modifiée.
