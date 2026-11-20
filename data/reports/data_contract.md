# Régularité mensuelle des TGV SNCF : contrat de données partagé

**Statut :** proposition d’interface partagée, version 1.0, à examiner en équipe
**Périmètre :** représentation tabulaire brute et réutilisable de l’export SNCF de régularité mensuelle des TGV. Ce document définit le sens des champs partagés et les attentes d’échange. Il ne met pas en œuvre de nettoyage et n’impose aucune bibliothèque particulière pour les DataFrame.

## 1. Objectif et périmètre

L’EDA, l’analyse de graphes, le machine learning, l’audit et les futurs travaux ETL doivent partager une interprétation commune des lignes et des champs source. Un contrat commun limite les divergences accidentelles de noms de champs, d’interprétation des dates, de traitement des valeurs manquantes et d’unités lors des échanges entre modules.

Le contrat est **indépendant des bibliothèques**. Les consommateurs peuvent utiliser Pandas, Polars ou un autre outil approprié et fournir un petit adaptateur à leur interface. Le schéma partagé porte sur les noms des champs, leurs types logiques, leur sens et les règles de conservation ; il ne prescrit pas un type unique de DataFrame en mémoire et n’impose pas l’implémentation actuelle de l’audit sous Polars aux autres modules.

Cette proposition s’appuie sur `data/reports/cross_branch_cleaning_impact_report.md`, notamment ses sections 9.1 à 9.5. Lorsqu’il faut consulter le dictionnaire SNCF pour confirmer la définition exacte ou l’unité d’un champ, cela est explicitement indiqué. Les descriptions ci-dessous sont des interprétations de travail fondées sur les noms de l’export et les analyses existantes du projet ; elles ne prétendent pas définir officiellement ces champs.

## 2. Granularité des données et clé métier

Un enregistrement représente **une observation mensuelle de liaison et de service** dans le jeu de données SNCF.

La clé métier est :

```text
(date, service, gare_depart, gare_arrivee)
```

La liaison est orientée : `gare_depart` et `gare_arrivee` ne doivent être ni inversées ni fusionnées en une paire non orientée. La catégorie `service` doit également être conservée. Un même mois et une même paire de gares peuvent apparaître dans plusieurs catégories de service ; il s’agit alors d’observations distinctes. Conservez les valeurs et l’orthographe source de ces champs clés ; les éventuels libellés normalisés de liaison doivent être des champs dérivés.

## 3. Schéma canonique

Les noms canoniques des champs sont les 26 noms courts de l’export JSON SNCF et du schéma actuel de l’audit. Chaque champ est **nullable** dans le contrat partagé, même s’il ne comporte aucune valeur manquante dans un instantané donné. Les comptes et la durée prévue utilisent des entiers logiques ; les moyennes et les pourcentages utilisent des valeurs numériques décimales. Les types physiques Pandas/Polars peuvent différer à condition de préserver ces types logiques et les valeurs manquantes.

Les descriptions et unités accompagnées de la mention « à confirmer » doivent être vérifiées dans le dictionnaire SNCF de référence avant de servir à imposer des corrections ou des plages de validité.

