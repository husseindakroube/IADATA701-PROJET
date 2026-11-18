# Audit interbranches des usages des données et de l’impact du nettoyage

## 1. Périmètre et méthode

Comparaison en lecture seule de la copie de travail, des références Git locales et des états de branches distantes. Aucune branche n’a été extraite. Ce rapport est le seul fichier créé par l’investigation d’origine.

La branche active lors de l’inspection était `mian_ETL_GRAPH`. Elle comportait déjà un `pyproject.toml` modifié et des fichiers non suivis : `data/`, `image/`, `src/projet_kit_data/{etl,graph,ingestion}/`, `tests/` et `uv.lock`. Les références locales `main`, de développement et `origin/main` étaient restées au commit initial `a51e31d`. Les têtes distantes ont été examinées par empreinte : `Test_Shihao` (`cfed3df`), `hussein-eda` (`a7855d2`), `marius-eda` (`fc28172`) et `main` (`6dcf4be`). Les objets ont été récupérés pour lecture seule, sans mise à jour des références ou de l’arbre de travail. Le nom d’une branche n’est pas une preuve de propriété.

Le JSON local `data/raw/regularite-mensuelle-tgv-aqst.json` a été revérifié indépendamment : 12,907 observations, 26 champs et 105 mois. Les rapports `data/reports/data_quality_report.txt` et `data/reports/anomaly_investigation_report.md` ont été lus sans modification pendant l’audit. Les pourcentages utilisent 12,907 lignes ou l’effectif du mois indiqué. Les règles d’anomalie sont des diagnostics, pas des règles de correction acceptées.

## 2. Inventaire des branches et modules

| État de branche | Fichiers pertinents et usage observé | Relation avec la copie examinée |
| --- | --- | --- |
| `mian_ETL_GRAPH` (branche de l’inspection) | `src/projet_kit_data/etl/audit.py` audite les 26 champs bruts. `etl/cleaning.py`, `etl/preprocessing.py` et `graph/{construction,metrics,analysis}.py` sont alors des fichiers vides ; aucun traitement aval n’est évaluable. | État préservé ; l’arbre de travail était déjà modifié avant l’audit. |
| `hussein-eda` (`a7855d2`) | `src/sncf_tgv/eda/quality.py` contrôle la qualité ; `src/sncf_tgv/eda/report.py` agrège les résultats. `notebooks/01_eda_qualite.ipynb` audite les données et `notebooks/02_eda_analyse.ipynb` calcule les taux par liaison et mois. | Paquet distinct `sncf_tgv`, source CSV `data/brut/...csv` ; commit absent de l’historique local examiné. |
| `marius-eda` (`fc28172`) | Reprend le paquet et les carnets précédents, ajoute `notebooks/04_ml_baseline.ipynb`, constitué d’une seule cellule de projet rédigé. `notebooks/05_ml_graph_comparison.ipynb` est vide. | Aucun traitement prédictif ou de comparaison de graphe exécutable à retracer. |
| `Test_Shihao` (`cfed3df`) | Pages Streamlit et CSV distinct `data/initial/regularite-mensuelle-tgv-aqst.csv`. Le code examiné est une présentation et un tableau de bord, sans usage des champs suspects ni nettoyage observé. | Aucune preuve d’import des modules `projet_kit_data` dans cet état de l’application. |
| `main` distante (`6dcf4be`) | Message du dernier commit : `reinitialiser le projet` ; aucun module exploratoire, carnet d’analyse ou donnée brute correspondant à l’organisation examinée. | Arbre très différent de la branche locale ; les références locale et distante ne désignent pas le même commit. |

**Références sources vérifiées :**

