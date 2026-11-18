# TGVision — Analyse de la ponctualité des TGV

Ce projet est réalisé dans le cadre du module IADATA701.

Développée avec Streamlit, l’application web TGVision vise à étudier la ponctualité des TGV à partir de données mensuelles de régularité. Les résultats ont vocation à être présentés de manière interactive.

> **État du projet : développement en cours.**
> L’interface et la navigation sont déjà en place. Le traitement des données et les pages consacrées aux analyses restent à développer.

## Fonctionnalités et état d’avancement

### Éléments en place

- Une page d’accueil consacrée à la présentation du projet.
- Une organisation en plusieurs pages, avec une navigation personnalisée.
- Une identité visuelle définie dans les fichiers CSS.
- Des contenus visuels : images et animation.
- Un fichier CSV contenant les données de régularité mensuelle des TGV.
- Un workflow GitHub Actions assurant les vérifications de base du code Python.

### Étapes à venir

- Définir plus précisément la problématique et les axes d’analyse.
- Procéder à l’exploration et au nettoyage des données.
- Construire les indicateurs et les visualisations.
- Finaliser les pages qui sont encore provisoires.
- Mettre en place des tests pour le chargement des pages et le traitement des données.
- Préparer la mise en ligne de l’application.

## Technologies utilisées

| Outil | Utilisation |
|---|---|
| Python 3.12 | Développement de l’application |
| Streamlit | Interface web et navigation |
| HTML / CSS | Personnalisation de l’interface |
| uv | Gestion de l’environnement et des dépendances |
| Ruff | Analyse statique du code Python |
| GitHub Actions | Intégration continue |

Les dépendances de développement comprennent aussi `pytest` et `pytest-cov`, prévus pour les futurs tests automatisés.

## Structure du projet

```text
IADATA701-PROJET/
├── .github/
│   └── workflows/
│       └── ci.yml              # Workflow d’intégration continue
├── .streamlit/
│   └── config.toml             # Configuration Streamlit
├── app/
│   ├── app.py                  # Point d’entrée de l’application
│   ├── pages/                  # Accueil et pages de l’application
│   ├── styles/                 # Feuilles de style CSS
│   └── utils/
│       └── styles.py           # Chargement des styles
├── data/
│   └── initial/                # Données initiales au format CSV
├── images/                     # Logos, icônes et animations
├── src/
│   └── projet_kit_data/        # Package Python du projet
├── tests/                      # Emplacement prévu pour les tests
├── .python-version             # Version Python utilisée
├── pyproject.toml              # Configuration et dépendances
├── uv.lock                     # Versions verrouillées des dépendances
└── README.md
```

## Installation et lancement

### Prérequis

- Git
- uv
- Python 3.12, installable avec uv

### 1. Cloner le dépôt

```bash
git clone https://github.com/husseindakroube/IADATA701-PROJET.git
cd IADATA701-PROJET
```

### 2. Installer Python et les dépendances

Exécuter les commandes suivantes à la racine du projet :

```bash
uv python install
uv sync --locked --dev
```

Le fichier `.python-version` indique la version de Python à utiliser. Quant au fichier `uv.lock`, il fixe les versions des dépendances installées.

### 3. Démarrer l’application

```bash
uv run python -m streamlit run app/app.py
```

Une fois lancée, l’application est accessible à cette adresse :

http://localhost:8501

Pour arrêter le serveur, appuyer sur `Ctrl + C` dans le terminal.

### Sous Windows

Si une politique de sécurité empêche l’exécution directe de `streamlit.exe`, utiliser la commande ci-dessus, qui passe par `python -m streamlit`.

## Données

Les données initiales sont stockées dans le fichier suivant :

```text
data/initial/regularite-mensuelle-tgv-aqst.csv
```

Ce fichier servira de base aux analyses de régularité des TGV.

La documentation associée doit encore préciser les points suivants :

- La source des données et leur lien de téléchargement.
- La date de récupération et la période couverte.
- La description des colonnes.
- La licence et les conditions de réutilisation.
- Les règles de nettoyage et le traitement des valeurs manquantes.

À ce stade, ni les traitements ni les résultats d’analyse ne sont intégrés à l’application.

## Intégration continue — CI

Le fichier `.github/workflows/ci.yml` définit le workflow d’intégration continue.

Son exécution est prévue dans les cas suivants :

- Un push est effectué sur `Test_Shihao` ou `main`.
- Une pull request vers `main` est ouverte ou mise à jour.
- Un lancement manuel est demandé via `workflow_dispatch`, à condition que le workflow soit disponible sur la branche par défaut.

### Vérifications réalisées

Le workflow suit ces étapes :

1. Récupérer le code du dépôt.
2. Installer uv et Python.
3. Installer les dépendances à l’aide de `uv sync --locked --dev`.
4. Rechercher certaines erreurs Python avec Ruff.
5. Vérifier la syntaxe des fichiers Python.

Les vérifications du code peuvent aussi être exécutées localement :

```bash
uv run --locked ruff check app src --select E9,F63,F7,F82
uv run --locked python -m compileall -q app src
```

Ces contrôles ne lancent pas l’application et ne permettent pas encore de valider le comportement des pages. Le workflow n’exécute actuellement aucun test pytest.

## Déploiement

Le workflow actuel ne prévoit pas de déploiement automatique.

Les instructions précédentes permettent de lancer l’application en local. La procédure de déploiement et l’adresse de la version en ligne seront documentées dès qu’elles seront disponibles.

## Travail en équipe

L’organisation proposée repose sur les étapes suivantes :

1. Effectuer le développement sur une branche dédiée.
2. Vérifier les changements en local.
3. Pousser la branche sur GitHub.
4. Créer une pull request vers `main`.
5. Examiner les résultats de la CI et faire relire les modifications avant de les fusionner.
