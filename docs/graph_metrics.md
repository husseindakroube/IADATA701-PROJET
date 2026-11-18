# Métriques des graphes

## Contexte de recherche

La question est : *Dans quelle mesure la structure du réseau TGV est-elle associée à la régularité des liaisons ?* Cette phase décrit la topologie observée afin de permettre une comparaison ultérieure avec les observations opérationnelles mensuelles. Elle ne calcule pas d’association et n’établit aucune causalité.

Les arêtes suivent la direction origine-destination. Les services National et International sont analysés séparément. Les métriques ne sont pas pondérées : une connexion compte une fois, indépendamment du trafic, des retards et des annulations. Le graphe global est l’union des arêtes observées sur toute la période. Un graphe mensuel contient uniquement les arêtes du mois et les gares qui y participent. Les scores globaux et mensuels ne sont donc pas interchangeables.

Les liaisons ne sont ni des itinéraires confirmés, ni des correspondances, ni des tronçons physiques. Les plus courts chemins décrivent uniquement cette topologie. La centralité ne mesure pas les mouvements réels, le volume de voyageurs, l’importance opérationnelle ou la propagation des retards.

## Référence des métriques

Les calculs utilisent des graphes simples orientés NetworkX et des plus courts chemins non pondérés. `edge_id` identifie une arête dans un graphe service-période. Le degré compte les voisins distincts, pas la fréquence du service.

| Métrique | Définition et normalisation | Interprétation et limites |
|---|---|---|
| `in_degree` | Nombre de voisins entrants distincts | Nombre de connexions entrantes observées |
| `out_degree` | Nombre de voisins sortants distincts | Nombre de connexions sortantes observées |
| `degree` | `in_degree + out_degree` ; une boucle contribue une fois à chaque degré | Total des connexions orientées, pas du trafic |
| `in_degree_centrality` | `in_degree / (n - 1)` ; zéro si `n < 2` | Part des autres nœuds possibles reliés au nœud en entrée |
| `out_degree_centrality` | `out_degree / (n - 1)` ; zéro si `n < 2` | Part des autres nœuds possibles atteints directement |
| `betweenness_centrality` | Intermédiarité orientée normalisée NetworkX, sans pondération ni extrémités ; normalisation par paires ordonnées | Part des plus courts chemins passant par le nœud ; les paires déconnectées ne contribuent pas. Ce n’est pas une preuve de correspondances réelles |
| `in_closeness` | Proximité orientée sur le graphe d’origine, distances des nœuds pouvant atteindre le nœud étudié ; correction `wf_improved=True` | Des valeurs élevées indiquent de courts chemins entrants. Les nœuds inaccessibles sont exclus des distances et la part accessible réduit le score |
| `out_closeness` | Même calcul sur le graphe inversé et même correction d’accessibilité | Proximité sortante, distincte de la proximité entrante |
| `pagerank` | PageRank orienté non pondéré, `alpha=0.85`, `max_iter` et `tol` configurables ; redistribution des nœuds sans sortie selon la personnalisation, uniforme par défaut | Liens reçus de nœuds à PageRank élevé, sans mesure de trafic ou d’influence opérationnelle. En cas de non-convergence, tous les PageRank du graphe sont nuls, l’échec est documenté et les autres métriques restent disponibles |
| `edge_betweenness` | Intermédiarité orientée normalisée des arêtes sur les plus courts chemins non pondérés | Fréquence topologique de la liaison dans ces chemins, sans preuve qu’un train la traverse comme étape physique |

Les degrés normalisés utilisent `n - 1`. L’intermédiarité et la proximité suivent les conventions de normalisation orientée et d’accessibilité de NetworkX. Pour un seul nœud, ces centralités valent zéro. Une boucle reste une arête orientée et contribue aux degrés entrant et sortant.

## Modèle de données

La chaîne lit les résultats de construction existants et écrit `data/processed/graph/node_metrics.parquet`, `edge_metrics.parquet`, `metrics_metadata.json` et `data/reports/graph/metrics_report.md`.

### `node_metrics.parquet`

| Colonne | Type |
|---|---|
| `period` | String : `overall` ou `YYYY-MM` |
| `service`, `node_id`, `station_name` | String |
| `in_degree`, `out_degree`, `degree` | UInt32 |
| `in_degree_centrality`, `out_degree_centrality` | Float64 |
| `betweenness_centrality`, `in_closeness`, `out_closeness`, `pagerank` | Float64 ; PageRank peut être nul en cas de non-convergence |

Clé unique : `(period, service, node_id)`.

### `edge_metrics.parquet`

Les champs d’identité `period`, `service`, `edge_id`, `source` et `target` sont des chaînes. Ils sont suivis de `edge_betweenness` (Float64) et des métriques des nœuds préfixées par `source_` et `target_` : degrés, centralités de degré, intermédiarité, proximités et PageRank. Les degrés sont UInt32, les autres mesures Float64 ; PageRank peut être nul en cas de non-convergence.

Clé unique : `(period, service, edge_id)`. Les métriques des extrémités proviennent du même graphe service-période que l’arête. Les identifiants de construction sont réutilisés. Pour les données mensuelles, joindre sur `period = date`, `service` et `edge_id`, avec contrôle supplémentaire des extrémités si nécessaire. Ne pas joindre `period="overall"` comme un score mensuel.

## Exécution et configuration

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph import run_graph_metrics_pipeline; result = run_graph_metrics_pipeline()"
```

Interface publique :

```python
run_graph_metrics_pipeline(
    nodes_path="data/processed/graph/nodes.parquet",
    edges_path="data/processed/graph/edges.parquet",
    observations_path="data/processed/graph/edge_observations.parquet",
    output_dir="data/processed/graph",
    report_path="data/reports/graph/metrics_report.md",
    alpha=0.85,
    max_iter=1000,
    tol=1e-6,
)
```

`GraphMetricsResult` expose `node_metrics`, `edge_metrics`, `metadata` et `output_paths`. Les métadonnées décrivent les effectifs par graphe, définitions, versions logicielles, configuration, échecs de convergence, schémas, clés et avertissements. Le rapport présente les classements globaux, distributions, couverture et évolution mensuelle et limites. Cette exécution ne relance ni l’ETL ni la construction.

Pour reproduire les résultats, conserver les entrées de construction immuables et enregistrer leurs chemins, les versions NetworkX/Polars et les paramètres PageRank. Les services restent distincts dans les jointures et analyses ultérieures. Une association entre structure et régularité reste descriptive et ne prouve pas une causalité.
