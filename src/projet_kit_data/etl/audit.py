'Audit qualité en lecture seule des données brutes de régularité TGV SNCF.'

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl

DEFAULT_RAW_DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.json")
DEFAULT_REPORT_PATH = Path("data/reports/data_quality_report.txt")

EXPECTED_SCHEMA: dict[str, str] = {
    "date": "string",
    "service": "string",
    "gare_depart": "string",
    "gare_arrivee": "string",
    "duree_moyenne": "integer",
    "nb_train_prevu": "integer",
    "nb_annulation": "integer",
    "commentaire_annulation": "string",
    "nb_train_depart_retard": "integer",
    "retard_moyen_depart": "number",
    "retard_moyen_tous_trains_depart": "number",
    "commentaire_retards_depart": "string",
    "nb_train_retard_arrivee": "integer",
    "retard_moyen_arrivee": "number",
    "retard_moyen_tous_trains_arrivee": "number",
    "commentaires_retard_arrivee": "string",
    "nb_train_retard_sup_15": "integer",
    "retard_moyen_trains_retard_sup15": "number",
    "nb_train_retard_sup_30": "integer",
    "nb_train_retard_sup_60": "integer",
    "prct_cause_externe": "number",
    "prct_cause_infra": "number",
    "prct_cause_gestion_trafic": "number",
    "prct_cause_materiel_roulant": "number",
    "prct_cause_gestion_gare": "number",
    "prct_cause_prise_en_charge_voyageurs": "number",
}

BUSINESS_KEY = ("date", "service", "gare_depart", "gare_arrivee")
ANOMALY_EXAMPLE_LIMIT = 10
EXTREME_NEGATIVE_THRESHOLD = -15.0
_EXAMPLE_IDENTITY_FIELDS = ("date", "service", "gare_depart", "gare_arrivee")


def _json_records(path: Path) -> list[dict[str, Any]]:
    'Lit et valide un tableau JSON d’enregistrements sans imbrication.'
    with path.open("r", encoding="utf-8") as input_file:
        records = json.load(input_file)
    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        raise ValueError('Le JSON d’entrée doit être un tableau d’objets.')
    return records


def _value_type(value: Any) -> str:
    'Renvoie le libellé lisible du type d’une valeur compatible JSON.'
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_finite_number(value: Any) -> bool:
    'Indique si une valeur est un nombre fini et non un booléen.'
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _example_record(
    record: dict[str, Any],
    relevant_fields: tuple[str, ...],
) -> dict[str, Any]:
    'Sélectionne les champs d’identité et de diagnostic pour un exemple du rapport.'
    fields = dict.fromkeys((*_EXAMPLE_IDENTITY_FIELDS, *relevant_fields))
    return {field: record.get(field) for field in fields}


