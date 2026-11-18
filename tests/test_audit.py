'Tests de l’audit local de qualité des données SNCF.'

import json
from pathlib import Path
from typing import Any

import pytest

from projet_kit_data.etl.audit import audit_raw_data


def sample_records() -> list[dict[str, Any]]:
    'Renvoie un petit jeu de données avec des anomalies connues.'
    first = {
        "date": "2024-01",
        "service": "National",
        "gare_depart": "BORDEAUX ST JEAN",
        "gare_arrivee": "PARIS MONTPARNASSE",
        "nb_train_prevu": 10,
        "nb_annulation": 11,
        "nb_train_depart_retard": 12,
        "nb_train_retard_arrivee": 3,
        "nb_train_retard_sup_15": -1,
        "retard_moyen_depart": -5.0,
        "prct_cause_externe": 105.0,
        "commentaire_annulation": None,
        "extra_metric": 1,
    }
    exact_duplicate = first.copy()
    same_business_key = {
        **first,
        "nb_annulation": 0,
        "nb_train_depart_retard": 0,
        "nb_train_retard_arrivee": 11,
        "nb_train_retard_sup_15": 0,
        "retard_moyen_depart": -1.0,
        "prct_cause_externe": 50.0,
        "commentaire_annulation": "incident",
    }
    separate_key = {
        **same_business_key,
        "gare_depart": "LYON PART DIEU",
        "gare_arrivee": "PARIS GARE DE LYON",
        "retard_moyen_depart": 0.0,
        "prct_cause_externe": -2.0,
        "extra_metric": 4,
    }
    return [first, exact_duplicate, same_business_key, separate_key]


def write_records(path: Path, records: object) -> None:
    'Écrit un fichier JSON d’entrée temporaire.'
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")


