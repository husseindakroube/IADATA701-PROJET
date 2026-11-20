# Transfert des données vers Streamlit

## Contexte du projet

La question de recherche est : « Dans quelle mesure la structure du réseau TGV est-elle associée à la régularité des liaisons ? » Le package Graph Analysis prépare le graphe ainsi que les résultats de centralité, d’analyse descriptive et d’association. Le dépôt contient désormais une application Streamlit dans `app/app.py`, et Streamlit est déclaré dans `pyproject.toml`. L’application consomme certains artefacts Graph Analysis déjà produits; les autres restent disponibles pour des évolutions ultérieures. Ce document s’appuie sur les artefacts vérifiés dans le dépôt et ne nécessite pas de relancer les analyses en amont.

## Jeux de données de référence

| Chemin | Granularité et clé | Champs importants | Utilisation recommandée |
| --- | --- | --- | --- |
| `data/processed/research_dataset.parquet` | Un mois × service × liaison OD; clé unique `(date, service, gare_depart, gare_arrivee)` | `date` (chaîne `YYYY-MM`), `service`, `edge_id`, `source`, `target`, noms des gares de départ et d’arrivée, indicateurs opérationnels, `cancellation_rate`, `cancellation_rate_valid`, métriques du graphe, indicateurs qualité | Source des vues mensuelles opérationnelles et entrée de l’analyse d’association Graph Analysis. Streamlit affiche les tables Phase 3B déjà produites. Le fichier contient 12 907 lignes et 56 colonnes. |
| `data/processed/graph/nodes.parquet` | Une identité de gare; `node_id` unique | `node_id`, `station_name` | Correspondance des noms pour la topologie du réseau. Le fichier contient 59 identifiants de gare distincts, communs aux services. |
| `data/processed/graph/edges.parquet` | Une arête OD dirigée, associée à un service; `edge_id` unique | `edge_id`, `service`, `source`, `target`, `n_months_observed`, `first_date`, `last_date` | Topologie globale du réseau. |
| `data/processed/graph/node_metrics.parquet` | Une période × un service × une gare; clé unique `(period, service, node_id)`; 6 385 lignes × 13 colonnes | `period`, `service`, `node_id`, `station_name`, degrés, betweenness, closeness et champs PageRank | Métriques complémentaires des gares. Filtrer `period = "overall"` pour les attributs globaux des nœuds; des lignes mensuelles sont disponibles lorsqu’une métrique manque dans le jeu de recherche. |
| `data/processed/graph/edge_metrics.parquet` | Une période × un service × une arête dirigée; clé unique `(period, service, edge_id)`; 13 053 lignes × 24 colonnes | `period`, `service`, `edge_id`, `source`, `target`, `edge_betweenness` et métriques des nœuds source/cible | Métriques complémentaires des liaisons. Filtrer `period = "overall"` pour les attributs globaux des arêtes; utiliser les lignes mensuelles uniquement pour les métriques absentes du jeu de recherche. |
| `data/processed/graph/descriptive/monthly_summary.parquet` | Un mois × un service; clé unique `(period, service)` | `node_count`, `edge_count`, `mean_degree`, `max_pagerank`, `max_betweenness`, résumés de betweenness des arêtes | Évolution mensuelle de la topologie et des métriques. |

`data/processed/sncf.parquet` est la sortie ETL à 30 colonnes utilisée en amont. `data/processed/graph/edge_observations.parquet` est une entrée de construction : ses 33 colonnes et ses 12 907 enregistrements clés correspondent à un sous-ensemble de `research_dataset.parquet`. Aucun de ces deux fichiers ne doit être chargé comme second jeu principal du tableau de bord.

## Périmètres des agrégats de liaisons

`data/processed/liaisons_detail.csv` contient 130 lignes utilisées par la carte et ses vues de détail. Le script `scripts/exploration/generer_liaisons_detail.py` agrège les observations par `(gare_depart, gare_arrivee)`, sans inclure `service` dans cette clé, puis rattache les prédictions et les clusters.

