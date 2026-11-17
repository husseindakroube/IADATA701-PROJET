"""Create descriptive network and outcome charts as reusable PNG files."""

from __future__ import annotations

import math
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import polars as pl

GRAPH_DIR = Path("data/processed/graph")
DEFAULT_RESEARCH_PATH = Path("data/processed/research_dataset.parquet")
DEFAULT_NODE_METRICS_PATH = GRAPH_DIR / "node_metrics.parquet"
DEFAULT_EDGE_METRICS_PATH = GRAPH_DIR / "edge_metrics.parquet"
DEFAULT_NODES_PATH = GRAPH_DIR / "nodes.parquet"
DEFAULT_EDGES_PATH = GRAPH_DIR / "edges.parquet"
DEFAULT_OUTPUT_DIR = GRAPH_DIR / "visualizations"
SERVICE_COLORS = {"National": "#1769aa", "International": "#d95f02"}
SERVICE_ORDER = ("National", "International")


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(missing)}")


def _finish(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _component_layout(graph: nx.DiGraph) -> dict[str, np.ndarray]:
    """Lay out weak components independently in a compact grid."""
    components = sorted(nx.weakly_connected_components(graph), key=len, reverse=True)
    columns = (
        len(components)
        if len(components) <= 3
        else math.ceil(math.sqrt(len(components)))
    )
    rows = math.ceil(len(components) / columns)
    positions: dict[str, np.ndarray] = {}
    for index, component in enumerate(components):
        subgraph = graph.subgraph(component).to_undirected()
        local = (
            nx.kamada_kawai_layout(subgraph)
            if len(subgraph) > 2
            else nx.spring_layout(subgraph, seed=42)
        )
        values = np.array(list(local.values()), dtype=float)
        span = np.ptp(values, axis=0)
        span[span == 0] = 1.0
        normalized = {
            node: (point - values.min(axis=0)) / span - 0.5
            for node, point in local.items()
        }
        row, column = divmod(index, columns)
        center = np.array([column - (columns - 1) / 2, (rows - 1) / 2 - row])
        for node, point in normalized.items():
            positions[node] = center + point * 0.78
    return positions


def _network_chart(
    service: str,
    nodes: pl.DataFrame,
    edges: pl.DataFrame,
    overall_metrics: pl.DataFrame,
    output_path: Path,
) -> None:
    service_edges = edges.filter(pl.col("service") == service)
    graph = nx.DiGraph()
    graph.add_edges_from(service_edges.select("source", "target").iter_rows())
    values = overall_metrics.filter(pl.col("service") == service)
    graph.add_nodes_from(values["node_id"].to_list())
    metric = dict(
        zip(values["node_id"].to_list(), values["betweenness_centrality"].to_list())
    )
    labels = dict(zip(nodes["node_id"].to_list(), nodes["station_name"].to_list()))
    layout = (
        _component_layout(graph)
        if service == "International"
        else nx.kamada_kawai_layout(graph.to_undirected())
    )
    node_sizes = [480 + 1900 * metric.get(node, 0.0) for node in graph]
    top_labels = [
        node
        for node, _ in sorted(metric.items(), key=lambda item: item[1], reverse=True)[
            :5
        ]
        if node in graph
    ]
    fig, axis = plt.subplots(figsize=(14, 10) if service == "National" else (12, 8))

    for source, target in graph.edges:
        reciprocal = graph.has_edge(target, source)
        if reciprocal:
            radius = 0.17 if str(source) < str(target) else -0.17
        else:
            radius = 0.04
        nx.draw_networkx_edges(
            graph,
            layout,
            edgelist=[(source, target)],
            ax=axis,
            edge_color="#697586",
            width=1.15,
            alpha=0.68,
            arrows=True,
            arrowsize=14,
            connectionstyle=f"arc3,rad={radius}",
            min_source_margin=10,
            min_target_margin=12,
        )
    nx.draw_networkx_nodes(
        graph,
        layout,
        ax=axis,
        node_size=node_sizes,
        node_color=SERVICE_COLORS.get(service, "#4c78a8"),
        alpha=0.92,
        linewidths=0.8,
        edgecolors="white",
    )

    center = np.mean(np.array(list(layout.values())), axis=0)
    for node in top_labels:
        point = np.asarray(layout[node])
        direction = point - center
        norm = np.linalg.norm(direction)
        direction = direction / norm if norm else np.array([0.0, 1.0])
        label_point = point + direction * 0.16
        axis.annotate(
            labels.get(node, str(node)),
            xy=point,
            xytext=label_point,
            textcoords="data",
            fontsize=8,
            ha="center",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.2",
                "fc": "white",
                "ec": "#cbd5e1",
                "alpha": 0.92,
            },
            arrowprops={"arrowstyle": "-", "color": "#64748b", "lw": 0.6},
        )
    axis.set_title(f"Réseau de liaisons OD observées — {service}", fontsize=15, pad=22)
    axis.margins(x=0.12, y=0.18)
    axis.text(
        0.01,
        0.01,
        "Taille des nœuds : intermédiarité globale. Les liens ne représentent ni trafic, ni itinéraire complet.",
        transform=axis.transAxes,
        fontsize=9,
        color="#444444",
    )
    axis.axis("off")
    _finish(fig, output_path)