- `hussein-eda` / `marius-eda` : `src/sncf_tgv/eda/quality.py`, lignes 190–260 (comptages), 285–345 (retards) ; `src/sncf_tgv/eda/report.py`, fonction `generate_quality_report`.
- `notebooks/01_eda_qualite.ipynb` : cellules de code 2 (téléchargement CSV), 15 (comptages), 25–30 (durées nulles et annulations excessives), 33 (seuils), 41 (export CSV des diagnostics).
- `notebooks/02_eda_analyse.ipynb` : cellule 3, lecture de `data/brut/regularite-mensuelle-tgv-aqst.csv` ; cellule 10, calcul de `circules = nb_train_prevu - nb_annulation` et filtre `circules > 0` ; cellules 12, 15, 21, 26, utilisation de `nb_train_retard_sup_15`, `nb_train_retard_arrivee` et totaux de trains par liaison, mois et année.
- Le carnet `notebooks/04_ml_baseline.ipynb` de `marius-eda` contient uniquement un projet de modélisation rédigé. Le carnet de comparaison du graphe est vide ; les variables prédictives et entrées du graphe ne sont pas encore vérifiables.
- Les modules et carnets exploratoires sont absents des arbres `Test_Shihao` et `main` distants examinés. Les fichiers Streamlit consultés n’accèdent pas aux variables suspectes.

## 3. Effectifs d’anomalies revérifiés

| Contrôle | Observations concernées | Part des 12,907 observations | Répartition et interprétation |
| --- | ---: | ---: | --- |
| `nb_train_retard_sup_30 < 0` | 43 | 0.33% | Janvier 2025 : 18/121 (14.88%) ; février : 15/121 (12.40%) ; mars : 10/121 (8.26%). 29 liaisons-service distinctes ; pas seulement janvier. |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | 354 | 2.74% | Janvier : 118/121 (97.52%) ; février : 117/121 (96.69%) ; mars : 119/121 (98.35%). Toutes au premier trimestre 2025, soit 354 des 363 lignes. |
| `nb_train_retard_sup_15 < nb_train_retard_sup_30` | 3 | 0.02% | Mai 2020 : 2 ; mars 2025 : 1. L’applicabilité de >15 dépend de la liaison, sans indicateur dédié dans les données. |
| `nb_annulation > nb_train_prevu` | 63 | 0.49% | Avril 2020 : 50/123 ; mai : 9/123 ; juin : 4/123. Les 63 lignes ont zéro train prévu, des annulations positives et des comptages/moyennes de retard nuls. |
| Au moins un retard moyen étudié `< -15` | 12 lignes uniques | 0.09% | 11 cas à l’arrivée de tous les trains, 5 au départ et 2 conditionnels à l’arrivée, avec recoupements. 10 des 11 cas d’arrivée et les 5 départs sont en octobre-décembre 2019 ; les 2 cas conditionnels sont en novembre 2019. |

L’audit trouve également 8 valeurs négatives de `retard_moyen_trains_retard_sup15` en 2018–2019. Ce ne sont pas des comptages et elles ne doivent pas être automatiquement remplacées par zéro. Les effectifs concordent avec les rapports existants ; un calcul direct sur le JSON brut confirme les totaux et répartitions mensuelles.

## 4. Effets des champs sur les analyses existantes

La dépendance aval directement observable la plus forte est le carnet exploratoire des branches `hussein-eda` et `marius-eda` :

