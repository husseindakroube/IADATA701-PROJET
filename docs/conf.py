"""Configuration Sphinx pour le guide et la référence Python de TGVision."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]
project = "TGVision"
author = "Équipe IADATA701"
language = "fr"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"]
html_theme = "alabaster"
exclude_patterns = ["_build"]
autodoc_member_order = "bysource"
autodoc_typehints = "description"
