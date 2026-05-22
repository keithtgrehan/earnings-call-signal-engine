#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from resource_registry_common import read_structured, write_json

REQUIRED_EVENT_STUDY_FIELDS = {
    "event_id",
    "event_date",
    "event_window",
    "estimation_window",
    "expected_return_model",
    "controls",
    "outputs",
    "failure_modes",
    "benchmark_gating",
    "exploratory_only",
    "claim_limitations",
    "provenance_hash",
}

EXPECTED_RETURN_MODELS = {"market_adjusted", "sector_adjusted", "market_model"}
REQUIRED_CONTROLS = {"earnings_surprise", "sector_return", "market_return"}
REQUIRED_OUTPUTS = {"abnormal_return", "cumulative_abnormal_return"}
UNSAFE_CLAIM_TERMS = {
    "alpha",
    "trading performance",
    "live execution",
    "production ml",
    "statistically significant",
    "statistical significance",
    "causal",
    "causality",
}
NEGATION_MARKERS = {"no ", "not ", "unsupported", "exploratory", "non-goal"}


def normalize_event_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("event_study_cases") or payload.get("cases") or payload.get("events")
    else:
        rows = None
    if not isinstance(rows, list):
        raise ValueError("Event-study registry must be a list or an object with event_study_cases/cases/events.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every event-study case must be an object.")
    return rows


def _claims_are_limited(text: str) -> bool:
    lowered = text.lower()
    if not any(term in lowered for term in UNSAFE_CLAIM_TERMS):
        return True
    return any(marker in lowered for marker in NEGATION_MARKERS)


def validate_event_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in sorted(REQUIRED_EVENT_STUDY_FIELDS - set(row)):
            errors.append(f"row {index}: missing required field {field}")
        model = str(row.get("expected_return_model", "")).strip()
        if model not in EXPECTED_RETURN_MODELS:
            errors.append(f"row {index}: expected_return_model must be one of {sorted(EXPECTED_RETURN_MODELS)}")
        controls = row.get("controls")
        if not isinstance(controls, dict):
            errors.append(f"row {index}: controls must be an object")
        else:
            missing_controls = sorted(REQUIRED_CONTROLS - set(controls))
            for control in missing_controls:
                errors.append(f"row {index}: missing control {control}")
        outputs = row.get("outputs")
        if not isinstance(outputs, dict):
            errors.append(f"row {index}: outputs must be an object")
        else:
            missing_outputs = sorted(REQUIRED_OUTPUTS - set(outputs))
            for output in missing_outputs:
                errors.append(f"row {index}: missing output {output}")
            for output_name, output_status in outputs.items():
                if output_name in REQUIRED_OUTPUTS and output_status != "exploratory_only":
                    errors.append(f"row {index}: {output_name} must be exploratory_only")
        failure_modes = row.get("failure_modes")
        if not isinstance(failure_modes, list) or len(failure_modes) < 3:
            errors.append(f"row {index}: failure_modes must list core confounding risks")
        benchmark_gating = row.get("benchmark_gating")
        if not isinstance(benchmark_gating, dict) or not benchmark_gating:
            errors.append(f"row {index}: benchmark_gating must be represented")
        if row.get("exploratory_only") is not True:
            errors.append(f"row {index}: event-study cases must be exploratory_only")
        claim_limitations = str(row.get("claim_limitations", ""))
        if not claim_limitations.strip():
            errors.append(f"row {index}: claim_limitations must be represented")
        if not _claims_are_limited(claim_limitations):
            errors.append(f"row {index}: unsafe event-study claim is not explicitly negated or limited")
        if row.get("claim_allowed") is True:
            errors.append(f"row {index}: event-study claim_allowed cannot be true in scaffold")
    return errors


def build_summary(path: Path) -> dict[str, Any]:
    rows = normalize_event_rows(read_structured(path))
    errors = validate_event_rows(rows)
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "row_count": len(rows),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate event-study scaffold cases without downloading price data.")
    parser.add_argument("--path", default="configs/event_study_cases.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "row_count": 0, "errors": [str(exc)]}

    if args.json_out:
        write_json(Path(args.json_out), summary)

    errors = summary["errors"]
    if errors:
        print(f"Event-study validation failed: {summary['row_count']} row(s), {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Event-study validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
