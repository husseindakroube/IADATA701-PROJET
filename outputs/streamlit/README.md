# RailInsight — Guide des livrables pour l'intégration Streamlit

Ce document décrit **les données et visualisations produites par le module « Analyse de graphe et ML enrichi par le graphe »**.

## 1. À retenir

- Les **six CSV** de `outputs/streamlit/` sont destinés à alimenter les tableaux, filtres et graphiques Streamlit.
- Les **PNG** de `outputs/reporting/` sont des exemples de visualisations statiques prêtes à être affichées ; ils peuvent aussi servir de référence pour recréer les graphiques dans Streamlit.
- `interactive_network_dashboard.html` est un **explorateur géographique autonome** : mois, gare et liaison se choisissent **dans les menus du panneau latéral**, qui affiche leurs caractéristiques. Il n'est **pas nécessaire ni prévu de cliquer directement sur les objets de la carte** pour sélectionner une gare ou une liaison. La carte reste zoomable et déplaçable.
- Le HTML et les PNG sont des **livrables générés**, pas des entrées obligatoires du pipeline.
- **Aucun PDF n'est nécessaire** : les descriptions ci-dessous servent à l'intégration des images et de leurs messages clés.

## 2. Fichiers nécessaires et ordre de génération

Exécuter les commandes **depuis la racine du dépôt** (`IADATA701-PROJET/`). Environnement : Python 3.12 et `uv`.

| Fichier | Rôle | Obligatoire pour |
| --- | --- | --- |
| `pyproject.toml` et `uv.lock` (si présent) | Dépendances Python | `uv sync` et scripts |
| `data/raw/regularite-mensuelle-tgv-aqst.csv` | Source mensuelle AQST (`;`) | Graphes, modèles, exports et dashboard |
| `data/reference/liste-des-gares.csv` | **Référentiel SNCF source**, avec `LIBELLE`, `X_WGS84`, `Y_WGS84` | **Génération des coordonnées** uniquement |
| `scripts/reporting/prepare_station_coordinates.py` | Rapproche les noms RailInsight / SNCF et complète les destinations étrangères | Génération des coordonnées |
| `data/reference/station_coordinates.csv` | **Fichier généré**, une ligne par destination, `station`, `lat`, `lon`, etc. | **Génération du dashboard cartographique** |
| `scripts/reporting/interactive_network_dashboard.py` | Construit le dashboard mensuel à partir des données AQST et des coordonnées | Génération du HTML |
| `scripts/reporting/generate_streamlit_assets.py` | Produit les visuels PNG de reporting | Génération des images |
| `scripts/experiments/analyze_predictions.py` | Produit l'analyse et les CSV de prédiction / erreurs | Génération des exports de résultats ML |
| `scripts/exploration/export_network.py` | Exporte les caractéristiques de gares et de liaisons | Génération des CSV de réseau |

**Attention :** le seul CSV source supplémentaire nécessaire à la géolocalisation est `liste-des-gares.csv`. Il doit être conservé dans `data/reference/` avec le CSV AQST dans `data/raw/`. Si `station_coordinates.csv` existe déjà, **l'ouverture d'un dashboard HTML déjà généré** ne nécessite pas de relire `liste-des-gares.csv`. Mais pour **reconstruire tout le pipeline depuis les sources**, il faut bien le référentiel SNCF.

L'étape de préparation des coordonnées est **reproductible et hors ligne** : les correspondances de noms et les coordonnées étrangères figurent dans le script Python (pas d'API de géocodage). Quelques libellés agrégés, tels que `ITALIE`, utilisent une **gare représentative** ; consulter les colonnes `reference_station`, `precision` et `source` du CSV pour ne pas les interpréter comme une gare observée précisément.

### Installation

```bash
uv sync
```

### Générer les coordonnées et le dashboard

```bash
uv run python scripts/reporting/prepare_station_coordinates.py
uv run python scripts/reporting/interactive_network_dashboard.py
```

Le premier script produit `data/reference/station_coordinates.csv` ; le second produit `outputs/reporting/interactive_network_dashboard.html`.

### Générer les exports et les images

```bash
uv run python scripts/exploration/export_network.py
uv run python scripts/experiments/analyze_predictions.py
uv run python scripts/reporting/generate_streamlit_assets.py
```

**Prérequis logique :** les scripts d'analyse prédictive dépendent de la préparation/évaluation des modèles et de leurs sorties. Pour repartir entièrement des données sources, exécuter également les expériences décrites dans le README principal (`compare_models.py`, `tune_models.py`, `evaluate_models.py`) avant d'analyser les prédictions. Vérifier les messages affichés par chaque script et les fichiers effectivement créés.

Pour contrôler les fichiers sur une machine :

