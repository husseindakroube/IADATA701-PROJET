# Régularité mensuelle TGV SNCF : contrat commun de données

**Statut :** interface commune proposée, version 1.0 soumise à l’équipe.
**Périmètre :** représentation tabulaire brute et réutilisable de l’export mensuel SNCF. Ce document définit le sens des champs et les échanges attendus sans implémenter de nettoyage ni imposer une bibliothèque de DataFrame.

## 1. Objectif et périmètre

L’exploration, l’analyse de graphe, l’apprentissage automatique, l’audit et l’ETL doivent partager la signification d’une ligne et de chaque champ. Le contrat réduit les divergences accidentelles de noms, dates, absences et unités entre modules.

Le contrat est **indépendant des bibliothèques**. Chaque consommateur peut utiliser Pandas, Polars ou un autre outil avec un adaptateur à sa frontière. Il définit noms, types logiques, sens et règles de conservation, sans imposer un type de table en mémoire ni l’implémentation Polars de l’audit.

Cette proposition prolonge `data/reports/cross_branch_cleaning_impact_report.md`, notamment ses sections 9.1–9.5. Les définitions et unités nécessitant le dictionnaire officiel SNCF sont signalées. Les descriptions sont des interprétations de travail fondées sur les noms et analyses existantes, pas de nouvelles définitions officielles.

## 2. Granularité et clé métier

Une ligne représente **une observation mensuelle d’un service et d’une liaison** dans les données SNCF.

La clé métier est :

```text
(date, service, gare_depart, gare_arrivee)
```

La liaison est orientée : ne pas échanger `gare_depart` et `gare_arrivee` ni les fusionner en paire non orientée. Conserver aussi `service` : un même mois et une même paire peuvent apparaître dans plusieurs services, qui restent des observations distinctes. Préserver valeurs et orthographe des clés ; les libellés normalisés éventuels doivent être dérivés.

## 3. Schéma canonique

Les noms canoniques sont les 26 noms courts de l’export JSON SNCF et de l’audit. Chaque champ accepte les **valeurs nulles**, même s’il est complet dans un état donné. Comptages et durée prévue sont des entiers logiques ; moyennes et pourcentages sont décimaux. Les types physiques Pandas/Polars peuvent différer s’ils préservent ces types et les absences.

Les descriptions et unités marquées « à confirmer » doivent être vérifiées dans le dictionnaire officiel avant d’imposer corrections ou plages de validité.

