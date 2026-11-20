# Analyse des associations pour l’intégration Streamlit

Le module d’analyse des associations lit le fichier existant de la phase 2,
`data/processed/research_dataset.parquet`. Il ne relance pas les étapes de
préparation en amont et ne modifie pas les données d’entrée. Il produit trois
tables Parquet compactes, des métadonnées, des figures PNG réutilisables et une
section balisée mise à jour dans le rapport de recherche unifié en français. Le
module ne dépend pas de Streamlit.

## Exécution

```powershell
uv run python -c "from projet_kit_data.graph import run_association_analysis_pipeline; result = run_association_analysis_pipeline()"
```

## Analyse

Les corrélations de Pearson et de Spearman utilisent les observations finies
disponibles par paire. Les observations du taux d’annulation ne sont incluses
que si le flag existant `cancellation_rate_valid` est vrai. La table de
corrélations conserve les valeurs p brutes comme champs exploratoires
facultatifs ; aucune correction pour comparaisons multiples n’est appliquée et
les valeurs p ne constituent pas une preuve confirmatoire. Les observations
mensuelles d’une même liaison orientée sont répétées ; les valeurs p classiques
peuvent donc surestimer le niveau de preuve statistique.

Les variables de résultat sont le retard moyen à l’arrivée de tous les trains,
le taux d’annulation valide et le retard moyen à l’arrivée des trains en retard.
Les variables explicatives sont les métriques existantes de betweenness des
arêtes, ainsi que le degré, la betweenness centrality et le PageRank des nœuds
source et cible. Le champ `nb_train_retard_sup_15`, dont le périmètre
d’application est restreint, n’est pas une variable de résultat ;
`arrival_delay_rate` n’est pas créé. Les services National et International
sont présentés séparément. La vue Overall est uniquement une synthèse
descriptive regroupée.

Des synthèses des résultats sont également fournies par groupe de centralité.
Les ex æquo sont conservés aux limites des groupes ; un groupe de valeurs
égales à zéro est séparé lorsque leur proportion atteint le seuil existant de 5 %.
Les exigences existantes relatives à la taille minimale des échantillons et au
nombre de valeurs distinctes restent en vigueur. Les synthèses comprennent la
taille de l’échantillon, la médiane, la moyenne, l’écart-type, les quartiles et
l’IQR.

Une table de robustesse compare les corrélations calculées sur toutes les
données à celles calculées, pour cette comparaison uniquement, après exclusion
des valeurs inférieures à -15 minutes. Les observations sous-jacentes restent
inchangées.

## Contrat de sortie

Les fichiers sont écrits dans `data/processed/graph/phase3b/` :

- `correlations.parquet` : une ligne par périmètre, service, variable
  explicative, résultat et méthode ; contient le coefficient, la valeur p brute
  et la taille effective de l’échantillon.
- `quantile_comparisons.parquet` : une ligne par groupe et périmètre/service,
  avec le libellé du groupe, la méthode de regroupement, la taille de
  l’échantillon, la médiane, la moyenne, l’écart-type, Q1, Q3 et l’IQR.
- `robustness_comparisons.parquet` : coefficients calculés sur l’ensemble des
  données et en analyse de sensibilité, différence entre les coefficients,
  méthode et tailles effectives des deux échantillons.
- `association_metadata.json` : dimensions et période des données d’entrée,
  nombres de liaisons par service, règles de regroupement, limites
  d’interprétation et schémas de sortie.

Quatre figures réutilisables sont écrites dans
`data/processed/graph/visualizations/phase3b/` : deux nuages de points, un par
service, une figure des résultats par groupe de centralité et une synthèse de
Spearman. La section générée dans `data/reports/graph/research_report.md` est
délimitée par des marqueurs dédiés aux associations ; le texte situé hors de
ces marqueurs est conservé.

## Limites d’interprétation

Les associations ne démontrent pas de lien causal. Les services National et
International ont des compositions de liaisons et des structures de réseau
différentes ; leurs résultats opérationnels ne doivent donc pas être comparés
sans réserve. Le service International comporte moins de liaisons OD
distinctes. Une liaison OD ne correspond pas nécessairement à un segment
physique adjacent ni à un itinéraire confirmé. Les données ne permettent
d’établir ni le volume de voyageurs ni la propagation des retards.