def test_audit_reports_overview_and_schema_differences(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.json"
    report_path = tmp_path / "reports" / "audit.txt"
    write_records(input_path, sample_records())

    results = audit_raw_data(input_path, report_path)

    overview = results["dataset_overview"]
    assert overview["record_count"] == 4
    assert overview["column_count"] == 13
    assert "extra_metric" in overview["unexpected_columns"]
    assert "date" in overview["available_columns"]
    assert "service" in overview["data_types"]
    assert overview["data_types"]["nb_train_prevu"]["polars_dtype"] == "Int64"
    assert "duree_moyenne" in overview["missing_expected_columns"]


def test_audit_counts_missing_values(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.json"
    write_records(input_path, sample_records())

    results = audit_raw_data(input_path, tmp_path / "audit.txt")

    assert results["missing_values"]["commentaire_annulation"] == {
        "count": 2,
        "percentage": 50.0,
        "percentage_denominator": 4,
    }
    assert results["missing_values"]["duree_moyenne"]["count"] == 4


def test_audit_counts_exact_and_business_key_duplicates(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.json"
    write_records(input_path, sample_records())

    results = audit_raw_data(input_path, tmp_path / "audit.txt")

    duplicates = results["duplicates"]
    assert duplicates["exact_duplicate_record_count"] == 1
    assert duplicates["exact_duplicate_group_count"] == 1
    assert duplicates["business_key_duplicate_record_count"] == 2
    assert duplicates["business_key_duplicate_group_count"] == 1


def test_audit_reports_negative_values_without_treating_them_as_invalid(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "raw.json"
    write_records(input_path, sample_records())

    results = audit_raw_data(input_path, tmp_path / "audit.txt")

    negative_delay = results["negative_values"]["retard_moyen_depart"]
    assert negative_delay["negative_count"] == 3
    assert negative_delay["numeric_value_count"] == 4
    assert negative_delay["percentage"] == 75.0
    assert results["numerical_statistics"]["retard_moyen_depart"]["minimum"] == -5.0
    assert results["numerical_statistics"]["retard_moyen_depart"]["maximum"] == 0.0
    assert results["numerical_statistics"]["retard_moyen_depart"]["quantiles"][
        "95"
    ] == pytest.approx(-0.15)


def test_audit_reports_logical_consistency_diagnostics(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.json"
    write_records(input_path, sample_records())

    results = audit_raw_data(input_path, tmp_path / "audit.txt")

    logical = results["logical_consistency"]
    checks = logical["count_greater_than_planned_checks"]
    assert (
        checks["nb_annulation_greater_than_nb_train_prevu"]["affected_record_count"]
        == 2
    )
    assert (
        checks["departure_delay_count_greater_than_nb_train_prevu"][
            "affected_record_count"
        ]
        == 2
    )
    assert (
        checks["nb_train_retard_arrivee_greater_than_nb_train_prevu"][
            "affected_record_count"
        ]
        == 2
    )
    assert logical["negative_count_fields"]["affected_record_count"] == 2
    assert logical["cause_percentages_outside_0_to_100"]["affected_record_count"] == 3


def test_audit_includes_anomaly_examples_and_threshold_ordering(
    tmp_path: Path,
) -> None:
    records = sample_records()
    for record in records:
        record.update(
            {
                "nb_train_retard_sup_30": -2,
                "nb_train_retard_sup_60": 0,
                "retard_moyen_trains_retard_sup15": -2.5,
                "retard_moyen_tous_trains_arrivee": -20.1,
                "retard_moyen_tous_trains_depart": -21.1,
                "retard_moyen_arrivee": -19.0,
            }
        )
    input_path = tmp_path / "raw.json"
    write_records(input_path, records)

    results = audit_raw_data(input_path, tmp_path / "audit.txt")

    anomalies = results["anomaly_examples"]
    checks = anomalies["checks"]
    negative_30 = checks["negative_nb_train_retard_sup_30"]
    assert negative_30["record_count"] == 4
    assert negative_30["examples"][0]["nb_train_retard_sup_30"] == -2
    assert negative_30["examples"][0]["date"] == "2024-01"
    assert checks["negative_retard_moyen_trains_retard_sup15"]["record_count"] == 4
    assert checks["cancellations_exceed_planned"]["record_count"] == 2
    assert (
        anomalies["extremely_negative_delay_values"][
            "retard_moyen_tous_trains_arrivee"
        ]["record_count"]
        == 4
    )
    assert (
        anomalies["extremely_negative_delay_values"]["retard_moyen_arrivee"][
            "examples"
        ][0]["nb_train_retard_arrivee"]
        == 3
    )
    ordering = anomalies["threshold_ordering"]
    assert ordering["expected_order"] == (
        "nb_train_retard_sup_15 >= nb_train_retard_sup_30 >= nb_train_retard_sup_60"
    )
    assert ordering["record_count"] == 4
    assert "concurrence avec l’avion" in ordering["note"]
    assert (
        ordering["pairwise_checks"]["nb_train_retard_sup_30_ge_nb_train_retard_sup_60"][
            "record_count"
        ]
        == 4
    )


def test_anomaly_examples_are_limited_to_ten(tmp_path: Path) -> None:
    records = sample_records() * 3
    for record in records:
        record["nb_train_retard_sup_30"] = -1
    input_path = tmp_path / "raw.json"
    write_records(input_path, records)

    results = audit_raw_data(input_path, tmp_path / "audit.txt")

    summary = results["anomaly_examples"]["checks"]["negative_nb_train_retard_sup_30"]
    assert summary["record_count"] == 12
    assert len(summary["examples"]) == 10


def test_audit_generates_readable_report_without_changing_raw_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "raw.json"
    report_path = tmp_path / "nested" / "audit.txt"
    write_records(input_path, sample_records())
    original_contents = input_path.read_bytes()

    audit_raw_data(input_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert 'Aperçu du jeu de données' in report
    assert 'Valeurs manquantes' in report
    assert "Duplicates" in report
    assert 'Valeurs numériques négatives' in report
    assert 'Statistiques numériques' in report
    assert 'Diagnostics de cohérence logique' in report
    assert 'Exemples d’anomalies' in report
    assert "negative_nb_train_retard_sup_30" in report
    assert "Threshold ordering" in report
    assert "Aucune observation ni valeur n’a été modifiée." in report
    assert input_path.read_bytes() == original_contents


def test_audit_handles_empty_dataset(tmp_path: Path) -> None:
    input_path = tmp_path / "empty.json"
    report_path = tmp_path / "audit.txt"
    write_records(input_path, [])

    results = audit_raw_data(input_path, report_path)

    assert results["dataset_overview"]["record_count"] == 0
    assert results["dataset_overview"]["column_count"] == 0
    assert results["duplicates"]["exact_duplicate_record_count"] == 0
    assert results["negative_values"]["nb_train_prevu"]["percentage"] is None
    assert report_path.exists()
    assert 'Observations : 0' in report_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("contents", "exception"),
    [
        ("{not-json", json.JSONDecodeError),
        ('{"not": "an array"}', ValueError),
        ("[1]", ValueError),
    ],
)
def test_audit_rejects_invalid_input(
    tmp_path: Path,
    contents: str,
    exception: type[Exception],
) -> None:
    input_path = tmp_path / "invalid.json"
    input_path.write_text(contents, encoding="utf-8")

    with pytest.raises(exception):
        audit_raw_data(input_path, tmp_path / "audit.txt")