| Nom canonique | Type logique | Signification de travail | Unité | Valeurs nulles et réserves sémantiques |
| --- | --- | --- | --- | --- |
| `date` | Chaîne, `YYYY-MM` | Mois de l’observation. | Mois calendaire | Nullable ; une valeur absente ou mal formée constitue une clé invalide. Ne pas la remplacer par une date journalière. |
| `service` | Chaîne | Catégorie du service. | Sans unité | Nullable ; conserver les catégories dans la clé. Définition officielle à confirmer auprès de la SNCF. |
| `gare_depart` | Chaîne | Nom de la gare d’origine. | Sans unité | Nullable ; conserver l’orthographe, la direction et son rôle dans la clé. |
| `gare_arrivee` | Chaîne | Nom de la gare de destination. | Sans unité | Nullable ; conserver l’orthographe, la direction et son rôle dans la clé. |
| `duree_moyenne` | Entier nullable | Durée moyenne prévue du trajet selon le nom du champ. | Minutes, définition à confirmer | Peut exceptionnellement valoir zéro ; ne pas confondre zéro et absence. Calcul et périmètre à confirmer. |
| `nb_train_prevu` | Comptage entier nullable | Nombre mensuel de trains ou circulations prévus. | Trains | Signaler les négatifs. Distinguer zéro et absence. Confirmer la version de l’horaire utilisée. |
| `nb_annulation` | Comptage entier nullable | Nombre de trains ou circulations annulés. | Trains | Signaler les négatifs. Les valeurs peuvent dépasser `nb_train_prevu` dans la source ; ne pas supprimer ou réécrire ces lignes sans confirmer les conventions SNCF. |
| `commentaire_annulation` | Chaîne nullable | Commentaire source sur les annulations. | Sans unité | Préserver le texte exact. Distinguer valeur nulle et chaîne vide sauf règle d’affichage explicite. |
| `nb_train_depart_retard` | Comptage entier nullable | Nombre de trains déclarés retardés au départ. | Trains | Signaler les négatifs ; seuil exact et population à confirmer. |
| `retard_moyen_depart` | Nombre décimal nullable | Retard moyen du sous-ensemble déclaré retardé au départ. | Minutes, définition à confirmer | Selon la définition, un négatif peut représenter une avance. Ne pas exclure ou borner sur le seul signe ; confirmer population et pondération. |
| `retard_moyen_tous_trains_depart` | Nombre décimal nullable | Retard moyen au départ de la population dite de tous les trains. | Minutes, définition à confirmer | Confirmer la population, les annulations et les avances ; conserver les négatifs dans l’attente. |
| `commentaire_retards_depart` | Chaîne nullable | Commentaire source sur les retards au départ. | Sans unité | Préserver le texte ; une valeur nulle n’est pas une chaîne vide. |
| `nb_train_retard_arrivee` | Comptage entier nullable | Nombre de trains déclarés retardés à l’arrivée. | Trains | Signaler les négatifs. Le seuil officiel peut dépendre de la durée ; vérifier le dictionnaire. |
| `retard_moyen_arrivee` | Nombre décimal nullable | Retard moyen du sous-ensemble retardé à l’arrivée. | Minutes, définition à confirmer | Ne pas borner automatiquement les négatifs ; vérifier définition et population admissible. |
| `retard_moyen_tous_trains_arrivee` | Nombre décimal nullable | Retard moyen à l’arrivée de la population dite de tous les trains. | Minutes, définition à confirmer | Population et pondération à confirmer. Les négatifs extrêmes sont des diagnostics, pas une preuve de la correction attendue. |
| `commentaires_retard_arrivee` | Chaîne nullable | Commentaire source sur les retards à l’arrivée. | Sans unité | Préserver le texte. Beaucoup d’absences dans l’état vérifié ; une absence n’est ni un zéro ni une explication vide. |
| `nb_train_retard_sup_15` | Comptage entier nullable | Nombre de trains dépassant 15 minutes de retard selon le nom du champ. | Trains | Applicabilité limitée aux liaisons en concurrence avec l’avion, sans indicateur dédié. Ne pas imposer universellement `sup_15 >= sup_30` ; confirmer le périmètre SNCF. |
| `retard_moyen_trains_retard_sup15` | Nombre décimal nullable | Retard moyen du groupe >15 minutes. | Minutes, définition à confirmer | Même réserve d’applicabilité. Un négatif peut refléter la définition publiée ou une incohérence ; ne pas le modifier automatiquement. |
| `nb_train_retard_sup_30` | Comptage entier nullable | Nombre de trains dépassant 30 minutes de retard. | Trains | Signaler les négatifs sans les remplacer par zéro sans preuve. Vérifier version/définition de la relation à `sup_60` au premier trimestre 2025. |
| `nb_train_retard_sup_60` | Comptage entier nullable | Nombre de trains dépassant 60 minutes de retard. | Trains | Signaler les négatifs. Ne pas écraser ou déduire `sup_30` depuis ce champ ; confirmer seuils et populations. |
| `prct_cause_externe` | Nombre décimal nullable | Pourcentage attribué aux causes externes. | Pourcentage, échelle attendue 0–100, à confirmer | Valeur nulle = inconnue/non publiée, pas zéro. Contrôler bornes et somme à titre diagnostique ; ne pas remplir les causes absentes par zéro. |
| `prct_cause_infra` | Nombre décimal nullable | Pourcentage attribué à l’infrastructure. | Pourcentage, échelle attendue 0–100, à confirmer | Distinguer absence et zéro ; périmètre de catégorie et dénominateur à confirmer. |
| `prct_cause_gestion_trafic` | Nombre décimal nullable | Pourcentage attribué à la gestion du trafic. | Pourcentage, échelle attendue 0–100, à confirmer | Distinguer absence et zéro ; périmètre de catégorie et dénominateur à confirmer. |
| `prct_cause_materiel_roulant` | Nombre décimal nullable | Pourcentage attribué au matériel roulant. | Pourcentage, échelle attendue 0–100, à confirmer | Distinguer absence et zéro ; périmètre de catégorie et dénominateur à confirmer. |
| `prct_cause_gestion_gare` | Nombre décimal nullable | Pourcentage attribué à la gestion des gares. | Pourcentage, échelle attendue 0–100, à confirmer | Distinguer absence et zéro ; causes incluses et dénominateur à confirmer. |
| `prct_cause_prise_en_charge_voyageurs` | Nombre décimal nullable | Pourcentage attribué à la prise en charge des voyageurs. | Pourcentage, échelle attendue 0–100, à confirmer | Distinguer absence et zéro ; causes incluses et dénominateur à confirmer. |

### Groupes de champs et types logiques attendus

