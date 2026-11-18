# Préparation des données de recherche

## Objectif et granularité

Cette phase prépare des données mensuelles joignables pour étudier l’association entre structure du réseau TGV et régularité. Elle ne calcule pas d’association statistique et ne déduit pas de causalité. Une observation correspond à une liaison orientée, un service et un mois, avec la clé unique `(date, service, gare_depart, gare_arrivee)`. Les champs de l’observation source sont conservés.

## Entrées et jointures

La chaîne lit les fichiers de la phase 1 sans relancer l’ETL, la construction ni les métriques :

| Entrée | Chemin par défaut | Usage |
|---|---|---|
| Observations mensuelles des arêtes | `data/processed/graph/edge_observations.parquet` | Valeurs opérationnelles, identifiants des extrémités et de l’arête |
| Métriques des arêtes | `data/processed/graph/edge_metrics.parquet` | Intermédiarité mensuelle `edge_betweenness` |
| Métriques des nœuds | `data/processed/graph/node_metrics.parquet` | Métriques mensuelles des gares de départ et d’arrivée |

Seules les lignes dont `period` est un mois participent aux jointures ; `period="overall"` est exclu. Les arêtes sont jointes sur `(date=period, service, edge_id)` et les identifiants d’extrémité sont contrôlés. Les nœuds sont joints séparément sur `(date=period, service, source=node_id)` et `(date=period, service, target=node_id)`, avec préfixes `source_` et `target_`. Les clés sont uniques, les jointures sont plusieurs-à-un et l’effectif est contrôlé après chacune. Les métriques absentes restent nulles sans supprimer d’observation.

## Variables opérationnelles

La variable principale est `retard_moyen_tous_trains_arrivee` ; les valeurs négatives et nulles sont préservées. `flag_primary_arrival_delay_below_minus_15` signale les valeurs inférieures à −15 minutes sans les exclure. `retard_moyen_arrivee` est un indicateur complémentaire de gravité. Les indicateurs qualité, comptages, seuils, causes et commentaires restent inchangés.

`cancellation_rate = nb_annulation / nb_train_prevu` est calculé uniquement si `nb_train_prevu > 0` et `0 <= nb_annulation <= nb_train_prevu`. Sinon, le taux est nul, les comptages sont conservés, `cancellation_rate_valid` vaut faux et `cancellation_rate_invalid_reason` indique la première condition non satisfaite. Une valeur nulle n’est jamais remplacée par zéro. `arrival_delay_rate` n’est pas calculé : son dénominateur de circulations effectives n’est pas établi dans ce traitement. Aucun taux de retard par seuil ni variable causale n’est ajouté.

## Sorties et reproductibilité

Depuis la racine du dépôt :

```powershell
uv run python -c "from projet_kit_data.graph.analysis import run_research_data_preparation_pipeline; result = run_research_data_preparation_pipeline()"
```

Les sorties sont `data/processed/research_dataset.parquet`, `data/processed/research_dataset_metadata.json` et `data/reports/graph/research_data_quality_report.md`. La table conserve les colonnes sources et ajoute `edge_betweenness`, les métriques mensuelles des extrémités, `flag_primary_arrival_delay_below_minus_15`, `cancellation_rate`, `cancellation_rate_valid` et `cancellation_rate_invalid_reason`. Les types Polars exacts figurent dans les métadonnées et le rapport. Les chemins sont configurables par l’interface publique.

Les métadonnées consignent granularité, effectifs, couverture mensuelle et par service, sources, clés et contrôles des jointures, métriques manquantes, validité des annulations, motifs d’invalidité, anomalies de retard, schéma et réserves. Le rapport qualité présente les mêmes résultats. Conserver les entrées de construction et de métriques de la phase 1 immuables pour reproduire les données dérivées.

## Limites

Les observations décrivent des relations origine-destination mensuelles, pas des trajets individuels ni des tronçons physiques. Les métriques structurelles ne prouvent ni mouvements réels ni propagation des retards. Les retards moyens négatifs sont conservés et signalés, sans correction automatique. Les taux d’annulation avec dénominateur non positif ou comptages incohérents sont indisponibles, pas nuls au sens numérique. Le dénominateur du taux d’arrivée tardive reste à établir ; ce taux est donc absent.