1. Il calcule `circules = nb_train_prevu - nb_annulation`, puis conserve uniquement `circules > 0` (cellule 10). Les 63 lignes d’annulations excessives sont ainsi exclues des taux de ponctualité, car leur dénominateur calculé est négatif. Le filtre empêche une division par un dénominateur non positif, mais exclut aussi toute ligne sans circulation, même sans anomalie d’audit.
2. Il utilise principalement `nb_train_retard_sup_15` comme numérateur à seuil fixe et `nb_train_retard_arrivee` pour comparaison au seuil officiel (cellules 12, 15, 21, 26). Modifier ou retirer des lignes au premier trimestre 2025 change les taux mensuels, par liaison et les classements annuels. L’anomalie de seuil concerne 354/363 lignes de ce trimestre.
3. Il additionne `nb_annulation` pour les synthèses mensuelles et annuelles (cellule 15). Un filtre antérieur peut modifier ces sommes, même si les lignes exclues ne participent pas au dénominateur. Supprimer toutes les annulations signalées retirerait leurs valeurs positives des totaux.
4. `quality.py` signale indépendamment les comptages négatifs, annulations excessives et comptages >60 dépassant >30 (lignes 190–260). Ses contrôles de durée signalent les moyennes négatives des trains *retardés* (lignes 285–345), sans établir que les retards moyens négatifs de tous les trains sont invalides.
5. Les trois modules de graphe de la branche examinée et le carnet de comparaison de `marius-eda` sont vides. L’impact sur le graphe reste prospectif : retirer une liaison-mois pourrait changer présence d’arêtes, poids ou couverture, mais aucun traitement existant ne permet alors de le quantifier.

La cellule 41 du carnet qualité crée une table *séparée* de suivi des anomalies, avec indicateurs et indice de ligne d’origine, sans modifier la table source. C’est le précédent le plus proche d’une transmission non destructive à l’ETL.

## 5. Évaluation de l’impact des opérations de nettoyage

Les impacts découlent de la structure des données et des formules observées. Décrire un impact ne signifie pas recommander une modification.

| Opération envisagée | Impact sur les données et analyses | Éléments de preuve et appréciation |
| --- | --- | --- |
| Supprimer les lignes avec `nb_train_retard_sup_30` négatif | Retire 43/12,907 lignes, concentrées au premier trimestre 2025 et incluses dans les anomalies >30/<60. Peut modifier taux, couverture du graphe et cibles supervisées. | Un **indicateur qualité par ligne** est justifié, pas une suppression complète : d’autres champs restent renseignés et aucun comptage corrigé n’est établi. |
| Remplacer les comptages >30 négatifs par zéro | Modifie 43 valeurs et les totaux. Ne résout pas l’anomalie d’ordre de 354 lignes : zéro reste inférieur à `sup_60` dans les lignes concernées. | Zéro respecte la non-négativité mais n’est pas démontré comme valeur réelle. Préférer, si nécessaire, une valeur dérivée explicitement nommée et conserver le champ brut. |
| Supprimer toutes les lignes où `sup_30 < sup_60` | Retire 354 observations (2.74%), dont 97.52% de janvier, 96.69% de février et 98.35% de mars 2025 : presque tout le trimestre, avec d’autres comptages apparemment utiles. | Un avertissement limité à la période est justifié, pas la suppression de toutes les colonnes. La continuité entre mois et liaisons suggère un problème propre à cette période sans donner les corrections. |
| Imposer `sup_30 >= sup_60` ou remplacer `sup_30` par `sup_60` | Modifie une grande partie du trimestre. Les comptages deviennent ordonnés par imputation d’une autre métrique ; taux et totaux ne représentent plus les données observées. | Non justifié : rien ne permet de reconstruire le seuil inférieur à partir du supérieur. Vérifier définitions et versions à la source. |
| Imposer `sup_15 >= sup_30` ou modifier les trois lignes | Seulement 3 lignes observées, mais le champ >15 n’est applicable qu’à certaines liaisons sans indicateur de périmètre. | Base insuffisante pour une règle générale ; conserver un diagnostic conditionnel. |
| Supprimer les annulations supérieures aux prévisions | Retire 63/12,907 lignes. Elles échouent déjà au filtre `circules > 0` de l’analyse des taux, mais leur suppression en amont retire aussi leurs annulations et observations liaison-mois. | Conserver les lignes et exclure les dénominateurs non positifs du taux est cohérent avec le calcul existant. La convention horaire du producteur reste à clarifier. |
| Remplacer `nb_train_prevu` par les annulations ou annuler celles-ci | Impose une interprétation non démontrée et modifie `circules` ainsi que les taux de 63 lignes. | Le JSON ne le justifie pas. Conserver les comptages et définir un masque propre à chaque métrique. |
| Supprimer, borner ou mettre à zéro les retards moyens négatifs | Le seuil extrême touche 12 observations uniques (0.09%), sur peu de liaisons surtout en octobre-décembre 2019. Modifie moyennes, médianes et classements ; une suppression retire aussi les comptages. Un retard négatif peut correspondre à une avance. | L’écart entre certaines moyennes tous trains, par exemple Nîmes → Paris Lyon en octobre 2019 (-90.63 à l’arrivée, -92.77 au départ), et les moyennes/comptages des trains retardés mérite vérification. Il justifie un signalement, pas une borne ou correction universelle. |
| Remplacer seulement une moyenne extrême par une valeur manquante en conservant la ligne | Préserve la liaison, le mois et les autres variables ; seules les métriques utilisant cette moyenne changent. | Option d’analyse de sensibilité réversible après clarification sémantique ; exige un masque documenté et une comparaison à la source. Ce n’est pas encore une décision de nettoyage. |
| Ajouter des indicateurs ou publier une vue d’analyse séparée | Conserve toutes les valeurs sources et permet des masques explicites propres à chaque métrique ou modèle. | Direction la mieux étayée, cohérente avec la table d’anomalies du carnet qualité et évitant une décision globale de suppression ou d’imputation. |

