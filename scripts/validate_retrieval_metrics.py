#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from resource_registry_common import read_structured, write_json

REQUIRED_TOP_LEVEL = {
    "retrieval_metrics_version",
    "synthetic_fixture_only",
    "embeddings_required",
    "vector_db_required",
    "provider_calls_allowed",
    "deterministic_override_allowed",
    "metric_groups",
}
REQUIRED_METRICS = {"recall_at_k", "mrr"}
REQUIRED_DESIGNS = {"ab_test", "multivariate"}


def validate_config(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(REQUIRED_TOP_LEVEL - set(payload)):
        errors.append(f"missing required field {field}")
    for field in ("synthetic_fixture_only",):
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in ("embeddings_required", "vector_db_required", "provider_calls_allowed", "deterministic_override_allowed"):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    groups = payload.get("metric_groups")
    if not isinstance(groups, list) or not groups:
        errors.append("metric_groups must be a non-empty list")
    else:
        for index, group in enumerate(groups, start=1):
            if not isinstance(group, dict):
                errors.append(f"metric_groups[{index}] must be an object")
                continue
            metrics = set(group.get("metrics") or [])
            for metric in sorted(REQUIRED_METRICS - metrics):
                errors.append(f"metric_groups[{index}] missing metric {metric}")
            designs = set(group.get("comparison_designs") or [])
            for design in sorted(REQUIRED_DESIGNS - designs):
                errors.append(f"metric_groups[{index}] missing comparison design {design}")
            if group.get("rights_required") is not True:
                errors.append(f"metric_groups[{index}] must require rights")
            if group.get("provenance_required") is not True:
                errors.append(f"metric_groups[{index}] must require provenance")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate synthetic retrieval metric guardrails.")
    parser.add_argument("--path", default="configs/retrieval_metrics.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        payload = read_structured(Path(args.path))
        if not isinstance(payload, dict):
            raise ValueError("Retrieval metrics config must be an object.")
        errors = validate_config(payload)
    except Exception as exc:
        errors = [str(exc)]
    summary = {"status": "valid" if not errors else "invalid", "errors": errors}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if errors:
        print(f"Retrieval metrics validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Retrieval metrics validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
