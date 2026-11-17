# RailInsight — Analyse de graphe et prédiction des retards TGV

Ce dépôt contient une contribution au projet **RailInsight**, consacrée à l'analyse du réseau ferroviaire TGV et à l'enrichissement de modèles de Machine Learning par des caractéristiques issues de la théorie des graphes.

L'objectif est d'étudier si la structure du réseau et les volumes de circulation peuvent améliorer la prédiction du taux de trains en retard de plus de 15 minutes sur une liaison donnée.

## 1. Données

Les données proviennent du jeu de données mensuel de régularité des TGV publié par l'AQST.

Le dataset utilisé couvre la période de **janvier 2018 à septembre 2026**.

| **Caractéristique**            | **Valeur** |
| ------------------------------ | ---------- |
| Observations brutes            | 12 907     |
| Gares distinctes               | 59         |
| Liaisons orientées distinctes  | 130        |
| Services                       | 2          |
| Observations avec cible valide | 12 832     |

Une observation correspond à une liaison orientée, un service et un mois.

### Variable cible

Nous cherchons à prédire :

$$
\text{delay\_rate\_15} =
\frac{\text{Nombre de trains en retard > 15 min}}{\text{Nombre de trains ayant circulé}}
$$

avec :

$$
\text{circulated} = \text{planned} - \text{cancelled}
$$

Une observation est considérée comme valide lorsque les comptages sont cohérents, que le nombre de trains ayant circulé est strictement positif et que le nombre de retards est compris entre zéro et le nombre de trains ayant circulé.

Les observations invalides sont exclues de l'entraînement et de l'évaluation.

### Qualité des données

Le diagnostic initial a notamment identifié :

- 75 observations avec une cible invalide ;
- 63 observations avec plus d'annulations que de circulations prévues ;
- 43 valeurs négatives pour les retards supérieurs à 30 minutes, toutes observées en 2025 ;
- 354 incohérences entre les comptages de retards supérieurs à 30 et 60 minutes ;
- aucun doublon exact ni doublon sur la combinaison mois, service et liaison.

Ces contrôles sont disponibles dans `scripts/exploration/data_quality.py`.

## 2. Modélisation du réseau ferroviaire

Le réseau est représenté par un **graphe orienté** :

- chaque nœud représente une gare ;
- chaque arête représente une liaison orientée entre deux gares ;
- le poids d'une arête représente le nombre de trains ayant circulé sur cette liaison pendant la période étudiée.

Deux représentations sont utilisées :

- un graphe non pondéré, pour étudier la structure du réseau ;
- un graphe pondéré par les circulations, pour prendre en compte les volumes de trafic.

### Variables de graphe

Pour chaque gare de départ et d'arrivée, plusieurs caractéristiques sont calculées :

| **Caractéristique**    | **Interprétation**                                      |
| ---------------------- | ------------------------------------------------------- |
| In-degree              | Nombre de liaisons entrantes                            |
| Out-degree             | Nombre de liaisons sortantes                            |
| Betweenness centrality | Position d'intermédiaire dans le réseau                 |
| PageRank               | Importance structurelle de la gare                      |
| In-strength            | Volume total de trains entrants                         |
| Out-strength           | Volume total de trains sortants                         |
| Weighted PageRank      | Importance prenant en compte les volumes de circulation |

Ces caractéristiques sont associées à chaque observation pour sa gare de départ et sa gare d'arrivée.

### Variables de liaison

Trois caractéristiques supplémentaires décrivent directement la liaison à prédire :

| **Variable**          | **Description**                                                   |
| --------------------- | ----------------------------------------------------------------- |
| `edge_volume`         | Nombre de trains sur la liaison orientée                          |
| `edge_traffic_share`  | Part de cette liaison dans le trafic sortant de la gare de départ |
| `edge_reverse_volume` | Nombre de trains circulant sur la liaison inverse                 |

Ces variables permettent de caractériser l'importance relative d'une liaison au sein du réseau.

## 3. Construction temporelle des variables

