# Métriques de graphe

## Contexte de recherche

La question du projet est : *Dans quelle mesure la structure du réseau TGV
est-elle associée à la régularité des liaisons ?* Cette étape décrit la
topologie observée du réseau afin qu’une étape ultérieure de préparation des
données de recherche puisse la rapprocher des observations opérationnelles
mensuelles. Elle ne calcule pas d’associations et n’en déduit pas de causes.

Les arêtes sont orientées de l’origine vers la destination, conformément au
sens de la liaison. Les services National et International sont analysés dans
des graphes distincts. Les premières métriques sont non pondérées : chaque
liaison compte une fois, quel que soit le nombre de trains ou les mesures de
retard et d’annulation. Un graphe global utilise l’union des arêtes observées
pour un service sur l’ensemble du jeu de données. Un graphe mensuel utilise
uniquement les arêtes de ce service observées pendant le mois sélectionné et ne
contient pas les gares absentes de ces arêtes. Les scores globaux et mensuels
correspondent donc à des instantanés différents et ne doivent pas être
interchangés.

Le graphe représente des liaisons origine-destination, et non des itinéraires
de train confirmés, des correspondances ou des segments physiques de voie. Les
plus courts chemins décrivent uniquement des chemins dans cette topologie
observée. La centralité ne démontre ni les déplacements réels des trains, ni
le volume de voyageurs, ni l’importance opérationnelle, ni la propagation des
retards.

## Référence des métriques

Tous les calculs utilisent des graphes orientés simples NetworkX et des plus
courts chemins non pondérés. Dans un graphe défini par service et période,
chaque arête est identifiée de manière unique par son `edge_id` de construction.
Le degré compte les voisins distincts, et non la fréquence du service.

| Métrique | Définition et normalisation | Interprétation et limites |
|---|---|---|
| `in_degree` | Nombre de voisins distincts entrants. | Une valeur élevée indique davantage de liaisons entrantes observées. |
| `out_degree` | Nombre de voisins distincts sortants. | Une valeur élevée indique davantage de liaisons sortantes observées. |
| `degree` | `in_degree + out_degree` ; une boucle contribue une fois à chaque degré. | Nombre total de connexions orientées, et non volume de trafic. |
| `in_degree_centrality` | `in_degree / (n - 1)` ; vaut zéro si `n < 2`. | Part des autres nœuds possibles qui pointent vers le nœud considéré. |
| `out_degree_centrality` | `out_degree / (n - 1)` ; vaut zéro si `n < 2`. | Part des autres nœuds possibles atteints directement depuis le nœud considéré. |
| `betweenness_centrality` | Betweenness orientée normalisée de NetworkX, calculée sur des plus courts chemins non pondérés, extrémités exclues. Pour les graphes orientés, la normalisation utilise les paires ordonnées de nœuds. | Un score élevé indique que le nœud appartient à une plus grande part des plus courts chemins orientés. Les paires déconnectées ne contribuent aucun chemin ; cela ne prouve pas l’existence de correspondances réelles. |
| `in_closeness` | Closeness orientée de NetworkX sur le graphe d’origine : distances depuis les nœuds pouvant atteindre le nœud considéré. Utilise la correction des nœuds accessibles (`wf_improved=True`). | Une valeur élevée indique des chemins entrants courts depuis les nœuds accessibles. Les nœuds inaccessibles sont exclus des sommes de distances et la fraction de nœuds accessibles réduit les scores. |
| `out_closeness` | Même calcul de closeness orientée sur le graphe inversé, donnant les distances du nœud considéré vers les nœuds qu’il peut atteindre. La même correction d’accessibilité est appliquée. | Une valeur élevée indique une accessibilité sortante courte. Cette mesure n’est pas interchangeable avec la closeness entrante. |
| `pagerank` | PageRank orienté NetworkX avec `alpha=0.85`, arêtes non pondérées et paramètres `max_iter` et `tol` configurables. Les nœuds pendants utilisent la redistribution par défaut de NetworkX selon le vecteur de personnalisation (uniforme en son absence). | Une valeur élevée signifie que le nœud reçoit des liens de nœuds ayant un PageRank plus élevé. Elle ne mesure ni le volume de voyageurs, ni la fréquence des trains, ni l’influence opérationnelle. En cas de non-convergence, la valeur PageRank est manquante (`None`) pour les nœuds du graphe concerné et une entrée détaillée est ajoutée aux métadonnées/au rapport ; les autres métriques restent disponibles. |
| `edge_betweenness` | Betweenness orientée normalisée des arêtes NetworkX, calculée sur des plus courts chemins non pondérés. | Une valeur élevée indique qu’une liaison orientée observée appartient à davantage de plus courts chemins. Elle n’affirme pas qu’un train parcourt physiquement cette liaison en un seul segment. |

