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
\mathrm{delay\_rate\_15} =
\frac{\text{Nombre de trains en retard > 15 min}}{\text{Nombre de trains ayant circulé}}
$$

avec :

`circulated = planned - cancelled`

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
\mathrm{historical\_delay\_rate\_15} =
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

## 8. Étude complémentaire : historique récent et tendance

Une expérience distincte a évalué, sur la **validation 2024** (entraînement 2019–2023), l'ajout d'une moyenne récente sur **3 mois** et d'une tendance de retard (taux récent sur 3 mois moins taux historique sur 12 mois) aux variables historiques et de liaison. Toutes ces variables sont calculées **avant le mois à prédire**.

| Configuration expérimentale | MAE | RMSE | MAE pondérée |
| --- | ---: | ---: | ---: |
| Historique 12 mois + liaisons | 0.030915 | 0.042623 | 0.026108 |
| + historique récent 3 mois | 0.030201 | 0.041711 | 0.025390 |
| + tendance 3 mois − 12 mois | **0.030029** | **0.041422** | **0.025244** |
| Baseline naïve historique 12 mois | 0.031055 | 0.042828 | 0.026113 |
| Baseline naïve historique 3 mois | 0.032404 | 0.045293 | 0.027713 |

Ces chiffres sont des **résultats de validation**, pas une réévaluation du modèle final sur 2025–2026. Le modèle final documenté en section 7 reste la comparaison historique / historique + liaison. Cette expérience complémentaire montre qu'un signal temporel récent pourrait être utile et mérite une évaluation finale spécifique avant toute revendication de gain hors échantillon.

Script : `scripts/experiments/compare_recent_features.py`.

## 9. Livrables d'analyse et d'intégration

En plus des scripts d'entraînement et d'évaluation, la contribution met à disposition :

- **Six CSV** dans `outputs/streamlit/` : `network_nodes.csv`, `network_edges.csv`, `predictions.csv`, `monthly_errors.csv`, `route_errors.csv`, `delay_level_errors.csv`.

- **Quatre PNG de reporting** générés par `scripts/reporting/generate_streamlit_assets.py`, à utiliser comme illustrations ou exemples à adapter à Streamlit.

- **Un explorateur cartographique mensuel**, `outputs/reporting/interactive_network_dashboard.html`, généré par `scripts/reporting/interactive_network_dashboard.py` à partir des données mensuelles et des coordonnées géographiques.

- **Un référentiel géographique reproductible**, construit par `scripts/reporting/prepare_station_coordinates.py` depuis `data/reference/liste-des-gares.csv` et les compléments étrangers définis dans le script.

Le guide **`outputs/streamlit/README.md`** donne les champs, la signification des visuels et les consignes d'intégration. Les **sélections par mois, gare et liaison** du dashboard se font via les **menus du panneau latéral**, pas par un clic sur la carte. Les centralités de la carte sont mensuelles, tandis que les caractéristiques ML utilisent un historique glissant pour éviter les fuites temporelles.

## 10. Organisation du code

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

│   ├── network_analysis.py

│   └── export_network.py

├── experiments/

│   ├── compare_models.py

│   ├── tune_models.py

│   ├── evaluate_models.py

│   ├── analyze_predictions.py

│   └── compare_recent_features.py

└── reporting/

    ├── prepare_station_coordinates.py

    ├── generate_streamlit_assets.py

    └── interactive_network_dashboard.py

data/

├── raw/regularite-mensuelle-tgv-aqst.csv

└── reference/

    ├── liste-des-gares.csv

    └── station_coordinates.csv       # généré

outputs/

├── streamlit/                       # six CSV et guide d'intégration

└── reporting/                       # quatre PNG et HTML générés

tests/

├── test_graph_features.py

├── test_ml_preprocessing.py

└── test_temporal_features.py

```

Les fonctions réutilisables sont placées dans `src/`, les scripts d'analyse et d'expérimentation dans `scripts/`, et les vérifications automatisées dans `tests/`.

## 11. Installation et reproduction

Le projet utilise Python 3.12 et `uv` pour gérer les dépendances. Toutes les commandes ci-dessous sont lancées **à la racine du dépôt**.

```bash

uv sync

```

### Fichiers sources indispensables

- `data/raw/regularite-mensuelle-tgv-aqst.csv` : dataset AQST des retards et circulations, nécessaire à l'analyse et au modèle.

- `data/reference/liste-des-gares.csv` : référentiel SNCF nécessaire à la **régénération des coordonnées**. Le script en extrait les positions françaises et utilise un référentiel explicite pour les destinations étrangères.

`data/reference/station_coordinates.csv` est une **sortie générée** ; elle est utilisée par le dashboard, mais n'a pas besoin d'être saisie manuellement.

### Exploration et ML

```bash

uv run python scripts/exploration/data_quality.py

uv run python scripts/exploration/network_analysis.py

uv run python scripts/experiments/compare_models.py

uv run python scripts/experiments/tune_models.py

uv run python scripts/experiments/evaluate_models.py

uv run python scripts/experiments/compare_recent_features.py

```

### Générer les CSV, les PNG et la carte

```bash

uv run python scripts/exploration/export_network.py

uv run python scripts/experiments/analyze_predictions.py

uv run python scripts/reporting/generate_streamlit_assets.py

uv run python scripts/reporting/prepare_station_coordinates.py

uv run python scripts/reporting/interactive_network_dashboard.py

```

\> Les scripts d'exports prédictifs nécessitent que les données, les modèles ou leurs calculs préalables soient disponibles suivant leur implémentation ; consulter également le guide `outputs/streamlit/README.md`.

### Ouvrir le dashboard cartographique

```bash

uv run python -m http.server 8000

```

Puis accéder à :

`http\://localhost:8000/outputs/reporting/interactive_network_dashboard.html`

**Important :** l'ouverture du HTML en `file://` a provoqué une carte blanche lors des essais. Le chargement par **HTTP local** a été testé et fonctionne. Les menus du panneau latéral permettent la sélection ; **la sélection par clic sur la carte n'est pas prise en charge** dans cette version.

### Exécuter les tests et contrôles

```bash

uv run pytest tests/ -v

uv run ruff check src/ scripts/ tests/

```

## 12. Limites et perspectives

- Les modèles ne bénéficient pas uniformément de toutes les centralités ; l'amélioration est observée sur la configuration et le découpage temporel étudiés.

- Les épisodes de retard extrême demeurent difficiles à prévoir et peuvent générer une sous-estimation.

- Les expériences de tendance récente sont des résultats de **validation 2024**, à confirmer sur un test final distinct.

- Certaines destinations de la carte sont des positions **représentatives** (par exemple `ITALIE`), faute de gare précise dans la source AQST.

- Les visuels PNG sont statiques ; les filtres avancés de Streamlit peuvent être construits depuis les CSV.

Cette contribution se concentre sur **l'analyse de graphe et l'amélioration de la prédiction des retards par des variables de réseau**, avec des livrables documentés pour intégration Streamlit.