#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from resource_registry_common import read_structured, write_json

REQUIRED_JOIN_KEYS = {"ticker", "fiscal_period", "call_datetime", "market_session"}
REQUIRED_CONTROLS = {"earnings_surprise_status", "market_proxy", "sector_proxy", "confounder_notes"}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    join_key = set(payload.get("join_key") or [])
    for key in sorted(REQUIRED_JOIN_KEYS - join_key):
        errors.append(f"missing join key {key}")
    controls = payload.get("required_controls")
    if not isinstance(controls, dict):
        errors.append("required_controls must be represented")
    else:
        for control in sorted(REQUIRED_CONTROLS - set(controls)):
            errors.append(f"missing required control {control}")
    gates = payload.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be represented")
    else:
        if gates.get("significance_claim_allowed") is not False:
            errors.append("significance_claim_allowed must be false by default")
        if int(gates.get("min_events", 0)) <= 0:
            errors.append("min_events must be positive")
        if int(gates.get("min_gold_labels", 0)) <= 0:
            errors.append("min_gold_labels must be positive")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must contain synthetic metadata examples")
    else:
        for index, row in enumerate(cases, start=1):
            for field in REQUIRED_JOIN_KEYS | REQUIRED_CONTROLS | {"gold_signal_join_status", "significance_claim_allowed"}:
                if field not in row:
                    errors.append(f"case {index}: missing field {field}")
            if row.get("significance_claim_allowed") is not False:
                errors.append(f"case {index}: significance_claim_allowed must be false")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate event-study metadata join policy without market-data fetches.")
    parser.add_argument("--path", default="configs/event_study_join_policy.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    try:
        payload = read_structured(Path(args.path))
        if not isinstance(payload, dict):
            raise ValueError("event-study join policy must be a YAML object")
        errors = validate_payload(payload)
    except Exception as exc:
        errors = [str(exc)]
    summary = {"status": "valid" if not errors else "invalid", "errors": errors}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if errors:
        print(f"Event-study join validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Event-study join validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
