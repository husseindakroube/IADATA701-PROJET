# Intégration et fonctionnalités restantes

Mise à jour du 18 novembre 2026 à partir du projet complémentaire. Seuls les travaux déjà fournis sont intégrés ; aucune nouvelle analyse ni aucun entraînement n'est exécuté.

| Page | Résultats intégrés | Restant ou à vérifier |
|---|---|---|
| Accueil | Design et filtres conservés, compteurs dynamiques | Taux globaux validés, trois découvertes quantifiées, date d'extraction, équipe |
| Qualité | Flags, observations distinctes signalées, manquants, rapports | Dictionnaire complet, mois manquants, comparaison avant/après nettoyage |
| Liaisons/réseau | Séries sources, annulations, causes mensuelles, graphes, centralités | Taux d'arrivée harmonisé, référence comparable, classement avec seuil de volume, carte, associations validées |
| Clusters | Nouveaux labels, profils et résumé, effectifs, durée, taux historique >15 min, figures PCA/coude | PCA interactive, stabilité selon initialisation, noms validés, dénominateurs des causes |
| Prédictions | Naïf et A/B/C/D sur le même test, MAE/RMSE/R², historique par liaison/mois/modèle, MAE par cluster avec effectifs | Erreurs par service, gain relatif explicite, stabilité temporelle, horizon opérationnel et manifeste complets, correspondance des sept anciennes expériences |
| Conclusions | Comparaison dynamique issue des prédictions et limites | Preuves suffisantes sur les associations réseau/ponctualité et stabilité de l'apport prédictif |

## Périmètres et réserves

- ETL : 12 907 observations de 2018-01 à 2026-09, dont 420 avec au moins un flag. Les 12 487 observations sans flag ne définissent pas tous les périmètres.
- Clusters : 65 paires non orientées ; effectifs 4, 18, 24 et 19 pour les groupes 0 à 3. Le notebook 04 utilise 9 414 observations sans flag jusqu'à 2024-05. StandardScaler et KMeans sont appris sur cette période uniquement.
- Le résumé du taux >15 min utilise les cibles valides du pipeline ML avant cette même borne, avec le ratio des sommes (retards / circulations). Son périmètre de qualité diffère de celui des profils. Ce taux ne doit pas être assimilé au taux officiel d'arrivée.
- Les moyennes des causes restent des variables techniques du clustering ; leur dénominateur n'est pas confirmé. Elles ne sont pas présentées comme une composition globale des retards.
- Notebook 05 : entraînement 2019-01 à 2024-05, validation 2024-06 à 2025-06, test 2025-07 à 2026-09 (1 857 lignes communes). Graphe construit sur train pour validation, puis train + validation pour test. Choix du modèle sur la MAE pondérée de validation.
- L'historique utilise les mois antérieurs : évaluation séquentielle et non prévision de tous les mois depuis une seule date. Le code corrige le périmètre d'apprentissage du clustering ; un audit complet de disponibilité et de provenance reste nécessaire.
- Les différences entre A/B/C/D sont faibles. Le naïf a un meilleur R² ; les chiffres 0,4513/0,4595 de la proposition ne décrivent pas ces exports.
- Figures PCA/coude extraites des sorties du nouveau notebook, sans réexécution. Pas de PCA interactive inventée.

## Structure et reproductibilité

Structure de l'équipe conservée : `src/projet_kit_data/`, `data/raw/`, `data/processed/`, `data/reports/`, `models/`, `notebooks/`, `scripts/exploration/`, `scripts/experiments/`, `docs/`, `tests/`. L'interface et les styles restent dans `app/` et `images/`.

Le module `comparaison.py`, son test et les exports 04/05 sont importés avec leurs empreintes dans `docs/integration_manifest.json`. L'application lit les résultats ; elle ne charge pas les fichiers joblib et ne réentraîne pas les modèles. Les données brutes et le projet complémentaire ne sont pas modifiés.

Restent : documentation Sphinx construite, preuve de CI distante et de couverture supérieure à 90 %, lien public fonctionnel, manifeste de génération/version/dépendances par produit. La configuration Docker/SSH existante est conservée (voir `docs/CI_CD.md`), sans nouveau déploiement. Prévisions futures et intervalles absents.

## Vérification locale

162 tests réussis, dont les six pages et les filtres ; couverture app + src : 90,47 %. Métriques comparées aux prédictions, correspondance de A avec la baseline et cohérence labels/profils/résumé vérifiées. Contrôle Ruff et compilation réussis ; 110 empreintes importées conformes. Précision du rapport de couverture fixée à deux décimales pour le seuil 90,1 %. CI distante et déploiement non vérifiés.
