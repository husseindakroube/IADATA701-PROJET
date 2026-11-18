# Intégration et fonctionnalités restantes

Cette intégration ajoute les six pages et expose les résultats déjà présents dans le
projet de l'équipe. Elle ne crée pas de nouvelle analyse scientifique, ne réentraîne
aucun modèle et ne certifie pas les résultats historiques des notebooks.

## Correspondance des pages

| Page | Éléments intégrés | Manques ou réserves |
|---|---|---|
| Accueil | Design TGVision conservé, compteurs dynamiques, filtres communs, accès aux cinq autres pages | Taux global d'arrivée validé, taux global d'annulation, trois découvertes scientifiques validées, date d'extraction, noms/rôles de l'équipe |
| Qualité | `sncf.parquet`, quatre flags existants, manquants, observations distinctes signalées, audit original, téléchargement | Dictionnaire complet et disponibilité prédictive, vérification des mois manquants, impact comparable des exclusions |
| Liaisons et réseau | Séries mensuelles sources, annulations du research dataset, causes non agrégées, graphes sauvegardés, centralités et détails de gare | Taux d'arrivée harmonisé, comparateur, classement avec volume minimal, carte, relations centralité/ponctualité validées |
| Profils et clusters | Labels du CSV, effectifs et liste des paires, figures du coude/PCA extraites sans exécuter le notebook 04 | PCA interactive, export des profils et période/version, noms validés, sensibilité aux graines, clustering prédictif sans fuite |
| Prédictions | Métriques existantes, vérification contre les prédictions, consultation liaison/mois et courbes du test | A/B/C/D harmonisés, R², gain relatif et stabilité, erreurs par groupe avec effectifs, protocole complet de disponibilité, audit des enrichissements |
| Conclusions | Limites, périmètre réseau, sources et notebooks téléchargeables | Réponse scientifique finale démontrée sur l'association et la valeur prédictive |

## Divergences importantes

- La clé descriptive est `(date, service, gare_depart, gare_arrivee)` : elle conserve
  les directions et les services. Les 65 labels de clusters sont des **paires non
  orientées**, avec des effectifs 25, 19, 5 et 16. Les décomptes ne sont pas interchangeables.
- Le snapshot ETL contient 12 907 observations, de 2018-01 à 2026-09. Il conserve
  toutes les lignes, dont 420 déclenchent au moins une des quatre règles. Le nombre
  12 487 correspond au filtre du notebook de clustering, pas à l'effectif ETL global.
- Le contrat de données laisse le dénominateur du taux officiel d'arrivée non établi.
  La page d'exploration affiche donc les champs sources et les annulations mensuelles
  existantes, sans inventer ce taux.
- La cible ML fournie est `nb_train_retard_sup_15 / (nb_train_prevu - nb_annulation)`.
  Le champ >15 min a un périmètre d'applicabilité particulier à confirmer. Le notebook
  de clustering utilise encore un ratio sur les trains **prévus**, ainsi que des
  moyennes de causes dont le dénominateur n'est pas confirmé. Ces taux et profils ne
  sont pas présentés comme des indicateurs harmonisés.
- Les métriques JSON contiennent seulement « Naïf historique » et
  « HistGradientBoosting final » (MAE, RMSE, MAE pondérée). Les expériences de sept
  jeux de variables et de clustering restent consultables dans les notebooks/scripts,
  mais ne constituent pas des résultats A/B/C/D exportés sous un protocole commun.
- Les figures PCA/coude sont des sorties historiques sauvegardées du notebook 04.
  Elles ne sont pas recalculées. Le CSV des labels ne fournit ni empreinte des données,
  ni date de génération, ni période exacte : la correspondance doit être vérifiée.
- Les R² 0,4513 et 0,4595 du cahier des charges ne sont pas affirmés comme résultats
  vérifiés de cette intégration. Les associations ne prouvent pas une causalité.

## Structure reprise de l'équipe

`src/projet_kit_data/` contient les modules `ingestion`, `etl`, `eda`, `graph`, `ml`
et les adaptateurs historiques. `data/raw/` conserve les fichiers sources ;
`data/processed/` les tables et résultats ; `data/reports/` les audits et rapports.
`notebooks/`, `scripts/exploration/`, `scripts/experiments/`, `models/`, `docs/` et
`tests/` reprennent la structure du projet complémentaire. L'interface reste dans
`app/` et son identité visuelle dans `app/styles/` et `images/`.

Les fichiers importés sont identifiés par SHA-256 dans `docs/integration_manifest.json`.
Ils ont été copiés sans réécrire les sources ni modifier le projet complémentaire.
Le module `web_data.py` et `app/utils/data.py` constituent uniquement la couche
de chargement, de validation et d'affichage nécessaire à l'intégration.

## Livraison non encore complète

Pas de déploiement public fourni ; pas de manifeste complet par modèle (version,
variables, split, environnement) ; pas de documentation Sphinx construite ; pas de
preuve de couverture supérieure à 90 %. La CI existante contrôle syntaxe et erreurs
Python critiques mais ne lance pas pytest. Ces éléments restent à réaliser, ainsi que
la validation scientifique des points ci-dessus. Ils ne sont pas développés dans cette
intégration, conformément au périmètre demandé. La prévision future est également absente.
