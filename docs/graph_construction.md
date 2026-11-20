# Passage de relais pour la construction du graphe SNCF

Ce module exporte des graphes orientés réutilisables et des observations
mensuelles d’arêtes destinés à Streamlit et à l’analyse de graphes. Il construit
uniquement la topologie : il ne calcule pas la centralité, ne teste pas les
associations et n’interprète pas la propagation des retards.

## Modèle et limites

- Un nœud correspond à un libellé exact de gare source. Son `node_id` est dérivé
  du nom de gare encodé en UTF-8 à l’aide de SHA-256 ; l’orthographe est
  conservée et les libellés ne sont ni rapprochés approximativement ni
  normalisés.
- Une arête va de `gare_depart` à `gare_arrivee`. Son orientation respecte celle
  de la liaison source. Les liaisons inverses ont une identité d’arête distincte.
- L’identité d’une arête est `(service, gare d’origine, gare de destination)`.
  Les mêmes nœuds de gare sont partagés entre les services, tandis que les
  identifiants d’arête les distinguent. L’objet en mémoire combiné est un
  `MultiDiGraph` NetworkX indexé par `edge_id` ; `service_graphs` fournit une
  topologie orientée distincte pour chaque service.
- Chaque ligne source admissible est conservée dans
  `edge_observations.parquet`, afin de pouvoir filtrer un service et un mois
  pour construire une vue instantanée. Les arêtes et leurs dates de synthèse ne
  remplacent pas ces enregistrements mensuels.

Une liaison est une paire origine-destination observée. Elle ne correspond pas
nécessairement à un segment ferroviaire physiquement adjacent, à deux étapes
consécutives d’un train ni à une correspondance confirmée. L’adjacence dans le
graphe ne prouve ni un déplacement réel de train ni une propagation des retards.

Les mesures manquantes restent manquantes ; les mesures égales à zéro restent
égales à zéro. Les flags diagnostiques existants et les
valeurs opérationnelles atypiques n’excluent pas les clés de graphe par ailleurs
valides. Les lignes dont les clés de graphe sont manquantes, vides ou invalides
sont signalées comme exclues. Pour garantir l’unicité des clés métier des
observations, toutes les lignes d’un groupe dupliqué
`(date, service, gare_depart, gare_arrivee)` sont exclues et comptabilisées ;
aucun doublon n’est sélectionné arbitrairement.

## Exécuter le pipeline

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph import run_graph_construction_pipeline; result = run_graph_construction_pipeline()"
```

Par défaut, le pipeline lit `data/processed/sncf.parquet` et écrit :

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

Si vous disposez déjà d’un DataFrame Polars, utilisez
`construct_graph_data(frame)` et, facultativement,
`export_graph_artifacts(result)`. Le `GraphConstructionResult` retourné expose
les tables Polars, le graphe NetworkX combiné, les graphes par service, les
métadonnées et les chemins de sortie.

## Schémas des artefacts

### `nodes.parquet`

| Colonne | Type Polars | Signification |
|---|---|---|
| `node_id` | String | Identifiant stable `node_<24 hex chars>` |
| `station_name` | String | Libellé exact de la gare source |

Chaque ligne représente un libellé de gare unique.

### `edges.parquet`

| Colonne | Type Polars | Signification |
|---|---|---|
| `edge_id` | String | Identifiant stable `edge_<24 hex chars>` |
| `service` | String | Catégorie de service source |
| `source` | String | `node_id` de la gare d’origine |
| `target` | String | `node_id` de la gare de destination |
| `n_months_observed` | UInt32 | Nombre de mois distincts où l’arête est observée |
| `first_date` | String | Première observation au format `YYYY-MM` |
| `last_date` | String | Dernière observation au format `YYYY-MM` |

`(service, source, target)` identifie une arête de manière unique. Les
directions opposées et les services différents restent distincts.

### `edge_observations.parquet`

Les cinq premiers champs sont `edge_id` (String), `date` (String, `YYYY-MM`),
`service` (String), `source` (identifiant de nœud String) et `target`
(identifiant de nœud String). La sortie ETL actuelle à 30 colonnes produit
exactement le schéma de table à 33 colonnes suivant :

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

Pour un DataFrame d’entrée compatible, chaque colonne source autre qu’une clé
est conservée avec son type Polars et ses valeurs d’origine. Les colonnes
source `date` et `service` sont également les champs date et service en sortie ;
elles ne sont pas dupliquées. Les colonnes source supplémentaires, le cas
échéant, sont conservées après les champs listés. La table conserve les libellés
de liaison source, les mesures opérationnelles, les commentaires, les valeurs
manquantes (`null`) et les flags diagnostiques. Après les exclusions explicites, chaque
ligne correspond à une clé métier mensuelle unique.

`graph_metadata.json` consigne la version du schéma, les nombres de sources et
de lignes, les motifs d’exclusion, les identités des graphes, les catégories de
service, la couverture temporelle, les décomptes par période, les diagnostics
du réseau orienté par service, les nombres d’enregistrements source signalés,
la configuration et les avertissements d’interprétation. `construction_report.md`
présente les mêmes faits principaux pour examen, notamment les observations
mensuelles, les nombres mensuels d’arêtes uniques, les changements de
couverture, les lacunes et les statistiques des composantes faibles et fortes.

## Charger et utiliser les artefacts

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

Pour utiliser NetworkX avec Pandas, joignez les lignes de la vue instantanée à
`nodes` sur `source` et `target`, ou chargez `edge_observations.parquet` avec
Polars et appelez `reconstruct_monthly_graph`. Cette fonction conserve les noms
de gare et les champs des observations d’origine comme attributs des nœuds et
des arêtes. Dans Streamlit, chargez les artefacts une seule fois, utilisez les
colonnes service et date pour les sélecteurs, filtrez les observations
mensuelles et reconstruisez la vue instantanée sans analyser le rapport
Markdown. Joignez les futures métriques de nœud sur `node_id` et les métriques
d’arête sur `edge_id`.

Le code n’ajoute volontairement ni `node_metrics.parquet`,
`edge_metrics.parquet`, ni synthèses d’analyse, visualisations ou pages
Streamlit prévues pour les étapes ultérieures.
