"""Télécharger et enregistrer le jeu complet de régularité SNCF brut."""

from projet_kit_data.ingestion.sncf_api import fetch_raw_data, save_raw_data


def main() -> None:
    """Récupérer les données SNCF, les enregistrer localement et afficher le résultat."""
    records = fetch_raw_data()
    output_path = save_raw_data(records)
    print(f"{len(records)} enregistrements téléchargés.")
    print(f"Données brutes enregistrées dans : {output_path}")


if __name__ == "__main__":
    main()