```bash
find outputs/streamlit -maxdepth 1 -type f -name '*.csv' -print | sort
find outputs/reporting -maxdepth 1 -type f \( -name '*.png' -o -name '*.html' \) -print | sort
```

## 3. Les six CSV disponibles pour Streamlit

Les fichiers présents dans `outputs/streamlit/` sont une **copie de mise à disposition** de résultats calculés dans le projet. Les données mensuelles de réseau ne sont pas interchangeables avec les caractéristiques historiques utilisées pour entraîner les modèles.

| CSV | Granularité | Contenu / intégration suggérée |
| --- | --- | --- |
| `network_nodes.csv` | Gare, pour **2024** (57 gares) | Centralités : degré entrant/sortant, betweenness, PageRank, trafic entrant/sortant et PageRank pondéré. Tableau des gares / classement / fiche gare. |
| `network_edges.csv` | Liaison **orientée**, pour **2024** (121 liaisons) | `edge_volume`, `edge_traffic_share`, `edge_reverse_volume`. Classement des liaisons et détails directionnels. |
| `predictions.csv` | Observation du **test 2025–sept. 2026** (2 583 lignes) | Date, service, départ, arrivée, trains circulés, réel, prédictions des deux modèles, erreurs. Comparaison détaillée, filtrage par trajet et par mois. |
| `monthly_errors.csv` | Mois de test (21 mois) | Comparaison des erreurs des deux modèles dans le temps. Courbe mensuelle. |
| `route_errors.csv` | Liaison orientée du test (121 liaisons) | Comparaison des MAE par liaison ; classement des gains et pertes. |
| `delay_level_errors.csv` | Classe de taux de retard réel | Erreurs et biais selon la gravité des retards ; analyse des cas difficiles. |

**Attention :** `network_nodes.csv` et `network_edges.csv` décrivent un **réseau agrégé sur 2024**. Le dashboard HTML construit, lui, **un réseau propre à chaque mois** ; ses centralités mensuelles peuvent donc différer. Les modèles ML exploitent encore un autre contexte : les caractéristiques calculées sur les **12 mois précédant la date prédite** afin d'éviter la fuite temporelle.

### Sémantique des indicateurs

- `edge_volume` : **nombre de trains ayant circulé**, pas nombre de voyageurs.
- `edge_traffic_share` : part du trafic sortant de la gare de départ correspondant à la liaison sélectionnée.
- `edge_reverse_volume` : volume de la liaison inverse ; **A → B** et **B → A** sont distinctes.
- `historical_delay_rate_15` : taux de retard historique calculé sur les circulations de la fenêtre antérieure, et non moyenne simple des taux mensuels.
- `actual`, `pred_historical`, `pred_graph` : taux, par exemple `0.05` = **5 %**, à multiplier par 100 pour l'affichage en pourcentage.
- `error_*` : vérifier le sens défini dans le script d'export avant d'annoter un graphique (erreur signée ou absolue).
- Les observations ayant une cible invalide ont été exclues de l'évaluation.

## 4. Les graphiques PNG : à quoi ils servent et comment les intégrer

Le script `scripts/reporting/generate_streamlit_assets.py` génère **quatre visuels statiques** dans `outputs/reporting/`. Les noms exacts des fichiers doivent être lus dans ce dossier ou dans le script, plutôt que d'être renommés arbitrairement :

```bash
find outputs/reporting -maxdepth 1 -name '*.png' -printf '%f\n' | sort
```

### Descriptions pour l'application

1. **Performance mensuelle des modèles** : comparaison de la MAE du modèle « historique » et du modèle « historique + liaison » sur les mois du test. **Message :** l'apport des variables de liaison s'apprécie mois par mois et non seulement à travers une métrique globale ; le modèle enrichi fait mieux sur **18 des 21 mois** du test.
2. **Performance par liaison** : comparaison des MAE par trajet orienté, permettant de distinguer les trajets où les variables du graphe aident de ceux où elles pénalisent les prédictions. **Message :** l'amélioration n'est pas uniforme ; elle concerne **106 des 121 liaisons** du test, mais certains trajets restent difficiles.
3. **Erreurs selon le niveau de retard** : performance ou biais des prévisions selon les classes de taux de retard observé. **Message :** les épisodes de retards élevés sont plus difficiles à anticiper ; éviter de ne présenter que l'erreur moyenne globale.
4. **Vue complémentaire du diagnostic prédictif** : se référer au titre et à la légende du **quatrième PNG réellement généré** pour l'identifier précisément (par exemple prédictions/réalisations ou distribution des erreurs). **Message :** contextualiser la performance et les limites, sans déduire du graphique un phénomène qu'il ne montre pas.

