"""Download and save the complete SNCF raw regularity dataset."""

from projet_kit_data.ingestion.sncf_api import fetch_raw_data, save_raw_data


def main() -> None:
    """Fetch SNCF records, save them locally, and report the result."""
    records = fetch_raw_data()
    output_path = save_raw_data(records)
    print(f"Downloaded {len(records)} records.")
    print(f"Saved raw data to: {output_path}")


if __name__ == "__main__":
    main()
