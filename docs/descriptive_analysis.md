# Analyse descriptive du réseau et visualisations

La phase 3A synthétise les métriques de graphe existantes de la phase 1 et les
observations opérationnelles de la phase 2. Elle ne recalcule pas les métriques,
ne rapproche pas les résultats structurels et opérationnels à des fins
d’inférence et ne réalise ni corrélations, ni tests, ni régressions. Les
services National et International sont présentés séparément.

## Exécution

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph.descriptive import run_descriptive_analysis; result = run_descriptive_analysis()"
uv run python -c "from projet_kit_data.graph.visualization import run_visualization_pipeline; paths = run_visualization_pipeline()"
```

Les tables descriptives sont écrites dans
`data/processed/graph/descriptive/`, les figures dans
`data/processed/graph/visualizations/` et le rapport narratif est maintenu dans
`data/reports/graph/research_report.md`. Le générateur ne remplace que la
section descriptive balisée et conserve le reste du rapport.

## Tables descriptives produites

- `network_summary.parquet` : une ligne par service ; nombres globaux de nœuds et d’arêtes,
  nombres de composantes faibles/fortes, taille de la plus grande composante faible, nombres
  de nœuds à degrés entrant/sortant multiples et boucles. Les composantes sont calculées à
  partir de la table d’arêtes orientées existante et comparées aux métadonnées de construction.
- `node_metric_summary.parquet` : une ligne par service et distributions globales des métriques
  des nœuds (nombre de valeurs présentes, nombre de valeurs manquantes, moyenne, écart-type,
  médiane, 25e/75e percentiles, minimum, maximum).
- `node_rankings.parquet` : premiers nœuds à valeur positive par service et mesure
  (`connectivity_degree`, `betweenness_centrality`, `pagerank`), avec rang, identifiant de gare,
  nom de gare et valeur en pleine précision. Les ex æquo au seuil `top_n` sont inclus ; les rangs
  ex æquo sont déterminés selon la précision affichée de la métrique. Les zéros sont exclus des
  classements, mais leur proportion reste indiquée dans le graphique de distribution.
- `edge_rankings.parquet` : premières liaisons orientées à valeur positive par service selon la
  betweenness des arêtes, avec l’identifiant de l’arête et les noms lisibles des gares d’origine
  et de destination. Les ex æquo selon la précision affichée au seuil `top_n` sont inclus. La
  sortie détaillée conserve les valeurs en pleine précision et le schéma de colonnes d’origine.
- `monthly_summary.parquet` : une ligne par mois et service, avec les nombres observés de nœuds et
  d’arêtes, le degré moyen, le PageRank maximal, la betweenness des nœuds maximale/médiane et la
  betweenness des arêtes moyenne/maximale.
- `operational_summary.parquet` : synthèses par service des distributions du retard moyen à
  l’arrivée de tous les trains, du taux d’annulation et du retard moyen à l’arrivée des trains
  retardés. Le fichier indique aussi les nombres de valeurs manquantes et de valeurs aberrantes
  descriptives selon la règle de Tukey à 1,5 IQR. Ces nombres ne filtrent ni ne modifient les
  observations.
- `quality_flag_summary.parquet` : nombres de valeurs booléennes `flag_*` existantes par service.

Les classements de nœuds et d’arêtes utilisent les métriques de toute la période
de la phase 1 (`period="overall"`). Les synthèses mensuelles n’utilisent que
les lignes de métriques mensuelles. Les synthèses des résultats opérationnels
proviennent du jeu de recherche mensuel de la phase 2 et ne sont pas mélangées
aux métriques globales du graphe.

`graph/presentation.py` contient l’unique dictionnaire d’affichage des
métriques de graphe. Il associe chaque colonne interne à un libellé français, à
une courte explication en français, à une unité et à une précision d’affichage.
La mise en forme ne modifie jamais les valeurs numériques stockées. Le rapport
de recherche unifié en français reste volontairement concis ; les classements
complets et lisibles par machine sont conservés en Parquet avec leurs
identifiants, tandis que les synthèses destinées aux lecteurs affichent les
noms des gares.

### Schémas de sortie

Toutes les tables sont des fichiers Parquet. Les champs d’identifiant, de gare,
de service, de période et de nom de métrique sont des chaînes de caractères ;
les synthèses numériques sont des colonnes numériques et peuvent contenir des
valeurs manquantes (`null`) lorsque les métriques source sont absentes.

| Fichier | Lignes | Colonnes et types |
| --- | --- | --- |
| `network_summary.parquet` | 1 par service | `service` (String) ; `node_count`, `edge_count`, `weakly_connected_components`, `strongly_connected_components`, `largest_weak_component`, `nodes_multiple_incoming`, `nodes_multiple_outgoing`, `self_loops` (Int64) |
| `node_metric_summary.parquet` | 1 par service | `service` (String) ; pour chaque métrique de nœud : `*_count` et `*_missing` (UInt32), puis `*_mean`, `*_std`, `*_median`, `*_q25`, `*_q75`, `*_min`, `*_max` (numériques ; les extrema du degré gardent un type entier) |
| `node_rankings.parquet` | Nœuds à valeur positive les mieux classés par service et mesure, ex æquo au seuil inclus | `rank` (UInt32), `service`, `ranking_metric`, `node_id`, `station_name` (String), `value` (Float64) |
| `edge_rankings.parquet` | Liaisons à valeur positive les mieux classées par service, ex æquo au seuil inclus | `service`, `edge_id`, `source`, `origin_name`, `target`, `destination_name` (String), `edge_betweenness` (Float64) |
| `monthly_summary.parquet` | 1 par mois et service | `period`, `service` (String) ; `node_count`, `edge_count` (UInt32) ; synthèses moyennes/maximales des métriques (Float64) |
| `operational_summary.parquet` | 1 par service | `service` (String) ; pour chaque résultat, nombre, valeurs manquantes et valeurs aberrantes (UInt32), ainsi que les statistiques récapitulatives (Float64) |
| `quality_flag_summary.parquet` | 1 par service | `service` (String) ; un compte UInt32 pour chaque indicateur de qualité booléen existant |

Les noms exacts des champs des synthèses mensuelles et des résultats sont
enregistrés dans les schémas Parquet correspondants. Ils dérivent des noms de
colonnes source existants des phases 1 et 2 et ne redéfinissent pas ces mesures.

## Figures

Les fichiers PNG générés sont :

- `network_national.png`, `network_international.png` : graphes OD orientés complets ; les
  directions réciproques sont courbées séparément, les composantes faibles International sont
  disposées indépendamment et la taille des nœuds représente leur betweenness globale.
- `degree_distributions.png` : barres groupées et normalisées des degrés entrant/sortant ; chaque
  panneau indique les degrés entiers et le nombre de nœuds du service.
- `node_centrality_distributions.png` : fonctions de répartition empiriques distinctes pour la
  betweenness centrality et le PageRank, avec la proportion de valeurs égales à zéro dans la légende.
- `leading_station_rankings.png` : noms lisibles des gares aux trois premiers rangs denses du
  degré, de la betweenness centrality et du PageRank. Les ex æquo sont inclus, les valeurs égales à zéro
  sont omises et les valeurs sous-jacentes restent inchangées.
- `edge_betweenness_distribution.png` : fonction de répartition empirique et histogramme
  complémentaire, avec annotations de la médiane et du 90e percentile. L’ancien graphique des
  dix premières arêtes a été retiré, car il ne retenait que la moitié des 20 arêtes International
  ex æquo au maximum ; toutes ces arêtes restent dans le classement Parquet.
- `monthly_network_evolution.png` : nombres de nœuds/arêtes et maxima mensuels du PageRank et de
  la betweenness centrality, avec les changements de topologie International observés en 2025.
  Les courbes de centralité montrent des maxima mensuels, et non des moyennes du réseau.
- `operational_outcome_distributions.png` : distributions par service du retard principal à
  l’arrivée, du retard à l’arrivée des trains retardés et du taux d’annulation. Les retards de
  tous les trains signalés sous -15 minutes sont exclus de l’histogramme principal ; les moyennes
  des trains retardés au-delà de 120 minutes sont isolées dans un panneau de queue ; les taux
  d’annulation sont présentés sur l’étendue complète et dans un zoom de 0 à 0,10. Les taux
  manquants restent manquants. Ces exclusions d’affichage ne modifient pas le fichier Parquet de
  recherche et la figure indique les nombres affichés.

## Limites d’interprétation

Le degré compte les voisins OD distincts observés ; il ne mesure ni la
fréquence des trains ni le trafic voyageurs. Les chemins du graphe ne
correspondent pas nécessairement à des itinéraires réels ni à des segments de
voie physique. La centralité ne prouve pas une propagation des retards. Les
valeurs négatives de retard à l’arrivée restent présentes dans les synthèses et
les figures descriptives ; les taux d’annulation égaux à zéro et les taux
manquants (`null`) restent distincts. Ces résultats décrivent uniquement les distributions et la
topologie. Toute évaluation des relations relève de la phase 3B et doit tenir
compte des observations répétées liaison-mois ainsi que de la structure
temporelle.
