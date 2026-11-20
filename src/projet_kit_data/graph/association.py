"""Associations exploratoires entre la structure du graphe et la régularité SNCF."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.stats import pearsonr, spearmanr

from projet_kit_data.graph.presentation import METRIC_PRESENTATION

GRAPH_DIR = Path("data/processed/graph")
DEFAULT_RESEARCH_PATH = Path("data/processed/research_dataset.parquet")
DEFAULT_OUTPUT_DIR = GRAPH_DIR / "phase3b"
DEFAULT_FIGURE_DIR = GRAPH_DIR / "visualizations" / "phase3b"
DEFAULT_REPORT_PATH = Path("data/reports/graph/research_report.md")

PRIMARY_OUTCOME = "retard_moyen_tous_trains_arrivee"
OUTCOMES = (
    PRIMARY_OUTCOME,
    "cancellation_rate",
    "retard_moyen_arrivee",
)
PREDICTORS = (
    "edge_betweenness",
    "source_degree",
    "target_degree",
    "source_betweenness_centrality",
    "target_betweenness_centrality",
    "source_pagerank",
    "target_pagerank",
)
CLUSTER_COLUMNS = ("service", "gare_depart", "gare_arrivee")
SCOPE_ORDER = ("Overall", "National", "International")
DEFAULT_QUANTILE_COUNT = 4
MIN_POSITIVE_QUANTILE_SIZE = 30
ZERO_SHARE_THRESHOLD = 0.05

_NUMERIC_COLUMNS = (*PREDICTORS, *OUTCOMES)
_CORRELATION_SCHEMA = {
    "analysis_scope": pl.String,
    "service": pl.String,
    "predictor": pl.String,
    "outcome": pl.String,
    "method": pl.String,
    "coefficient": pl.Float64,
    "p_value": pl.Float64,
    "n_valid": pl.UInt32,
}
_QUANTILE_SCHEMA = {
    "analysis_scope": pl.String,
    "service": pl.String,
    "predictor": pl.String,
    "outcome": pl.String,
    "group_label": pl.String,
    "grouping_strategy": pl.String,
    "n": pl.UInt32,
    "median": pl.Float64,
    "mean": pl.Float64,
    "std": pl.Float64,
    "q25": pl.Float64,
    "q75": pl.Float64,
    "iqr": pl.Float64,
}
_ROBUSTNESS_SCHEMA = {
    "analysis_scope": pl.String,
    "service": pl.String,
    "predictor": pl.String,
    "outcome": pl.String,
    "method": pl.String,
    "full_coefficient": pl.Float64,
    "sensitivity_coefficient": pl.Float64,
    "coefficient_difference": pl.Float64,
    "full_n_valid": pl.UInt32,
    "sensitivity_n_valid": pl.UInt32,
}


@dataclass
class AssociationResult:
    """Résultats lisibles par machine des analyses d’association.

    :ivar correlations: Estimations pairwise de Pearson et Spearman et valeurs p brutes.
    :ivar quantile_comparisons: Synthèses des résultats par groupes conservant les ex æquo.
    :ivar robustness_comparisons: Comparaison des données complètes et de l’analyse de sensibilité du résultat principal.
    :ivar metadata: Métadonnées sur les entrées, les regroupements et l’interprétation.
    :ivar output_paths: Chemins écrits par le pipeline fondé sur des fichiers.
    """

    correlations: pl.DataFrame
    quantile_comparisons: pl.DataFrame
    robustness_comparisons: pl.DataFrame
    metadata: dict[str, Any]
    output_paths: dict[str, Path] = field(default_factory=dict)


def _require_columns(frame: pl.DataFrame) -> None:
    required = {
        "service",
        "date",
        "gare_depart",
        "gare_arrivee",
        "cancellation_rate_valid",
        "flag_primary_arrival_delay_below_minus_15",
        *_NUMERIC_COLUMNS,
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            "research_data ne contient pas les colonnes requises : "
            + ", ".join(sorted(missing))
        )
    for column in _NUMERIC_COLUMNS:
        if not frame.schema[column].is_numeric():
            raise TypeError(
                f"research_data.{column} doit avoir un type numérique Polars"
            )
    for column in CLUSTER_COLUMNS:
        if frame.schema[column] != pl.String:
            raise TypeError(f"research_data.{column} doit être de type String Polars")


def _pair_arrays(
    frame: pl.DataFrame, predictor: str, outcome: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = frame[predictor].cast(pl.Float64).to_numpy()
    y = frame[outcome].cast(pl.Float64).to_numpy()
    valid = np.isfinite(x) & np.isfinite(y)
    if outcome == "cancellation_rate":
        valid &= frame["cancellation_rate_valid"].fill_null(False).to_numpy()
    return x[valid], y[valid], valid


def _correlation(
    x: np.ndarray, y: np.ndarray, method: str
) -> tuple[float | None, float | None]:
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return None, None
    if method == "pearson":
        result = pearsonr(x, y)
    elif method == "spearman":
        result = spearmanr(x, y)
    else:
        raise ValueError(f"Méthode de corrélation non prise en charge : {method}")
    coefficient = float(result.statistic)
    p_value = float(result.pvalue)
    if not np.isfinite(coefficient) or not np.isfinite(p_value):
        return None, None
    return coefficient, p_value


def _group_labels(
    values: np.ndarray,
    quantile_count: int,
    min_positive_size: int = MIN_POSITIVE_QUANTILE_SIZE,
    zero_share_threshold: float = ZERO_SHARE_THRESHOLD,
) -> tuple[np.ndarray, str]:
    """Créer des groupes de quantiles sans répartir les valeurs ex æquo du prédicteur."""
    labels = np.full(len(values), "", dtype=object)
    finite = np.isfinite(values)
    if not finite.any():
        return labels, "no_valid_predictor_values"
    zero_mask = finite & (values == 0)
    zero_share = zero_mask.sum() / finite.sum()
    separate_zero = zero_share >= zero_share_threshold
    labels[zero_mask & separate_zero] = "Zero"
    quantile_mask = finite & (~zero_mask if separate_zero else True)
    quantile_values = values[quantile_mask]
    if not len(quantile_values):
        strategy = "zero_only" if separate_zero else "no_valid_predictor_values"
        return labels, strategy

    unique, inverse, counts = np.unique(
        quantile_values, return_inverse=True, return_counts=True
    )
    if len(quantile_values) >= min_positive_size and len(unique) >= 3:
        group_count = min(quantile_count, len(unique))
        cumulative = np.cumsum(counts)
        boundaries = []
        for group_index in range(1, group_count):
            min_split = (boundaries[-1] + 1) if boundaries else 1
            max_split = len(unique) - (group_count - group_index)
            candidates = np.arange(min_split, max_split + 1)
            target = len(quantile_values) * group_index / group_count
            split = int(
                candidates[np.argmin(np.abs(cumulative[candidates - 1] - target))]
            )
            boundaries.append(split)
        group_for_unique = np.searchsorted(
            boundaries, np.arange(len(unique)), side="right"
        )
        group_for_row = group_for_unique[inverse]
        prefix = "Positive " if separate_zero else ""
        labels[quantile_mask] = [f"{prefix}Q{group + 1}" for group in group_for_row]
        strategy = (
            "zero_plus_tie_preserving_quantiles"
            if separate_zero
            else "tie_preserving_quantiles"
        )
    else:
        labels[quantile_mask] = "Positive" if separate_zero else "All values"
        strategy = (
            "zero_plus_positive_only"
            if separate_zero
            else "insufficient_unique_values_for_quantiles"
        )
    return labels, strategy


def _scope_frames(frame: pl.DataFrame) -> list[tuple[str, str, pl.DataFrame]]:
    scopes = [("overall", "Overall", frame)]
    for service in ("National", "International"):
        subset = frame.filter(pl.col("service") == service)
        if subset.height:
            scopes.append(("service", service, subset))
    return scopes


def build_association_results(
    research_data: pl.DataFrame,
    quantile_count: int = DEFAULT_QUANTILE_COUNT,
) -> AssociationResult:
    """Calculer des corrélations exploratoires et des synthèses par groupe de centralité.

    Les corrélations utilisent les observations finies disponibles par paire.
    Les paires du taux d’annulation doivent également satisfaire le flag
    ``cancellation_rate_valid``. Les synthèses de groupes appliquent les règles
    existantes de quantiles conservant les ex æquo et de groupe de zéros.
    L’analyse de sensibilité du résultat principal exclut les valeurs sous
    -15 minutes de ce seul calcul ; elle ne modifie jamais ``research_data``.
    Les valeurs p classiques sont conservées à titre exploratoire complémentaire
    et ne tiennent pas compte des observations mensuelles répétées d’une liaison.

    :param research_data: DataFrame de recherche existant à la granularité liaison-mois.
    :type research_data: polars.DataFrame
    :param quantile_count: Nombre demandé de groupes de valeurs positives/toutes valeurs conservant les ex æquo.
    :type quantile_count: int
    :returns: Corrélations, synthèses des groupes, résultats de robustesse et métadonnées.
    :rtype: AssociationResult
    :raises TypeError: Si l’entrée n’est pas un DataFrame Polars ou si les colonnes
        requises ont des types non pris en charge.
    :raises ValueError: Si des colonnes requises sont absentes ou si les paramètres sont invalides.
    """
    if not isinstance(research_data, pl.DataFrame):
        raise TypeError("research_data doit être un DataFrame Polars")
    if quantile_count < 2:
        raise ValueError("quantile_count doit être supérieur ou égal à 2")
    _require_columns(research_data)

    correlation_rows: list[dict[str, Any]] = []
    quantile_rows: list[dict[str, Any]] = []
    robustness_rows: list[dict[str, Any]] = []
    scope_frames = _scope_frames(research_data)
    correlation_lookup: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

    for scope, service, data in scope_frames:
        for outcome in OUTCOMES:
            for predictor in PREDICTORS:
                x, y, valid = _pair_arrays(data, predictor, outcome)
                n_valid = int(valid.sum())
                for method in ("pearson", "spearman"):
                    coefficient, p_value = _correlation(x, y, method)
                    row = {
                        "analysis_scope": scope,
                        "service": service,
                        "predictor": predictor,
                        "outcome": outcome,
                        "method": method,
                        "coefficient": coefficient,
                        "p_value": p_value,
                        "n_valid": n_valid,
                    }
                    correlation_rows.append(row)
                    correlation_lookup[(scope, service, predictor, outcome, method)] = (
                        row
                    )

        sensitivity = data.filter(
            pl.col(PRIMARY_OUTCOME).is_null() | (pl.col(PRIMARY_OUTCOME) >= -15)
        )
        for predictor in PREDICTORS:
            for method in ("pearson", "spearman"):
                full = correlation_lookup[
                    (scope, service, predictor, PRIMARY_OUTCOME, method)
                ]
                x, y, valid = _pair_arrays(sensitivity, predictor, PRIMARY_OUTCOME)
                sensitivity_coefficient, _ = _correlation(x, y, method)
                full_coefficient = full["coefficient"]
                robustness_rows.append(
                    {
                        "analysis_scope": scope,
                        "service": service,
                        "predictor": predictor,
                        "outcome": PRIMARY_OUTCOME,
                        "method": method,
                        "full_coefficient": full_coefficient,
                        "sensitivity_coefficient": sensitivity_coefficient,
                        "coefficient_difference": (
                            None
                            if full_coefficient is None
                            or sensitivity_coefficient is None
                            else sensitivity_coefficient - full_coefficient
                        ),
                        "full_n_valid": full["n_valid"],
                        "sensitivity_n_valid": int(valid.sum()),
                    }
                )

        for outcome in OUTCOMES:
            for predictor in PREDICTORS:
                values = data[predictor].cast(pl.Float64).to_numpy()
                group_labels, strategy = _group_labels(values, quantile_count)
                outcome_values = data[outcome].cast(pl.Float64).to_numpy()
                valid_outcome = np.isfinite(outcome_values)
                if outcome == "cancellation_rate":
                    valid_outcome &= (
                        data["cancellation_rate_valid"].fill_null(False).to_numpy()
                    )
                for group_label in dict.fromkeys(group_labels[valid_outcome]):
                    if not group_label:
                        continue
                    group_mask = valid_outcome & (group_labels == group_label)
                    group_values = outcome_values[group_mask]
                    if not len(group_values):
                        continue
                    q25, median, q75 = np.quantile(group_values, [0.25, 0.5, 0.75])
                    quantile_rows.append(
                        {
                            "analysis_scope": scope,
                            "service": service,
                            "predictor": predictor,
                            "outcome": outcome,
                            "group_label": str(group_label),
                            "grouping_strategy": strategy,
                            "n": len(group_values),
                            "median": float(median),
                            "mean": float(np.mean(group_values)),
                            "std": float(np.std(group_values, ddof=1))
                            if len(group_values) > 1
                            else None,
                            "q25": float(q25),
                            "q75": float(q75),
                            "iqr": float(q75 - q25),
                        }
                    )

    cluster_counts = {
        service: int(subset.select(pl.struct(list(CLUSTER_COLUMNS)).n_unique()).item())
        for service in research_data["service"].unique().to_list()
        for subset in [research_data.filter(pl.col("service") == service)]
    }
    primary_flag = research_data["flag_primary_arrival_delay_below_minus_15"].fill_null(
        False
    )
    metadata = {
        "input_rows": research_data.height,
        "input_columns": research_data.width,
        "input_services": sorted(research_data["service"].unique().to_list()),
        "date_min": research_data["date"].min() if research_data.height else None,
        "date_max": research_data["date"].max() if research_data.height else None,
        "directed_cluster_count_by_service": cluster_counts,
        "business_key_duplicate_count": research_data.height
        - research_data.select(
            pl.struct(["date", "service", "gare_depart", "gare_arrivee"]).n_unique()
        ).item(),
        "primary_outcome_extreme_count_below_minus_15": int(primary_flag.sum()),
        "primary_outcome_extreme_count_verified_by_value": research_data.filter(
            pl.col(PRIMARY_OUTCOME) < -15
        ).height,
        "cancellation_rate_valid_count": research_data.filter(
            pl.col("cancellation_rate_valid")
        ).height,
        "cancellation_rate_invalid_or_missing_count": research_data.filter(
            ~pl.col("cancellation_rate_valid").fill_null(False)
        ).height,
        "predictors": list(PREDICTORS),
        "outcomes": list(OUTCOMES),
        "quantile_grouping": {
            "requested_positive_or_all_value_groups": quantile_count,
            "ties_split": False,
            "zero_share_threshold": ZERO_SHARE_THRESHOLD,
            "minimum_positive_rows_for_quantiles": MIN_POSITIVE_QUANTILE_SIZE,
            "minimum_unique_values_for_quantiles": 3,
        },
        "interpretation_limits": [
            "Les observations mensuelles d’une même liaison orientée sont répétées et ne constituent pas des échantillons pleinement indépendants.",
            "Les valeurs p usuelles de Pearson et Spearman sont exploratoires ; la répétition des observations peut conduire à surestimer la force probante des résultats statistiques.",
            "Les associations sont observationnelles et ne démontrent ni causalité, ni itinéraires de train, ni volumes de voyageurs, ni propagation des retards.",
            "Les services National et International ont des topologies et des compositions de liaisons différentes ; les comparaisons de résultats doivent être nuancées.",
            "Seule l’analyse de sensibilité du résultat principal exclut les valeurs inférieures à -15 minutes ; les enregistrements source restent inchangés.",
        ],
    }
    return AssociationResult(
        pl.DataFrame(correlation_rows, schema=_CORRELATION_SCHEMA),
        pl.DataFrame(quantile_rows, schema=_QUANTILE_SCHEMA),
        pl.DataFrame(robustness_rows, schema=_ROBUSTNESS_SCHEMA),
        metadata,
    )


def _format_r(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}".replace(".", ",")


def _predictor_label(column: str) -> str:
    endpoint = ""
    metric = column
    for prefix, label in (
        ("source_", "Gare d’origine — "),
        ("target_", "Gare de destination — "),
    ):
        if column.startswith(prefix):
            endpoint = label
            metric = column.removeprefix(prefix)
            break
    presentation = METRIC_PRESENTATION.get(metric)
    return endpoint + (presentation.label if presentation else metric.replace("_", " "))


def _markdown_table(frame: pl.DataFrame) -> str:
    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join("---" for _ in frame.columns) + " |",
    ]
    for row in frame.to_dicts():
        values = [
            "—" if row[column] is None else str(row[column]) for column in frame.columns
        ]
        lines.append(
            "| " + " | ".join(value.replace("|", "\\|") for value in values) + " |"
        )
    return "\n".join(lines)


def _write_report(result: AssociationResult, report_path: Path) -> None:
    """Maintenir le texte français sur les associations dans le rapport unifié."""
    begin = "<!-- BEGIN GENERATED ASSOCIATION CONTENT -->"
    end = "<!-- END GENERATED ASSOCIATION CONTENT -->"
    image_dir = "../../processed/graph/visualizations/phase3b"
    primary = result.correlations.filter(
        (pl.col("outcome") == PRIMARY_OUTCOME) & pl.col("coefficient").is_not_null()
    )
    method_labels = {"pearson": "Pearson r", "spearman": "Spearman rho"}
    primary_rows: list[dict[str, Any]] = []
    for service in SCOPE_ORDER:
        for method in ("pearson", "spearman"):
            candidates = primary.filter(
                (pl.col("service") == service) & (pl.col("method") == method)
            ).to_dicts()
            if not candidates:
                continue
            best = max(candidates, key=lambda row: abs(row["coefficient"]))
            primary_rows.append(
                {
                    "Périmètre": service,
                    "Méthode": method_labels[method],
                    "Prédicteur le plus associé en valeur absolue": _predictor_label(
                        best["predictor"]
                    ),
                    "Coefficient": _format_r(best["coefficient"]),
                    "n valide": best["n_valid"],
                }
            )
    primary_table = pl.DataFrame(primary_rows) if primary_rows else pl.DataFrame()

    secondary_labels = {
        "cancellation_rate": "Taux d’annulation valide",
        "retard_moyen_arrivee": "Retard moyen des trains retardés",
    }
    secondary_rows: list[dict[str, Any]] = []
    for outcome, label in secondary_labels.items():
        for service in ("National", "International"):
            candidates = result.correlations.filter(
                (pl.col("outcome") == outcome)
                & (pl.col("service") == service)
                & (pl.col("method") == "spearman")
                & pl.col("coefficient").is_not_null()
            ).to_dicts()
            if not candidates:
                continue
            best = max(candidates, key=lambda row: abs(row["coefficient"]))
            secondary_rows.append(
                {
                    "Résultat": label,
                    "Service": service,
                    "Prédicteur": _predictor_label(best["predictor"]),
                    "rho": _format_r(best["coefficient"]),
                    "n valide": best["n_valid"],
                }
            )
    secondary_table = pl.DataFrame(secondary_rows) if secondary_rows else pl.DataFrame()
    primary_spearman = primary.filter(pl.col("method") == "spearman")
    largest_abs_spearman = primary_spearman.select(
        pl.col("coefficient").abs().max()
    ).item()

    group_statistics = (
        result.quantile_comparisons.filter(
            (pl.col("analysis_scope") == "service")
            & (pl.col("predictor") == "edge_betweenness")
            & (pl.col("outcome") == PRIMARY_OUTCOME)
        )
        .select(
            pl.col("service").alias("Service"),
            pl.col("group_label")
            .str.replace("^Positive ", "Positif ")
            .replace(
                {
                    "Zero": "Zéro",
                    "Positive": "Positif",
                    "All values": "Toutes les valeurs",
                }
            )
            .alias("Groupe Edge betweenness"),
            pl.col("n").alias("n"),
            pl.col("median").round(2).alias("Médiane du retard (min)"),
            pl.col("mean").round(2).alias("Moyenne (min)"),
            pl.col("std").round(2).alias("Écart-type (min)"),
            pl.col("iqr").round(2).alias("IQR (min)"),
        )
        .sort("Service", "Groupe Edge betweenness")
    )
    national_groups = result.quantile_comparisons.filter(
        (pl.col("service") == "National")
        & (pl.col("predictor") == "edge_betweenness")
        & (pl.col("outcome") == PRIMARY_OUTCOME)
    )
    international_groups = result.quantile_comparisons.filter(
        (pl.col("service") == "International")
        & (pl.col("predictor") == "edge_betweenness")
        & (pl.col("outcome") == PRIMARY_OUTCOME)
    )
    national_q3 = national_groups.filter(pl.col("group_label") == "Q3")
    national_q4 = national_groups.filter(pl.col("group_label") == "Q4")
    international_q2 = international_groups.filter(pl.col("group_label") == "Q2")
    if national_q3.height and national_q4.height and international_q2.height:
        n3 = national_q3.row(0, named=True)
        n4 = national_q4.row(0, named=True)
        i2 = international_q2.row(0, named=True)
        group_interpretation = f"Les médianes ne suivent pas une progression régulière : National Q3 est à {n3['median']:.2f} min (n={n3['n']}), puis Q4 à {n4['median']:.2f} min; International Q2 atteint {i2['median']:.2f} min (n={i2['n']}). Les groupes sont inégaux parce que les ex æquo sont conservés. Il s’agit de comparaisons descriptives, sans test d’inférence."
    else:
        group_interpretation = "Les groupes sont descriptifs, leurs tailles peuvent différer puisque les ex æquo ne sont pas séparés."

    robustness = result.robustness_comparisons.filter(
        (pl.col("method") == "spearman")
        & pl.col("analysis_scope").is_in(["overall", "service"])
    )
    robustness_rows = []
    for service in SCOPE_ORDER:
        candidates = primary_spearman.filter(pl.col("service") == service).to_dicts()
        if not candidates:
            continue
        strongest = max(candidates, key=lambda row: abs(row["coefficient"]))
        robust_row = robustness.filter(
            (pl.col("service") == service)
            & (pl.col("predictor") == strongest["predictor"])
        )
        if robust_row.height:
            row = robust_row.row(0, named=True)
            robustness_rows.append(
                {
                    "Périmètre": service,
                    "Prédicteur": _predictor_label(strongest["predictor"]),
                    "rho complet": _format_r(row["full_coefficient"]),
                    "rho sensibilité": _format_r(row["sensitivity_coefficient"]),
                    "Écart": _format_r(row["coefficient_difference"]),
                    "n complet / sensibilité": f"{row['full_n_valid']} / {row['sensitivity_n_valid']}",
                }
            )
    robustness_table = (
        pl.DataFrame(robustness_rows) if robustness_rows else pl.DataFrame()
    )
    metadata = result.metadata
    cluster_counts = metadata.get("directed_cluster_count_by_service", {})
    count_text = ", ".join(
        f"{service} : {count} liaisons dirigées"
        for service, count in cluster_counts.items()
    )
    content = [
        "## 5. Association entre structure du réseau et régularité",
        "",
        "Après avoir décrit séparément la topologie et les résultats opérationnels, nous examinons leur association à l’échelle des observations mensuelles. Les prédicteurs sont les métriques existantes des liaisons et de leurs gares d’origine et de destination. Les résultats sont calculés séparément pour les services `National` et `International` ; la catégorie `Overall` fournit une vue descriptive regroupée.",
        "",
        "Pearson mesure une association linéaire et Spearman une association monotone fondée sur les rangs. Les deux coefficients utilisent les paires valides; pour le taux d’annulation, seules les lignes marquées `cancellation_rate_valid` sont retenues. Le tableau ci-dessous choisit, pour chaque périmètre et méthode, le prédicteur dont la valeur absolue du coefficient est la plus élevée pour le retard moyen tous trains. Cette sélection est descriptive, pas confirmatoire.",
        "",
        _markdown_table(primary_table)
        if primary_table.height
        else "Aucune corrélation calculable pour le résultat principal.",
        "",
        f"![Corrélations Spearman avec le retard moyen tous trains]({image_dir}/primary_spearman_overview.png)",
        "",
        f"![Edge betweenness et retard moyen tous trains]({image_dir}/edge_betweenness_scatter.png)",
        "",
        f"![Degré de la gare cible et retard moyen tous trains]({image_dir}/target_degree_scatter.png)",
        "",
        f"Pour le retard moyen tous trains, la plus grande valeur absolue de Spearman est {_format_r(largest_abs_spearman)}. Les coefficients restent faibles : le signe est positif pour le meilleur prédicteur National et négatif pour International. Cela répond à la question de recherche par une association limitée et différente selon le service, pas par un effet opérationnel important démontré.",
        "",
        "Pour les deux autres résultats, le tableau donne le prédicteur présentant la plus forte valeur absolue de Spearman dans chaque service. Ces valeurs sont également exploratoires et servent à comparer les ordres de grandeur; elles ne constituent pas une sélection confirmatoire.",
        "",
        _markdown_table(secondary_table)
        if secondary_table.height
        else "Aucune corrélation calculable pour les résultats complémentaires.",
        "",
        "Les p-values brutes restent disponibles dans `correlations.parquet`; elles ne sont pas reprises ici comme preuve de significativité. Chaque liaison contribue à plusieurs mois d’observation, de sorte que les lignes ne sont pas indépendantes et que les p-values classiques peuvent surestimer la force de la preuve. Aucun ajustement multiple n’est appliqué dans cette version exploratoire.",
        "",
        "### Comparaison descriptive par groupes de centralité",
        "",
        "Le tableau et la figure comparent le retard moyen selon les groupes Edge betweenness, séparément par service. Les groupes conservent les valeurs ex æquo et n’ont donc pas nécessairement la même taille.",
        "",
        _markdown_table(group_statistics)
        if group_statistics.height
        else "Aucun résumé Edge betweenness calculable.",
        "",
        f"![Groupes Edge betweenness et résultats opérationnels]({image_dir}/edge_betweenness_quantile_groups.png)",
        "",
        group_interpretation,
        "",
        "### Sensibilité aux retards extrêmes",
        "",
        f"Nous avons recalculé les corrélations du résultat principal en écartant, pour cette comparaison seulement, les {metadata['primary_outcome_extreme_count_below_minus_15']} observations sous −15 minutes. Elles restent dans le jeu de recherche et dans les résultats complets.",
        "",
        _markdown_table(robustness_table)
        if robustness_table.height
        else "Aucune comparaison de sensibilité calculable.",
        "",
        "Pour les prédicteurs résumés ici, les écarts de coefficients sont faibles. Cette vérification ne concerne que le résultat principal et le seuil choisi; elle ne démontre pas que l’ensemble de l’analyse est insensible aux valeurs extrêmes.",
        "",
        "## 6. Discussion",
        "",
        "Les deux graphes ont des topologies et des compositions de liaisons différentes, et les distributions opérationnelles diffèrent elles aussi. Les associations faibles observées ne suffisent pas à attribuer ces différences à la position des gares ou des liaisons. De plus, une même liaison est observée sur plusieurs mois et le réseau International compte relativement peu de liaisons distinctes ("
        + f"{count_text}). Les coefficients et les comparaisons de groupes doivent donc être lus comme des descriptions exploratoires.",
        "",
        "Les OD représentent des paires origine-destination observées, pas nécessairement des segments ferroviaires adjacents ou des itinéraires confirmés. Les métriques ne mesurent ni le trafic voyageurs ni la propagation des retards; le jeu de données n’établit aucun mécanisme causal.",
        "",
        "## 7. Conclusion et limites",
        "",
        "À la question « Dans quelle mesure la structure du réseau TGV est-elle associée à la régularité des liaisons ? », les résultats disponibles indiquent des associations de faible amplitude, dont le sens varie entre National et International. Les comparaisons par groupes ne montrent pas de progression monotone simple, et la sensibilité au seuil de −15 minutes modifie peu les coefficients résumés. La conclusion est donc nuancée : la structure du graphe et les indicateurs de régularité varient parfois ensemble, mais cette analyse ne montre pas que l’une détermine l’autre.",
        "",
        "Les p-values de corrélation restent exploratoires en raison des observations mensuelles répétées; les différences de composition et le nombre limité de liaisons International imposent aussi de la prudence. Ces limites excluent toute conclusion causale et toute interprétation en termes de fréquentation ou de propagation des retards.",
        "",
    ]
    replacement = "\n".join(content)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    if begin in existing and end in existing:
        prefix, remainder = existing.split(begin, maxsplit=1)
        _, suffix = remainder.split(end, maxsplit=1)
        updated = f"{prefix}{begin}\n{replacement}\n{end}{suffix}"
    else:
        separator = "" if not existing or existing.endswith("\n\n") else "\n"
        updated = f"{existing}{separator}\n{begin}\n{replacement}\n{end}\n"
    report_path.write_text(updated, encoding="utf-8")


def _make_figures(
    research_data: pl.DataFrame,
    result: AssociationResult,
    figure_dir: Path,
) -> dict[str, Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    colors = {"National": "#1769aa", "International": "#d95f02"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    for axis, service in zip(axes, ("National", "International"), strict=True):
        subset = research_data.filter(pl.col("service") == service)
        x, y, valid = _pair_arrays(subset, "edge_betweenness", PRIMARY_OUTCOME)
        axis.scatter(x, y, s=12, alpha=0.28, color=colors[service], rasterized=True)
        axis.set_yscale("symlog", linthresh=15)
        axis.set_title(f"{service} (n={int(valid.sum())})")
        axis.set_xlabel(METRIC_PRESENTATION["edge_betweenness"].label)
        axis.grid(alpha=0.2)
    axes[0].set_ylabel("Retard moyen tous trains à l’arrivée (minutes; échelle symlog)")
    fig.suptitle("Betweenness des arêtes et régularité mensuelle à l’arrivée")
    fig.tight_layout()
    path = figure_dir / "edge_betweenness_scatter.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    paths["edge_betweenness_scatter"] = path

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    for axis, service in zip(axes, ("National", "International"), strict=True):
        subset = research_data.filter(pl.col("service") == service)
        x, y, valid = _pair_arrays(subset, "target_degree", PRIMARY_OUTCOME)
        axis.scatter(x, y, s=12, alpha=0.24, color=colors[service], rasterized=True)
        axis.set_yscale("symlog", linthresh=15)
        axis.set_title(f"{service} (n={int(valid.sum())})")
        axis.set_xlabel(
            f"Degré de la gare cible : {METRIC_PRESENTATION['degree'].label}"
        )
        axis.grid(alpha=0.2)
    axes[0].set_ylabel("Retard moyen tous trains à l’arrivée (minutes; échelle symlog)")
    fig.suptitle("Degré de la gare cible et régularité mensuelle à l’arrivée")
    fig.tight_layout()
    path = figure_dir / "target_degree_scatter.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    paths["target_degree_scatter"] = path

    selected = result.quantile_comparisons.filter(
        (pl.col("analysis_scope") == "service")
        & (pl.col("predictor") == "edge_betweenness")
        & (pl.col("outcome") == PRIMARY_OUTCOME)
    ).sort("service", "group_label")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    for axis, service in zip(axes, ("National", "International"), strict=True):
        subset = selected.filter(pl.col("service") == service)
        labels = subset["group_label"].to_list()
        sample_sizes = subset["n"].to_list()
        samples = []
        raw = research_data.filter(pl.col("service") == service)
        x = raw["edge_betweenness"].to_numpy()
        y = raw[PRIMARY_OUTCOME].to_numpy()
        grouped, _ = _group_labels(x, DEFAULT_QUANTILE_COUNT)
        for label in labels:
            mask = (grouped == label) & np.isfinite(y)
            samples.append(y[mask])
        if samples:
            axis.boxplot(
                samples,
                tick_labels=[
                    f"{label}\nn={sample_size}"
                    for label, sample_size in zip(labels, sample_sizes, strict=True)
                ],
            )
        axis.set_title(service)
        axis.set_xlabel("Groupe de betweenness des arêtes conservant les ex æquo")
        axis.tick_params(axis="x", rotation=30)
        axis.set_yscale("symlog", linthresh=15)
        axis.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Retard moyen tous trains à l’arrivée (minutes; symlog)")
    fig.suptitle("Résultat principal par groupe de betweenness des arêtes")
    fig.tight_layout()
    path = figure_dir / "edge_betweenness_quantile_groups.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    paths["edge_betweenness_quantile_groups"] = path

    correlations = result.correlations.filter(
        (pl.col("outcome") == PRIMARY_OUTCOME) & (pl.col("method") == "spearman")
    )
    predictors = list(PREDICTORS)
    fig, axes = plt.subplots(1, 3, figsize=(17, 6), sharey=True, layout="constrained")
    for axis, service in zip(axes, SCOPE_ORDER, strict=True):
        subset = correlations.filter(pl.col("service") == service)
        lookup = {row["predictor"]: row["coefficient"] for row in subset.to_dicts()}
        values = np.array(
            [
                np.nan if lookup.get(predictor) is None else lookup[predictor]
                for predictor in predictors
            ]
        )
        image = axis.imshow(
            values[:, None], cmap="coolwarm", vmin=-1, vmax=1, aspect="auto"
        )
        axis.set_title(service)
        axis.set_xticks([0], ["Rho de Spearman"])
        axis.set_yticks(
            range(len(predictors)), [_predictor_label(name) for name in predictors]
        )
        for row, value in enumerate(values):
            if np.isfinite(value):
                axis.text(0, row, f"{value:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(
        image, ax=axes, label="Coefficient de corrélation de Spearman", shrink=0.8
    )
    fig.suptitle("Métriques du graphe et résultat opérationnel principal")
    path = figure_dir / "primary_spearman_overview.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    paths["primary_spearman_overview"] = path
    return paths


def run_association_analysis_pipeline(
    research_data_path: str | os.PathLike[str] = DEFAULT_RESEARCH_PATH,
    output_dir: str | os.PathLike[str] = DEFAULT_OUTPUT_DIR,
    figure_dir: str | os.PathLike[str] = DEFAULT_FIGURE_DIR,
    report_path: str | os.PathLike[str] = DEFAULT_REPORT_PATH,
    quantile_count: int = DEFAULT_QUANTILE_COUNT,
) -> AssociationResult:
    """Exécuter l’analyse simplifiée à partir du jeu de données existant.

    Le pipeline lit le jeu de recherche et les métriques de graphe en amont sans
    jamais les réécrire. Il produit des tables de corrélation, de groupes de
    centralité et de robustesse, des figures réutilisables, des métadonnées et
    une section balisée dans le rapport de recherche unifié en français.

    :param research_data_path: Chemin du jeu de recherche existant.
    :type research_data_path: str | os.PathLike[str]
    :param output_dir: Répertoire des fichiers Parquet de résultats et des métadonnées.
    :type output_dir: str | os.PathLike[str]
    :param figure_dir: Répertoire réservé aux visualisations.
    :type figure_dir: str | os.PathLike[str]
    :param report_path: Chemin du rapport de recherche unifié en français.
    :type report_path: str | os.PathLike[str]
    :param quantile_count: Nombre demandé de groupes de valeurs conservant les ex æquo.
    :type quantile_count: int
    :returns: Tables d’analyse, métadonnées et chemins de sortie.
    :rtype: AssociationResult
    :raises OSError: Si les entrées ne peuvent pas être lues ou les sorties écrites.
    :raises TypeError: Si les types du schéma d’entrée sont invalides.
    :raises ValueError: Si des champs requis ou paramètres d’analyse sont invalides.
    """
    research_path = Path(research_data_path)
    research_data = pl.read_parquet(research_path)
    result = build_association_results(
        research_data,
        quantile_count=quantile_count,
    )
    result.metadata["input_path"] = str(research_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    tables = {
        "correlations": result.correlations,
        "quantile_comparisons": result.quantile_comparisons,
        "robustness_comparisons": result.robustness_comparisons,
    }
    result.metadata["output_tables"] = {
        name: {
            "rows": table.height,
            "columns": table.width,
            "schema": {column: str(dtype) for column, dtype in table.schema.items()},
        }
        for name, table in tables.items()
    }
    for name, table in tables.items():
        path = destination / f"{name}.parquet"
        table.write_parquet(path)
        paths[name] = path
    metadata_path = destination / "association_metadata.json"
    metadata_path.write_text(
        json.dumps(result.metadata, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    paths["metadata"] = metadata_path
    paths.update(_make_figures(research_data, result, Path(figure_dir)))
    _write_report(result, Path(report_path))
    paths["report"] = Path(report_path)
    result.output_paths = paths
    return result