def _anomaly_examples(records: list[dict[str, Any]]) -> dict[str, Any]:
    'Recueille les effectifs et jusqu’à dix exemples bruts des anomalies choisies.'
    checks: dict[str, dict[str, Any]] = {}

    field_checks = {
        "negative_nb_train_retard_sup_30": (
            "nb_train_retard_sup_30",
            ("nb_train_retard_sup_15", "nb_train_retard_sup_60"),
            lambda value: value < 0,
        ),
        "negative_retard_moyen_trains_retard_sup15": (
            "retard_moyen_trains_retard_sup15",
            ("nb_train_retard_sup_15", "retard_moyen_arrivee"),
            lambda value: value < 0,
        ),
    }
    for check_name, (field, related_fields, condition) in field_checks.items():
        matches = [
            record
            for record in records
            if _is_finite_number(record.get(field)) and condition(record[field])
        ]
        checks[check_name] = {
            "field": field,
            "condition": "< 0",
            "record_count": len(matches),
            "examples": [
                _example_record(record, (field, *related_fields))
                for record in matches[:ANOMALY_EXAMPLE_LIMIT]
            ],
        }

    extreme_fields = {
        "retard_moyen_tous_trains_arrivee": (
            "retard_moyen_arrivee",
            "nb_train_retard_arrivee",
            "nb_train_prevu",
        ),
        "retard_moyen_tous_trains_depart": (
            "retard_moyen_depart",
            "nb_train_depart_retard",
            "nb_train_prevu",
        ),
        "retard_moyen_arrivee": (
            "nb_train_retard_arrivee",
            "nb_train_prevu",
            "retard_moyen_tous_trains_arrivee",
        ),
    }
    extreme_examples: dict[str, dict[str, Any]] = {}
    for field, related_fields in extreme_fields.items():
        matches = [
            record
            for record in records
            if _is_finite_number(record.get(field))
            and record[field] < EXTREME_NEGATIVE_THRESHOLD
        ]
        extreme_examples[field] = {
            "condition": f"< {EXTREME_NEGATIVE_THRESHOLD:g}",
            "record_count": len(matches),
            "examples": [
                _example_record(record, (field, *related_fields))
                for record in matches[:ANOMALY_EXAMPLE_LIMIT]
            ],
        }

    cancellation_matches = [
        record
        for record in records
        if _is_finite_number(record.get("nb_annulation"))
        and _is_finite_number(record.get("nb_train_prevu"))
        and record["nb_annulation"] > record["nb_train_prevu"]
    ]
    checks["cancellations_exceed_planned"] = {
        "condition": "nb_annulation > nb_train_prevu",
        "record_count": len(cancellation_matches),
        "examples": [
            _example_record(
                record,
                (
                    "nb_annulation",
                    "nb_train_prevu",
                    "nb_train_depart_retard",
                    "nb_train_retard_arrivee",
                ),
            )
            for record in cancellation_matches[:ANOMALY_EXAMPLE_LIMIT]
        ],
    }

    threshold_fields = (
        "nb_train_retard_sup_15",
        "nb_train_retard_sup_30",
        "nb_train_retard_sup_60",
    )
    complete_threshold_records = [
        record
        for record in records
        if all(_is_finite_number(record.get(field)) for field in threshold_fields)
    ]
    threshold_violations = [
        record
        for record in complete_threshold_records
        if not (
            record[threshold_fields[0]]
            >= record[threshold_fields[1]]
            >= record[threshold_fields[2]]
        )
    ]
    pairwise_checks: dict[str, dict[str, Any]] = {}
    for lower_threshold, higher_threshold in (
        (threshold_fields[0], threshold_fields[1]),
        (threshold_fields[1], threshold_fields[2]),
    ):
        checked_records = [
            record
            for record in records
            if _is_finite_number(record.get(lower_threshold))
            and _is_finite_number(record.get(higher_threshold))
        ]
        violations = [
            record
            for record in checked_records
            if record[lower_threshold] < record[higher_threshold]
        ]
        pairwise_checks[f"{lower_threshold}_ge_{higher_threshold}"] = {
            "fields": [lower_threshold, higher_threshold],
            "records_checked": len(checked_records),
            "record_count": len(violations),
            "note": (
                'Le comptage >15 concerne les liaisons en concurrence avec l’avion ; aucun indicateur d’applicabilité n’est fourni.'
                if lower_threshold == "nb_train_retard_sup_15"
                else 'Le comptage >60 minutes est un sous-ensemble du comptage >30 minutes.'
            ),
            "examples": [
                _example_record(record, (lower_threshold, higher_threshold))
                for record in violations[:ANOMALY_EXAMPLE_LIMIT]
            ],
        }

    return {
        "example_limit": ANOMALY_EXAMPLE_LIMIT,
        "extreme_negative_threshold": EXTREME_NEGATIVE_THRESHOLD,
        "checks": checks,
        "extremely_negative_delay_values": extreme_examples,
        "threshold_ordering": {
            "fields": list(threshold_fields),
            "expected_order": (
                "nb_train_retard_sup_15 >= nb_train_retard_sup_30 "
                ">= nb_train_retard_sup_60"
            ),
            "records_checked": len(complete_threshold_records),
            "record_count": len(threshold_violations),
            "pairwise_checks": pairwise_checks,
            "note": (
                'Ce contrôle d’ordre est indicatif : le schéma SNCF réserve nb_train_retard_sup_15 aux liaisons en concurrence avec l’avion, mais aucun indicateur d’applicabilité n’est fourni.'
            ),
            "examples": [
                _example_record(record, threshold_fields)
                for record in threshold_violations[:ANOMALY_EXAMPLE_LIMIT]
            ],
        },
    }


