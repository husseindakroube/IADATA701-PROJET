# CI et déploiement Streamlit Community Cloud

## Répartition des responsabilités

GitHub Actions (`.github/workflows/ci.yml`) vérifie la qualité du projet.
Streamlit Community Cloud héberge l'application et suit la branche configurée.
Le workflow ne construit plus d'image Docker, ne publie plus sur GHCR et ne
déploie plus par SSH. Les fichiers Docker et les scripts SSH existants restent
disponibles comme alternative manuelle ; la CI ne les exécute pas.

## Contrôles automatiques

Chaque push sur une branche, Pull Request vers `main` ou lancement manuel exécute :

1. Installation avec uv 0.12.13, `.python-version` et `uv.lock` (`--locked --dev`).
2. Ruff : style (`E`, `W`), erreurs (`F`), docstrings publiques (`D1`) et formatage.
   Les textes longs sont exemptés de `E501`, les tests de `D1`.
3. Compilation Python et construction Sphinx avec avertissements bloquants.
4. Génération des logs simulés, sans données d'utilisateurs réels.
5. Suite pytest complète, dont les six pages, la carte et les flèches du graphe.
   La couverture de `app/` et `src/projet_kit_data/` doit atteindre **90,1 %**.

Les rapports JUnit, couverture XML/HTML et logs d'exemple sont conservés dans
`test-reports-<commit>`. La documentation HTML est dans `sphinx-html-<commit>`.
Les fichiers disponibles sont conservés 14 jours, même après un échec.

## Protéger la branche publiée

Parcours prévu : **branche de développement → CI → Pull Request vers main →
fusion validée → actualisation de l'application**.

Dans les paramètres GitHub, configurer une protection ou un ruleset actif pour `main` :

- Exiger une Pull Request avant fusion.
- Exiger le contrôle **Code, tests et couverture**, après sa première exécution.
- Exiger une branche à jour et limiter les possibilités de contournement.
- Retirer une éventuelle exigence de l'ancien contrôle Docker, devenu obsolète.

Cette protection est un réglage GitHub : le fichier YAML ne la crée pas.
Community Cloud n'attend pas la réussite de GitHub Actions pour se mettre à jour.
Un push direct sur la branche publiée peut donc déployer du code non validé si
les règles du dépôt permettent de contourner la CI.

## Première mise en ligne

1. Fusionner la version à publier dans `main` après réussite de la CI.
2. Ouvrir [Streamlit Community Cloud](https://share.streamlit.io/) avec un compte
   disposant des droits nécessaires sur le dépôt.
3. Choisir **Create app**, puis **Yup, I have an app**.
4. Renseigner :

   | Champ | Valeur |
   |---|---|
   | Repository | `husseindakroube/IADATA701-PROJET` |
   | Branch | `main` |
   | Main file path | `app/app.py` |
   | Python version (Advanced settings) | `3.12` |

5. Choisir éventuellement un sous-domaine disponible, puis **Deploy**.
   Les dépendances sont fournies par `uv.lock` à la racine du dépôt.
6. Vérifier les six pages depuis une fenêtre privée, notamment carte, filtres,
   comparaison et prédictions. Ajouter l'URL réelle au README.

Si une application de test suit déjà `Test_Shihao`, elle continue de suivre cette
branche : modifier le YAML ne la bascule pas vers `main`. Créer la publication
finale depuis `main` après fusion et vérifier l'URL avant de la transmettre.

Les secrets `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PORT`, `DEPLOY_SSH_KEY`,
`DEPLOY_KNOWN_HOSTS` et la variable `DEPLOY_ENABLED` ne sont plus utilisés par ce
workflow. Aucune suppression des paramètres distants n'est effectuée ici.

## Vérification locale et limites

```bash
uv sync --locked --dev
uv run --locked ruff check app src scripts tests docs/conf.py
uv run --locked ruff format --check app src scripts tests docs/conf.py
uv run --locked pytest -q --cov=src/projet_kit_data --cov=app --cov-fail-under=90.1
uv run --locked sphinx-build -W --keep-going -b html docs docs/_build/html
```

Dernière validation complète du code : 172 tests réussis, couverture 91,95 %.
Une validation locale ne prouve ni la réussite d'un run GitHub Linux ni la mise
en ligne effective. Le compte Community Cloud, la protection de `main` et
l'accès à l'URL publique restent à vérifier séparément.

Références : [déployer sur Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
[gestion des dépendances](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
