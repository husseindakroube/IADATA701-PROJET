## Installation et lancement de l'application

### Prérequis

- Python 3.12 ou version compatible avec le projet
- uv, pour la gestion des dépendances Python
- Git

### 1. Cloner le dépôt GitHub

```bash
git clone [<URL_DU_REPOSITORY>](https://github.com/husseindakroube/IADATA701-PROJET.git)
cd IADATA701-PROJET
```

### 2. Installer les dépendances

Le projet utilise **uv** pour gérer l'environnement Python et les dépendances.

```bash
uv sync
```

### 3. Lancer l'application Streamlit

Depuis la racine du projet, exécuter :

```bash
uv run python -m streamlit run app/main.py
```

### 4. Accéder à l'application

Une fois le serveur démarré, ouvrir un navigateur à l'adresse suivante :

http://localhost:8501

### 5. Arrêter l'application

Pour arrêter le serveur Streamlit, appuyer sur `Ctrl + C` dans le terminal.

### Remarque pour Windows

Sur certains environnements Windows, l'exécution directe de `streamlit.exe` peut être bloquée par une politique de sécurité.

L'utilisation de `python -m streamlit` permet de lancer Streamlit via le module Python, sans exécuter directement ce fichier.
