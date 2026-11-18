# Analyse descriptive et visualisations du réseau

La phase 3A résume les métriques de graphe de la phase 1 et les observations opérationnelles de la phase 2. Elle ne recalcule pas les métriques et ne réalise ni comparaison inférentielle, ni corrélation, ni test, ni régression. Les services National et International sont présentés séparément.

## Exécution

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph.descriptive import run_descriptive_analysis; result = run_descriptive_analysis()"
uv run python -c "from projet_kit_data.graph.visualization import run_visualization_pipeline; paths = run_visualization_pipeline()"
```

Les tables sont écrites dans `data/processed/graph/descriptive/`, les figures dans `data/processed/graph/visualizations/` et le rapport dans `data/reports/graph/research_report.md`. Le générateur remplace uniquement sa section délimitée et conserve les autres contenus.

## Tables descriptives

- `network_summary.parquet` : une ligne par service ; nombres de nœuds, arêtes, composantes faiblement et fortement connexes, taille de la plus grande composante faible, nœuds à plusieurs voisins entrants/sortants et boucles. Les composantes sont calculées sur les arêtes existantes et comparées aux métadonnées de construction.
- `node_metric_summary.parquet` : une ligne par service ; effectifs non nuls et manquants, moyenne, écart-type, médiane, quartiles, minimum et maximum de chaque métrique globale des nœuds.
- `node_rankings.parquet` : jusqu’à dix gares par service et mesure (`connectivity_degree`, `betweenness_centrality`, `pagerank`), avec rang, identifiant, nom et valeur.
- `edge_rankings.parquet` : jusqu’à dix liaisons orientées globales par service, classées par intermédiarité, avec identifiant et noms d’origine/destination.
- `monthly_summary.parquet` : une ligne par mois/service ; nombres de nœuds et arêtes, degré moyen, PageRank maximal, intermédiarité maximale et médiane des nœuds, intermédiarité moyenne et maximale des arêtes.
- `operational_summary.parquet` : distributions par service du retard moyen à l’arrivée de tous les trains, du taux d’annulation et du retard moyen des trains retardés. Inclut les valeurs manquantes et les valeurs atypiques selon Tukey, à 1,5 écart interquartile. Ces comptages ne filtrent ni ne modifient les observations.
- `quality_flag_summary.parquet` : effectifs des indicateurs booléens `flag_*` existants par service.

Les classements utilisent les métriques globales `period="overall"`. Les synthèses mensuelles utilisent seulement les lignes mensuelles. Les résultats opérationnels viennent du jeu mensuel de recherche et ne sont pas mélangés aux métriques globales.

### Schémas de sortie

Toutes les tables sont au format Parquet. Identifiants, gares, services, périodes et noms de métriques sont des chaînes. Les synthèses numériques peuvent être nulles si les sources sont manquantes.

| Fichier | Lignes | Colonnes et types |
|---|---|---|
| `network_summary.parquet` | Une par service | `service` (String) ; `node_count`, `edge_count`, `weakly_connected_components`, `strongly_connected_components`, `largest_weak_component`, `nodes_multiple_incoming`, `nodes_multiple_outgoing`, `self_loops` (Int64) |
| `node_metric_summary.parquet` | Une par service | `service` (String) ; pour chaque métrique : `*_count`, `*_missing` (UInt32), `*_mean`, `*_std`, `*_median`, `*_q25`, `*_q75`, `*_min`, `*_max` (numériques ; extrema des degrés entiers) |
| `node_rankings.parquet` | Jusqu’à dix par service et mesure | `rank` (UInt32), `service`, `ranking_metric`, `node_id`, `station_name` (String), `value` (Float64) |
| `edge_rankings.parquet` | Jusqu’à dix par service | `service`, `edge_id`, `source`, `origin_name`, `target`, `destination_name` (String), `edge_betweenness` (Float64) |
| `monthly_summary.parquet` | Une par mois/service | `period`, `service` (String), `node_count`, `edge_count` (UInt32), synthèses moyennes et maximales (Float64) |
| `operational_summary.parquet` | Une par service | `service` (String), effectifs valides, manquants et atypiques de chaque indicateur (UInt32), statistiques (Float64) |
| `quality_flag_summary.parquet` | Une par service | `service` (String), un comptage UInt32 par indicateur booléen existant |

Les noms exacts des champs mensuels et opérationnels figurent dans leurs schémas Parquet. Ils sont dérivés des colonnes des phases 1 et 2 sans redéfinir les mesures sources.

## Figures

- `network_national.png`, `network_international.png` : graphes orientés origine-destination complets ; les directions réciproques sont courbées séparément, les composantes internationales sont disposées indépendamment et la taille des nœuds représente l’intermédiarité globale.
- `degree_distributions.png` : barres regroupées et normalisées des degrés entrants/sortants, valeurs entières et effectif de gares par service.
- `node_centrality_distributions.png` : fonctions de répartition empiriques de l’intermédiarité et du PageRank, avec proportions de valeurs nulles au sens numérique dans la légende.
- `top10_station_rankings.png` : noms des dix gares les mieux classées par degré, intermédiarité et PageRank, par service.
- `edge_betweenness_distribution.png` : fonction de répartition et histogramme complémentaire, médiane et 90e percentile.
- `top10_edge_rankings.png` : dix liaisons à plus forte intermédiarité par service, avec noms d’origine/destination.
- `monthly_network_evolution.png` : effectifs de nœuds/arêtes et maxima mensuels de PageRank/intermédiarité ; annotations des changements internationaux en 2025.
- `operational_outcome_distributions.png` : distributions du retard principal, du retard complémentaire des trains retardés et du taux d’annulation. L’histogramme central de tous les trains omet les valeurs signalées sous −15 minutes ; les moyennes des trains retardés au-delà de 120 minutes ont un panneau distinct. Les annulations disposent d’une vue complète et d’un zoom 0–0,10. Les taux absents restent absents. Ces choix d’affichage ne modifient pas le fichier de recherche ; les effectifs affichés sont indiqués.

## Limites d’interprétation

Le degré compte les voisins origine-destination observés, pas la fréquence des trains ou le trafic voyageurs. Les chemins ne sont pas nécessairement des itinéraires réels ou des voies physiques. La centralité ne prouve pas une propagation des retards. Les retards négatifs restent dans les synthèses ; les taux d’annulation nuls et absents restent distincts. Ces résultats décrivent uniquement distributions et topologie. L’étude des relations relève de la phase 3B et doit tenir compte des observations répétées liaison-mois et de la structure temporelle.
