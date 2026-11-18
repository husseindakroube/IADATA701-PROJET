"""Vérifie les pages avec les seules dépendances de production, sans navigateur."""

from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))


def main() -> None:
    app = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=60).run()
    if app.exception:
        raise RuntimeError(f"Accueil : {app.exception}")
    for page in ["data_quality", "routes_network", "clusters", "predictions", "conclusions"]:
        app.switch_page(f"pages/{page}.py").run()
        if app.exception:
            raise RuntimeError(f"{page} : {app.exception}")
        print(f"Page validée : {page}", flush=True)
    print("Les six pages sont chargées.", flush=True)


if __name__ == "__main__":
    main()