### Exposition approximative dans les analyses connues

- Supprimer `sup_30 < sup_60` ne laisserait que 3/121 lignes de janvier, 4/121 de février et 2/121 de mars 2025, soit 9 au total. Les comparaisons du trimestre seraient dominées par cette exclusion sélective.
- Le taux exploratoire exclut déjà `circules <= 0`, donc les annulations signalées de ses dénominateurs. Cette règle appartient à ce carnet et ne garantit rien pour l’ETL futur, les totaux d’annulation ou les arêtes.
- Retirer les 12 lignes extrêmes uniques toucherait 9 liaisons-service, avec répétitions de Nîmes, Valence Alixan TGV et Montpellier vers Paris Lyon. L’impact par liaison peut être disproportionné malgré la faible part globale.
- Les catégories se recoupent : ne pas additionner leurs effectifs pour compter les lignes uniques. L’union des retards extrêmes vaut 12, pas 18.

## 6. Recommandations et décisions nécessaires

### Éléments adaptés à une proposition de nettoyage

- Conserver le JSON source immuable et créer un jeu ou une vue d’analyse séparé et versionné.
- Ajouter des indicateurs de comptages négatifs et d’ordre des seuils, en conservant les valeurs et l’identité source.
- Définir la validité du dénominateur par métrique. Pour la ponctualité, exiger un `circules` positif documenté, compter les exclusions et conserver séparément les totaux d’annulation.
- Comparer trois scénarios : valeurs brutes, exclusions propres à la métrique et remplacements proposés dans une vue séparée. Examiner tendances mensuelles, classements et couverture du graphe avant toute adoption.
- Demander au producteur la définition/version de >30 et >60 au premier trimestre 2025, la convention d’annulation avec prévisions nulles et les définitions/unités des moyennes tous trains d’octobre-décembre 2019.

### Opérations non justifiées à ce stade

- Remplacer les négatifs par zéro, déduire `sup_30` de `sup_60`, imposer `sup_15 >= sup_30`, supprimer les annulations excessives, borner les moyennes négatives ou supprimer toutes les lignes signalées.
- L’anomalie >30/<60 justifie une validation ou un avertissement daté, pas une imputation.
- Un comptage littéralement négatif est impossible et peut être invalidé pour un calcul de comptage ; le traitement de la ligne et la correction nécessitent des preuves du producteur.
- Le motif d’avril 2020 est cohérent en interne : prévisions/retards nuls et annulations positives. Son caractère erroné dépend des définitions du programme et des annulations.
- Les moyennes négatives extrêmes appellent un contrôle ciblé. Leur ampleur et désaccord avec d’autres indicateurs signalent une incohérence sans identifier le champ à corriger.

