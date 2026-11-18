# Construction des graphes SNCF

Ce module exporte des graphes orientés réutilisables et les observations mensuelles des arêtes pour l’interface et l’analyse de réseau. Il construit uniquement la topologie : il ne calcule pas les centralités, ne teste pas les associations et n’interprète pas la propagation des retards.

## Modèle et limites

- Un nœud correspond au libellé exact d’une gare source. Son `node_id` est calculé par SHA-256 sur le nom UTF-8. Aucune normalisation ni correspondance approximative n’est appliquée.
- Une arête va de `gare_depart` à `gare_arrivee`. La direction inverse conserve une identité distincte.
- L’identité d’arête est `(service, gare d’origine, gare de destination)`. Les nœuds sont communs aux services mais les identifiants d’arête les distinguent. Le graphe combiné en mémoire est un `MultiDiGraph` NetworkX indexé par `edge_id`. `service_graphs` fournit une topologie orientée par service.
- Chaque ligne source admissible est conservée dans `edge_observations.parquet` pour reconstruire un état par service et mois. Les arêtes et leurs dates récapitulatives ne remplacent pas ces observations.

Une liaison est une paire origine-destination observée. Elle ne correspond pas nécessairement à un tronçon physique adjacent, à une étape consécutive de trajet ou à une correspondance confirmée. L’adjacence ne prouve ni circulation réelle ni propagation des retards.

Les mesures nulles restent nulles. Les indicateurs qualité et valeurs opérationnelles anormales n’excluent pas une clé de graphe valide. Les clés absentes, vides ou invalides sont signalées comme exclusions. Toutes les lignes d’un groupe dupliqué `(date, service, gare_depart, gare_arrivee)` sont exclues et comptées ; aucun doublon n’est choisi arbitrairement.

## Exécution

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph import run_graph_construction_pipeline; result = run_graph_construction_pipeline()"
```

Par défaut, l’entrée est `data/processed/sncf.parquet` et les sorties sont :

```text
data/processed/graph/nodes.parquet
data/processed/graph/edges.parquet
data/processed/graph/edge_observations.parquet
data/processed/graph/graph_metadata.json
data/reports/graph/construction_report.md
```

Les chemins sont configurables :

```python
from projet_kit_data.graph import run_graph_construction_pipeline

result = run_graph_construction_pipeline(
    input_path="data/processed/sncf.parquet",
    output_dir="data/processed/graph",
    report_path="data/reports/graph/construction_report.md",
)
```

Pour une table Polars déjà chargée, utiliser `construct_graph_data(frame)`, puis éventuellement `export_graph_artifacts(result)`. Le résultat `GraphConstructionResult` expose les tables Polars, le graphe NetworkX combiné, les graphes par service, les métadonnées et les chemins de sortie.

## Schémas des fichiers

### `nodes.parquet`

| Colonne | Type Polars | Signification |
|---|---|---|
| `node_id` | String | Identifiant stable : préfixe `node_` suivi de 24 caractères hexadécimaux |
| `station_name` | String | Libellé exact de la gare source |

Une ligne par libellé unique de gare.

### `edges.parquet`

| Colonne | Type Polars | Signification |
|---|---|---|
| `edge_id` | String | Identifiant stable : préfixe `edge_` suivi de 24 caractères hexadécimaux |
| `service` | String | Catégorie de service d’origine |
| `source` | String | `node_id` de départ |
| `target` | String | `node_id` d’arrivée |
| `n_months_observed` | UInt32 | Nombre de mois distincts observés |
| `first_date` | String | Première observation au format `YYYY-MM` |
| `last_date` | String | Dernière observation au format `YYYY-MM` |

La clé `(service, source, target)` est unique. Les directions opposées et les services différents restent distincts.

### `edge_observations.parquet`

Les cinq premiers champs sont `edge_id`, `date` (format `YYYY-MM`), `service`, `source` et `target`, tous de type String. La sortie ETL actuelle à 30 colonnes produit cette table à 33 colonnes :

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

Chaque colonne source hors clé conserve son type Polars et ses valeurs. `date` et `service` ne sont pas dupliquées. Les colonnes supplémentaires sont conservées après les champs listés. La table conserve les noms de liaisons, mesures, commentaires, valeurs nulles et indicateurs. Une ligne correspond à une clé métier mensuelle unique après les exclusions explicites.

`graph_metadata.json` consigne la version du schéma, la source, les effectifs, les motifs d’exclusion, les identités, services, dates, comptages temporels, diagnostics topologiques, effectifs signalés, configuration et réserves d’interprétation. `construction_report.md` présente les mêmes éléments, y compris les changements de couverture mensuelle, les lacunes et les composantes faiblement ou fortement connexes.

## Chargement et utilisation

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

Avec Pandas et NetworkX, joindre les lignes sélectionnées à `nodes` sur `source` et `target`, ou charger les observations avec Polars et appeler `reconstruct_monthly_graph`. Cette fonction conserve les noms et attributs sources. Dans Streamlit, charger les résultats une fois, filtrer par service et date et reconstruire le graphe sans analyser le rapport Markdown. Joindre les métriques de nœuds sur `node_id` et celles d’arêtes sur `edge_id`.

Ce module de construction ne génère pas les fichiers de métriques, les synthèses d’analyse, les visualisations ni les pages Streamlit, qui relèvent d’autres modules.