| Nom canonique | Type logique | Sens provisoire | Unité | Nullabilité et réserves sémantiques |
| --- | --- | --- | --- | --- |
| `date` | Chaîne, `YYYY-MM` | Mois de référence de l’observation. | Mois calendaire | Nullable selon le contrat ; une valeur manquante ou mal formée constitue une clé invalide. Ne pas la remplacer par une date source au jour près. |
| `service` | Chaîne | Catégorie de service associée à l’observation. | Aucune | Nullable selon le contrat ; conserver les libellés de catégorie et inclure ce champ dans la clé métier. Les définitions officielles doivent être vérifiées dans le dictionnaire SNCF. |
| `gare_depart` | Chaîne | Libellé de la gare d’origine. | Aucune | Nullable selon le contrat ; conserver l’orthographe source. Ce champ est directionnel et fait partie de la clé. |
| `gare_arrivee` | Chaîne | Libellé de la gare de destination. | Aucune | Nullable selon le contrat ; conserver l’orthographe source. Ce champ est directionnel et fait partie de la clé. |
| `duree_moyenne` | Entier nullable | Durée moyenne prévue du trajet, d’après le nom du champ. | Minutes (définition exacte à confirmer) | Peut valoir zéro dans des cas particuliers ; ne pas traiter zéro comme une valeur nulle. La méthode de calcul et le périmètre doivent être confirmés par la SNCF. |
| `nb_train_prevu` | Compte entier nullable | Nombre de trains/circulations prévus pour le mois, d’après le nom du champ. | Trains | Les valeurs négatives sont incompatibles avec la sémantique d’un compte et doivent être signalées. Zéro est distinct d’une valeur manquante. Confirmer la version de l’horaire prise en compte. |
| `nb_annulation` | Compte entier nullable | Nombre de trains/circulations annulés, d’après le nom du champ. | Trains | Les valeurs négatives sont incompatibles avec la sémantique d’un compte et doivent être signalées. Dans la source observée, le champ peut dépasser `nb_train_prevu` ; ne pas supprimer ni réécrire globalement ces lignes sans confirmer les conventions de comptage SNCF. |
| `commentaire_annulation` | Chaîne nullable | Commentaire source associé aux annulations. | Aucune | Conserver le texte à l’identique. Une valeur nulle et une chaîne vide sont distinctes, sauf règle limitée à l’affichage. |
| `nb_train_depart_retard` | Compte entier nullable | Nombre de trains signalés en retard au départ. | Trains | Les valeurs négatives sont incompatibles avec la sémantique d’un compte et doivent être signalées. Le seuil de retard exact et le périmètre doivent être confirmés par la SNCF. |
| `retard_moyen_depart` | Nombre décimal nullable | Retard moyen pour le sous-ensemble décrit comme en retard au départ, d’après le nom du champ. | Minutes (définition exacte à confirmer) | Selon certaines définitions, les valeurs négatives peuvent représenter une avance ; ne pas les rejeter ni les borner en fonction de leur seul signe. Confirmer la population et la pondération. |
| `retard_moyen_tous_trains_depart` | Nombre décimal nullable | Retard moyen au départ pour la population indiquée comme comprenant tous les trains. | Minutes (définition exacte à confirmer) | La population « tous les trains » et le traitement des annulations et des avances doivent être confirmés par la SNCF. Dans l’attente, conserver les valeurs négatives. |
| `commentaire_retards_depart` | Chaîne nullable | Commentaire source associé aux retards au départ. | Aucune | Conserver le texte source ; une valeur nulle n’équivaut pas à une chaîne vide. |
| `nb_train_retard_arrivee` | Compte entier nullable | Nombre de trains signalés en retard à l’arrivée. | Trains | Les valeurs négatives sont incompatibles avec la sémantique d’un compte et doivent être signalées. Le seuil « officiel » d’arrivée peut dépendre de la durée du trajet ; le vérifier dans le dictionnaire. |
| `retard_moyen_arrivee` | Nombre décimal nullable | Retard moyen à l’arrivée pour le sous-ensemble décrit comme en retard à l’arrivée. | Minutes (définition exacte à confirmer) | Ne pas borner automatiquement les valeurs négatives ; vérifier d’abord la définition et la population admissible. |
| `retard_moyen_tous_trains_arrivee` | Nombre décimal nullable | Retard moyen à l’arrivée pour la population indiquée comme comprenant tous les trains. | Minutes (définition exacte à confirmer) | La population « tous les trains » et la pondération doivent être confirmées par la SNCF. Les valeurs très négatives sont des signaux diagnostiques, pas une preuve de la valeur de remplacement correcte. |
| `commentaires_retard_arrivee` | Chaîne nullable | Commentaire source associé aux retards à l’arrivée. | Aucune | Conserver le texte source ; les valeurs manquantes sont nombreuses dans l’instantané vérifié. Une valeur nulle n’est ni un zéro observé ni une explication vide. |
| `nb_train_retard_sup_15` | Compte entier nullable | Nombre de trains dépassant le seuil de 15 minutes, d’après le nom du champ. | Trains | La description du jeu de données limite l’application aux liaisons en concurrence avec l’avion. Le jeu ne contient pas de flag d’applicabilité ; ne pas imposer universellement `sup_15 >= sup_30`. Confirmer le périmètre exact auprès de la SNCF. |
| `retard_moyen_trains_retard_sup15` | Nombre décimal nullable | Retard moyen du groupe dépassant 15 minutes, d’après le nom du champ. | Minutes (définition exacte à confirmer) | La limitation d’applicabilité du seuil >15 s’applique également ici. Une valeur négative peut découler de la définition publiée ou d’une incohérence de la source ; ne pas la modifier automatiquement. |
| `nb_train_retard_sup_30` | Compte entier nullable | Nombre de trains dépassant le seuil de 30 minutes, d’après le nom du champ. | Trains | Les valeurs négatives sont incompatibles avec la sémantique d’un compte et doivent être signalées, sans être remplacées par zéro faute de preuve. La relation observée au T1 2025 avec `sup_60` nécessite un examen des versions et définitions source. |
| `nb_train_retard_sup_60` | Compte entier nullable | Nombre de trains dépassant le seuil de 60 minutes, d’après le nom du champ. | Trains | Les valeurs négatives sont incompatibles avec la sémantique d’un compte et doivent être signalées. Ne pas écraser `sup_30` ni en déduire la valeur à partir de ce champ. Confirmer les définitions du seuil et de la population. |
| `prct_cause_externe` | Nombre décimal nullable | Pourcentage attribué aux causes externes, d’après le nom du champ. | Points de pourcentage, échelle attendue 0–100 (définition à confirmer) | Une valeur nulle signifie inconnue/non renseignée, et non zéro. Vérifier diagnostiquement les bornes et le total ; ne pas remplacer les causes manquantes par zéro. |
| `prct_cause_infra` | Nombre décimal nullable | Pourcentage attribué aux causes liées à l’infrastructure. | Points de pourcentage, échelle attendue 0–100 (définition à confirmer) | Une valeur nulle signifie inconnue/non renseignée, et non zéro. Les limites exactes de la catégorie et le dénominateur doivent être confirmés par la SNCF. |
| `prct_cause_gestion_trafic` | Nombre décimal nullable | Pourcentage attribué aux causes liées à la gestion du trafic. | Points de pourcentage, échelle attendue 0–100 (définition à confirmer) | Une valeur nulle signifie inconnue/non renseignée, et non zéro. Les limites exactes de la catégorie et le dénominateur doivent être confirmés par la SNCF. |
| `prct_cause_materiel_roulant` | Nombre décimal nullable | Pourcentage attribué aux causes liées au matériel roulant. | Points de pourcentage, échelle attendue 0–100 (définition à confirmer) | Une valeur nulle signifie inconnue/non renseignée, et non zéro. Les limites exactes de la catégorie et le dénominateur doivent être confirmés par la SNCF. |
| `prct_cause_gestion_gare` | Nombre décimal nullable | Pourcentage attribué aux causes liées à la gestion des gares, d’après le nom du champ. | Points de pourcentage, échelle attendue 0–100 (définition à confirmer) | Une valeur nulle signifie inconnue/non renseignée, et non zéro. Les causes incluses précisément et le dénominateur doivent être confirmés par la SNCF. |
| `prct_cause_prise_en_charge_voyageurs` | Nombre décimal nullable | Pourcentage attribué à la prise en charge des voyageurs, d’après le nom du champ. | Points de pourcentage, échelle attendue 0–100 (définition à confirmer) | Une valeur nulle signifie inconnue/non renseignée, et non zéro. Les causes incluses précisément et le dénominateur doivent être confirmés par la SNCF. |

