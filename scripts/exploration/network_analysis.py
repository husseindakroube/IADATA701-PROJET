"""Analyse de la structure et de l'évolution du réseau ferroviaire."""

from pathlib import Path

import pandas as pd

from sncf_rail_insight.graph.network import build_railway_graph
from sncf_rail_insight.preprocessing import prepare_graph_data

DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.csv")

def main() -> None:
    """Décrit le réseau et compare sa structure entre les années."""
    raw = pd.read_csv(DATA_PATH, sep=";")
    data = prepare_graph_data(raw)

    # Graphe global
    global_graph = build_railway_graph(data)

    print("=== RESEAU GLOBAL ===")
    print(f"Gares : {global_graph.number_of_nodes()}")
    print(f"Liaisons orientées : {global_graph.number_of_edges()}")

    # Évolution annuelle
    years = sorted(data["date"].dt.year.unique())
    annual_graphs = {}

    print("\n=== EVOLUTION ANNUELLE ===")

    for year in years:
        year_data = data.loc[data["date"].dt.year == year]
        graph = build_railway_graph(year_data)
        annual_graphs[year] = graph

        print(
            f"{year} : "
            f"{graph.number_of_nodes()} gares | "
            f"{graph.number_of_edges()} liaisons"
        )

    # Comparaison avec le réseau initial
    reference_year = years[0]
    reference = annual_graphs[reference_year]

    print(f"\n=== EVOLUTION PAR RAPPORT A {reference_year} ===")

    for year in years[1:]:
        graph = annual_graphs[year]

        new_stations = set(graph.nodes) - set(reference.nodes)
        new_routes = set(graph.edges) - set(reference.edges)
        missing_routes = set(reference.edges) - set(graph.edges)

        print(
            f"{year} : "
            f"{len(new_stations)} nouvelles gares | "
            f"{len(new_routes)} nouvelles liaisons | "
            f"{len(missing_routes)} liaisons absentes"
        )


if __name__ == "__main__":
    main()