> **Point à vérifier avant publication :** les quatre descriptions ci-dessus sont des rôles éditoriaux. Associer chaque texte au PNG correspondant après avoir vérifié son **titre, ses axes et sa légende**. Le nom et le contenu du quatrième PNG n'ont pas été établis ici ; ne pas lui attribuer une interprétation non vérifiée.

### Proposition de présentation Streamlit

- Une section **« Résultats des prédictions »** avec les deux premiers PNG et une courte légende sous chaque figure.
- Une section **« Où le modèle se trompe-t-il ? »** avec les autres diagnostics, et éventuellement des filtres alimentés par `predictions.csv`, `route_errors.csv` et `delay_level_errors.csv`.
- Un résumé de l'évaluation finale dans un encadré de métriques : **MAE 0,040603 → 0,039209** (amélioration relative **≈ 3,43 %**), RMSE **0,064661 → 0,062477**, MAE pondérée **0,034638 → 0,033309**. Période de test : **2025–septembre 2026**.

Pour afficher un PNG sans coder un nouveau graphique :

```python
import streamlit as st

st.image("outputs/reporting/NOM_REEL_DU_GRAPHIQUE.png", use_container_width=True)
st.caption("Interprétation vérifiée à partir des axes et de la légende du graphique.")
```

Pour un affichage recalculable ou filtrable par l'utilisateur, préférer un graphique Streamlit / Plotly construit à partir des **CSV** plutôt que tenter de filtrer un PNG.

## 5. Explorateur cartographique interactif

### Ce qu'il permet

- Choisir **un mois** : la carte et ses indicateurs sont recalculés pour ce mois.
- Choisir **une gare dans le menu latéral** : ses liaisons sont mises en évidence et sa fiche présente ses caractéristiques.
- Choisir **une liaison orientée dans le menu latéral** : le sens de circulation, le nombre de trains circulés, la part du trafic sortant et le trafic inverse sont détaillés.
- **Zoomer avec la molette** et se déplacer sur la carte.
- Réinitialiser les filtres via le bouton prévu.

Les couleurs et tailles représentent des indicateurs de **réseau**, non des flux de passagers ; le nombre de trains correspond au nombre de **circulations**. Les centralités affichées sont calculées **pour le mois sélectionné**, indépendamment des variables historiques du modèle ML.

### Génération

```bash
uv run python scripts/reporting/prepare_station_coordinates.py
uv run python scripts/reporting/interactive_network_dashboard.py
```

### Ouverture : impérativement par HTTP local

```bash
uv run python -m http.server 8000
```

Puis ouvrir :

`http://localhost:8000/outputs/reporting/interactive_network_dashboard.html`

**Ne pas ouvrir le HTML directement en `file://`.** Sur l'environnement de développement, cette méthode produisait une carte blanche : le chargement en **HTTP local a été testé et fonctionne**. Le terminal qui héberge le serveur doit rester ouvert pendant la consultation. Les tuiles de fond de carte peuvent exiger un accès réseau.

### Intégration dans Streamlit

Le HTML est un **prototype de visualisation complet et autonome**. L'intégrateur peut soit l'afficher dans un composant HTML adapté, soit reconstruire une carte directement dans Streamlit ; la compatibilité des interactions doit être testée dans le navigateur et l'environnement de déploiement. Le serveur `http.server` est destiné à la **consultation locale**, pas à l'hébergement de production.

L'intérêt de conserver les scripts est de pouvoir régénérer les données mensuelles, sans saisir de coordonnées ni dessiner les liaisons à la main.

## 6. Bonnes pratiques d'intégration

1. Toujours préciser la **période** présentée (réseau 2024, réseau d'un mois, test ML 2025–2026).
2. Différencier **liaison orientée**, **gare** et **service** ; ne pas confondre nombre de trains et flux de voyageurs.
3. Afficher les taux de retard en **%** et la MAE dans une unité cohérente : une MAE de `0.039209` sur un taux correspond à **3,92 points de pourcentage**, et non à 0,039 %.
4. Ne pas présenter le gain moyen comme systématique : certaines liaisons ou périodes se dégradent.
5. Mentionner la convention des destinations agrégées / représentatives (`ITALIE`, etc.) dans la carte.
6. Éviter de déduire des causalités des scores de centralité ou des améliorations prédictives.

## 7. Vérifications avant livraison

```bash
uv run pytest tests/ -v
uv run ruff check src/ scripts/ tests/
```

Vérifier également la présence du CSV SNCF, la régénération des coordonnées, la génération du dashboard, ses menus déroulants, l'ouverture via `localhost`, les six CSV attendus et les quatre PNG réellement exportés.

**Périmètre :** ce guide documente la contribution graphe / ML et fournit les ressources à réutiliser dans Streamlit.