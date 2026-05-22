from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import json

import yaml

from signal_engine.benchmarks import classify_benchmark_groups, load_benchmark_registry, validate_benchmark_rows

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = ROOT / "scripts" / "validate_benchmark_registry.py"
BYOK_SCRIPT = ROOT / "scripts" / "validate_byok_reviewer_config.py"


def test_benchmark_registry_external_and_weak_labels_cannot_write_gold() -> None:
    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--path", "configs/benchmark_registry.example.yml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_benchmark_registry_rejects_external_gold_write(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "benchmark_registry.example.yml").read_text(encoding="utf-8"))
    payload["benchmarks"][2]["writes_gold"] = True
    path = tmp_path / "bad_benchmarks.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "must not write gold" in result.stdout


def test_benchmark_helper_groups_and_rejects_external_gold_write() -> None:
    rows = load_benchmark_registry(ROOT / "configs" / "benchmark_registry.example.yml")
    grouped = classify_benchmark_groups(rows)
    assert grouped["external_dataset"][0]["default_use"] == "benchmark_only"

    bad_rows = [dict(row) for row in rows]
    bad_rows[2]["writes_gold"] = True
    errors = validate_benchmark_rows(bad_rows)

    assert any("must not write gold" in error for error in errors)


def test_external_dataset_metadata_blocks_training_by_default() -> None:
    rows = load_benchmark_registry(ROOT / "configs" / "benchmark_registry.example.yml")
    external = next(row for row in rows if row["benchmark_group"] == "external_dataset")

    assert external["default_use"] == "benchmark_only"
    assert external["training_allowed"] is False
    assert external["writes_gold"] is False
    assert external["weak_labels_can_be_gold"] is False
    assert all(dataset["training_allowed"] is False for dataset in external["datasets"])
    assert {dataset["dataset_id"] for dataset in external["datasets"]} >= {
        "ectsum",
        "financebench",
        "financial_phrasebank",
        "fiqa",
        "finqa",
        "convfinqa",
        "finmteb",
        "finben",
        "flame",
    }


def test_byok_output_role_cannot_be_canonical(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "byok_reviewer.example.yml").read_text(encoding="utf-8"))
    payload["output_role"] = "canonical"
    path = tmp_path / "bad_byok.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(BYOK_SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "reviewer or candidate" in result.stdout


def test_byok_provider_calls_and_canonical_output_blocked(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "byok_reviewer.example.yml").read_text(encoding="utf-8"))
    payload["canonical_output"] = True
    payload["provider_calls_enabled"] = True
    path = tmp_path / "bad_byok_calls.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(BYOK_SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "canonical_output must be false" in result.stdout
    assert "provider_calls_enabled must be false" in result.stdout


def test_byok_request_response_schemas_are_reviewer_only() -> None:
    request_schema = json.loads((ROOT / "schemas" / "byok_reviewer_request.schema.json").read_text(encoding="utf-8"))
    response_schema = json.loads((ROOT / "schemas" / "byok_reviewer_response.schema.json").read_text(encoding="utf-8"))

    assert "canonical_output" in request_schema["required"]
    assert request_schema["properties"]["canonical_output"]["const"] is False
    assert request_schema["properties"]["provider_calls_enabled"]["const"] is False
    assert response_schema["properties"]["canonical_output"]["const"] is False
    assert response_schema["properties"]["provider_calls_performed"]["const"] is False
