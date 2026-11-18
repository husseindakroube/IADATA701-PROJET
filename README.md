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
  comparaison.py           Fonctions des expériences A/B/C/D de l’équipe
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

La mise à jour intègre les profils de clusters appris sur la période d’entraînement et
les prédictions A/B/C/D sur les mêmes 1 857 observations de test, avec erreurs par cluster.

## Sources et génération des résultats

Les scripts et notebooks importés restent disponibles pour étudier la génération
originale ; ils ne constituent pas encore une chaîne unique entièrement harmonisée.
Leurs paramètres et chemins de lancement sont documentés dans leurs sources.
Les notebooks sont téléchargeables depuis la page Conclusions.

`docs/integration_manifest.json` conserve les chemins et empreintes SHA-256 des
fichiers importés. `data/reports/clustering/elbow.png`, `pca.png` et `pca.txt`
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
La CI lance désormais la suite complète, publie les rapports et exige au moins
90,1 % de couverture sur `app/` et `src/projet_kit_data/`. Le relevé local initial
a été actualisé à 90,47 % (162 tests), le 18 novembre 2026. Les tests de déploiement sont également exécutés.

## Documentation et déploiement

Les documents Markdown importés sont dans `docs/` et `data/reports/`. Le projet ne
fournit pas encore de construction Sphinx complète ni de lien d'application publique.
Le workflow construit et vérifie une image Docker, la publie sur GHCR depuis main,
puis peut la déployer par SSH avec contrôle de santé et retour à la version précédente
en cas d’échec. Configurer les Secrets de production et `DEPLOY_ENABLED` avant activation.
Voir [la configuration CI/CD](docs/CI_CD.md) pour le serveur, le proxy et les commandes.
Le déploiement réel et la construction Sphinx restent à valider.

## Équipe et dépôt

Projet collectif IADATA701 : interface TGVision et analyses de l'équipe.
Les noms et rôles détaillés restent à renseigner.
[Dépôt du projet](https://github.com/husseindakroube/IADATA701-PROJET)

## Journalisation (logging)

L'application utilise le module standard `logging`. Les fichiers sont créés
automatiquement dans `logs/`, indépendamment du répertoire de lancement :

- `logs/debug.log` : DEBUG et niveaux supérieurs ; démarrage, chargement des
  données, navigation, filtres, sélection de liaison/gare/cluster, consultation
  d'une prédiction et clic sur le téléchargement d'un rapport.
- `logs/error.log` : uniquement ERROR et CRITICAL, avec la trace des exceptions
  (fichier illisible, schéma invalide, métriques incohérentes ou erreur de page).
  Ces événements sont également présents dans le journal debug pour le contexte.

Chaque entrée indique la date, l'heure locale du processus, le niveau, le logger
et le message. Les actions portent un identifiant de session aléatoire, sans nom,
email ni adresse IP. Les sélections initiales et leurs changements sont journalisés ;
un rerun Streamlit identique ne duplique pas l'événement. Un clic de téléchargement
est enregistré comme une demande, pas comme la preuve d'un transfert terminé.

Configuration : `src/projet_kit_data/logging_config.py`. Chaque fichier est limité
à 5 Mio avec trois sauvegardes (`.log.1` à `.log.3`), en UTF-8. La configuration
est réutilisée à chaque rerun. Les fichiers de logs et leurs sauvegardes sont
ignorés par Git. L'ancien `app.log`, s'il existe, n'est plus alimenté.

Le dossier doit être accessible en écriture. En cas d'échec, l'application affiche
un message et envoie l'erreur à la console. Dans Docker, les fichiers résident dans
`/app/logs` ; sans volume dédié, ils ne survivent pas au remplacement du conteneur.
Pour les scripts hors interface, appeler `configure_logging()` au point d'entrée
avant d'utiliser `logging.getLogger("projet_kit_data.nom_du_module")`.

Tests dédiés : `uv run --locked pytest tests/test_logging.py -q`.