À l’inverse, `data/processed/graph/edges.parquet` contient 146 arêtes dirigées identifiées par service. Les deux nombres proviennent donc d’artefacts, de clés et de périmètres différents. Ils ne sont pas directement comparables; leur écart ne prouve pas à lui seul qu’il manque des données ou qu’il existe une incohérence.

## Tables d’analyse

Les sorties Phase 3A se trouvent dans `data/processed/graph/descriptive/` :

- `network_summary.parquet` (2 × 9) : nombres de nœuds, d’arêtes et indicateurs de connexité par service. Les 52 nœuds National et 18 nœuds International représentent 70 appartenances gare-service; plusieurs appartiennent aux deux services, pour 59 `node_id` distincts dans `nodes.parquet`.
- `monthly_summary.parquet` (210 × 10) : résumés mensuels de la topologie et des métriques.
- `node_rankings.parquet` (113 × 6) : gares en tête des classements par service et par métrique; les ex æquo sont conservés.
- `edge_rankings.parquet` (52 × 7) : liaisons à forte edge-betweenness avec noms d’origine et de destination lisibles. Le fichier ne contient pas de colonne de rang; conserver les valeurs égales aux seuils d’affichage.
- `operational_summary.parquet` (2 × 31) : statistiques opérationnelles descriptives par service.
- `quality_flag_summary.parquet` (2 × 6) : aperçu facultatif des flags qualité.
- `node_metric_summary.parquet` (2 × 82) : résumé complémentaire large; préférer `node_metrics.parquet` ou `node_rankings.parquet` pour les vues interactives.

Les sorties Phase 3B se trouvent dans `data/processed/graph/phase3b/` :

- `correlations.parquet` (126 × 8) : clé unique `(analysis_scope, service, predictor, outcome, method)`; coefficient, `p_value` exploratoire brut et `n_valid`.
- `quantile_comparisons.parquet` (270 × 13) : groupes de centralité, stratégie de regroupement, taille d’échantillon, médiane, moyenne, écart-type, quartiles et IQR.
- `robustness_comparisons.parquet` (42 × 10) : coefficients et tailles d’échantillon effectives pour les comparaisons complètes et de sensibilité de la variable principale.

## Visualisations

Les chemins des figures actuelles sont listés ci-dessous. Les PNG sont des instantanés prêts à intégrer dans un rapport; pour permettre des filtres ou des infobulles dans l’application, reconstruire les figures à partir des Parquet correspondants.

| Chemin | Objectif et recommandation |
| --- | --- |
| `data/processed/graph/visualizations/network_national.png` | Graphe orienté global National; Paris Lyon ressort visuellement. L’image statique peut être utilisée dans un rapport, mais les libellés et les arêtes se chevauchent; reconstruire une vue interactive à partir de `nodes.parquet` et `edges.parquet`. |
| `data/processed/graph/visualizations/network_international.png` | Graphe global International montrant ses composantes déconnectées. L’image statique peut être utilisée dans un rapport; une vue interactive permettrait d’identifier les composantes et les gares. |
| `data/processed/graph/visualizations/degree_distributions.png` | Proportions des degrés entrants et sortants par service. Reconstruire la figure si des filtres de service ou de métrique sont ajoutés. |
| `data/processed/graph/visualizations/node_centrality_distributions.png` | Distributions de betweenness et PageRank, y compris les proportions de valeurs égales à zéro. Vue d’ensemble statique ou sélecteur interactif de métrique. |
| `data/processed/graph/visualizations/leading_station_rankings.png` | Gares en tête des classements Degree, Betweenness et PageRank. Reconstruire à partir de `node_rankings.parquet` pour ajouter des sélecteurs. |
| `data/processed/graph/visualizations/edge_betweenness_distribution.png` | ECDF de edge-betweenness et histogramme complémentaire avec médiane et P90. Contexte statique utile; une vue interactive peut exposer les noms des liaisons. |
| `data/processed/graph/visualizations/monthly_network_evolution.png` | Quatre séries mensuelles; les lignes PageRank et Betweenness sont des maxima mensuels. Reconstruire à partir de `monthly_summary.parquet`. |
| `data/processed/graph/visualizations/operational_outcome_distributions.png` | Distributions des retards, avec une queue extrême séparée, et vues du taux d’annulation à l’échelle complète et près de zéro. Reconstruire à partir de `research_dataset.parquet` pour ajouter des filtres. |
| `data/processed/graph/visualizations/phase3b/edge_betweenness_scatter.png` | Variable principale de retard en fonction de edge-betweenness, par service. Reconstruire à partir du jeu de recherche pour les infobulles et les filtres; les points se chevauchent. |
| `data/processed/graph/visualizations/phase3b/target_degree_scatter.png` | Variable principale en fonction du degré cible, par service. Une reconstruction interactive est recommandée; les degrés discrets se chevauchent. |
| `data/processed/graph/visualizations/phase3b/edge_betweenness_quantile_groups.png` | Diagrammes en boîtes de la variable principale par groupes de edge-betweenness qui préservent les ex æquo. Reconstruire pour ajouter des sélecteurs de prédicteur et de variable cible. |
| `data/processed/graph/visualizations/phase3b/primary_spearman_overview.png` | Vue d’ensemble de Spearman pour la variable principale dans les périmètres Overall, National et International. Le tableau des corrélations reste la source filtrable de référence. |

