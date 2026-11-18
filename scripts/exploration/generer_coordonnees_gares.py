"""Genere le fichier des coordonnees GPS des gares utilisees dans le projet.

Les coordonnees sont codees en dur pour garantir la reproductibilite et
eviter une dependance a une API externe. Sources: OpenStreetMap et sites
officiels des gares concernees.
"""

from pathlib import Path

import pandas as pd

COORDONNEES = {
    "AIX EN PROVENCE TGV": (43.4559, 5.3177),
    "ANGERS SAINT LAUD": (47.4642, -0.5580),
    "ANGOULEME": (45.6540, 0.1646),
    "ANNECY": (45.9024, 6.1230),
    "ARRAS": (50.2869, 2.7817),
    "AVIGNON TGV": (43.9219, 4.7867),
    "BARCELONA": (41.3797, 2.1403),
    "BELLEGARDE (AIN)": (46.1097, 5.8229),
    "BESANCON FRANCHE COMTE TGV": (47.3080, 5.9553),
    "BORDEAUX ST JEAN": (44.8260, -0.5559),
    "BREST": (48.3881, -4.4812),
    "CHAMBERY CHALLES LES EAUX": (45.5706, 5.9190),
    "DIJON VILLE": (47.3237, 5.0272),
    "DOUAI": (50.3700, 3.0794),
    "DUNKERQUE": (51.0345, 2.3684),
    "FRANCFORT": (50.1070, 8.6633),
    "GENEVE": (46.2104, 6.1428),
    "GRENOBLE": (45.1912, 5.7140),
    "ITALIE": (45.4854, 9.2039),
    "LA ROCHELLE VILLE": (46.1546, -1.1452),
    "LAUSANNE": (46.5168, 6.6291),
    "LAVAL": (48.0774, -0.7681),
    "LE CREUSOT MONTCEAU MONTCHANIN": (46.7656, 4.5174),
    "LE MANS": (47.9956, 0.1932),
    "LILLE": (50.6366, 3.0712),
    "LYON PART DIEU": (45.7606, 4.8595),
    "MACON LOCHE": (46.3084, 4.7867),
    "MADRID": (40.4064, -3.6916),
    "MARNE LA VALLEE": (48.8731, 2.7805),
    "MARSEILLE ST CHARLES": (43.3025, 5.3805),
    "METZ": (49.1097, 6.1775),
    "MONTPELLIER": (43.6050, 3.8803),
    "MULHOUSE VILLE": (47.7418, 7.3417),
    "NANCY": (48.6898, 6.1731),
    "NANTES": (47.2170, -1.5415),
    "NICE VILLE": (43.7047, 7.2615),
    "NIMES": (43.8325, 4.3657),
    "PARIS EST": (48.8769, 2.3592),
    "PARIS LYON": (48.8443, 2.3736),
    "PARIS MONTPARNASSE": (48.8407, 2.3209),
    "PARIS NORD": (48.8809, 2.3553),
    "PARIS VAUGIRARD": (48.8395, 2.3017),
    "PERPIGNAN": (42.6969, 2.8793),
    "POITIERS": (46.5820, 0.3339),
    "QUIMPER": (47.9966, -4.1109),
    "REIMS": (49.2576, 4.0241),
    "RENNES": (48.1035, -1.6723),
    "SAINT ETIENNE CHATEAUCREUX": (45.4270, 4.3917),
    "ST MALO": (48.6386, -2.0181),
    "ST PIERRE DES CORPS": (47.3861, 0.7281),
    "STRASBOURG": (48.5848, 7.7340),
    "STUTTGART": (48.7838, 9.1818),
    "TOULON": (43.1286, 5.9262),
    "TOULOUSE MATABIAU": (43.6111, 1.4542),
    "TOURCOING": (50.7236, 3.1619),
    "TOURS": (47.3900, 0.6939),
    "VALENCE ALIXAN TGV": (44.9910, 4.9793),
    "VANNES": (47.6547, -2.7589),
    "ZURICH": (47.3781, 8.5403),
}


def main() -> None:
    rows = [{"gare": g, "latitude": lat, "longitude": lon}
            for g, (lat, lon) in COORDONNEES.items()]
    df = pd.DataFrame(rows).sort_values("gare").reset_index(drop=True)
    sortie = Path(__file__).resolve().parents[2] / "data" / "raw" / "coordonnees_gares.csv"
    df.to_csv(sortie, index=False)
    print(f"Ecrit {len(df)} gares dans {sortie}")


if __name__ == "__main__":
    main()
