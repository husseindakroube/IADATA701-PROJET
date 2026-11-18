'Télécharge et enregistre l’ensemble des données brutes de régularité SNCF.'

from projet_kit_data.ingestion.sncf_api import fetch_raw_data, save_raw_data


def main() -> None:
    'Récupère les observations SNCF, les enregistre localement et indique le résultat.'
    records = fetch_raw_data()
    output_path = save_raw_data(records)
    print(f"Téléchargement effectué : {len(records)} observations.")
    print(f"Données brutes enregistrées dans : {output_path}")


if __name__ == "__main__":
    main()
