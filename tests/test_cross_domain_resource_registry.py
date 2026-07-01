from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "research" / "cross_domain_resource_registry.csv"

REQUIRED_COLUMNS = [
    "name",
    "domain",
    "modality",
    "task",
    "source_type",
    "license_status",
    "allowed_use",
    "benchmark_only_default",
    "training_allowed",
    "signal_engine_relevance",
    "dating_relevance",
    "affective_relevance",
    "risk_level",
    "notes",
]

FORBIDDEN_TERMS = [
    "buy recommendation",
    "sell recommendation",
    "alpha signal",
    "deception detection",
    "emotion truth",
    "loves you",
    "lying",
    "vulnerability targeting",
]


def load_rows() -> list[dict[str, str]]:
    with REGISTRY_PATH.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_csv_exists() -> None:
    assert REGISTRY_PATH.exists()


def test_required_columns_exist() -> None:
    with REGISTRY_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames is not None
        for column in REQUIRED_COLUMNS:
            assert column in reader.fieldnames


def test_no_blank_names() -> None:
    rows = load_rows()

    assert rows
    assert all(row["name"].strip() for row in rows)


def test_all_external_resources_are_benchmark_only_by_default() -> None:
    rows = load_rows()

    for row in rows:
        if row["source_type"] != "placeholder":
            assert row["benchmark_only_default"].lower() == "true", row["name"]


def test_training_allowed_false_without_explicit_license_review() -> None:
    rows = load_rows()

    for row in rows:
        if "explicit license review" not in row["notes"].lower():
            assert row["training_allowed"].lower() == "false", row["name"]


def test_risk_level_enum_valid() -> None:
    rows = load_rows()

    assert {row["risk_level"] for row in rows} <= {"low", "medium", "high"}


def test_allowed_use_does_not_make_gold_label_claims() -> None:
    rows = load_rows()

    for row in rows:
        assert "gold label" not in row["allowed_use"].lower(), row["name"]


def test_no_forbidden_terms_in_registry_rows() -> None:
    rows = load_rows()

    for row in rows:
        text = " ".join(row.values()).lower()
        for term in FORBIDDEN_TERMS:
            assert term not in text, f"{row['name']} uses forbidden term: {term}"