## 7. Limites

- Les états distants ont été examinés par commits immuables. Les références locales `main` et `origin/main` étaient anciennes ; les têtes récupérées sont explicitement identifiées sans les assimiler aux branches locales. `git ls-remote` a réussi avant récupération des objets ; aucun changement de branche n’a été effectué.
- Les CSV des branches sont des états distincts, pas forcément identiques au JSON local. Les effectifs numériques ont été recalculés sur ce JSON ; chemins et formules proviennent des commits examinés.
- Les indices des cellules commencent à zéro, les carnets n’ayant pas de numéros de ligne stables. Leurs sorties peuvent être anciennes ; les effectifs indiqués comme revérifiés ont été recalculés sur le JSON local.
- Les modules graphe et nettoyage/prétraitement étaient vides lors de l’inspection : l’impact sur topologie, poids et modèles n’était pas mesurable. L’évaluation du graphe est prospective.
- Les données ne permettent d’établir ni causes, ni changements amont, ni valeurs de remplacement prévues.

## 8. État après l’inspection d’origine

Aucun code, donnée brute, carnet, configuration, rapport existant, branche, référence ou arbre de travail n’a été modifié par cette investigation. Seuls des objets de commits distants ont été ajoutés pour lecture. Ce rapport Markdown était le seul nouveau fichier.

## 9. Contrat commun et compatibilité

Cette section décrit les lecteurs réellement trouvés dans les états examinés. Le contrat proposé définit la signification et la représentation des champs sans imposer une bibliothèque de DataFrame commune ni le format interne Polars de l’audit.

### 9.1 Utilisation par les modules au moment de l’inspection