Les anciennes figures `top10_edge_rankings.png` et `top10_station_rankings.png` sont absentes et ne sont pas utilisées par le tableau de bord.

## Intégration actuelle dans Streamlit

L’application charge les observations mensuelles depuis `data/processed/sncf.parquet`. Dans la vue détaillée d’une liaison, elle lit aussi `research_dataset.parquet` pour afficher le taux d’annulation. Elle consomme également `nodes.parquet`, `edges.parquet` et `node_metrics.parquet` pour l’ego-graphe et les métriques par gare, `network_summary.parquet` et `node_rankings.parquet` pour la synthèse réseau et les classements, ainsi que les images statiques des réseaux National et International.

Pour construire l’ego-graphe, l’application convertit les identifiants `source` et `target` des arêtes en noms via `nodes.node_id`, puis sélectionne les métriques globales par `service` et `period = "overall"` et les associe actuellement à `station_name`. Les noms sont uniques dans les artefacts vérifiés. Pour toute nouvelle jointure entre métriques et nœuds, la clé recommandée reste `(service, node_id)`.

La page `Structure et régularité` consomme désormais les tables `correlations.parquet`, `quantile_comparisons.parquet` et `robustness_comparisons.parquet` de Phase 3B. Les tables `edge_metrics.parquet`, `edge_rankings.parquet`, `monthly_summary.parquet`, `operational_summary.parquet`, `quality_flag_summary.parquet` et `node_metric_summary.parquet` restent disponibles mais ne sont pas utilisées par l’application. Les autres visualisations de rapport, notamment les quatre PNG Phase 3B, restent statiques et ne sont pas intégrées à l’interface.

## Intégration Phase 2 : structure et régularité

La navigation comporte sept pages, dans cet ordre : **Accueil**, **Qualité des données**, **Liaisons et réseau**, **Structure et régularité**, **Profils et clusters**, **Prédictions**, puis **Conclusions**. La page `Liaisons et réseau` conserve exactement trois onglets : **Carte interactive**, **Explorer une liaison** et **Comparer deux liaisons**. L’ancien onglet « Comprendre le réseau » n’y apparaît plus.

La page `Structure et régularité` reprend dans l’onglet **Structure du réseau** le contenu auparavant présent dans « Comprendre le réseau » : synthèse des réseaux, choix du service, ego-graphe, visualisation statique du réseau, classements et détails des métriques par gare.

La page `Structure et régularité` comporte exactement cinq onglets, dans cet ordre : **Structure du réseau**, **Corrélations**, **Comparaison par quantiles**, **Robustesse** et **Synthèse**. Le cinquième onglet réunit les résultats topologiques et Phase 3B pour répondre à la question de recherche de cette page; il ne remplace pas la page globale **Conclusions** et ne recalcule aucun résultat.

