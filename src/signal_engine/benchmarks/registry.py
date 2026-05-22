from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_GROUPS = {
    "deterministic_extraction",
    "retrieval",
    "external_dataset",
    "media",
    "byok_llm_reviewer",
}


def load_benchmark_registry(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("benchmarks"), list):
        raise ValueError("Benchmark registry must be an object with a benchmarks list.")
    rows = payload["benchmarks"]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every benchmark entry must be an object.")
    return rows


def classify_benchmark_groups(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {group: [] for group in REQUIRED_GROUPS}
    for row in rows:
        grouped.setdefault(str(row.get("benchmark_group", "")), []).append(row)
    return grouped


def validate_benchmark_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    groups = {str(row.get("benchmark_group", "")) for row in rows}
    for group in sorted(REQUIRED_GROUPS - groups):
        errors.append(f"missing benchmark_group {group}")
    for index, row in enumerate(rows, start=1):
        for field in (
            "benchmark_id",
            "benchmark_group",
            "status",
            "default_use",
            "minimum_gold_labels",
            "writes_gold",
            "weak_labels_can_be_gold",
            "production_ml_claim_allowed",
        ):
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        if row.get("benchmark_group") == "external_dataset" and row.get("default_use") != "benchmark_only":
            errors.append(f"row {index}: external datasets must default to benchmark_only")
        if row.get("benchmark_group") == "external_dataset":
            if row.get("training_allowed") is not False:
                errors.append(f"row {index}: external benchmark group cannot allow training by default")
            datasets = row.get("datasets") or []
            if not isinstance(datasets, list):
                errors.append(f"row {index}: datasets must be a list")
            for dataset_index, dataset in enumerate(datasets, start=1):
                if isinstance(dataset, str):
                    continue
                if not isinstance(dataset, dict):
                    errors.append(f"row {index}: datasets[{dataset_index}] must be a string or object")
                    continue
                if dataset.get("default_use") != "benchmark_only":
                    errors.append(f"row {index}: datasets[{dataset_index}] must default to benchmark_only")
                if dataset.get("training_allowed") is not False:
                    errors.append(f"row {index}: datasets[{dataset_index}] cannot allow training by default")
                if not str(dataset.get("source_reference", "")).strip():
                    errors.append(f"row {index}: datasets[{dataset_index}] missing source_reference")
                if not str(dataset.get("rights_caveat", "")).strip():
                    errors.append(f"row {index}: datasets[{dataset_index}] missing rights_caveat")
        if row.get("writes_gold") is not False:
            errors.append(f"row {index}: benchmark entries must not write gold labels")
        if row.get("weak_labels_can_be_gold") is not False:
            errors.append(f"row {index}: weak labels cannot become gold")
        if row.get("production_ml_claim_allowed") is not False:
            errors.append(f"row {index}: production ML quality claims are not allowed")
    return errors
