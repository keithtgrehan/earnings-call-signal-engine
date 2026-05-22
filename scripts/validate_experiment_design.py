#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from resource_registry_common import read_structured, write_json

REQUIRED_VARIANTS = {
    "deterministic_only",
    "deterministic_plus_retrieval",
    "deterministic_plus_byok_reviewer",
    "deterministic_plus_audio_metadata",
    "deterministic_plus_event_study_context",
}
FORBIDDEN_METRIC_TERMS = {"alpha", "trading", "live_execution", "buy", "sell"}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    variants = payload.get("variants")
    if not isinstance(variants, list):
        errors.append("variants must be a list")
        variant_ids: set[str] = set()
    else:
        variant_ids = {str(row.get("variant_id", "")) for row in variants if isinstance(row, dict)}
        for row in variants:
            if isinstance(row, dict) and row.get("deterministic_output_override_allowed") is not False:
                errors.append(f"variant {row.get('variant_id')}: deterministic override must be false")
    for variant in sorted(REQUIRED_VARIANTS - variant_ids):
        errors.append(f"missing variant {variant}")
    metrics = payload.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append("metrics must be a non-empty list")
    else:
        for metric in metrics:
            lowered = str(metric).lower()
            if any(term in lowered for term in FORBIDDEN_METRIC_TERMS):
                errors.append(f"forbidden primary metric {metric!r}")
    gate = payload.get("sample_gate")
    if not isinstance(gate, dict):
        errors.append("sample_gate must be represented")
    elif gate.get("power_check_required_before_significance_language") is not True:
        errors.append("sample gate must require power check before significance language")
    if payload.get("significance_claim_allowed") is not False:
        errors.append("significance_claim_allowed must be false")
    multivariate = payload.get("multivariate")
    if not isinstance(multivariate, dict):
        errors.append("multivariate design must be represented")
    else:
        for field in ("factors", "outcomes", "confounders", "stopping_rules"):
            if not multivariate.get(field):
                errors.append(f"multivariate.{field} must be represented")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate A/B and multivariate experiment-design guardrails.")
    parser.add_argument("--path", default="configs/experiment_design.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    try:
        payload = read_structured(Path(args.path))
        if not isinstance(payload, dict):
            raise ValueError("experiment design must be a YAML object")
        errors = validate_payload(payload)
    except Exception as exc:
        errors = [str(exc)]
    summary = {"status": "valid" if not errors else "invalid", "errors": errors}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if errors:
        print(f"Experiment design validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Experiment design validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
