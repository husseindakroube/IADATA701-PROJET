Installation et utilisation
===================================

Environnement
---------------------

Depuis la racine du dépôt, avec Python 3.12 et uv :

.. code-block:: console

   uv sync --locked --dev
   uv run --locked streamlit run app/app.py

Les ressources sont résolues depuis le dépôt. Les fichiers de résultats sont
déjà inclus ; il n'est pas nécessaire de relancer les notebooks pour visiter
l'application. La page clusters calcule une PCA et la courbe du coude ; les
prédictions supervisées sont lues depuis les exports enregistrés.

Parcours de l'application
---------------------------------

* Accueil : problématique, chiffres clés et navigation.
* Qualité : signalements, valeurs manquantes et étapes de préparation.
* Liaisons : carte filtrable, séries mensuelles, comparaison de deux trajets
  et réseau d'une gare. Les flèches rouges partent de la gare centrale,
  les bleues y arrivent ; les couleurs des points identifient les gares.
* Clusters : profils, projection PCA et détail des paires de gares.
* Prédictions : comparaison des modèles et erreurs sur la période de test.
* Conclusions : synthèse des résultats et limites.

Architecture
--------------------

``app/`` contient les pages et composants Streamlit. ``src/projet_kit_data/``
regroupe ingestion, préparation, graphes et modèles. Les fichiers sources et
produits sont dans ``data/raw/`` et ``data/processed/``. Les analyses exploratoires
restent dans ``notebooks/`` ; les scripts reproductibles sont dans ``scripts/``.
Les résultats de graphe utilisent des dataclasses ; ``SNCFAPIError`` distingue
les erreurs d'acquisition des erreurs de validation des données.

Vérification et documentation
-------------------------------------

.. code-block:: console

   uv run --locked ruff check app src scripts tests docs/conf.py
   uv run --locked ruff format --check app src scripts tests docs/conf.py
   uv run --locked pytest --cov=src/projet_kit_data --cov=app --cov-fail-under=90.1
   uv run --locked sphinx-build -W --keep-going -b html docs docs/_build/html

Ouvrir ensuite ``docs/_build/html/index.html``. La CI conserve aussi le site
HTML dans un artefact téléchargeable. Les règles Ruff vérifient les erreurs,
le style et la présence des docstrings publiques. Les tests sont dispensés
des docstrings ; les URL et textes longs ne sont pas coupés par une règle
de longueur, mais le format du code est contrôlé séparément.

Déploiement
-------------------

Le workflow construit l'image Docker, contrôle son état de santé puis charge
les six pages avec les dépendances de production. La publication GHCR est
limitée à ``main``. Le déploiement SSH est facultatif et activé par
``DEPLOY_ENABLED=true`` ; voir ``docs/CI_CD.md`` pour les secrets, les prérequis
serveur et le retour arrière. Aucune URL publique n'est attestée par un test
local ; le lien final doit être ajouté au README après déploiement effectif.