1. **Structure du réseau** : artefacts Phase 1 existants (`network_summary.parquet`, `nodes.parquet`, `edges.parquet`, `node_metrics.parquet`, `node_rankings.parquet` et les images statiques National/International). L’application ne recalcule aucune métrique de graphe.
2. **Corrélations** : `phase3b/correlations.parquet`; filtres de périmètre, méthode, métrique et indicateur; carte thermique des coefficients et tableau comprenant coefficient, effectif valide et p-value brute exploratoire.
3. **Comparaison par quantiles** : `phase3b/quantile_comparisons.parquet`; filtres de périmètre, métrique et indicateur; médiane avec intervalle Q1–Q3, tailles d’échantillon et tableau des statistiques descriptives enregistrées. Les groupes d’origine et les ex æquo sont conservés.
4. **Robustesse** : `phase3b/robustness_comparisons.parquet`; filtres de périmètre, métrique et méthode; comparaison des coefficients complets et de sensibilité, avec leur différence et leurs tailles d’échantillon. L’artefact ne contient pas de p-value.
5. **Synthèse** : narration en français des résultats vérifiés de topologie, de corrélation, de comparaison par quantiles et de sensibilité, avec une réponse circonscrite à la question de structure et régularité. Les constats sont éditorialisés à partir des artefacts existants; ils ne sont pas rechargés ni recalculés au rendu. En cas de régénération des artefacts, le texte doit être revérifié. L’onglet n’ajoute ni visualisation ni calcul analytique.

Les résultats Phase 3B couvrent la période complète 2018-01 → 2026-09 et n’ont pas de dimension mensuelle; l’interface ne propose donc pas de filtre par mois. `Overall` désigne un périmètre agrégé, et non un troisième service. Les 73 taux d’annulation invalides ou manquants sont exclus des calculs concernés, jamais remplacés par zéro. L’analyse de sensibilité exclut les retards de l’indicateur principal inférieurs à −15 minutes uniquement pour ce calcul; les observations originales restent dans le jeu de recherche. Les p-values sont brutes et exploratoires, les observations mensuelles d’une même liaison sont répétées, et les associations ne démontrent pas de causalité.

### Lecture analytique affichée dans l’application

Les 126 coefficients enregistrés varient de −0,227 à +0,187; leur amplitude reste limitée. Le résultat le plus marqué est la relation négative entre la Betweenness des arêtes et le taux d’annulation dans le périmètre International (Spearman, `n = 1 541`). La plus forte association positive relie également la Betweenness des arêtes au retard moyen à l’arrivée des trains retardés en International (Spearman, `r = +0,187`). Les maxima diffèrent selon le périmètre : en National, le degré du nœud d’arrivée présente l’association la plus marquée avec le retard moyen de tous les trains; en Overall, c’est le PageRank du nœud d’arrivée. Pearson et Spearman donnent le même sens dans 57 des 63 comparaisons appariées.

Les groupes par quantiles montrent rarement une progression régulière : 59 des 63 séquences de médianes ordonnées sont irrégulières. Dans l’exemple Overall de la Betweenness des arêtes, les médianes du retard moyen de tous les trains sont de 6,79, 4,62, 8,71 et 5,73 minutes de Q1 à Q4. Les intervalles centraux se chevauchent pour 185 des 189 comparaisons de groupes voisins. Les quatre profils monotones apparaissent dans le périmètre International, notamment le taux d’annulation selon la Betweenness des arêtes et le retard principal selon des groupes de Betweenness Centrality positive. La sensibilité aux 11 retards inférieurs à −15 minutes modifie peu la plupart des coefficients (différence absolue médiane de 0,0033), même si une association National liée au PageRank source devient plus négative. Ces résultats suggèrent un lien statistique partiel et dépendant du périmètre, sans établir de mécanisme causal.

## Pages et filtres suggérés

Cette liste distingue les vues déjà intégrées des évolutions encore possibles :

