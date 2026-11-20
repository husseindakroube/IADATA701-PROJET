# Préparation du jeu de données de recherche

## Objectif et granularité

Cette étape prépare un jeu de données mensuel joignable pour répondre à la question : *Dans quelle
mesure la structure du réseau TGV est-elle associée à la régularité des
liaisons ?* Cette étape ne calcule pas d’associations statistiques et ne déduit
aucun lien de causalité. La granularité est une liaison orientée, un service et
un mois, identifiés de façon unique par `(date, service, gare_depart,
gare_arrivee)`. L’observation source d’origine et ses champs sont conservés
dans la sortie.

## Entrées et jointures

Le pipeline lit les artefacts existants de la phase 1 ; il ne relance ni l’ETL,
ni la construction, ni le calcul des métriques de graphe :

| Entrée | Chemin par défaut | Rôle dans la jointure |
|---|---|---|
| Observations mensuelles des arêtes | `data/processed/graph/edge_observations.parquet` | Valeurs opérationnelles source, identifiants des nœuds source/cible et identifiant d’arête |
| Métriques des arêtes | `data/processed/graph/edge_metrics.parquet` | `edge_betweenness` mensuelle |
| Métriques des nœuds | `data/processed/graph/node_metrics.parquet` | Métriques structurelles mensuelles des gares source et cible |

Seules les lignes dont la période correspond à un mois peuvent être jointes.
`period="overall"` est explicitement exclue. Les métriques d’arête sont
jointes sur `(date=period, service, edge_id)` et leurs identifiants source/cible
stockés sont comparés à ceux de l’observation. Les métriques de nœud sont
jointes séparément sur `(date=period, service, source=node_id)` et
`(date=period, service, target=node_id)`. Les valeurs des nœuds reçoivent les
préfixes `source_` et `target_`. L’unicité de chaque clé de recherche est
vérifiée ; les jointures sont de type plusieurs-vers-un et le nombre de lignes
est contrôlé après chacune d’elles. Les métriques manquantes restent manquantes
(`null` dans les données) et ne suppriment pas les observations source.

## Variables opérationnelles

Le résultat principal est `retard_moyen_tous_trains_arrivee` ; sa valeur source,
y compris les valeurs négatives et égales à zéro, est conservée. Le flag booléen
`flag_primary_arrival_delay_below_minus_15` signale les valeurs inférieures à
-15 minutes sans les exclure. `retard_moyen_arrivee` est conservé comme
indicateur complémentaire de gravité. Les flags de qualité source existants,
les comptes opérationnels, les comptes par seuil, les pourcentages de causes et
les commentaires sont conservés sans modification.

`cancellation_rate` est calculé comme suit :
`nb_annulation / nb_train_prevu` uniquement si `nb_train_prevu > 0` et
`0 <= nb_annulation <= nb_train_prevu`. Dans les autres cas, le taux est
manquant (`None`), les comptes source sont conservés,
`cancellation_rate_valid` vaut false et
`cancellation_rate_invalid_reason` indique la première condition non satisfaite.
Une valeur manquante (`None`) n’est jamais remplacée par zéro. Aucun `arrival_delay_rate`
n’est calculé, car les champs disponibles ne permettent pas d’établir le
dénominateur correspondant aux trains réellement exploités. Aucun taux de
retard fondé sur un seuil ni aucune variable causale n’est créé.

## Sortie et reproductibilité

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph.analysis import run_research_data_preparation_pipeline; result = run_research_data_preparation_pipeline()"
```

Les sorties sont `data/processed/research_dataset.parquet`,
`data/processed/research_dataset_metadata.json`, ainsi que
`data/reports/graph/research_data_quality_report.md`. Le fichier Parquet contient
toutes les colonnes des observations source, ainsi que `edge_betweenness`, les
métriques mensuelles des nœuds préfixées par source/cible,
`flag_primary_arrival_delay_below_minus_15`, `cancellation_rate`,
`cancellation_rate_valid` et `cancellation_rate_invalid_reason`. Les types
Polars exacts sont consignés dans les métadonnées et le rapport. Les chemins
sont configurables via l’API publique.

Les métadonnées enregistrent la granularité, les nombres de lignes et de
colonnes, la couverture des mois et des services, les chemins et nombres de
lignes des entrées, les clés et contrôles de jointure, les nombres de métriques
manquantes, la validité des taux d’annulation et les comptes par motif, les
anomalies de retard, le schéma de sortie et les réserves pertinentes. Le
rapport qualité Markdown présente les mêmes résultats pour examen. Conservez
les artefacts de construction et de métriques de la phase 1 comme entrées
immuables afin de pouvoir reproduire le jeu dérivé.

## Limites

Les lignes SNCF décrivent des relations origine-destination mensuelles, et non
des parcours individuels de train ou des segments physiques de voie. Les
métriques structurelles ne démontrent ni les déplacements réels des trains ni
la propagation des retards. Les retards moyens négatifs sont conservés et
signalés ; ils ne sont ni considérés comme des erreurs ni corrigés. Les taux
d’annulation dont le dénominateur est nul ou négatif, ou dont les comptes sont
incohérents, sont indisponibles et ne valent pas zéro. Le dénominateur du taux
de retard à l’arrivée reste indéterminé ; ce taux est donc volontairement
absent.
