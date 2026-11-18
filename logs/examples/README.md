# Journaux de démonstration

`debug.log` et `error.log` sont produits par le vrai système de journalisation,
avec des actions et incidents **simulés**, sans session réelle ni données privées.
Les lignes `DEMONSTRATION` ne représentent pas des pannes du site.

- `debug.log` reçoit DEBUG, INFO, WARNING, ERROR et CRITICAL.
- `error.log` reçoit uniquement ERROR et CRITICAL.
- La répétition de `page_view` n'apparaît qu'une fois ; chaque demande de
  téléchargement reste enregistrée.

Pour reproduire les fichiers dans un nouveau dossier :

```bash
uv run --locked python scripts/deployment/generate_log_examples.py reports/log-examples
```

Le générateur refuse d'écraser des fichiers existants ou d'utiliser `logs/`
directement. Les journaux réels restent locaux et ignorés par Git. La CI publie
un nouvel exemple dans ses rapports à chaque exécution.
