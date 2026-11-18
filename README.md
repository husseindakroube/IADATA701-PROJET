# TGVision — SNCF TGV

Application Streamlit du projet IADATA701. L'interface TGVision intègre les analyses
et fichiers de résultats du projet complémentaire de l'équipe.

Six pages : accueil, qualité, liaisons/réseau, profils/clusters, prédictions,
conclusions. Les filtres descriptifs sont communs ; graphes, clusters et tests ML
conservent leur propre périmètre explicite. Aucun notebook ni entraînement ne
s'exécute au démarrage.

## Installation et lancement

Python 3.12 ou supérieur, avec `uv` :

```powershell
uv sync --locked --dev
uv run --locked streamlit run app/app.py
```

Les chemins des ressources sont résolus par rapport au projet. Le démarrage depuis
un autre dossier est possible en indiquant le chemin absolu de `app/app.py`.

Les données et résultats importés sont déjà inclus. Ne pas régénérer les fichiers
pour simplement consulter le site. Les fichiers bruts restent inchangés.

## Organisation

```text
app/                       Interface Streamlit, pages, styles, composants
images/                    Identité visuelle TGVision existante
image/                     Illustration du projet complémentaire
src/projet_kit_data/
  ingestion/               Acquisition des sources
  etl/                     Audit, types et flags non destructifs
  eda/                     Analyses exploratoires
  graph/                   Construction, centralités, rapports et figures
  ml/                      Préparation, historique, modèles et évaluation
  web_data.py              Lecture/validation pour le site
data/
  raw/                     Sources immuables
  processed/               ETL, graphe, clustering et résultats de test ML
  reports/                 Audits et rapports ; figures extraites du notebook 04
notebooks/                 Travaux d'exploration et expériences de l'équipe
scripts/
  exploration/             Scripts d'analyse existants
  experiments/             Scripts ML existants
models/                    Modèle enregistré (non chargé par l'application)
docs/                      Documentation et bilan d'intégration
tests/                     Tests importés et tests d'intégration de l'application
logs/                      Journal local de l'application
```

## Sources et génération des résultats

Les scripts et notebooks importés restent disponibles pour étudier la génération
originale ; ils ne constituent pas encore une chaîne unique entièrement harmonisée.
Leurs paramètres et chemins de lancement sont documentés dans leurs sources.
Les notebooks sont téléchargeables depuis la page Conclusions.

`docs/integration_manifest.json` conserve les chemins et empreintes SHA-256 des
102 fichiers importés. `data/reports/clustering/elbow.png`, `pca.png` et `pca.txt`
sont extraits des sorties enregistrées du notebook 04, sans exécuter celui-ci.

Le site expose les résultats compatibles. Il ne publie pas un taux global d'arrivée
non validé et ne transforme pas les expériences historiques en conclusions vérifiées.
Voir [le bilan complet et les manques](docs/INTEGRATION_GAPS.md).

## Vérifications

```powershell
uv run --locked pytest -q
uv run --locked ruff check app src --select E9,F63,F7,F82
uv run --locked python -m compileall -q app src
```

Les tests d'intégration vérifient le chargement des six pages, les filtres, les clés
métier et la correspondance des métriques avec les mêmes observations de test.
La CI existante contrôle la syntaxe et les erreurs critiques ; son exécution de
pytest reste à ajouter. Une couverture supérieure à 90 % n'est pas certifiée.

## Documentation et déploiement

Les documents Markdown importés sont dans `docs/` et `data/reports/`. Le projet ne
fournit pas encore de construction Sphinx complète ni de lien d'application publique.
Ces éléments restent à réaliser conformément au cahier des charges ; ils n'ont pas
été inventés lors de l'intégration.

## Équipe et dépôt

Projet collectif IADATA701 : interface TGVision et analyses de l'équipe.
Les noms et rôles détaillés restent à renseigner.
[Dépôt du projet](https://github.com/husseindakroube/IADATA701-PROJET)