Les centralités de degré utilisent explicitement le dénominateur `n - 1`. La
betweenness et la closeness suivent respectivement les conventions NetworkX de
normalisation orientée et de prise en compte des nœuds accessibles. Pour un
graphe à un seul nœud, les centralités de degré normalisées valent zéro ;
NetworkX renvoie zéro pour la closeness et la betweenness. Une boucle reste une
arête orientée et contribue au degré entrant comme au degré sortant.

## Modèle de données

Le pipeline lit les sorties existantes de la construction et écrit
`data/processed/graph/node_metrics.parquet`, `edge_metrics.parquet` et
`metrics_metadata.json`, ainsi que `data/reports/graph/metrics_report.md`.

### `node_metrics.parquet`

| Colonne | Type |
|---|---|
| `period` | String : `overall` ou `YYYY-MM` |
| `service` | String |
| `node_id` | String |
| `station_name` | String |
| `in_degree`, `out_degree`, `degree` | UInt32 |
| `in_degree_centrality`, `out_degree_centrality` | Float64 |
| `betweenness_centrality`, `in_closeness`, `out_closeness`, `pagerank` | Float64 ; le PageRank peut être manquant (`None`) en cas d’échec de convergence |

Clé unique : `(period, service, node_id)`.

### `edge_metrics.parquet`

Les champs d’identification sont `period` (String), `service` (String), `edge_id`
(String), `source` (identifiant de nœud String) et `target` (identifiant de nœud
String). Ils sont suivis de `edge_betweenness` (Float64), puis des champs de
métriques de nœud préfixés par `source_` et `target_`. Les champs des extrémités
incluent les degrés entrant et sortant, le degré, les centralités de degré
entrante/sortante, la betweenness, la closeness entrante/sortante et le PageRank.
Les degrés sont de type UInt32 ; les autres valeurs sont des Float64. Le
PageRank est manquant (`None`) si le graphe n’a pas convergé.

Clé unique : `(period, service, edge_id)`. Les métriques des extrémités sont
calculées dans le même graphe service-période que leur arête. Les valeurs
`edge_id` issues de la construction sont réutilisées ; aucun identifiant
concurrent n’est créé.

Le jeu de recherche mensuel ultérieur doit joindre les métriques à l’aide de
`period = date`, `service` et `edge_id` (ou vérifier également `source` et
`target` comme contrôles d’intégrité). `period = "overall"` est une synthèse
distincte et ne doit pas être joint comme s’il s’agissait d’un score mensuel.

## Exécution et configuration

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph import run_graph_metrics_pipeline; result = run_graph_metrics_pipeline()"
```

L’API publique est :

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

Le `GraphMetricsResult` retourné expose `node_metrics`, `edge_metrics`,
`metadata` et `output_paths`. Les métadonnées comprennent les nombres de nœuds
et d’arêtes par graphe, les définitions des métriques, les versions logicielles,
la configuration, les échecs de convergence, les schémas, les clés uniques et
les avertissements. Le rapport présente les classements globaux, les synthèses
des métriques globales, la couverture et l’évolution mensuelles, ainsi que les
limites d’interprétation. L’exécution ne relance ni l’ETL ni la construction du
graphe.

Pour assurer la reproductibilité, conservez les artefacts de construction
d’entrée sans modification et consignez dans les métadonnées les chemins
d’entrée, les versions de NetworkX et de Polars ainsi que les paramètres de
PageRank. Les services National et International doivent rester séparés dans
toutes les jointures et analyses ultérieures. Toute association entre ces
métriques structurelles et la régularité opérationnelle constitue un constat
descriptif, et non une preuve de causalité.
