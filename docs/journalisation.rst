Journalisation
======================

Configuration
---------------------

``configure_logging`` crée ``logs/debug.log`` (DEBUG et plus) et
``logs/error.log`` (ERROR et CRITICAL). Chaque fichier tourne à 5 Mio avec
trois sauvegardes. La configuration est réutilisée lors des reruns Streamlit.
Les erreurs de page et de lecture incluent une trace d'exception.

Actions utilisateur
---------------------------

Les actions sont écrites par ``projet_kit_data.activity`` avec une session
aléatoire et des détails JSON : page, filtres, liaison, comparaison, gare,
cluster, modèle et demande de téléchargement. Aucun nom, email ou adresse IP
n'est ajouté par ce logger. ``log_selection`` évite les répétitions identiques ;
``log_action`` conserve chaque action explicite. Les onglets masqués sont aussi
calculés : une sélection enregistrée n'atteste pas qu'un onglet a été vu.

Livraison et exploitation
---------------------------------

Les journaux réels ne sont pas des fichiers à publier. ``logs/examples/`` contient
deux exemples contrôlés, générés avec des données fictives. La CI régénère ces
exemples dans ``reports/log-examples/``. Les tests vérifient les niveaux, la
rotation, les exceptions, la déduplication et l'absence d'écrasement des exemples.

Les avertissements internes de Streamlit restent dans la console ; ils ne sont
pas automatiquement copiés dans ``error.log``. Le dossier ``logs/`` doit être
accessible en écriture. Sans volume dédié, ses fichiers dans Docker disparaissent
au remplacement du conteneur. Deux instances locales doivent éviter de partager
les mêmes fichiers lors d'une rotation simultanée.