def _degree_chart(
    overall_nodes: pl.DataFrame, services: list[str], destination: Path
) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.8), sharey=True)
    for axis, column, title in zip(
        axes,
        ("in_degree", "out_degree"),
        ("Degré entrant", "Degré sortant"),
        strict=True,
    ):
        distributions = {}
        for service in services:
            frame = overall_nodes.filter(pl.col("service") == service)
            counts = frame.group_by(column).len().sort(column)
            distributions[service] = {
                int(row[column]): row["len"] / frame.height * 100
                for row in counts.to_dicts()
            }
        observed_degrees = [
            degree for values in distributions.values() for degree in values
        ]
        degrees = list(range(min(observed_degrees), max(observed_degrees) + 1))
        width = 0.38
        for offset, service in zip((-width / 2, width / 2), services, strict=True):
            y = [distributions[service].get(degree, 0.0) for degree in degrees]
            n_nodes = overall_nodes.filter(pl.col("service") == service).height
            axis.bar(
                np.asarray(degrees) + offset,
                y,
                width=width,
                label=f"{service} (n={n_nodes})",
                color=SERVICE_COLORS.get(service),
                alpha=0.88,
            )
        axis.set_title(title)
        axis.set_xlabel("Nombre de voisins distincts")
        axis.set_xticks(degrees, [str(value) for value in degrees], rotation=90)
        axis.grid(axis="y", alpha=0.22)
        axis.legend(frameon=False)
    axes[0].set_ylabel("Part des gares (%)")
    path = destination / "degree_distributions.png"
    _finish(fig, path)
    return path


def _ecdf(axis: plt.Axes, values: list[float], **kwargs: object) -> None:
    ordered = np.sort(np.asarray(values, dtype=float))
    if len(ordered):
        axis.step(
            ordered,
            np.arange(1, len(ordered) + 1) / len(ordered),
            where="post",
            **kwargs,
        )


def _centrality_chart(
    overall_nodes: pl.DataFrame, services: list[str], destination: Path
) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    for axis, column, title in zip(
        axes,
        ("betweenness_centrality", "pagerank"),
        ("Intermédiarité des gares", "PageRank des gares"),
        strict=True,
    ):
        for service in services:
            frame = overall_nodes.filter(pl.col("service") == service)
            values = frame[column].drop_nulls().to_list()
            zero_share = (
                100 * sum(value == 0 for value in values) / len(values)
                if values
                else 0.0
            )
            _ecdf(
                axis,
                values,
                color=SERVICE_COLORS.get(service),
                label=f"{service} (zéro : {zero_share:.1f} %)",
                linewidth=1.8,
            )
        axis.set_title(title)
        axis.set_xlabel("Valeur")
        axis.set_ylabel("Proportion cumulée")
        axis.set_ylim(0, 1.02)
        axis.grid(alpha=0.22)
        axis.legend(frameon=False)
    fig.suptitle("Distributions empiriques des centralités globales")
    path = destination / "node_centrality_distributions.png"
    _finish(fig, path)
    return path


