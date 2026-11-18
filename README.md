# TGVision — Comprendre la régularité des TGV

TGVision est une application Streamlit réalisée dans le cadre du projet **IADATA701**.
Elle permet d'explorer la ponctualité des liaisons TGV, les causes de retard,
la structure du réseau et les résultats de modèles de prédiction.

**Problématique :** dans quelle mesure la structure du réseau TGV est-elle associée
à la régularité des liaisons, et peut-on exploiter cette structure pour améliorer
la prédiction des retards ?

**État de livraison :** l'application fonctionne localement et dispose de tests,
d'une documentation Sphinx et d'un workflow CI. La mise en ligne sur Streamlit
Community Cloud reste à effectuer ; l'URL publique sera ajoutée ici après validation.

## Découvrir l'application

| Page | Fonctionnalités |
|---|---|
| **Accueil** | Présentation de la problématique, chiffres clés et parcours d'exploration. |
| **Qualité des données** | Signalements d'anomalies, valeurs manquantes, unicité des observations et étapes ETL. |
| **Liaisons et réseau** | Carte interactive, filtres, détail d'une liaison, comparaison de deux trajets, séries mensuelles et centralités. |
| **Profils et clusters** | Quatre profils de liaisons, comparaison des causes, projection PCA, courbe du coude et composition des groupes. |
| **Prédictions** | Comparaison des modèles, MAE/RMSE/R², erreurs par cluster et exploration par liaison et modèle. |
| **Conclusions** | Synthèse des résultats, réponse à la problématique et limites de l'étude. |

Sur la carte, les couleurs représentent le cluster ou le taux de retard selon le
mode choisi. Sur le graphe d'une gare, les couleurs des points identifient les gares :
les noms figurent dans la légende. Les flèches rouges représentent les départs de
la gare centrale et les bleues les arrivées, avec des courbes séparées pour les
liaisons aller-retour.

## Démarrer en local

Prérequis : **Git**, **uv** et **Python 3.12**. La version de développement est fixée
dans `.python-version` ; les dépendances sont déclarées dans `pyproject.toml`
et verrouillées dans `uv.lock`.

```bash
git clone https://github.com/husseindakroube/IADATA701-PROJET.git
cd IADATA701-PROJET
uv sync --locked --dev
uv run --locked streamlit run app/app.py
```

Ouvrir l'adresse locale affichée par Streamlit, généralement `http://localhost:8501`.
Pour un dépôt déjà cloné, exécuter les deux dernières commandes depuis sa racine.
Les ressources sont résolues par rapport au projet, et non au dossier de lancement.

Les données et résultats nécessaires sont inclus dans le dépôt. Aucun notebook
n'est exécuté pour démarrer l'application. Les prédictions sont lues depuis les
exports enregistrés ; la page clusters recalcule la PCA et les ajustements K-Means
utilisés pour la courbe du coude.

## Données et méthode

Le projet exploite le jeu public SNCF **Régularité mensuelle TGV AQST**. Les analyses
portent sur des observations mensuelles par service, gare de départ et gare d'arrivée.

Les fichiers présents dans le dépôt couvrent les périmètres suivants :

| Produit | Périmètre |
|---|---|
| Observations traitées (`sncf.parquet`) | 12 907 observations, de janvier 2018 à septembre 2026 ; 59 gares et 146 combinaisons distinctes service/départ/arrivée. |
| Agrégat de la carte (`liaisons_detail.csv`) | 130 liaisons orientées avec statistiques, clusters, coordonnées et prédictions agrégées. |
| Clustering (`clusters_liaisons.csv`) | 65 paires de gares non orientées, réparties en quatre groupes. |
| Comparaison des modèles | 1 857 observations communes de test, de juillet 2025 à septembre 2026. |

Ces périmètres sont différents : les 130 lignes de la carte ne représentent pas
la totalité des combinaisons du fichier d'observations. Les filtres descriptifs,
les graphes, le clustering et les évaluations ML doivent être interprétés dans
leur périmètre respectif.

Le travail suit quatre étapes :

1. **Préparation et qualité** : contrôle du schéma, des clés et des comptages ;
   ajout de flags pour rendre les anomalies visibles sans les corriger silencieusement.
2. **Analyse du réseau** : construction de graphes orientés et calcul des degrés,
   de l'intermédiarité, de la proximité et du PageRank.
3. **Clustering** : regroupement des paires de gares selon leurs caractéristiques,
   avec standardisation, K-Means et visualisation des profils.
4. **Prédiction** : comparaison d'un naïf historique et de quatre variantes :
   A (baseline), B (+ graphe), C (+ cluster) et D (+ graphe et cluster).

Les exports montrent des écarts faibles entre A/B/C/D. Le modèle A est retenu
dans l'application pour sa simplicité ; il n'est pas le meilleur selon toutes
les métriques. Le naïf historique obtient notamment un meilleur R² sur ce test.
Les observations mensuelles et les associations de réseau ne permettent pas de
conclure à une propagation causale des retards entre gares.

Les notebooks `01` à `05` conservent les étapes d'exploration, de clustering et de
comparaison. Les scripts associés sont disponibles dans `scripts/`. Ils ne forment
pas encore une commande unique de régénération complète : consulter leurs paramètres
et chemins avant exécution. Le manifeste d'import initial est conservé dans
[docs/integration_manifest.json](docs/integration_manifest.json).

## Organisation du dépôt