Pour éviter toute **fuite temporelle (*data leakage*)**, les variables de graphe et les statistiques historiques sont construites à partir des **12 mois précédant le mois à prédire**.

Par exemple, pour une observation de janvier 2025 :

- le réseau est construit avec les données de janvier à décembre 2024 ;
- les centralités et les volumes des liaisons sont calculés sur cet historique ;
- les données de janvier 2025 ne participent pas à la construction de ces variables.

Une variable supplémentaire est calculée pour chaque liaison :

$$
\text{historical\_delay\_rate\_15} =
\frac{\sum_{\text{historique}} \text{late\_15}}{\sum_{\text{historique}} \text{circulated}}
$$

Ce taux historique tient compte des volumes de circulation plutôt que de calculer une simple moyenne des taux mensuels.

La première année sert à constituer l'historique initial. Le dataset ML commence donc en **janvier 2019**.

Après construction des caractéristiques et filtrage des cibles invalides, il contient **11 272 observations**.

Les caractéristiques absentes de l'historique restent manquantes lors de la construction du dataset. Leur imputation est réalisée ensuite dans le pipeline ML.

## 4. Modélisation Machine Learning

Le modèle utilisé est un `HistGradientBoostingRegressor` de scikit-learn.

Les variables catégorielles (`service`, `departure`, `arrival`) sont encodées avec `OneHotEncoder`.

Le mois est conservé comme variable numérique. Les caractéristiques numériques supplémentaires sont imputées en cas de valeurs manquantes, avec ajout d'indicateurs de valeurs manquantes.

### Découpage temporel

Le découpage respecte l'ordre chronologique des observations :

| **Ensemble**         | **Période**         | **Utilisation**                            |
| -------------------- | ------------------- | ------------------------------------------ |
| Entraînement initial | 2019–2023           | Comparaison et optimisation des modèles    |
| Validation           | 2024                | Sélection des variables et hyperparamètres |
| Test final           | 2025–septembre 2026 | Évaluation hors échantillon                |

Pour l'évaluation finale, le modèle est réentraîné sur **2019–2024**, puis évalué sur **2025–2026**.

Aucune répartition aléatoire des observations n'est utilisée.

## 5. Étude d'ablation

Plusieurs groupes de variables sont comparés afin d'évaluer leur intérêt prédictif.

La baseline utilise uniquement le service, la gare de départ, la gare d'arrivée et le mois.

Les expériences d'ablation utilisent les mêmes hyperparamètres afin d'isoler l'effet des variables ajoutées.

### Résultats sur la validation 2024

| **Configuration**         | **MAE**  | **RMSE** | **MAE pondérée** |
| ------------------------- | -------- | -------- | ---------------- |
| Historique                | 0.031594 | 0.044013 | 0.026628         |
| Historique + liaisons     | 0.031604 | 0.044230 | 0.026600         |
| Liaisons                  | 0.032339 | 0.045192 | 0.027354         |
| Baseline                  | 0.032626 | 0.045984 | 0.027392         |
| Centralités structurelles | 0.033362 | 0.046562 | 0.027998         |
| Réseau complet            | 0.037344 | 0.049666 | 0.033048         |
| Centralités pondérées     | 0.038082 | 0.049524 | 0.034663         |

Le taux historique de retard constitue la variable supplémentaire la plus informative dans cette comparaison.

Les caractéristiques de liaison apportent également de l'information, tandis que l'ajout de toutes les centralités ne garantit pas une amélioration des prédictions.

Ces résultats montrent l'intérêt d'une sélection ciblée des variables de graphe plutôt que de leur ajout systématique.

## 6. Optimisation des hyperparamètres

Une recherche sur grille est effectuée sur les deux configurations les plus prometteuses :

- Historique
- Historique + liaisons.

La grille explore :

| **Hyperparamètre** | **Valeurs**      |
| ------------------ | ---------------- |
| `max_iter`         | 100, 150, 250    |
| `learning_rate`    | 0.03, 0.05, 0.10 |
| `max_leaf_nodes`   | 7, 15, 31        |

La sélection est réalisée selon la **MAE sur la validation 2024**.

Les configurations retenues sont :