### Groupes de champs et types logiques attendus

- **Identifiants et catégorie :** `date`, `service`, `gare_depart`, `gare_arrivee` sont des chaînes de caractères.
- **Durée prévue et comptes :** `duree_moyenne`, `nb_train_prevu`, `nb_annulation`, `nb_train_depart_retard`, `nb_train_retard_arrivee`, `nb_train_retard_sup_15`, `nb_train_retard_sup_30` et `nb_train_retard_sup_60` sont des entiers nullables. Les comptes doivent être des nombres entiers ; les chaînes numériques invalides et les valeurs fractionnaires doivent être signalées.
- **Moyennes de retard :** `retard_moyen_depart`, `retard_moyen_tous_trains_depart`, `retard_moyen_arrivee`, `retard_moyen_tous_trains_arrivee` et `retard_moyen_trains_retard_sup15` sont des nombres décimaux nullables, exprimés en minutes dans l’attente de la confirmation des définitions SNCF exactes.
- **Pourcentages de causes :** les six champs `prct_cause_*` sont des nombres décimaux nullables exprimés en points de pourcentage, et non en proportions de 0 à 1. Confirmer leur dénominateur précis et la définition des catégories dans le dictionnaire officiel.
- **Commentaires :** les trois champs de commentaire sont des chaînes nullables.