| Module / état | Format et emplacement | Bibliothèque, noms et types attendus | Obligatoire ou facultatif | Dates et valeurs manquantes | Transformations propres au module |
| --- | --- | --- | --- | --- | --- |
| Acquisition, `src/projet_kit_data/ingestion/sncf_api.py` | Export JSON SNCF Explore v2.1 ; chemin par défaut `data/raw/regularite-mensuelle-tgv-aqst.json`. | Requests produit `list[dict[str, Any]]`, sans DataFrame ni renommage ; types scalaires JSON conservés. | Vérifie le tableau racine et ses objets, sans liste fixe de colonnes ; tous les champs sont conservés. | `date` reste la chaîne source (`YYYY-MM` dans cet état) et null reste `None`. | Aucun nettoyage, conversion forcée ou création de variables ; JSON UTF-8 avec `ensure_ascii=False`. |
| Audit, `src/projet_kit_data/etl/audit.py` | JSON brut ci-dessus ; rapport `data/reports/data_quality_report.txt`. | Polars, contrôle des 26 noms canoniques ; résultats diagnostiques également renvoyés en dictionnaire. | Compare les champs au schéma ; les contrôles disponibles sont exécutés et les absences/suppléments signalés. | Mois sous forme de chaînes ; valeurs nulles conservées. Deux commentaires entièrement nuls, commentaires d’arrivée nuls à 94.59%. | Schémas, types, manquants, doublons, négatifs, statistiques, règles logiques et exemples, sans modification. |
| Paquet ETL/graphe examiné | `etl/cleaning.py`, `etl/preprocessing.py`, `graph/construction.py`, `graph/metrics.py`, `graph/analysis.py` sont vides. | Aucun lecteur, bibliothèque ou contrat exécutable vérifiable. | Indéterminé. | Indéterminé. | Aucun traitement implémenté ; un fichier vide ne prouve pas la compatibilité. |
| Module qualité `hussein-eda` / `marius-eda` | `src/sncf_tgv/eda/quality.py` reçoit un `pandas.DataFrame` ; le carnet télécharge ou lit `data/brut/regularite-mensuelle-tgv-aqst.csv`. | Pandas, noms canoniques, comptages, retards, six causes et commentaires ; `pd.to_numeric(..., errors="coerce")` pour les contrôles numériques. | `check_identifiers` : 4 clés ; `check_train_counts` : 7 comptages ; `check_durations` : durée et 5 moyennes ; `check_percentages` : 6 causes ; `check_comments` : 3 commentaires. L’agrégateur nécessite les 26 champs. | Date interprétable, format `YYYY-MM` préservé par le renommage ; `isna()`, valeurs nulles et conversion numérique. Texte non numérique signalé invalide. | Doublons, dates, cohérence, moyennes négatives des trains retardés, bornes/sommes de pourcentages et complétude des commentaires ; synthèses, pas lignes nettoyées. |
| Carnet `notebooks/02_eda_analyse.ipynb` de `hussein-eda` / `marius-eda` | CSV séparé par point-virgule, UTF-8-SIG, dans `data/brut/regularite-mensuelle-tgv-aqst.csv`. | Pandas ; en-têtes français traduits en 26 noms courts à la cellule 4. Colonnes numériques attendues après lecture, sans schéma formel de types. | Table de renommage complète ; calculs sur clés, date, durée, prévisions, annulations et retards >15/à l’arrivée. Commentaires et causes secondaires. | Date `YYYY-MM` pour groupements, conversion temporelle pour graphiques ; lecture des valeurs manquantes par défaut et hypothèse de nombres utilisables. | Crée `liaison`, `circules = planned - cancelled`, filtre `circules > 0`, calcule taux, agrégats, classes de durée, classements et directions : variables analytiques, pas nettoyage partagé. |
| Application `Test_Shihao` | CSV distinct dans `data/initial/regularite-mensuelle-tgv-aqst.csv`. | Aucun chargeur ni référence aux champs suspects dans les pages examinées ; types et chemin d’utilisation non vérifiés. | Indéterminé. | Indéterminé. | Aucune transformation vérifiable dans les sources examinées. |
| `main` distante | Aucun module ou entrée exploratoire correspondant dans l’arbre examiné. | Aucun consommateur trouvé. | Sans objet. | Sans objet. | Sans objet. |
| Carnets prédictifs/graphe de `marius-eda` | Référence prédictive : une cellule rédigée ; comparaison du graphe : vide. | Aucun chargeur ni liste de variables exécutable. | Indéterminé. | Indéterminé. | Aucun traitement implémenté dans ces deux carnets. |

Les types Polars inférés sont : chaînes pour identités, commentaires et date ; entiers pour comptages et `duree_moyenne` ; flottants pour moyennes et pourcentages ; `Null` pour colonnes entièrement nulles. Le JSON ne déclare pas de schéma. Le contrat propose des types logiques acceptant les valeurs nulles : un commentaire entièrement absent reste une chaîne nullable et non une colonne définitivement de type Null.

### 9.2 Contrat sémantique commun proposé

**Granularité et identité.** Une ligne représente une observation mensuelle liaison-service SNCF. Clé recommandée : `(date, service, gare_depart, gare_arrivee)`. Départ et arrivée sont ordonnés, pas interchangeables. `service` reste dans la clé car National et International peuvent partager liaison et mois.

**Date.** `date` est un mois ISO `YYYY-MM`, pas un instant journalier. Vérifier format et mois sans conversion silencieuse en jour ou fuseau. Une date dérivée au premier du mois peut servir aux graphiques ou index, en conservant la date du contrat.

**Noms canoniques et types logiques.** Conserver les noms courts de l’API utilisés par l’audit et le module qualité après renommage. Tous les champs acceptent des valeurs nulles au niveau du contrat ; leur complétude dans un état donné ne garantit pas les exports futurs.