| **Modèle**            | **max_iter** | **learning_rate** | **max_leaf_nodes** |
| --------------------- | ------------ | ----------------- | ------------------ |
| Historique            | 100          | 0.03              | 7                  |
| Historique + liaisons | 150          | 0.05              | 7                  |

## 7. Évaluation finale

Après sélection des hyperparamètres, les modèles sont réentraînés sur les observations de 2019 à 2024 et évalués sur la période 2025–septembre 2026.

- Observations d'entraînement : **8 689**
- Observations de test : **2 583**

| **Modèle**                | **MAE**      | **RMSE**     | **MAE pondérée** |
| ------------------------- | ------------ | ------------ | ---------------- |
| Historique                | 0.040603     | 0.064661     | 0.034638         |
| **Historique + liaisons** | **0.039209** | **0.062477** | **0.033309**     |

L'ajout des caractéristiques de liaison au taux historique de retard permet une **réduction relative d'environ 3,43 % de la MAE** sur le jeu de test.

Les trois métriques sont améliorées.

La MAE pondérée utilise le nombre de trains circulés comme poids : les observations correspondant à des volumes de trafic importants contribuent davantage à cette mesure.

### Interprétation

Les résultats suggèrent que les caractéristiques directement associées aux liaisons apportent une information prédictive complémentaire à l'historique des retards.

En revanche, les centralités globales du réseau ne se révèlent pas systématiquement bénéfiques avec le modèle et les paramètres étudiés.

Il s'agit d'une amélioration mesurée sur ce dataset et ce découpage temporel, et non d'une garantie de généralisation à d'autres périodes ou réseaux.

## 8. Organisation du code

```text
src/sncf_rail_insight/
├── dataset.py
├── preprocessing.py
├── graph/
│   ├── network.py
│   ├── centrality.py
│   └── routes.py
└── ml/
    ├── historical.py
    ├── enrichment.py
    ├── temporal.py
    ├── models.py
    └── evaluation.py

scripts/
├── exploration/
│   ├── data_quality.py
│   └── network_analysis.py
└── experiments/
    ├── compare_models.py
    ├── tune_models.py
    └── evaluate_models.py

tests/
├── test_graph_features.py
├── test_ml_preprocessing.py
└── test_temporal_features.py

```

Les fonctions réutilisables sont placées dans `src/`, les scripts d'analyse et d'expérimentation dans `scripts/`, et les vérifications automatisées dans `tests/`.

## 9. Installation et reproduction

Le projet utilise Python 3.12 et `uv` pour la gestion de l'environnement.

Depuis la racine du dépôt :

```bash
uv sync
```

Le fichier de données attendu est :

```text
data/raw/regularite-mensuelle-tgv-aqst.csv
```

### Explorer les données

```bash
uv run python scripts/exploration/data_quality.py
uv run python scripts/exploration/network_analysis.py
```

### Reproduire les expériences

```bash
# Comparaison des groupes de variables
uv run python scripts/experiments/compare_models.py

# Optimisation des hyperparamètres
uv run python scripts/experiments/tune_models.py

# Évaluation finale
uv run python scripts/experiments/evaluate_models.py
```

### Exécuter les tests

```bash
uv run pytest tests/ -v
uv run ruff check src/ scripts/ tests/
```

Les tests couvrent notamment l'encodage, les valeurs manquantes, le calcul des caractéristiques de liaison et l'absence de fuite temporelle dans le feature engineering.

## 10. Limites et perspectives

Plusieurs pistes restent ouvertes :

- Étudier les erreurs par liaison, période et niveau de trafic.
- Analyser plus précisément l'apport individuel des caractéristiques de graphe.
- Évaluer la robustesse des résultats sur plusieurs fenêtres temporelles.
- Explorer des modèles plus directement adaptés aux données relationnelles ou spatio-temporelles.
- Étudier l'effet de variables externes, notamment les événements perturbant l'exploitation ferroviaire.

Cette contribution se concentre donc sur **l'analyse du graphe ferroviaire et l'amélioration de la prédiction des retards par des variables de réseau**.