## 4. Conventions de date

`date` doit rester une chaîne représentant un mois au format `YYYY-MM`, par exemple `2025-01`.

Vérifiez le format et la validité du mois : sa composante doit être comprise entre `01` et `12`. Ne convertissez pas silencieusement le champ contractuel en date au jour près ou en horodatage avec fuseau. Un consommateur peut dériver une colonne datetime distincte correspondant au premier jour du mois pour les graphiques ou les séries temporelles, tout en conservant la valeur `date` d’origine et la granularité.

## 5. Valeurs manquantes et gestion des types

1. **Une valeur nulle n’est pas zéro.** Conservez les valeurs absentes sous forme de null/NA. Un compte ou un pourcentage mesuré à zéro est une valeur observée et doit rester distinct d’une donnée inconnue ou non renseignée.
2. **Aucun remplissage silencieux.** Ne remplacez pas les valeurs nulles par zéro pour permettre un calcul. Un calcul nécessitant des entrées complètes doit définir son propre masque d’admissibilité et indiquer le nombre de lignes exclues.
3. **Les types logiques sont indépendants des bibliothèques.** Utilisez les types nullable chaîne, entier, nombre décimal et chaîne de commentaire spécifiés ci-dessus. Pandas peut employer des types d’extension nullables ; Polars peut utiliser ses types natifs. La représentation sur disque ou le type physique du DataFrame ne modifie pas le contrat logique.
4. **Les erreurs d’analyse sont visibles.** Lors de la lecture d’un CSV ou d’un autre texte typé, analysez les champs numériques selon leur groupe. Toute valeur non vide impossible à analyser, ou toute valeur fractionnaire dans un champ de compte, doit être enregistrée comme échec d’analyse/de validation avec le champ et la ligne concernés. Ne la laissez pas silencieusement sous forme de texte et ne la convertissez pas en zéro. Conservez la représentation d’origine dans la source immuable afin de pouvoir retrouver l’anomalie.
5. **Les colonnes composées uniquement de valeurs manquantes conservent un type logique.** Dans l’instantané vérifié de 12 907 enregistrements, `commentaire_annulation` et `commentaire_retards_depart` ne contiennent que des valeurs manquantes (JSON `null`, 100 % chacun), tandis que `commentaires_retard_arrivee` contient 12 209 valeurs manquantes (JSON `null`, 94,59 %) et 698 valeurs renseignées. Selon ce contrat, les deux premiers champs restent des chaînes nullables, même si Polars leur attribue le type physique `Null` dans cet instantané. Ne supprimez pas ces colonnes et ne considérez pas ces valeurs manquantes comme la preuve qu’elles seront toujours inutilisées.

## 6. Qualité des données et traitement des anomalies

L’export brut constitue la référence. Les constats de l’audit sont des flags à examiner et peuvent servir à définir l’admissibilité propre à une métrique ; à eux seuls, ils ne justifient pas de réécrire les valeurs source.

### Règles de validation et règles de correction

Les **règles de validation** peuvent signaler qu’un champ est manquant, qu’il a un type inattendu, qu’il ne respecte pas une contrainte de format ou de logique, ou qu’il participe à une relation suspecte. Un résultat de validation doit indiquer le prédicat, les champs et lignes concernés ainsi que leur nombre, sans modifier l’enregistrement.

Les **règles de correction** modifient une valeur, suppriment une ligne ou remplacent une représentation source. N’en appliquez que si elles reposent sur une définition faisant autorité ou sur une décision documentée et examinée. Conservez la valeur d’origine, le motif de correction, la règle et sa version, ainsi qu’un moyen de relier la ligne de sortie à sa source brute.