```text
app/                       Entrée Streamlit, six pages, composants et CSS
src/projet_kit_data/        Code métier : ingestion, ETL, EDA, graphes et ML
data/raw/                  Données sources et coordonnées des gares
data/processed/            Tables traitées, graphes, clusters et prédictions
data/reports/              Audits, rapports d'analyse et figures
notebooks/                 Notebooks d'analyse 01 à 05
scripts/exploration/       Analyses et génération des données de la carte
scripts/experiments/       Comparaison, évaluation et réglage des modèles
scripts/deployment/        Outils de vérification, exemples de logs et anciens outils SSH
tests/                     Tests unitaires et tests d'intégration Streamlit
docs/                      Sources Sphinx et documentation technique
logs/examples/             Journaux simulés livrés avec le projet
images/                    Ressources visuelles de l'application
models/                    Modèles enregistrés, non chargés par l'interface
.github/workflows/ci.yml    Contrôles automatisés GitHub Actions
```

La stack principale repose sur Streamlit, Pandas/Polars, Plotly, Folium,
NetworkX et scikit-learn. Les versions exactes sont disponibles dans `uv.lock`.

## Qualité du code et tests

Depuis la racine du projet :

```bash
uv run --locked ruff check app src scripts tests docs/conf.py
uv run --locked ruff format --check app src scripts tests docs/conf.py
uv run --locked python -m compileall -q app src scripts
uv run --locked pytest -q --cov=src/projet_kit_data --cov=app --cov-fail-under=90.1 --cov-report=term-missing --cov-report=html:reports/coverage
```

**Dernière validation complète locale, le 18 novembre 2026 : 172 tests réussis,
91,95 % de couverture sur `app/` et `src/projet_kit_data/`.** Ce relevé ne remplace
pas le résultat du dernier run GitHub Actions.

Les tests couvrent notamment les règles de préparation, les calculs de graphes,
les métriques ML, le chargement des six pages, les interactions de la carte,
les courbes directionnelles et le fonctionnement des logs.

Ruff vérifie le style (`E`, `W`), les erreurs (`F`) et la présence des docstrings
publiques (`D1`). Le formatage est contrôlé séparément. Les textes et URL longs
sont exemptés de `E501` ; les tests sont exemptés de `D1`.

## Documentation Sphinx

La documentation comprend un guide d'installation et d'utilisation, l'architecture,
la journalisation et une référence API générée depuis les docstrings.

```bash
uv run --locked sphinx-build -W --keep-going -b html docs docs/_build/html
```

Ouvrir ensuite `docs/_build/html/index.html`. Les fichiers HTML sont générés
localement et ignorés par Git ; leurs sources sont dans `docs/`. La CI construit
la documentation avec les avertissements traités comme des erreurs et conserve
le résultat dans l'artefact **`sphinx-html-<commit>`**.

## Journalisation

Le module standard `logging` écrit automatiquement deux fichiers UTF-8 :

| Fichier | Contenu |
|---|---|
| `logs/debug.log` | DEBUG et niveaux supérieurs : initialisation, lectures de données, sélections, filtres et demandes de téléchargement. |
| `logs/error.log` | ERROR et CRITICAL, avec les traces des exceptions journalisées. |

Chaque fichier est limité à **5 Mio**, avec **trois sauvegardes**. Les événements
d'erreur figurent aussi dans `debug.log`. Les actions utilisent un identifiant
de session aléatoire et des détails JSON ; ce logger n'ajoute ni nom, ni email,
ni adresse IP. Les sélections inchangées sont dédupliquées lors des reruns,
tandis que chaque demande de téléchargement est enregistrée.

Les journaux réels restent locaux. Les [exemples livrés](logs/examples/README.md)
sont générés avec le même logger à partir d'actions et d'incidents **simulés**.
Pour les reproduire dans un dossier neuf :

```bash
uv run --locked python scripts/deployment/generate_log_examples.py reports/log-examples
```

Le générateur refuse d'écraser des fichiers existants. Les avertissements internes
de Streamlit restent dans la console et ne sont pas automatiquement copiés dans
`error.log`. Les sélections enregistrées décrivent les contrôles calculés, y compris
dans les onglets masqués ; elles ne constituent pas une mesure de fréquentation.
Le dossier de logs doit être accessible en écriture. Sur un hébergement distant,
les fichiers locaux ne constituent pas une archive durable.

## CI et mise en ligne

Le workflow [CI](.github/workflows/ci.yml) s'exécute à chaque push, lors des Pull
Requests vers `main` et sur lancement manuel. Il installe l'environnement verrouillé,
vérifie le style, le formatage, les docstrings et la syntaxe, construit Sphinx,
génère les logs d'exemple et exécute les tests avec un seuil de couverture de **90,1 %**.
Les rapports et la documentation disponibles sont conservés **14 jours**.

Le parcours de publication prévu est :

**Branche de développement → CI → Pull Request → fusion dans `main` → Streamlit Community Cloud.**

La configuration à utiliser sur Community Cloud est :

| Champ | Valeur |
|---|---|
| Repository | `husseindakroube/IADATA701-PROJET` |
| Branch | `main` |
| Main file path | `app/app.py` |
| Python version | `3.12` |

La création de l'application sur Community Cloud et la protection de `main`
sont des réglages externes au dépôt. Exiger le contrôle **Code, tests et couverture**
avant fusion : Community Cloud n'attend pas lui-même la réussite de la CI pour
actualiser l'application. Après déploiement, vérifier les six pages depuis une
fenêtre privée puis ajouter l'URL publique en tête de ce README.

La procédure détaillée et les points restant à configurer sont dans
[docs/CI_CD.md](docs/CI_CD.md). Les tâches Docker, GHCR et SSH ont été retirées
du workflow ; les fichiers correspondants restent disponibles comme alternative
manuelle. Aucun secret SSH ni variable `DEPLOY_ENABLED` n'est requis pour le
parcours Community Cloud.