def _stat_expression(column: str, dtype: pl.DataType) -> pl.Expr:
    'Renvoie une expression Polars traitant NaN comme une valeur manquante dans les statistiques.'
    expression = pl.col(column)
    if dtype.is_float():
        expression = expression.fill_nan(None)
    return expression


def _duplicate_summary(
    frame: pl.DataFrame,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    'Compte les doublons exacts et les doublons de clés métier complètes.'
    columns = frame.columns
    exact_duplicate_count = 0
    exact_duplicate_group_count = 0
    if columns:
        exact_groups = frame.group_by(columns).len(name="group_size")
        duplicate_groups = exact_groups.filter(pl.col("group_size") > 1)
        exact_duplicate_group_count = duplicate_groups.height
        exact_duplicate_count = int(
            duplicate_groups.select((pl.col("group_size") - 1).sum()).item() or 0
        )

    key_columns_available = all(column in columns for column in BUSINESS_KEY)
    if key_columns_available:
        complete_key_frame = frame.filter(
            pl.all_horizontal([pl.col(column).is_not_null() for column in BUSINESS_KEY])
        )
        key_groups = complete_key_frame.group_by(list(BUSINESS_KEY)).len(
            name="group_size"
        )
        duplicate_key_groups = key_groups.filter(pl.col("group_size") > 1)
        business_key_duplicate_group_count = duplicate_key_groups.height
        business_key_duplicate_count = int(
            duplicate_key_groups.select((pl.col("group_size") - 1).sum()).item() or 0
        )
        incomplete_key_count = frame.height - complete_key_frame.height
    else:
        business_key_duplicate_group_count = 0
        business_key_duplicate_count = 0
        incomplete_key_count = len(records)

    return {
        "exact_duplicate_record_count": exact_duplicate_count,
        "exact_duplicate_group_count": exact_duplicate_group_count,
        "business_key": list(BUSINESS_KEY),
        "business_key_duplicate_record_count": business_key_duplicate_count,
        "business_key_duplicate_group_count": business_key_duplicate_group_count,
        "records_with_incomplete_business_key": incomplete_key_count,
    }


def _logical_checks(
    frame: pl.DataFrame,
    negative_summary: dict[str, dict[str, int | float | None]],
) -> dict[str, Any]:
    'Compte les diagnostics explicites de cohérence par ligne avec Polars.'
    columns = set(frame.columns)
    schema = frame.schema
    planned = "nb_train_prevu"
    comparisons: dict[str, dict[str, Any]] = {}

    for field in ("nb_annulation", "nb_train_retard_arrivee"):
        check_name = f"{field}_greater_than_{planned}"
        checked = 0
        affected = 0
        if (
            field in columns
            and planned in columns
            and schema[field].is_numeric()
            and schema[planned].is_numeric()
        ):
            left = _stat_expression(field, schema[field])
            right = _stat_expression(planned, schema[planned])
            valid = frame.filter(left.is_not_null() & right.is_not_null())
            checked = valid.height
            affected = valid.filter(left > right).height
        comparisons[check_name] = {
            "fields": [field, planned],
            "records_checked": checked,
            "affected_record_count": affected,
        }

    departure_fields = [
        field
        for field in ("nb_train_depart_retard", "nb_train_retard_depart")
        if field in columns and schema[field].is_numeric()
    ]
    departure_checked = 0
    departure_affected = 0
    if departure_fields and planned in columns and schema[planned].is_numeric():
        planned_expression = _stat_expression(planned, schema[planned])
        departure_expressions = [
            _stat_expression(field, schema[field]) for field in departure_fields
        ]
        has_departure_count = pl.any_horizontal(
            [expression.is_not_null() for expression in departure_expressions]
        )
        valid = frame.filter(planned_expression.is_not_null() & has_departure_count)
        departure_checked = valid.height
        departure_affected = valid.filter(
            pl.any_horizontal(
                [
                    expression > planned_expression
                    for expression in departure_expressions
                ]
            )
        ).height
    comparisons[f"departure_delay_count_greater_than_{planned}"] = {
        "fields": [*departure_fields, planned],
        "records_checked": departure_checked,
        "affected_record_count": departure_affected,
        "note": (
            'Le champ officiel SNCF est nb_train_depart_retard ; nb_train_retard_depart est également reconnu comme alias.'
        ),
    }

    count_columns = sorted(
        column
        for column in frame.columns
        if column.startswith("nb_") and schema[column].is_numeric()
    )
    negative_count_by_column = {
        column: negative_summary.get(column, {}).get("negative_count", 0)
        for column in count_columns
    }
    if count_columns:
        negative_count_records = frame.select(
            pl.any_horizontal([pl.col(column) < 0 for column in count_columns])
            .fill_null(False)
            .sum()
        ).item()
    else:
        negative_count_records = 0

    percentage_columns = sorted(
        column
        for column in frame.columns
        if column.startswith("prct_cause_") and schema[column].is_numeric()
    )
    if percentage_columns:
        outside_range = [
            (pl.col(column) < 0) | (pl.col(column) > 100)
            for column in percentage_columns
        ]
        cause_percentage_affected = frame.select(
            pl.any_horizontal(outside_range).fill_null(False).sum()
        ).item()
        percentage_by_column = {
            column: int(
                frame.filter((pl.col(column) < 0) | (pl.col(column) > 100)).height
            )
            for column in percentage_columns
        }
    else:
        cause_percentage_affected = 0
        percentage_by_column = {}

    return {
        "count_greater_than_planned_checks": comparisons,
        "negative_count_fields": {
            "columns": negative_count_by_column,
            "affected_record_count": int(negative_count_records or 0),
        },
        "cause_percentages_outside_0_to_100": {
            "columns": percentage_by_column,
            "affected_record_count": int(cause_percentage_affected or 0),
        },
    }


def _display_percentage(value: float | None) -> str:
    'Formate un pourcentage, y compris lorsqu’il est indéfini sur des données vides.'
    return "N/A" if value is None else f"{value:.2f}%"


def _append_examples(
    lines: list[str],
    title: str,
    summary: dict[str, Any],
) -> None:
    'Ajoute le nombre d’anomalies et leurs exemples au format JSON.'
    condition = summary.get("condition", 'condition enregistrée dans les résultats structurés')
    lines.append(f"{title}: {summary['record_count']} observations ({condition})")
    if not summary["examples"]:
        lines.append('  (aucun exemple)')
        return
    for index, example in enumerate(summary["examples"], start=1):
        lines.append(
            f"  {index}. {json.dumps(example, ensure_ascii=False, default=str)}"
        )


def _format_report(results: dict[str, Any]) -> str:
    'Présente les résultats structurés de l’audit dans un rapport textuel lisible.'
    overview = results["dataset_overview"]
    lines = [
        'Audit qualité des données de régularité TGV SNCF',
        "=" * 42,
        "",
        'Aperçu du jeu de données',
        "-----------------",
        f"Fichier d’entrée : {overview['input_path']}",
        f"Observations : {overview['record_count']}",
        f"Colonnes : {overview['column_count']}",
        'Colonnes disponibles : ' + (", ".join(overview["available_columns"]) or '(aucun)'),
        'Colonnes attendues absentes : '
        + (", ".join(overview["missing_expected_columns"]) or '(aucun)'),
        'Colonnes inattendues : '
        + (", ".join(overview["unexpected_columns"]) or '(aucun)'),
        "",
        'Types observés par colonne',
        "------------------------------",
    ]
    for column, type_summary in overview["data_types"].items():
        observed = ", ".join(
            f"{name}: {count}"
            for name, count in type_summary["observed_value_types"].items()
        )
        lines.append(
            f"{column}: Polars {type_summary['polars_dtype']}; "
            f"expected SNCF type: {type_summary['expected_schema_type']}; "
            f"observed values: {observed or '(aucun)'}"
        )

    lines.extend(
        [
            "",
            'Valeurs manquantes',
            "---------------",
            'Les pourcentages utilisent le nombre total d’observations au dénominateur.',
        ]
    )
    for column, summary in results["missing_values"].items():
        lines.append(
            f"{column}: {summary['count']} "
            f"({_display_percentage(summary['percentage'])}; "
            f"{summary['percentage_denominator']} observations)"
        )

    duplicates = results["duplicates"]
    lines.extend(
        [
            "",
            "Duplicates",
            "----------",
            'Les doublons comptent les lignes après la première occurrence de chaque groupe.',
            (
                f"Observations entièrement dupliquées : "
                f"{duplicates['exact_duplicate_record_count']} "
                f"in {duplicates['exact_duplicate_group_count']} groupes"
            ),
            (
                f"Doublons de clé métier ({', '.join(BUSINESS_KEY)}): "
                f"{duplicates['business_key_duplicate_record_count']} "
                f"in {duplicates['business_key_duplicate_group_count']} groupes"
            ),
            (
                "Records omitted from business-key comparison due to missing key "
                f"values: {duplicates['records_with_incomplete_business_key']}"
            ),
            "",
            'Valeurs numériques négatives',
            "-------------------------",
            'Les pourcentages utilisent les valeurs numériques finies non manquantes de chaque colonne.',
        ]
    )
    for column, summary in results["negative_values"].items():
        lines.append(
            f"{column}: {summary['negative_count']} "
            f"({_display_percentage(summary['percentage'])}; "
            f"{summary['numeric_value_count']} valeurs numériques)"
        )

    lines.extend(["", 'Statistiques numériques', "---------------------"])
    for column, summary in results["numerical_statistics"].items():
        lines.append(f"{column} (n={summary['count']}):")
        for statistic_name in (
            "minimum",
            "maximum",
            "mean",
            "median",
            "standard_deviation",
        ):
            lines.append(f"  {statistic_name}: {summary[statistic_name]}")
        quantiles = ", ".join(
            f"{percentile}%={value}"
            for percentile, value in summary["quantiles"].items()
        )
        lines.append(f"  quantiles: {quantiles}")

    logical = results["logical_consistency"]
    lines.extend(
        ["", 'Diagnostics de cohérence logique', "-------------------------------"]
    )
    for check_name, summary in logical["count_greater_than_planned_checks"].items():
        lines.append(
            f"{check_name}: {summary['affected_record_count']} concernés / "
            f"{summary['records_checked']} contrôlés"
        )
    negative_counts = logical["negative_count_fields"]
    lines.append(
        'Observations avec un comptage négatif : '
        f"{negative_counts['affected_record_count']}"
    )
    for column, count in negative_counts["columns"].items():
        lines.append(f"  {column}: {count}")
    cause_percentages = logical["cause_percentages_outside_0_to_100"]
    lines.append(
        'Observations avec un pourcentage de cause hors de [0, 100] : '
        f"{cause_percentages['affected_record_count']}"
    )
    for column, count in cause_percentages["columns"].items():
        lines.append(f"  {column}: {count}")

    anomaly_results = results["anomaly_examples"]
    lines.extend(
        [
            "",
            'Exemples d’anomalies',
            "-----------------",
            f"Affichage d’au plus {anomaly_results['example_limit']} observations par contrôle.",
            'Les exemples comprennent la date, le service, les gares et les valeurs concernées.',
        ]
    )
    for check_name, summary in anomaly_results["checks"].items():
        _append_examples(lines, check_name, summary)

    lines.append(
        "Extremely negative delays use the explicit diagnostic threshold "
        f"< {anomaly_results['extreme_negative_threshold']:g} minutes."
    )
    for column, summary in anomaly_results["extremely_negative_delay_values"].items():
        _append_examples(lines, column, summary)

    threshold_ordering = anomaly_results["threshold_ordering"]
    for check_name, summary in threshold_ordering["pairwise_checks"].items():
        lines.append(
            f"Ordre par paire {check_name}: {summary['record_count']} potential "
            f"violations / {summary['records_checked']} contrôlés"
        )
        lines.append(f"  Note: {summary['note']}")
        for index, example in enumerate(summary["examples"], start=1):
            lines.append(
                f"  {index}. {json.dumps(example, ensure_ascii=False, default=str)}"
            )
        if not summary["examples"]:
            lines.append('  (aucun exemple)')
    lines.append(
        "Threshold ordering "
        f"({threshold_ordering['expected_order']}): "
        f"{threshold_ordering['record_count']} anomalies potentielles / "
        f"{threshold_ordering['records_checked']} contrôlés"
    )
    lines.append(f"  Note: {threshold_ordering['note']}")
    for index, example in enumerate(threshold_ordering["examples"], start=1):
        lines.append(
            f"  {index}. {json.dumps(example, ensure_ascii=False, default=str)}"
        )
    if not threshold_ordering["examples"]:
        lines.append('  (aucun exemple)')

    lines.extend(
        [
            "",
            "Notes",
            "-----",
            'Tous les contrôles sont des diagnostics. Aucune observation ni valeur n’a été modifiée.',
            'Les retards négatifs sont signalés sans être automatiquement considérés comme invalides.',
            f"Fichier du rapport : {results['report_path']}",
        ]
    )
    return "\n".join(lines) + "\n"


def audit_raw_data(
    input_path: str | Path = DEFAULT_RAW_DATA_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> dict[str, Any]:
    """Audite le JSON brut SNCF et enregistre un rapport textuel lisible.
    
    Le fichier source est ouvert en lecture seule. Polars examine les colonnes,
    valeurs nulles, doublons, valeurs numériques et statistiques. Le dictionnaire
    renvoyé contient les mêmes résultats que le rapport et reste réutilisable.
    Aucune observation source n’est modifiée.
    
    :param input_path: Chemin du tableau JSON brut ; données SNCF de ``data/raw`` par défaut.
    :type input_path: str | pathlib.Path
    :param report_path: Rapport textuel ; ``data/reports/data_quality_report.txt`` par défaut.
    :type report_path: str | pathlib.Path
    :returns: Résultats structurés : aperçu, valeurs manquantes, doublons, valeurs négatives, statistiques numériques et contrôles logiques.
    :rtype: dict[str, Any]
    :raises OSError: Si la source est illisible ou le rapport ne peut pas être écrit.
    :raises json.JSONDecodeError: Si le fichier ne contient pas de JSON valide.
    :raises ValueError: Si la racine JSON n’est pas un tableau d’objets."""
    source_path = Path(input_path)
    records = _json_records(source_path)
    try:
        frame = pl.DataFrame(records, infer_schema_length=None, strict=False)
    except Exception as exc:
        raise ValueError(f"Impossible de construire un DataFrame Polars : {exc}") from exc

    columns = frame.columns
    column_set = set(columns)
    expected_columns = set(EXPECTED_SCHEMA)
    missing_columns = sorted(expected_columns - column_set)
    unexpected_columns = sorted(column_set - expected_columns)

    data_types: dict[str, dict[str, Any]] = {}
    for column in columns:
        observed_types = Counter(_value_type(record.get(column)) for record in records)
        data_types[column] = {
            "polars_dtype": str(frame.schema[column]),
            "expected_schema_type": EXPECTED_SCHEMA.get(column),
            "observed_value_types": dict(sorted(observed_types.items())),
        }

    missing_values: dict[str, dict[str, int | float | None]] = {}
    for column in [*columns, *missing_columns]:
        if column in column_set:
            series = frame[column]
            missing_count = series.null_count()
            if series.dtype.is_float():
                missing_count += int(series.is_nan().sum() or 0)
        else:
            missing_count = len(records)
        missing_values[column] = {
            "count": int(missing_count),
            "percentage": (missing_count / len(records) * 100 if records else None),
            "percentage_denominator": len(records),
        }

    numeric_columns = {
        column
        for column, schema_type in EXPECTED_SCHEMA.items()
        if schema_type in {"integer", "number"}
    }
    numeric_columns.update(
        column for column, dtype in frame.schema.items() if dtype.is_numeric()
    )

    negative_values: dict[str, dict[str, int | float | None]] = {}
    numerical_statistics: dict[str, dict[str, Any]] = {}
    for column in sorted(numeric_columns):
        if column not in column_set or not frame.schema[column].is_numeric():
            numeric_count = 0
            negative_count = 0
            values: dict[str, Any] = {}
        else:
            dtype = frame.schema[column]
            expression = _stat_expression(column, dtype)
            series = frame[column]
            numeric_count = len(records) - series.null_count()
            if dtype.is_float():
                numeric_count -= int(series.is_nan().sum() or 0)
            negative_count = int(
                frame.select((expression < 0).fill_null(False).sum()).item() or 0
            )
            values = frame.select(
                expression.min().alias("minimum"),
                expression.max().alias("maximum"),
                expression.mean().alias("mean"),
                expression.median().alias("median"),
                expression.std(ddof=1).alias("standard_deviation"),
                expression.quantile(0.25, interpolation="linear").alias("q25"),
                expression.quantile(0.50, interpolation="linear").alias("q50"),
                expression.quantile(0.75, interpolation="linear").alias("q75"),
                expression.quantile(0.95, interpolation="linear").alias("q95"),
            ).row(0, named=True)

        negative_values[column] = {
            "negative_count": negative_count,
            "numeric_value_count": numeric_count,
            "percentage": (
                negative_count / numeric_count * 100 if numeric_count else None
            ),
        }
        numerical_statistics[column] = {
            "count": numeric_count,
            "minimum": values.get("minimum"),
            "maximum": values.get("maximum"),
            "mean": values.get("mean"),
            "median": values.get("median"),
            "standard_deviation": values.get("standard_deviation"),
            "quantiles": {
                "25": values.get("q25"),
                "50": values.get("q50"),
                "75": values.get("q75"),
                "95": values.get("q95"),
            },
        }

    report_destination = Path(report_path)
    results: dict[str, Any] = {
        "dataset_overview": {
            "input_path": str(source_path),
            "record_count": len(records),
            "column_count": len(columns),
            "available_columns": columns,
            "missing_expected_columns": missing_columns,
            "unexpected_columns": unexpected_columns,
            "data_types": data_types,
        },
        "missing_values": missing_values,
        "duplicates": _duplicate_summary(frame, records),
        "negative_values": negative_values,
        "numerical_statistics": numerical_statistics,
        "logical_consistency": _logical_checks(frame, negative_values),
        "anomaly_examples": _anomaly_examples(records),
        "report_path": str(report_destination),
    }

    report_destination.parent.mkdir(parents=True, exist_ok=True)
    report_destination.write_text(_format_report(results), encoding="utf-8")
    return results


def _main() -> None:
    'Exécute l’interface en ligne de commande de l’audit.'
    parser = argparse.ArgumentParser(
        description='Audite le jeu JSON brut SNCF téléchargé localement.'
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_RAW_DATA_PATH,
        help=f"Fichier JSON brut en entrée (par défaut : {DEFAULT_RAW_DATA_PATH})",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Rapport textuel en sortie (par défaut : {DEFAULT_REPORT_PATH})",
    )
    arguments = parser.parse_args()
    results = audit_raw_data(arguments.input, arguments.report)
    print(
        f"Audit effectué sur {results['dataset_overview']['record_count']} observations. "
        f"Rapport enregistré dans {results['report_path']}"
    )


if __name__ == "__main__":
    _main()