La politique d’investigation suivante s’applique :

 - Conservez le JSON d’origine comme artefact source immuable et préservez les valeurs observées dans toutes les données dérivées.
 - Ajoutez des flags diagnostiques ou des métadonnées qualité distinctes au lieu de supprimer automatiquement les lignes suspectes.
 - Ne remplacez pas les comptes négatifs par zéro sans preuve provenant de la source. Ces valeurs contredisent la sémantique d’un compte et doivent être signalées pour les calculs fondés sur des comptes ; la valeur de remplacement correcte est inconnue.
 - N’imposez pas `nb_train_retard_sup_30 >= nb_train_retard_sup_60`. Le motif observé au T1 2025 constitue un signal diagnostique fort, mais ne permet pas d’établir les valeurs corrigées de `sup_30`.
 - N’imposez pas automatiquement `nb_train_retard_sup_15 >= nb_train_retard_sup_30`. Le champ >15 ne s’applique qu’à un ensemble limité de liaisons et l’export ne contient aucun champ indiquant les liaisons admissibles.
 - Ne supprimez pas globalement les enregistrements où `nb_annulation > nb_train_prevu`. Leur interprétation exacte dépend des horaires SNCF et des conventions de comptage des annulations.
 - Ne bornez pas automatiquement les retards moyens négatifs. Une circulation en avance peut être représentée par une valeur négative ; les définitions et populations exactes doivent être confirmées.
 - Pour les calculs, définissez des conditions d’admissibilité explicites et propres à chaque métrique (par exemple, un dénominateur positif) et indiquez les lignes exclues. Ces exclusions ne doivent pas supprimer la ligne source du jeu de données partagé.

## 7. Prétraitement partagé et transformations propres aux modules

| Couche | Responsabilité selon ce contrat |
| --- | --- |
| Ingestion | Récupérer l’export source et préserver les noms de champs, les valeurs et les valeurs nulles JSON. Enregistrer le JSON téléchargé sans modification ETL. |
| Audit | Examiner le schéma, les valeurs manquantes, les doublons, les types et les anomalies logiques. Émettre des constats ou des flags sans modifier les enregistrements source. |
| Nettoyage | Appliquer uniquement des règles de correction confirmées et documentées. Préserver les valeurs brutes et la traçabilité des lignes ; rendre les changements reproductibles et vérifiables. Le présent document n’autorise à lui seul aucune règle de ce type. |
| Prétraitement | Fournir une représentation typée et réutilisable conforme au schéma canonique, à la convention de date et à la politique de valeurs nulles. Limiter le prétraitement partagé à l’analyse, à la validation des types et à la traçabilité. |
| EDA | Choisir les définitions du numérateur, les populations admissibles et les dénominateurs propres à l’analyse ; consigner les exclusions et les mesures dérivées avec l’analyse. |
| Analyse de graphes | Choisir l’inclusion des arêtes, la représentation du sens, la fenêtre d’agrégation, les poids des arêtes et le traitement des mesures manquantes ou signalées. Préserver le sens des liaisons source, sauf si une vue non orientée est explicitement nécessaire. |
| ML | Définir la cible, les variables prédictives, les fenêtres temporelles des caractéristiques, les partitions entraînement/validation/test et les contrôles de fuite de données. Garder les caractéristiques du modèle propres au flux de modélisation. |

Le prétraitement partagé ne doit pas absorber les définitions de taux propres à l’EDA, l’ingénierie des arêtes de graphe ni les cibles/caractéristiques du ML. Ces choix répondent à des questions propres à chaque module et peuvent s’appuyer sur des populations admissibles différentes.

## 8. Stockage et compatibilité