| Champs canoniques | Type logique | Signification et unité |
| --- | --- | --- |
| `date` | Chaîne, mois ISO `YYYY-MM` | Mois de l’observation. |
| `service` | Chaîne | Catégorie SNCF, par exemple National ou International ; ne pas supprimer cette distinction par normalisation. |
| `gare_depart`, `gare_arrivee` | Chaîne | Noms de départ et d’arrivée, avec direction et orthographe sources conservées. |
| `duree_moyenne` | Entier nullable | Durée moyenne prévue du trajet, en minutes. |
| `nb_train_prevu`, `nb_annulation`, `nb_train_depart_retard`, `nb_train_retard_arrivee`, `nb_train_retard_sup_15`, `nb_train_retard_sup_30`, `nb_train_retard_sup_60` | Comptages entiers nullables | Nombres mensuels de trains prévus, annulés, retardés au départ/à l’arrivée ou au-delà du seuil indiqué. Les négatifs sont signalés sans correction déduite. >15 a une applicabilité limitée selon la description. |
| `retard_moyen_depart`, `retard_moyen_tous_trains_depart`, `retard_moyen_arrivee`, `retard_moyen_tous_trains_arrivee`, `retard_moyen_trains_retard_sup15` | Nombre décimal nullable, minutes | Distinguer moyennes des trains retardés, de tous les trains et conditionnelles >15. Une valeur négative peut représenter une avance selon la définition ; son signe seul ne définit pas un nettoyage. |
| `prct_cause_externe`, `prct_cause_infra`, `prct_cause_gestion_trafic`, `prct_cause_materiel_roulant`, `prct_cause_gestion_gare`, `prct_cause_prise_en_charge_voyageurs` | Nombre décimal nullable, pourcentage de 0 à 100 | Part des retards attribuée à chaque cause ; pas une fraction de 0 à 1. Distinguer inconnue et zéro. |
| `commentaire_annulation`, `commentaire_retards_depart`, `commentaires_retard_arrivee` | Chaîne nullable | Commentaire libre source ; conserver texte et orthographe, distinguer chaîne vide et valeur nulle sauf règle d’affichage explicite. |

**Valeurs manquantes et types.** Représenter les absences par null/NA sans remplissage numérique à zéro. Zéro est une observation, distincte de l’inconnu. JSON null correspond à `None`, aux valeurs manquantes Pandas ou null Polars. Les champs numériques CSV doivent être explicitement convertis ; compter et signaler les échecs plutôt que conserver silencieusement du texte. Les types physiques peuvent varier selon la bibliothèque.

**Stockage.** Conserver le JSON brut immuable et sans perte. Le contrat concerne une table dérivée indépendante du format et de la bibliothèque. Si un fichier partagé est immédiatement nécessaire, proposer un CSV UTF-8 à 26 noms canoniques, avec encodage des absences documenté, date `YYYY-MM`, comptages entiers et mesures décimales. Maintenir l’export de compatibilité à point-virgule et en-têtes français, ou un adaptateur Pandas, jusqu’à migration du carnet. Ne pas imposer Polars. Parquet peut être envisagé après accord sur moteur, dépendances et schéma ; il n’est pas requis pour ce premier contrat.

### 9.3 Compatibilité et modifications minimales

