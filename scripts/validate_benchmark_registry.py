#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from resource_registry_common import write_json

REQUIRED_GROUPS = {
    "deterministic_extraction",
    "retrieval",
    "external_dataset",
    "media",
    "byok_llm_reviewer",
}


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("benchmarks"), list):
        rows = payload["benchmarks"]
    else:
        raise ValueError("Benchmark registry must be an object with a benchmarks list.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every benchmark entry must be an object.")
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    groups = {str(row.get("benchmark_group", "")) for row in rows}
    for group in sorted(REQUIRED_GROUPS - groups):
        errors.append(f"missing benchmark_group {group}")
    for index, row in enumerate(rows, start=1):
        for field in ("benchmark_id", "benchmark_group", "status", "default_use", "writes_gold", "production_ml_claim_allowed"):
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        if row.get("benchmark_group") == "external_dataset" and row.get("default_use") != "benchmark_only":
            errors.append(f"row {index}: external datasets must default to benchmark_only")
        if row.get("writes_gold") is not False:
            errors.append(f"row {index}: benchmark entries must not write gold labels")
        if row.get("weak_labels_can_be_gold") is not False:
            errors.append(f"row {index}: weak labels cannot become gold")
        if row.get("production_ml_claim_allowed") is not False:
            errors.append(f"row {index}: production ML quality claims are not allowed")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate benchmark registry guardrails.")
    parser.add_argument("--path", default="configs/benchmark_registry.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        rows = _rows(yaml.safe_load(Path(args.path).read_text(encoding="utf-8")))
        errors = validate_rows(rows)
    except Exception as exc:
        rows = []
        errors = [str(exc)]
    summary = {"status": "valid" if not errors else "invalid", "row_count": len(rows), "errors": errors}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if errors:
        print(f"Benchmark registry validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Benchmark registry validation passed: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