- **Source brute :** conservez `data/raw/regularite-mensuelle-tgv-aqst.json` comme tableau JSON immuable téléchargé depuis l’export SNCF vérifié. Ne le réécrivez pas pendant le nettoyage ou le prétraitement.
- **Schéma logique :** utilisez les 26 noms de champs courts canoniques de la section 3 dans les sorties typées et les API partagées. Évitez de créer des noms de champs source alternatifs ; les correspondances de compatibilité doivent rester aux interfaces d’entrée/sortie.
- **Compatibilité avec l’EDA historique :** le notebook EDA examiné lit un CSV séparé par des points-virgules, encodé en UTF-8-SIG et doté d’en-têtes d’affichage français, puis associe ces en-têtes aux noms courts canoniques. Si cette entrée historique est conservée, fournissez un export reproductible avec `;`, UTF-8-SIG et les en-têtes français existants, ou gardez l’adaptateur Pandas du notebook pour faire la correspondance. Ne rendez pas le contrat canonique dépendant de ce format historique.
- **Pandas et Polars :** permettez aux adaptateurs de construire le même schéma logique dans chaque bibliothèque. Aucune migration de bibliothèque n’est nécessaire. Conservez l’interface Pandas du module qualité si elle reste utile ; l’audit actuel peut continuer à utiliser Polars.
- **Parquet :** Parquet pourra être envisagé ultérieurement si l’équipe s’accorde sur les métadonnées de schéma et le moteur/la dépendance nécessaires. Il n’est requis ni par ce contrat ni par la migration actuelle.
- **Sérialisation des valeurs nulles :** documentez le codage des valeurs nulles dans tout CSV dérivé. Évitez un codage qui rendrait un zéro réel ou un commentaire vide indiscernable d’une donnée manquante.

## 9. Versionnement et migration

Ce document propose une version simple du contrat, indépendante de la version de publication du jeu source. Indiquez la version du contrat dans la documentation ou les métadonnées des artefacts ; ne l’ajoutez pas comme colonne source SNCF fictive.

Séquence de migration recommandée :

1. Conservez le JSON brut sans modification et identifiez-le par l’instantané/la date source ou par une empreinte lorsque la reproductibilité l’exige.
2. Adoptez les 26 noms canoniques et leurs types logiques aux interfaces des modules avant de modifier l’implémentation interne d’un consommateur.
3. Implémentez au besoin des chargeurs/adaptateurs typés pour Pandas et Polars. Signalez explicitement les erreurs d’analyse et préservez les valeurs nulles.
4. Préservez l’interface CSV historique de l’EDA pendant la transition, au moyen d’un export de compatibilité (`;`, UTF-8-SIG, en-têtes français) ou d’un petit adaptateur de chargement/d’en-têtes.
5. Exécutez les anciens et nouveaux chargeurs en parallèle. Comparez le nombre de lignes, la couverture des clés et des dates, les nombres de valeurs nulles, ainsi que les principaux taux et synthèses de liaisons de l’EDA avant de basculer ce consommateur. Pour les futurs consommateurs Graph/ML, comparez selon le cas la couverture/pondération des arêtes ou les populations de cibles/caractéristiques.
6. Basculez les consommateurs un par un après examen ; n’imposez pas de migration coordonnée de bibliothèque. Gardez localement les choix d’admissibilité et de caractéristiques propres à chaque module.
7. Documentez les futures évolutions du schéma en indiquant la version du contrat, les champs/types/sémantiques modifiés, l’impact sur la compatibilité et les correspondances de migration éventuelles. Ne détournez jamais silencieusement le sens d’un nom de champ existant.

## 10. Questions sémantiques en suspens

Les points suivants doivent être confirmés dans le dictionnaire SNCF de référence avant de pouvoir fonder des règles de correction strictes :

- La population exacte, la méthode de calcul et la pondération de chaque champ `retard_moyen_*`, en particulier « tous trains » et la mesure conditionnelle >15.
- Les définitions exactes des seuils et des périmètres d’application de `nb_train_depart_retard`, `nb_train_retard_arrivee` et `nb_train_retard_sup_15`.
- La raison de l’inversion observée entre `nb_train_retard_sup_30` et `nb_train_retard_sup_60` au T1 2025, et l’éventuelle évolution de la définition du champ ou du processus source à cette période.
- La possibilité que `nb_annulation` se rapporte à un horaire antérieur, tandis que `nb_train_prevu` reflète un horaire ultérieur ou actuel, ce qui pourrait expliquer des comptes prévus nuls associés à des annulations positives.
- La définition exacte de la durée pour `duree_moyenne` et le dénominateur/les limites des catégories des six pourcentages de causes.
- La représentation attendue des retards moyens négatifs et le sens SNCF des valeurs négatives de très grande amplitude.

Tant que ces questions ne sont pas résolues, elles restent des incertitudes documentées. Ce contrat n’affirme aucun lien de causalité, ne prescrit aucune valeur de remplacement et ne prétend pas que l’instantané actuel représente les futurs exports.