| Consommateur | Compatibilité directe avec un JSON/CSV canonique | Action minimale |
| --- | --- | --- |
| Acquisition `load_raw_data()` | Oui pour le tableau JSON d’objets aux mêmes noms. | Aucune pour le JSON brut ; la sortie reste des observations Python, pas un DataFrame. |
| Audit | Oui pour le JSON canonique, déjà chargé avec Polars. | Pour un CSV, adapter seulement le lecteur/chemin ou continuer à lire le JSON ; ne pas changer les conditions pour satisfaire un consommateur. |
| `sncf_tgv.eda.quality` | Oui après chargement dans Pandas avec tous les champs canoniques requis. | JSON : `pd.read_json` et conversions explicites ; CSV : `pd.read_csv` avec types adaptés. Conserver le renommage des anciens en-têtes français. Traiter explicitement les colonnes absentes : l’agrégateur les refuse. Aucune migration vers Polars nécessaire. |
| `notebooks/02_eda_analyse.ipynb` | Pas directement depuis JSON ou CSV canonique à virgules. | Garder Pandas : exporter le CSV attendu à point-virgule et en-têtes français, ou adapter uniquement le lecteur/renommage. Conserver les mois textuels, documenter nombres/absences et revoir `circules > 0` comme règle analytique locale. |
| Modules nettoyage/prétraitement et graphe | Compatibilité d’exécution non évaluable car non implémentés lors de l’audit. | Accepter le schéma logique commun aux frontières et garder les variables dérivées locales ; choisir la bibliothèque lorsque les interfaces existent. |
| Application `Test_Shihao` | Impossible à établir à partir des sources examinées. | Identifier d’abord chargeur et schéma ; adapter les en-têtes à la frontière si nécessaire, sans déduire la bibliothèque du nom de branche. |
| Carnets de référence et comparaison du graphe de `marius-eda` | Sans objet : aucun traitement implémenté. | Définir cible et variables après le chargeur ; utiliser un adaptateur local Pandas si les carnets exploratoires restent sous Pandas. |
| `main` distante | Aucun consommateur identifié. | Aucune action avant ajout d’un consommateur. |

### 9.4 Séparer préparation commune et variables propres aux modules

**Préparation commune** : conserver valeurs et traçabilité, vérifier les champs, convertir les types sans altération destructive, normaliser les absences en les distinguant de zéro, valider `YYYY-MM`, préserver la granularité service-liaison-mois et publier séparément les diagnostics. L’interopérabilité ne décide pas de la validité d’une ligne pour toute analyse.

**Variables propres aux modules**, selon leurs objectifs :

- L’analyse exploratoire peut calculer `circules = nb_train_prevu - nb_annulation`, imposer un dénominateur positif et choisir un seuil ; documenter les effectifs admissibles et exclus.
- Le graphe peut définir présence mensuelle d’arête, direction, pondération et traitement des absences/anomalies. Aucune telle règle n’était implémentée à ce stade.
- La prédiction peut définir cible, fenêtre, découpage temporel et contrôles de fuite. Le carnet de référence était seulement rédigé ; ne pas imposer ces variables à une table globale nettoyée.
- L’audit doit continuer à fournir diagnostics et effectifs, pas un jeu implicitement nettoyé.

### 9.5 Migration à faible risque

1. Garder le JSON téléchargé immuable et ses 26 noms/valeurs comme contrat brut.
2. Publier une note de schéma et un chargeur/adaptateur typé aux frontières des modules, en conservant les bibliothèques de chaque équipe.
3. Pour l’exploration, fournir d’abord un CSV compatible `sep=";"`, en-têtes français et UTF-8-SIG, ou adapter le seul chargeur. Comparer effectifs, absences, dates et agrégats au CSV actuel avant bascule.
4. Laisser chaque module gérer ses masques et variables. Produire côte à côte anciennes/nouvelles sorties et comparer taux, classements, annulations et couverture ; ne remplacer l’ancien résultat qu’après examen.
5. N’envisager l’abandon du CSV à en-têtes français qu’après migration des consommateurs. Versionner ou rendre reproductibles les sources et exports, avec version de schéma et date des données.

**Portée des preuves :** le tableau décrit l’export vérifié et le schéma d’audit à 26 champs. Significations et unités suivent les descriptions et conventions d’analyse de l’équipe ; confirmer les définitions SNCF avant d’imposer bornes ou corrections. L’inspection concerne les lecteurs et traitements présents dans ces commits, pas des travaux futurs ou absents.
