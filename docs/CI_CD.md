# CI/CD — TGVision

## Déroulement automatique

Le processus est défini dans `.github/workflows/ci.yml`.

1. Un envoi sur toute branche, une demande de fusion vers `main` ou un lancement manuel déclenche les vérifications.
2. L’environnement est installé à partir de `.python-version` et `uv.lock`, avec uv 0.12.13.
3. Ruff vérifie le style (`E`, `W`), les erreurs (`F`), les docstrings publiques (`D1`) et le formatage. Les URL et textes longs sont exemptés de `E501` ; les tests sont exemptés de `D1`, mais restent formatés et analysés. Python vérifie la syntaxe. Sphinx construit le guide et la référence API en traitant ses avertissements comme des erreurs. Pytest exécute tous les tests, dont les six pages Streamlit. La couverture de `app/` et `src/projet_kit_data/` doit atteindre **90,1 %**, sans réduire le périmètre mesuré.
4. Les rapports JUnit, la couverture XML/HTML, les exemples de logs simulés et la documentation HTML Sphinx disponibles sont conservés pendant 14 jours, même en cas d’échec. Les exemples sont générés dans `reports/log-examples/` et ne contiennent aucune session réelle. Le site Sphinx figure dans l'artefact `sphinx-html-<commit>`.
5. Après validation, une image Docker `linux/amd64` est construite et un conteneur est réellement démarré pour contrôler son état de santé. Un second conteneur sans réseau exécute `scripts/deployment/smoke_app.py` : les six pages doivent se charger avec les dépendances et ressources de production avant publication.
6. Seuls les envois ou lancements manuels sur `main` publient l’image dans GHCR. Une demande de fusion ne déclenche ni connexion au registre, ni publication, ni déploiement.
7. Lorsque le déploiement est activé, l’image testée et publiée est déployée avec son empreinte SHA-256 immuable. L’étiquette `latest` ne sert pas de référence en production.

## Configuration initiale de GitHub

Créer l’environnement **production** dans les paramètres du dépôt, rubrique Environnements. Y configurer les secrets suivants :

| Secret | Contenu |
|---|---|
| `DEPLOY_HOST` | Nom de domaine ou adresse IPv4 du serveur Linux, sans protocole |
| `DEPLOY_USER` | Compte SSH dédié autorisé à utiliser Docker |
| `DEPLOY_PORT` | Port SSH facultatif ; 22 par défaut |
| `DEPLOY_SSH_KEY` | Clé privée SSH complète ; la clé publique correspondante doit déjà être installée sur le serveur |
| `DEPLOY_KNOWN_HOSTS` | Clé publique du serveur vérifiée par un canal fiable ; format `[host]:port` si le port diffère de 22 |

Au niveau du dépôt, dans les variables Actions, définir `DEPLOY_ENABLED=true` pour activer le déploiement. Sans cette variable, les vérifications et la publication depuis `main` continuent, mais le déploiement est ignoré. Ne jamais transmettre la clé privée dans une conversation ni la versionner.

GHCR utilise automatiquement `GITHUB_TOKEN` ; aucun secret supplémentaire de registre n’est nécessaire. Pour réutiliser un paquet GHCR, autoriser les Actions de ce dépôt à le lire et à l’écrire. Si l’organisation interdit la publication de paquets, un administrateur doit adapter les permissions.

L’équipe peut imposer une approbation dans l’environnement production et exiger les vérifications « Code, tests et couverture » et « Construction et vérification de l’image Docker » dans les règles de protection de `main`.

## Préparation du serveur

- Linux **x86-64/amd64**, Python 3, Docker Engine et Compose v2 installé sur le système, avec prise en charge de `up --wait --wait-timeout`. Adapter l’architecture de l’image pour un serveur ARM.
- Le compte SSH doit pouvoir lancer Docker sans demande interactive de sudo. Ces droits sont élevés : utiliser un compte dédié.
- L’exécuteur GitHub doit pouvoir joindre le serveur en SSH, et le serveur doit pouvoir télécharger les images GHCR.
- Les fichiers de déploiement sont placés dans `~/.local/share/tgvision/`. Un verrou empêche les modifications concurrentes.
- L’application écoute uniquement sur `127.0.0.1:8501` du serveur. Un mandataire inverse Nginx ou Caddy doit rediriger les requêtes vers cette adresse et gérer le domaine, TLS et WebSocket. Aucun site public n’est créé automatiquement sans cette configuration.

Le conteneur utilise un compte non privilégié. Il ne lance aucun carnet de calcul et lit les prédictions enregistrées ; la page clusters recalcule la PCA et les ajustements K-Means de la courbe du coude. L’image contient le code, les données, les rapports, les ressources statiques et les carnets sources. Les modèles sérialisés, l’environnement de développement, les résultats des tests et l’ancien GIF d’accueil sont exclus.

## Mise à jour et retour à la version précédente

`deploy.py` valide les entrées, vérifie strictement l’identité SSH et transmet les données de déploiement par l’entrée standard. L’image est téléchargée avant le remplacement du service. Les identifiants GHCR sont conservés dans un dossier temporaire supprimé à la fin. Compose attend un état sain avant de signaler la réussite.

En cas d’échec, les journaux du conteneur sont affichés et l’ancienne configuration Compose et son image sont restaurées ; leur état de santé est à nouveau vérifié. Le processus reste en échec même si la restauration réussit. Si le premier déploiement échoue, le service et sa configuration sont retirés. Après une réussite, `compose.previous.yaml` et `.env.previous` permettent un retour manuel :

```bash
cd ~/.local/share/tgvision
docker compose --project-directory "$PWD" --env-file .env.previous -f compose.previous.yaml up -d --wait --wait-timeout 120
```

Si l’ancienne image est encore présente localement, aucune connexion supplémentaire n’est nécessaire. Sinon, des identifiants GHCR autorisés à lire le paquet sont requis. Cette mise à jour d’une instance unique peut provoquer une brève interruption de service.

## Reproduction locale

```bash
uv sync --locked --dev
uv run --locked pytest -q --cov=src/projet_kit_data --cov=app --cov-fail-under=90.1
docker build -t tgvision:local .
TGVISION_IMAGE=tgvision:local docker compose up -d --wait
```

Sous PowerShell, remplacer la dernière commande par :

```powershell
$env:TGVISION_IMAGE = 'tgvision:local'
docker compose up -d --wait
```

## Périmètre des vérifications

Lors de la configuration initiale, les 147 tests existants réussissaient avec une couverture de 90,19 %. Des tests hors connexion ont ensuite été ajoutés pour les entrées de déploiement et la restauration. Après l’ajout de la journalisation, 166 tests réussissaient localement avec une couverture de 90,43 %.

La capture GitHub fournie montre la réussite des vérifications et de la construction/validation Docker, tandis que le déploiement est ignoré. Aucun accès public à une application déployée n’a été confirmé. Les résultats locaux ne remplacent pas les contrôles Linux effectués par GitHub Actions.

Références : [Actions Docker](https://docs.docker.com/build/ci/github-actions/), [récupération du dépôt](https://github.com/actions/checkout), [publication des rapports](https://github.com/actions/upload-artifact).