- **Identifiants et catégorie :** `date`, `service`, `gare_depart`, `gare_arrivee` sont des chaînes.
- **Durée prévue et comptages :** `duree_moyenne`, `nb_train_prevu`, `nb_annulation`, `nb_train_depart_retard`, `nb_train_retard_arrivee`, `nb_train_retard_sup_15`, `nb_train_retard_sup_30`, `nb_train_retard_sup_60` sont des entiers nullables. Signaler les textes numériques invalides et valeurs fractionnaires.
- **Retards moyens :** `retard_moyen_depart`, `retard_moyen_tous_trains_depart`, `retard_moyen_arrivee`, `retard_moyen_tous_trains_arrivee`, `retard_moyen_trains_retard_sup15` sont décimaux nullables, interprétés en minutes sous réserve de confirmation SNCF.
- **Causes :** les six champs `prct_cause_*` sont décimaux nullables, en points de pourcentage et non en fractions de 0 à 1. Confirmer dénominateurs et catégories.
- **Commentaires :** les trois champs de commentaires sont des chaînes nullables.

## 4. Convention des dates

`date` reste une chaîne mensuelle `YYYY-MM`, par exemple `2025-01`.

Valider le format et le mois, de `01` à `12`. Ne pas convertir silencieusement ce champ en jour ou en instant avec fuseau. Une colonne séparée au premier du mois peut être dérivée pour graphiques ou séries temporelles tout en conservant valeur et granularité d’origine.

## 5. Valeurs manquantes et types

1. **Une absence n’est pas zéro.** Conserver les absences comme null/NA. Un comptage ou pourcentage zéro est observé et reste distinct de l’inconnu ou non publié.
2. **Aucun remplissage silencieux.** Ne pas remplacer les absences par zéro pour permettre un calcul. Définir un masque d’admissibilité et indiquer le nombre de lignes exclues.
3. **Types logiques indépendants des bibliothèques.** Respecter les chaînes, entiers et décimaux nullables définis ici. Pandas peut utiliser ses types d’extension et Polars ses types natifs ; le format de transport ne change pas le contrat.
4. **Échecs de conversion visibles.** Interpréter les textes numériques selon les groupes. Une valeur non vide illisible ou fractionnaire dans un comptage doit produire un diagnostic avec champ et ligne. Ne pas la laisser silencieusement en texte ni la remplacer par zéro. Conserver la représentation originale dans la source immuable.
5. **Les colonnes entièrement nulles gardent un type logique.** Sur 12,907 observations, `commentaire_annulation` et `commentaire_retards_depart` sont absents à 100% ; `commentaires_retard_arrivee` est absent dans 12,209 lignes (94.59%) et renseigné dans 698. Les deux premiers restent des chaînes nullables même si Polars infère Null. Ne pas supprimer ces colonnes ni considérer leur absence actuelle comme permanente.

## 6. Politique de qualité et d’anomalies

L’export brut constitue une preuve. Les constats d’audit servent à l’examen et à l’admissibilité propre à chaque métrique ; ils ne constituent pas seuls une instruction de réécriture.

### Validation et correction

Une **règle de validation** signale un champ absent, un type inattendu, une contrainte non respectée ou une relation suspecte. Elle identifie condition, champs, lignes et effectifs sans modifier l’observation.

Une **règle de correction** change une valeur, retire une ligne ou remplace une représentation. Elle exige une définition officielle ou une décision documentée et revue. Conserver valeur originale, justification, version de règle et traçabilité vers la source.

La politique d’investigation est la suivante :

- Conserver le JSON original immuable et les valeurs observées dans les données dérivées.
- Ajouter des indicateurs ou métadonnées qualité séparés plutôt que supprimer automatiquement les lignes suspectes.
- Ne pas remplacer les comptages négatifs par zéro sans preuve. Ils sont incompatibles avec le sens d’un comptage et doivent être signalés, mais la correction reste inconnue.
- Ne pas imposer `nb_train_retard_sup_30 >= nb_train_retard_sup_60`. Le premier trimestre 2025 fournit un signal fort sans déterminer les valeurs corrigées.
- Ne pas imposer automatiquement `nb_train_retard_sup_15 >= nb_train_retard_sup_30` : l’applicabilité de >15 est limitée et les liaisons admissibles ne sont pas identifiées.
- Ne pas supprimer globalement `nb_annulation > nb_train_prevu` ; l’interprétation dépend des conventions de programme et d’annulation SNCF.
- Ne pas borner automatiquement les moyennes négatives : elles peuvent représenter une avance ; définitions et populations sont à confirmer.
- Définir les conditions d’admissibilité propres à chaque métrique, par exemple un dénominateur positif, et compter les exclusions sans supprimer la ligne source du jeu partagé.

## 7. Préparation commune et transformations propres aux modules