def _edge_betweenness_chart(
    overall_edges: pl.DataFrame, services: list[str], destination: Path
) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3))
    for service in services:
        values = (
            overall_edges.filter(pl.col("service") == service)["edge_betweenness"]
            .drop_nulls()
            .to_list()
        )
        if not values:
            continue
        color = SERVICE_COLORS.get(service)
        _ecdf(axes[0], values, color=color, label=service, linewidth=1.8)
        axes[1].hist(values, bins="auto", color=color, alpha=0.4, label=service)
        median, percentile_90 = np.quantile(values, [0.5, 0.9])
        axes[0].axvline(median, color=color, linestyle="--", alpha=0.8)
        axes[0].axvline(percentile_90, color=color, linestyle=":", alpha=0.9)
        axes[1].axvline(median, color=color, linestyle="--", linewidth=1.5)
        axes[1].axvline(percentile_90, color=color, linestyle=":", linewidth=1.7)
        axes[0].text(
            0.02,
            0.96 - 0.12 * list(services).index(service),
            f"{service}: médiane={median:.3f}; P90={percentile_90:.3f}",
            transform=axes[0].transAxes,
            va="top",
            fontsize=8,
            color=color,
        )
    axes[0].set(
        title="Fonction de répartition empirique",
        xlabel="Intermédiarité des liaisons",
        ylabel="Proportion cumulée",
    )
    axes[1].set(
        title="Histogramme complémentaire",
        xlabel="Intermédiarité des liaisons",
        ylabel="Nombre de liaisons",
    )
    for axis in axes:
        axis.grid(alpha=0.2)
        axis.legend(frameon=False)
    fig.suptitle(
        "Intermédiarité des liaisons — mesure topologique, pas un volume de trafic"
    )
    path = destination / "edge_betweenness_distribution.png"
    _finish(fig, path)
    return path


