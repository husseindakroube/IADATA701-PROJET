"""Export des caractéristiques du réseau pour la visualisation."""

from pathlib import Path

import pandas as pd

from sncf_rail_insight.graph.centrality import compute_all_graph_features
from sncf_rail_insight.graph.network import build_weighted_railway_graph
from sncf_rail_insight.graph.routes import compute_edge_features
from sncf_rail_insight.preprocessing import prepare_graph_data

DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.csv")
OUTPUT_DIR = Path("data/processed")

START_DATE = "2024-01-01"
END_DATE = "2025-01-01"


def main() -> None:
    """Exporte les nœuds et les arêtes du réseau sur l'année 2024."""
    raw = pd.read_csv(DATA_PATH, sep=";")
    data = prepare_graph_data(raw)

    historical_data = data.loc[
        (data["date"] >= START_DATE)
        & (data["date"] < END_DATE)
    ]

    graph = build_weighted_railway_graph(historical_data)

    nodes = compute_all_graph_features(graph)
    edges = compute_edge_features(graph)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    nodes.to_csv(OUTPUT_DIR / "network_nodes.csv", index=False)
    edges.to_csv(OUTPUT_DIR / "network_edges.csv", index=False)

    print("=== EXPORT DU RESEAU 2024 ===")
    print(f"Période : {START_DATE} -> 2024-12-31")
    print(f"Gares : {graph.number_of_nodes()}")
    print(f"Liaisons : {graph.number_of_edges()}")

    print("\n=== NOEUDS ===")
    print("Dimensions :", nodes.shape)
    print("Colonnes :", nodes.columns.tolist())
    print(nodes.head().to_string(index=False))

    print("\n=== ARETES ===")
    print("Dimensions :", edges.shape)
    print("Colonnes :", edges.columns.tolist())
    print(edges.head().to_string(index=False))

    print(f"\nFichiers enregistrés dans : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
