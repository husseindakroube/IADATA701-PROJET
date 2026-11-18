"""Reconstitue les coordonnées RailInsight depuis le référentiel SNCF.

Usage depuis la racine du dépôt :
    uv run python scripts/reporting/prepare_station_coordinates.py

Source française : data/reference/liste-des-gares.csv (versionner ce CSV).
Les destinations étrangères et quelques points représentatifs sont documentés ici.
Aucune API, aucun géocodage approximatif et aucune connexion réseau nécessaires.
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.csv")
SOURCE_PATH = Path("data/reference/liste-des-gares.csv")
OUTPUT_PATH = Path("data/reference/station_coordinates.csv")

# Correspondances explicites quand les deux jeux de données emploient
# des noms différents. Le choix est fait pour un affichage cartographique.
SNCF_ALIASES = {
    'ANGERS SAINT LAUD': 'Angers-St-Laud',
    'BELLEGARDE (AIN)': 'Bellegarde',
    'LILLE': 'Lille-Europe',
    'MACON LOCHE': 'Mâcon-Loché-TGV',
    'METZ': 'Metz-Ville',
    'MONTPELLIER': 'Montpellier-St-Roch',
    'NANCY': 'Nancy-Ville',
    'PARIS LYON': 'Paris-Gare-de-Lyon',
    'PARIS MONTPARNASSE': 'Paris-Montparnasse-Pasteur',
    'PARIS NORD': 'Paris-Nord',
    'SAINT ETIENNE CHATEAUCREUX': 'St-Étienne-Châteaucreux',
    'STRASBOURG': 'Strasbourg-Ville',
    'VALENCE ALIXAN TGV': 'Valence-TGV',
}

# Coordonnées WGS84 (latitude, longitude, pays, gare représentative, source).
# Ces coordonnées sont des constantes de référence reproductibles.
FOREIGN_STATIONS = {
    'BARCELONA': (41.3788900, 2.1400000, 'ES', 'Barcelona Sants', 'https://en.wikipedia.org/wiki/Barcelona_Sants_railway_station'),
    'FRANCFORT': (50.1069400, 8.6625000, 'DE', 'Frankfurt (Main) Hbf', 'https://en.wikipedia.org/wiki/Frankfurt_(Main)_Hauptbahnhof'),
    'GENEVE': (46.2102170, 6.1424470, 'CH', 'Genève-Cornavin', 'https://en.wikipedia.org/wiki/Gen%C3%A8ve-Cornavin_railway_station'),
    'ITALIE': (45.4847200, 9.1875000, 'IT', 'Milano Porta Garibaldi', 'https://en.wikipedia.org/wiki/Milano_Porta_Garibaldi_railway_station'),
    'LAUSANNE': (46.5168000, 6.6291000, 'CH', 'Lausanne', 'https://en.wikipedia.org/wiki/Lausanne_railway_station'),
    'MADRID': (40.4065000, -3.6893000, 'ES', 'Madrid Atocha', 'https://en.wikipedia.org/wiki/Madrid_Atocha_railway_station'),
    'STUTTGART': (48.7838900, 9.1816700, 'DE', 'Stuttgart Hauptbahnhof', 'https://en.wikipedia.org/wiki/Stuttgart_Hauptbahnhof'),
    'ZURICH': (47.3781690, 8.5401780, 'CH', 'Zürich Hauptbahnhof', 'https://en.wikipedia.org/wiki/Z%C3%BCrich_Hauptbahnhof'),
}

# Ces libellés ne désignent pas nécessairement une gare unique.
# Pour MARNE LA VALLEE, la gare de Chessy n'est pas présente dans le
# référentiel fourni : une position représentative explicite est utilisée.
MANUAL_FRENCH_STATIONS = {
    "MARNE LA VALLEE": (
        48.8704, 2.782799, "Marne-la-Vallée–Chessy",
        "https://en.wikipedia.org/wiki/Marne-la-Vall%C3%A9e%E2%80%93Chessy_station",
    ),
}
REPRESENTATIVE = {"LILLE", "MONTPELLIER", "PARIS MONTPARNASSE", "MARNE LA VALLEE", "ITALIE"}


def normalize(text: str) -> str:
    """Uniformise accents, espaces et ponctuation pour le rapprochement."""
    text = unicodedata.normalize("NFKD", str(text))
    text = text.encode("ascii", errors="ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def main() -> None:
    """Génère un fichier complet, signale les ambiguïtés et refuse les manques."""
    raw = pd.read_csv(RAW_PATH, sep=";")
    stations = sorted(set(raw["Gare de départ"].dropna().str.strip().str.upper())
                      | set(raw["Gare d'arrivée"].dropna().str.strip().str.upper()))

    # Le CSV source possède une BOM dans son premier en-tête.
    sncf = pd.read_csv(SOURCE_PATH, sep=None, engine="python")
    sncf.columns = sncf.columns.str.replace("\ufeff", "", regex=False)
    sncf["key"] = sncf["LIBELLE"].map(normalize)
    sncf["X_WGS84"] = pd.to_numeric(sncf["X_WGS84"], errors="coerce")
    sncf["Y_WGS84"] = pd.to_numeric(sncf["Y_WGS84"], errors="coerce")

    rows = []
    missing = []
    for station in stations:
        if station in FOREIGN_STATIONS:
            lat, lon, country, ref, source = FOREIGN_STATIONS[station]
            precision = ("point représentatif, destination agrégée" if station == "ITALIE"
                         else "gare étrangère représentative")
        elif station in MANUAL_FRENCH_STATIONS:
            lat, lon, ref, source = MANUAL_FRENCH_STATIONS[station]
            country, precision = "FR", "gare française représentative hors référentiel"
        else:
            reference_name = SNCF_ALIASES.get(station, station)
            matches = sncf.loc[
                sncf["key"] == normalize(reference_name)
            ].dropna(subset=["X_WGS84", "Y_WGS84"])
            if matches.empty:
                missing.append(station)
                continue
            # Certaines gares ont plusieurs points SNCF (quais / entrées).
            # On retient le premier enregistrement dans l'ordre du CSV source.
            selected = matches.iloc[0]
            lat = float(selected["Y_WGS84"])
            lon = float(selected["X_WGS84"])
            country, ref = "FR", str(selected["LIBELLE"])
            precision = ("gare représentative, libellé agrégé" if station in REPRESENTATIVE
                         else "point SNCF")
            source = "liste-des-gares.csv (X_WGS84/Y_WGS84)"
            if len(matches) > 1:
                print(f"Plusieurs points SNCF pour {station} : "
                      f"premier point de {ref} sélectionné ({len(matches)} entrées)")

        rows.append({
            "station": station,
            "lat": lat,
            "lon": lon,
            "country": country,
            "reference_station": ref,
            "precision": precision,
            "source": source,
        })

    if missing:
        raise ValueError(f"Gares sans coordonnées : {missing}")

    result = pd.DataFrame(rows)
    if result[["lat", "lon"]].isna().any().any() or len(result) != len(stations):
        raise ValueError("Coordonnées incomplètes ou nombre de gares incorrect.")
    if not result["lat"].between(-90, 90).all() or not result["lon"].between(-180, 180).all():
        raise ValueError("Latitude ou longitude hors limites WGS84.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False, float_format="%.7f")
    print(f"Fichier créé : {OUTPUT_PATH}")
    print(f"{len(result)} destinations, {sum(result['country'] == 'FR')} françaises, "
          f"{sum(result['country'] != 'FR')} étrangères")


if __name__ == "__main__":
    main()