def _ranking_charts(
    overall_nodes: pl.DataFrame,
    overall_edges: pl.DataFrame,
    nodes: pl.DataFrame,
    edges: pl.DataFrame,
    services: list[str],
    destination: Path,
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    node_names = dict(zip(nodes["node_id"].to_list(), nodes["station_name"].to_list()))
    metrics = (
        ("degree", "Degré"),
        ("betweenness_centrality", "Intermédiarité"),
        ("pagerank", "PageRank"),
    )
    fig, axes = plt.subplots(3, 2, figsize=(15, 14))
    for row, (metric, title) in enumerate(metrics):
        for column, service in enumerate(services):
            axis = axes[row, column]
            subset = (
                overall_nodes.filter(pl.col("service") == service)
                .sort(metric, descending=True)
                .head(10)
            )
            names = (
                subset["station_name"].to_list()
                if "station_name" in subset.columns
                else [
                    node_names.get(value, value)
                    for value in subset["node_id"].to_list()
                ]
            )
            values = subset[metric].to_list()
            positions = np.arange(len(names))
            axis.barh(positions, values, color=SERVICE_COLORS.get(service), alpha=0.88)
            axis.set_yticks(positions, names, fontsize=8)
            axis.invert_yaxis()
            axis.set_title(f"{service} — {title}")
            axis.grid(axis="x", alpha=0.2)
            axis.set_xlabel("Valeur de la mesure")
    fig.suptitle("Dix premières gares selon trois mesures distinctes", fontsize=15)
    path = destination / "top10_station_rankings.png"
    _finish(fig, path)
    paths["top10_station_rankings"] = path

    named_edges = (
        overall_edges.join(
            edges.select("edge_id", "service", "source", "target"),
            on=["edge_id", "service"],
            how="left",
        )
        .join(nodes, left_on="source", right_on="node_id", how="left")
        .rename({"station_name": "origin"})
        .join(nodes, left_on="target", right_on="node_id", how="left")
        .rename({"station_name": "destination"})
    )
    fig, axes = plt.subplots(
        1, len(services), figsize=(16, max(6, len(services) * 4)), squeeze=False
    )
    for column, service in enumerate(services):
        subset = (
            named_edges.filter(pl.col("service") == service)
            .sort("edge_betweenness", descending=True)
            .head(10)
        )
        labels = [
            f"{origin} → {target}"
            for origin, target in zip(
                subset["origin"].to_list(), subset["destination"].to_list(), strict=True
            )
        ]
        values = subset["edge_betweenness"].to_list()
        positions = np.arange(len(labels))
        axis = axes[0, column]
        axis.barh(positions, values, color=SERVICE_COLORS.get(service), alpha=0.88)
        axis.set_yticks(positions, labels, fontsize=8)
        axis.invert_yaxis()
        axis.set_title(service)
        axis.set_xlabel("Intermédiarité de liaison")
        axis.grid(axis="x", alpha=0.2)
    fig.suptitle(
        "Dix premières liaisons selon l’intermédiarité topologique", fontsize=15
    )
    path = destination / "top10_edge_rankings.png"
    _finish(fig, path)
    paths["top10_edge_rankings"] = path
    return paths


def _monthly_chart(
    node_metrics: pl.DataFrame,
    edge_metrics: pl.DataFrame,
    services: list[str],
    destination: Path,
) -> Path:
    monthly_nodes = (
        node_metrics.filter(pl.col("period") != "overall")
        .group_by("period", "service")
        .agg(
            pl.col("node_id").n_unique().alias("nodes"),
            pl.col("degree").mean().alias("mean_degree"),
            pl.col("pagerank").max().alias("max_pagerank"),
            pl.col("betweenness_centrality").max().alias("max_betweenness"),
        )
        .sort("period")
    )
    monthly_edges = (
        edge_metrics.filter(pl.col("period") != "overall")
        .group_by("period", "service")
        .agg(pl.col("edge_id").n_unique().alias("edges"))
    )
    monthly = monthly_nodes.join(monthly_edges, on=["period", "service"], how="left")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    series = (
        (axes[0, 0], "nodes", "Gares observées", "Nombre de gares"),
        (axes[0, 1], "edges", "Liaisons dirigées observées", "Nombre de liaisons"),
        (axes[1, 0], "max_pagerank", "Maximum mensuel du PageRank", "PageRank maximal"),
        (
            axes[1, 1],
            "max_betweenness",
            "Maximum mensuel de l’intermédiarité",
            "Intermédiarité maximale",
        ),
    )
    for service in services:
        subset = monthly.filter(pl.col("service") == service).sort("period")
        periods = subset["period"].to_list()
        x = np.arange(len(periods))
        for axis, column, _, _ in series:
            axis.plot(
                x,
                subset[column].to_list(),
                label=service,
                color=SERVICE_COLORS.get(service),
                linewidth=1.5,
            )
            axis.set_xticks(x[::12], periods[::12], rotation=45, ha="right")
            axis.grid(alpha=0.2)
    for axis, _, title, ylabel in series:
        axis.set_title(title)
        axis.set_ylabel(ylabel)
    axes[0, 0].set_ylim(bottom=0)
    axes[0, 1].set_ylim(bottom=0)

    international = monthly.filter(pl.col("service") == "International").sort("period")
    periods = international["period"].to_list()
    if periods:
        nodes_count = international["nodes"].to_list()
        edges_count = international["edges"].to_list()
        change_points = []
        for index, period in enumerate(periods):
            if not period.startswith("2025-"):
                continue
            prior_nodes = nodes_count[index - 1] if index else nodes_count[index]
            prior_edges = edges_count[index - 1] if index else edges_count[index]
            delta = abs(nodes_count[index] - prior_nodes) + abs(
                edges_count[index] - prior_edges
            )
            if delta:
                change_points.append((delta, index, period))
        for _, index, period in sorted(change_points, reverse=True)[:4]:
            axes[0, 0].scatter(
                index,
                nodes_count[index],
                color=SERVICE_COLORS["International"],
                edgecolor="white",
                zorder=5,
            )
            axes[0, 0].annotate(
                f"{period}: {nodes_count[index]} gares",
                (index, nodes_count[index]),
                xytext=(4, 8),
                textcoords="offset points",
                fontsize=7,
                rotation=25,
            )
            axes[0, 1].scatter(
                index,
                edges_count[index],
                color=SERVICE_COLORS["International"],
                edgecolor="white",
                zorder=5,
            )
            axes[0, 1].annotate(
                f"{period}: {edges_count[index]} liaisons",
                (index, edges_count[index]),
                xytext=(4, 8),
                textcoords="offset points",
                fontsize=7,
                rotation=25,
            )
    axes[0, 0].legend(frameon=False)
    fig.suptitle(
        "Évolution mensuelle — les deux centralités sont des maxima, pas des moyennes",
        fontsize=14,
    )
    path = destination / "monthly_network_evolution.png"
    _finish(fig, path)
    return path


def _operational_chart(
    research_data: pl.DataFrame, services: list[str], destination: Path
) -> Path:
    primary_column = "retard_moyen_tous_trains_arrivee"
    primary_flag = "flag_primary_arrival_delay_below_minus_15"
    primary_extreme = (
        pl.col(primary_flag).fill_null(False)
        if primary_flag in research_data.columns
        else pl.col(primary_column) < -15
    )
    primary_excluded = research_data.filter(primary_extreme)
    primary_excluded_by_service = {
        row["service"]: row["count"]
        for row in primary_excluded.group_by("service")
        .agg(pl.len().alias("count"))
        .to_dicts()
    }
    primary_excluded_breakdown = ", ".join(
        f"{service} {primary_excluded_by_service.get(service, 0)}"
        for service in services
    )
    primary_plot_values = (
        research_data.filter(~primary_extreme)[primary_column].drop_nulls().to_list()
    )
    primary_min = min(primary_plot_values, default=-15)
    primary_max = max(primary_plot_values, default=100)
    primary_bins = np.arange(
        np.floor(primary_min / 2.5) * 2.5,
        np.ceil(primary_max / 2.5) * 2.5 + 2.5,
        2.5,
    )
    delayed_column = "retard_moyen_arrivee"
    delayed_tail = research_data.filter(pl.col(delayed_column) > 120)
    rate_column = "cancellation_rate"
    rate_valid_count = research_data[rate_column].count()
    rate_missing_count = research_data[rate_column].null_count()

    fig, axes = plt.subplots(2, 3, figsize=(17, 9.5))
    primary_axis, delayed_axis, tail_axis = axes[0]
    rate_axis, rate_zoom_axis, note_axis = axes[1]
    for service in services:
        service_data = research_data.filter(pl.col("service") == service)
        color = SERVICE_COLORS.get(service)

        primary_values = (
            service_data.filter(~primary_extreme)[primary_column].drop_nulls().to_list()
        )
        primary_n = service_data[primary_column].count()
        if primary_values:
            primary_axis.hist(
                primary_values,
                bins=primary_bins,
                weights=np.full(len(primary_values), 100 / primary_n),
                alpha=0.48,
                color=color,
                label=f"{service} (n={primary_n})",
            )

        delayed_values = (
            service_data.filter(pl.col(delayed_column) <= 120)[delayed_column]
            .drop_nulls()
            .to_list()
        )
        delayed_n = service_data[delayed_column].count()
        if delayed_values:
            delayed_axis.hist(
                delayed_values,
                bins=np.arange(-45, 126, 5),
                weights=np.full(len(delayed_values), 100 / delayed_n),
                alpha=0.48,
                color=color,
                label=f"{service} (n={delayed_n})",
            )

        rate_values = service_data[rate_column].drop_nulls().to_list()
        rate_n = len(rate_values)
        if rate_values:
            weights = np.full(len(rate_values), 100 / rate_n)
            rate_axis.hist(
                rate_values,
                bins=np.linspace(0, 1, 51),
                weights=weights,
                alpha=0.48,
                color=color,
                label=f"{service} (n={rate_n})",
            )
            rate_zoom_axis.hist(
                rate_values,
                bins=np.linspace(0, 0.1, 21),
                weights=weights,
                alpha=0.48,
                color=color,
                label=f"{service} (n={rate_n})",
            )

    for service in services:
        values = (
            research_data.filter(
                (pl.col("service") == service) & (pl.col(delayed_column) > 120)
            )[delayed_column]
            .drop_nulls()
            .to_list()
        )
        if values:
            service_y = services.index(service)
            jitter = np.linspace(-0.12, 0.12, len(values)) if len(values) > 1 else [0]
            tail_axis.scatter(
                values,
                service_y + jitter,
                color=SERVICE_COLORS.get(service),
                alpha=0.82,
                s=38,
                label=f"{service} (n={len(values)})",
                edgecolors="white",
                linewidths=0.4,
            )

    primary_excluded_count = primary_excluded.height
    primary_axis.set_title(
        f"Retard moyen à l’arrivée — tous les trains\n{primary_excluded_count} valeurs < −15 min exclues"
    )
    primary_axis.set_xlabel("Minutes")
    primary_axis.set_ylabel("Part des observations du service (%)")
    primary_axis.axvline(0, color="#555555", linewidth=0.8, linestyle="--")
    primary_axis.grid(axis="y", alpha=0.2)
    primary_axis.legend(frameon=False)

    delayed_axis.set_title(
        f"Retard moyen à l’arrivée — trains retardés\n{delayed_tail.height} valeurs > 120 min montrées à droite"
    )
    delayed_axis.set_xlabel("Minutes")
    delayed_axis.set_ylabel("Part des observations du service (%)")
    delayed_axis.axvline(0, color="#555555", linewidth=0.8, linestyle="--")
    delayed_axis.grid(axis="y", alpha=0.2)
    delayed_axis.legend(frameon=False)

    tail_axis.set_title("Valeurs au-delà de 120 min")
    tail_axis.set_xlabel("Retard moyen (minutes)")
    tail_axis.set_yticks(range(len(services)), services)
    tail_axis.set_ylim(-0.5, len(services) - 0.5)
    tail_axis.grid(axis="x", alpha=0.2)
    if tail_axis.get_legend_handles_labels()[0]:
        tail_axis.legend(frameon=False)
    else:
        tail_axis.text(
            0.5,
            0.5,
            "Aucune observation au-delà de 120 min",
            transform=tail_axis.transAxes,
            ha="center",
            va="center",
        )

    rate_axis.set_title(
        f"Taux d’annulation — plage complète\n{rate_missing_count} valeurs manquantes"
    )
    rate_axis.set_xlabel("Part des trains planifiés")
    rate_axis.set_ylabel("Part des taux valides du service (%)")
    rate_axis.grid(axis="y", alpha=0.2)
    rate_axis.legend(frameon=False)
    rate_zoom_axis.set_title("Taux d’annulation — zoom près de zéro")
    rate_zoom_axis.set_xlabel("Part des trains planifiés (0–0,10)")
    rate_zoom_axis.set_ylabel("Part des taux valides du service (%)")
    rate_zoom_axis.set_xlim(0, 0.1)
    rate_zoom_axis.grid(axis="y", alpha=0.2)
    rate_zoom_axis.legend(frameon=False)
    above_zoom = research_data.filter(pl.col(rate_column) > 0.1).height
    rate_zoom_axis.text(
        0.02,
        0.96,
        f"{above_zoom} taux > 0,10 restent visibles dans le panneau complet",
        transform=rate_zoom_axis.transAxes,
        va="top",
        fontsize=8,
    )

    note_axis.axis("off")
    note_axis.text(
        0.03,
        0.95,
        "Traitement limité à l’affichage\n\n"
        f"• Retards tous trains : {primary_excluded_count} valeurs sous −15 min omises du panneau principal ({primary_excluded_breakdown}).\n"
        f"• Trains retardés : {delayed_tail.height} valeurs au-dessus de 120 min sont séparées dans le panneau supérieur droit.\n"
        f"• Annulations : les {rate_valid_count} taux valides figurent dans la plage complète; le zoom ne montre que 0–0,10.\n"
        f"• {rate_missing_count} taux manquants restent manquants.\n\n"
        "Aucune ligne ni valeur n’est supprimée du fichier Parquet; les statistiques du rapport utilisent toutes les observations.",
        transform=note_axis.transAxes,
        va="top",
        fontsize=9,
        wrap=True,
    )
    fig.suptitle("Distributions descriptives des indicateurs opérationnels")
    path = destination / "operational_outcome_distributions.png"
    _finish(fig, path)
    return path


def generate_visualizations(
    research_data: pl.DataFrame,
    node_metrics: pl.DataFrame,
    edge_metrics: pl.DataFrame,
    nodes: pl.DataFrame,
    edges: pl.DataFrame,
    output_dir: str | os.PathLike[str] = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    """Generate comparative distribution, topology, and outcome charts.

    :param research_data: Monthly research dataset with operational outcomes.
    :type research_data: polars.DataFrame
    :param node_metrics: Existing overall and monthly node metrics.
    :type node_metrics: polars.DataFrame
    :param edge_metrics: Existing overall and monthly edge metrics.
    :type edge_metrics: polars.DataFrame
    :param nodes: Existing station ID/name mapping.
    :type nodes: polars.DataFrame
    :param edges: Existing service-aware directed edge table.
    :type edges: polars.DataFrame
    :param output_dir: Destination directory for PNG files.
    :type output_dir: str | os.PathLike[str]
    :returns: Mapping of descriptive chart names to saved paths.
    :rtype: dict[str, pathlib.Path]
    :raises TypeError: If any input is not a Polars DataFrame.
    :raises ValueError: If required chart fields are missing.
    :raises OSError: If chart files cannot be written.
    """
    frames = (research_data, node_metrics, edge_metrics, nodes, edges)
    if any(not isinstance(frame, pl.DataFrame) for frame in frames):
        raise TypeError("all visualization inputs must be Polars DataFrames")
    _require(
        research_data,
        {
            "date",
            "service",
            "retard_moyen_tous_trains_arrivee",
            "retard_moyen_arrivee",
            "cancellation_rate",
        },
        "research_data",
    )
    _require(
        node_metrics,
        {
            "period",
            "service",
            "node_id",
            "in_degree",
            "out_degree",
            "degree",
            "betweenness_centrality",
            "pagerank",
        },
        "node_metrics",
    )
    _require(
        edge_metrics,
        {"period", "service", "edge_id", "edge_betweenness"},
        "edge_metrics",
    )
    _require(nodes, {"node_id", "station_name"}, "nodes")
    _require(edges, {"service", "source", "target"}, "edges")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    services = [
        service for service in SERVICE_ORDER if service in edges["service"].to_list()
    ]
    services.extend(
        service
        for service in sorted(edges["service"].unique().to_list())
        if service not in services
    )
    overall_nodes = node_metrics.filter(pl.col("period") == "overall")
    overall_edges = edge_metrics.filter(pl.col("period") == "overall")
    paths: dict[str, Path] = {}
    for service in services:
        path = destination / f"network_{service.lower()}.png"
        _network_chart(service, nodes, edges, overall_nodes, path)
        paths[f"network_{service.lower()}"] = path
    paths["degree_distributions"] = _degree_chart(overall_nodes, services, destination)
    paths["node_centrality_distributions"] = _centrality_chart(
        overall_nodes, services, destination
    )
    paths["edge_betweenness_distribution"] = _edge_betweenness_chart(
        overall_edges, services, destination
    )
    paths.update(
        _ranking_charts(
            overall_nodes, overall_edges, nodes, edges, services, destination
        )
    )
    paths["monthly_network_evolution"] = _monthly_chart(
        node_metrics, edge_metrics, services, destination
    )
    paths["operational_outcome_distributions"] = _operational_chart(
        research_data, services, destination
    )
    return paths


def run_visualization_pipeline(
    research_data_path: str | os.PathLike[str] = DEFAULT_RESEARCH_PATH,
    node_metrics_path: str | os.PathLike[str] = DEFAULT_NODE_METRICS_PATH,
    edge_metrics_path: str | os.PathLike[str] = DEFAULT_EDGE_METRICS_PATH,
    nodes_path: str | os.PathLike[str] = DEFAULT_NODES_PATH,
    edges_path: str | os.PathLike[str] = DEFAULT_EDGES_PATH,
    output_dir: str | os.PathLike[str] = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    """Load existing artifacts and generate descriptive PNG visualizations.

    :param research_data_path: Monthly research dataset path.
    :type research_data_path: str | os.PathLike[str]
    :param node_metrics_path: Existing node metrics path.
    :type node_metrics_path: str | os.PathLike[str]
    :param edge_metrics_path: Existing edge metrics path.
    :type edge_metrics_path: str | os.PathLike[str]
    :param nodes_path: Existing station mapping path.
    :type nodes_path: str | os.PathLike[str]
    :param edges_path: Existing directed edges path.
    :type edges_path: str | os.PathLike[str]
    :param output_dir: Destination directory for charts.
    :type output_dir: str | os.PathLike[str]
    :returns: Chart names mapped to generated PNG paths.
    :rtype: dict[str, pathlib.Path]
    :raises OSError: If inputs cannot be read or charts cannot be saved.
    :raises ValueError: If required input fields are absent.
    """
    return generate_visualizations(
        pl.read_parquet(research_data_path),
        pl.read_parquet(node_metrics_path),
        pl.read_parquet(edge_metrics_path),
        pl.read_parquet(nodes_path),
        pl.read_parquet(edges_path),
        output_dir=output_dir,
    )