1. **Vue d’ensemble :** période observée, nombre d’enregistrements mensuels, taille des réseaux et médianes des résultats par service. Utiliser `network_summary.parquet`, `operational_summary.parquet` et le jeu de recherche. Filtrer par service.
2. **Structure du réseau :** la page intégrée présente la synthèse des réseaux, l’ego-graphe, les classements des gares et les métriques détaillées d’une gare. Les classements d’arêtes issus de `edge_rankings.parquet` restent une évolution possible.
3. **Évolution du réseau :** nombres mensuels de nœuds et d’arêtes, et séries de métriques issues de `monthly_summary.parquet`. Filtrer par service et période. Présenter PageRank et Betweenness comme des maxima mensuels.
4. **Régularité opérationnelle :** distributions des retards et des taux d’annulation valides, ou résumés mensuels/par liaison issus de `research_dataset.parquet`. Filtrer par service, mois, origine, destination et variable étudiée.
5. **Structure et régularité :** cette vue est intégrée à la page dédiée décrite ci-dessus. Les nuages de points au niveau des lignes ne sont pas proposés par cette intégration; toute évolution de ce type devra utiliser directement le jeu de recherche et respecter les clés de jointure documentées.

## Règles de jointure

- Les vues mensuelles opérationnelles utilisent directement `research_dataset.parquet`, qui contient déjà les métriques mensuelles associées; ne pas le joindre à nouveau à `node_metrics.parquet` ou `edge_metrics.parquet`. L’analyse d’association Graph Analysis produit les tables Phase 3B à partir de ce jeu; la page Streamlit lit les tables Phase 3B et ne recalcule pas ces résultats.
- Pour la topologie, relier séparément `edges.source` et `edges.target` à `nodes.node_id`; conserver `service` lors du filtrage des arêtes.
- Pour ajouter une métrique globale à un nœud du réseau, utiliser `data/processed/graph/node_metrics.parquet`, filtrer `period = "overall"` et joindre sur `(service, node_id)`. Pour une métrique globale d’arête, utiliser `data/processed/graph/edge_metrics.parquet`, filtrer `period = "overall"` et joindre sur `(service, edge_id)`.
- Pour une métrique mensuelle absente du jeu de recherche, faire correspondre `date = period`, `service` et `edge_id` pour les arêtes, ou `date = period`, `service` et `node_id` pour les nœuds. Ne pas joindre uniquement par identifiant de gare ou d’arête entre plusieurs services ou périodes.
- Utiliser `monthly_summary.parquet` plutôt que de recalculer les métriques mensuelles de topologie dans l’application.

## Valeurs manquantes et interprétation

- `cancellation_rate` n’est utilisable que si `cancellation_rate_valid` vaut `True`. Il y a 73 taux invalides ou manquants; les métadonnées indiquent un dénominateur `nb_train_prevu` non positif. Ne jamais les remplacer par zéro.
- Une valeur PageRank manquante (notamment après une non-convergence) reste indisponible; ne pas l’afficher comme zéro.
- Conserver les retards négatifs. Les 11 observations dont le résultat principal est inférieur à −15 minutes sont exclues uniquement de la comparaison de sensibilité, pas du jeu de recherche.
- `date` est une chaîne mensuelle (`YYYY-MM`), et non une date journalière.
- Les résultats Overall regroupent les deux services et sont descriptifs. Les services National et International ont des compositions de liaisons et des structures de graphe différentes.
- Les lignes mensuelles d’une liaison sont des observations répétées. Les p-values de Pearson/Spearman sont exploratoires et ne constituent pas une preuve définitive. Une corrélation n’implique pas de causalité. Les liaisons OD ne sont pas nécessairement des segments ferroviaires adjacents ni des itinéraires confirmés; la centralité ne mesure pas le trafic de voyageurs et n’établit pas une propagation des retards.

## Répartition des responsabilités

Graph Analysis est responsable de la construction du graphe, des centralités, des résumés descriptifs, des calculs de corrélation, de l’affectation des groupes qui préserve les ex æquo et du calcul de sensibilité aux retards extrêmes. Streamlit charge les sorties vérifiées, les filtre et les présente, et peut reconstruire des figures interactives lorsque c’est utile. L’application ne doit pas recalculer les métriques du graphe, redéfinir la validité des taux d’annulation, remplacer les taux manquants par zéro ni présenter les p-values ordinaires comme confirmatoires.
