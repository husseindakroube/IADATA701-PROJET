# Analyse de la régularité des liaisons TGV — SNCF

Ce projet étudie les liaisons TGV mensuelles de la SNCF et la question suivante :

> **Dans quelle mesure la structure du réseau TGV est-elle associée à la régularité des liaisons ?**

Le dépôt rassemble la préparation des données, la construction et l’analyse de graphes, puis les résultats destinés à la suite du projet collectif.

## Vue d’ensemble du projet

Le schéma ci-dessous présente le flux de travail global du projet, de l’ingestion des données à l’application envisagée :

![Schéma global du projet SNCF](docs/images/Projet_SNCF.svg)

Le périmètre actuellement disponible dans ce dépôt comprend l’ingestion, le prétraitement, la construction des graphes, les métriques, la préparation du jeu de recherche, les analyses descriptives et les analyses d’association. Le schéma inclut aussi la prédiction et une application Streamlit, qui constituent la suite du travail collectif; aucune application Streamlit ni pipeline de prédiction n’est présent dans le package Python actuel.

## Ma contribution

Ma contribution porte principalement sur deux volets : **le prétraitement des données** et **l’analyse de graphes**. L’ingestion SNCF fournit les données brutes nécessaires à ces étapes.

### 1. Prétraitement des données

Les données sources proviennent du jeu mensuel SNCF de régularité des TGV (`regularite-mensuelle-tgv-aqst`). Le module d’ingestion récupère l’export JSON complet et le conserve localement dans `data/raw/regularite-mensuelle-tgv-aqst.json`.

Le pipeline ETL réalise ensuite les opérations suivantes :

1. charge le JSON brut déjà présent sur le disque;
2. convertit les enregistrements vers un schéma Polars canonique de 26 champs, avec des types explicites;
3. ajoute quatre indicateurs booléens de diagnostic aux colonnes sources;
4. écrit le résultat en Parquet dans `data/processed/sncf.parquet`.

Les indicateurs signalent les comptes négatifs, l’ordre incohérent de certains seuils de retard et les annulations supérieures au nombre de trains prévus. Ils servent à repérer des lignes à examiner : le pipeline ne corrige ni ne supprime les observations. Les valeurs nulles et les colonnes d’origine sont conservées.

Un audit indépendant produit `data/reports/data_quality_report.txt` pour éclairer la définition de futures règles de nettoyage. Il décrit notamment le schéma, les valeurs manquantes, les doublons, les valeurs numériques et les incohérences logiques, avec des exemples d’anomalies. L’audit ne modifie pas le fichier brut.

### 2. Analyse de graphes

L’analyse utilise le Parquet préparé et les métriques existantes pour représenter les relations origine-destination mensuelles.

1. **Construction** — chaque gare devient un nœud; une liaison dirigée va de la gare de départ à la gare d’arrivée. Le service est conservé dans l’identité des liaisons. Les tables de nœuds, de liaisons et d’observations mensuelles sont écrites sous `data/processed/graph/`.
2. **Métriques** — les graphes orientés non pondérés National et International sont traités séparément. Les indicateurs comprennent les degrés entrants et sortants, la centralité d’intermédiarité, la proximité orientée, PageRank et l’intermédiarité des liaisons. Les métriques de nœuds et de liaisons sont conservées en Parquet.
3. **Jeu de recherche** — les observations opérationnelles mensuelles sont associées aux métriques de graphe correspondantes. Le fichier `data/processed/research_dataset.parquet` conserve une ligne par mois, service et liaison origine-destination. Le taux d’annulation reste manquant quand son dénominateur ne permet pas de le calculer; il n’est pas remplacé par zéro.
4. **Description et visualisation** — les sorties résument la topologie, les composantes connexes, les distributions de centralité, les liaisons importantes, l’évolution mensuelle et les résultats opérationnels. Les figures sont rangées sous `data/processed/graph/visualizations/`.
5. **Associations exploratoires** — les coefficients de Pearson et Spearman, les comparaisons par groupes de centralité et une analyse de sensibilité du résultat principal (exclusion, pour ce calcul seulement, des 11 retards inférieurs à −15 minutes) sont enregistrés sous `data/processed/graph/phase3b/`. Les observations originales restent dans le jeu de recherche.

Les résultats sont rassemblés dans un rapport de recherche unique en français : `data/reports/graph/research_report.md`. Les documents de [construction](docs/graph_construction.md), de [métriques](docs/graph_metrics.md), de [préparation du jeu de recherche](docs/research_data_preparation.md), d’[analyse descriptive](docs/descriptive_analysis.md) et d’[associations](docs/association_analysis.md) détaillent les choix et les sorties de chaque étape.

## Reproduire le flux de données

Les commandes suivantes s’exécutent depuis la racine du dépôt. Pour commencer, installer les dépendances :

```powershell
uv sync
```

Télécharger le JSON brut, puis lancer l’audit et préparer le Parquet ETL :

```powershell
uv run python -m projet_kit_data.ingestion.download_data
uv run python -m projet_kit_data.etl.audit
uv run python -c "from projet_kit_data.etl import run_and_save_etl; run_and_save_etl()"
```

Construire les graphes et leurs métriques, puis produire le jeu de recherche et les analyses :

```powershell
uv run python -c "from projet_kit_data.graph import run_graph_construction_pipeline; run_graph_construction_pipeline()"
uv run python -c "from projet_kit_data.graph import run_graph_metrics_pipeline; run_graph_metrics_pipeline()"
uv run python -c "from projet_kit_data.graph import run_research_data_preparation_pipeline; run_research_data_preparation_pipeline()"
uv run python -c "from projet_kit_data.graph import run_descriptive_analysis; run_descriptive_analysis()"
uv run python -c "from projet_kit_data.graph import run_visualization_pipeline; run_visualization_pipeline()"
uv run python -c "from projet_kit_data.graph import run_association_analysis_pipeline; run_association_analysis_pipeline()"
```

Chaque étape réutilise les fichiers locaux produits par les étapes précédentes. Les pipelines de graphes ne téléchargent pas automatiquement les données SNCF. Les fonctions acceptent des chemins personnalisés; leurs paramètres et leurs contrats sont décrits dans les documents techniques ci-dessus.

## Précautions d’interprétation

- Une liaison origine-destination observée n’est pas nécessairement un segment ferroviaire adjacent ni un itinéraire réellement parcouru par un train.
- Les métriques de centralité décrivent la position dans le graphe construit; elles ne mesurent ni la fréquence des trains ni le nombre de voyageurs.
- Les associations sont exploratoires et ne démontrent pas de causalité ou de propagation des retards. Les observations mensuelles d’une même liaison sont répétées, ce qui limite l’interprétation des p-values usuelles.
- Les valeurs de retard négatives sont conservées. Les observations extrêmes exclues de certaines vues ou de l’analyse de sensibilité restent présentes dans le jeu de recherche.
- Un taux d’annulation égal à 0 n’est pas équivalent à un taux manquant.

## Tests et qualité du code

Les tests unitaires couvrent l’ingestion, l’ETL, la construction des graphes, les métriques, les visualisations et les analyses :

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