| Couche | Responsabilité dans ce contrat |
| --- | --- |
| Acquisition | Récupérer l’export et conserver noms, valeurs et nulls JSON ; stocker la source sans transformation ETL. |
| Audit | Diagnostiquer schéma, absences, doublons, types et anomalies logiques ; publier les constats sans modifier la source. |
| Nettoyage | Appliquer seulement les corrections confirmées et documentées, avec valeurs brutes, traçabilité et reproductibilité. Ce document seul n’autorise aucune correction. |
| Prétraitement | Produire une représentation typée réutilisable conforme au schéma, aux dates et aux absences ; limiter la préparation commune à la lecture, aux types et à la traçabilité. |
| Exploration | Choisir numérateurs, populations admissibles et dénominateurs propres à l’analyse ; documenter exclusions et mesures dérivées. |
| Graphe | Définir inclusion des arêtes, directions, fenêtres, pondération et gestion des absences/anomalies ; préserver la direction source sauf vue explicitement non orientée. |
| Apprentissage automatique | Définir cible, prédicteurs, fenêtres historiques, ensembles d’entraînement/validation/test et contrôles de fuite ; conserver ces choix dans le traitement de modélisation. |

Le prétraitement commun ne doit pas absorber les définitions de taux exploratoires, la construction d’arêtes ou les cibles/variables prédictives : ces décisions répondent à des objectifs et populations différents.

## 8. Stockage et compatibilité

- **Source brute :** conserver `data/raw/regularite-mensuelle-tgv-aqst.json` comme tableau JSON immuable de l’export SNCF vérifié. Ne pas le réécrire lors du nettoyage ou prétraitement.
- **Schéma logique :** utiliser les 26 noms courts canoniques dans les sorties typées et interfaces. Les correspondances de compatibilité appartiennent aux frontières d’entrée/sortie.
- **Ancienne interface exploratoire :** le carnet examiné lit un CSV à point-virgule en UTF-8-SIG avec en-têtes français, ensuite renommés. Conserver cet export reproductible ou un adaptateur Pandas, sans rendre le contrat dépendant de cet ancien format.
- **Pandas et Polars :** permettre des adaptateurs vers le même schéma logique, sans migration obligatoire. Le module qualité peut rester sous Pandas et l’audit sous Polars.
- **Parquet :** option ultérieure après accord sur métadonnées, moteur et dépendances ; non requis pour ce contrat initial.
- **Sérialisation des absences :** documenter leur encodage dans les CSV dérivés et les distinguer du zéro réel ou du commentaire vide.

## 9. Versionnement et migration

La version de ce contrat est indépendante de la version de publication SNCF. L’inscrire dans la documentation ou les métadonnées des fichiers, pas dans une colonne source SNCF inventée.

Migration recommandée :

1. Conserver le JSON brut et l’identifier par date, état source ou empreinte si nécessaire à la reproductibilité.
2. Adopter les 26 noms et types canoniques aux frontières avant de modifier les traitements internes.
3. Fournir les chargeurs typés Pandas/Polars nécessaires, signaler les échecs et préserver les absences.
4. Maintenir l’ancienne interface CSV pendant la transition par export compatible (`;`, UTF-8-SIG, en-têtes français) ou petit adaptateur.
5. Exécuter anciens et nouveaux chargeurs côte à côte. Comparer effectifs, clés, dates, absences, taux et synthèses par liaison avant bascule. Pour graphe/prédiction, comparer couverture/poids ou populations de cibles/variables.
6. Migrer chaque consommateur après revue, sans imposer une migration simultanée de bibliothèque. Garder localement les choix d’admissibilité et de variables.
7. Documenter toute évolution de schéma : version, champs, types, sens, compatibilité et correspondances. Ne jamais réutiliser silencieusement un nom pour une autre signification.

## 10. Questions sémantiques ouvertes

Les points suivants nécessitent confirmation du dictionnaire officiel SNCF avant de justifier des corrections strictes :

- Population, calcul et pondération de chaque `retard_moyen_*`, notamment tous trains et conditionnel >15.
- Seuils et applicabilité de `nb_train_depart_retard`, `nb_train_retard_arrivee` et `nb_train_retard_sup_15`.
- Inversion >30/>60 au premier trimestre 2025 : éventuel changement de définition ou de production.
- Éventuelle référence de `nb_annulation` à un programme antérieur et de `nb_train_prevu` à un programme ultérieur, expliquant annulations positives et prévisions nulles.
- Définition exacte de `duree_moyenne`, dénominateurs et frontières des six catégories de causes.
- Signification des moyennes négatives et, en particulier, de leurs amplitudes extrêmes.

Ces points restent des incertitudes documentées. Le contrat n’affirme aucune causalité, ne prescrit aucune valeur de remplacement et ne prétend pas que l’état observé représente les exports futurs.
