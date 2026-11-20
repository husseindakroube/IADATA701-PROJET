# TGVision — paquet d intégration complet

Refonte des 6 pages de l app Streamlit TGVision pour rendre l interface
plus analytique, plus professionnelle, et prête pour la soutenance. Toutes
les tournures défensives ont été retirées, les graphiques basiques sont
passés en plotly interactif, et une carte géographique interactive a été
ajoutée.

## Contenu du paquet

### Nouveau fichier utilitaire
| Fichier | Rôle |
|---|---|
| `app/utils/carte.py` | Module helper pour la carte interactive folium, le graphe ego-radial du réseau, et les fonctions partagées (couleurs, libellés, formatage) |

### Pages refondues
| Fichier | Changements principaux |
|---|---|
| `app/pages/main.py` | Suppression des filtres d accueil et avertissements défensifs. Bandeau de 5 métriques, section "Trois résultats clés", 5 cartes de navigation réordonnées |
| `app/pages/data_quality.py` | Métriques globales fixes, bar charts plotly pour flags et valeurs manquantes, pipeline ETL en 4 étapes |
| `app/pages/routes_network.py` | 4 onglets : Carte interactive (nouvelle), Explorer une liaison (polish plotly), Comparer deux liaisons (nouveau), Comprendre le réseau (ego-graphe interactif) |
| `app/pages/clusters.py` | Bandeau 4 clusters, grouped bar chart des causes, PCA interactive, courbe du coude interactive |
| `app/pages/predictions.py` | 2 bar charts MAE/R², bloc "Modèle A retenu", erreurs par cluster, exploration plotly, conclusion scientifique |
| `app/pages/conclusions.py` | Réponse à la problématique en 2 blocs couleur, 4 cartes de résultats par pilier, perspectives, reproductibilité structurée |

### Nouvelles données
| Fichier | Rôle |
|---|---|
| `data/processed/liaisons_detail.csv` | Agrégat par liaison : durée, taux observé, taux prédit par modèle A, cluster, coordonnées GPS |
| `data/raw/coordonnees_gares.csv` | Coordonnées GPS des 59 gares du projet |

### Scripts de reproductibilité
| Fichier | Rôle |
|---|---|
| `scripts/exploration/generer_coordonnees_gares.py` | Régénère le CSV des coordonnées |
| `scripts/exploration/generer_liaisons_detail.py` | Régénère l agrégat par liaison depuis sncf.parquet, clusters, prédictions |

## Marche à suivre pour ShiHao

Depuis la racine du dépôt, sur sa branche `Test_Shihao` :

```bash
# Extraire le paquet au bon endroit
tar xzf tgvision_refonte.tar.gz

# Installer les 3 nouvelles dépendances
uv add folium streamlit-folium networkx

# Synchroniser
uv sync

# Lancer l app
uv run streamlit run app/app.py
```

## Compatibilité

L intégration préserve intégralement l architecture existante :
- Le design CSS de l app (barre de navigation personnalisée, styles, footer)
- Le module `utils/data.py` avec `observations`, `filters`, `table`, `report`
- Le module `utils/activity.py` pour le logging des actions utilisateur
- L entrée `app/app.py` et son système de navigation
- Le module `projet_kit_data.web_data` et ses constantes

Aucun changement sur `app/app.py`, `app/utils/styles.py`, `app/utils/footer.py`,
`app/utils/activity.py`, `app/utils/data.py`.

## Vérifications visuelles à faire

1. **Accueil** : les 5 métriques affichent 12 907, 59, etc.
2. **Qualité** : 4 flags en bar chart, puis valeurs manquantes en bar chart orange
3. **Liaisons et réseau** : les 4 onglets sont bien là, la carte interactive affiche les 130 lignes colorées par cluster
4. **Profils et clusters** : bandeau 4 clusters, PCA avec 4 couleurs distinctes
5. **Prédictions** : les deux bar charts côte à côte, puis le gros bloc rouge "Modèle A retenu"
6. **Conclusions** : les deux blocs verts/rouges de la problématique, les 4 cartes par pilier
