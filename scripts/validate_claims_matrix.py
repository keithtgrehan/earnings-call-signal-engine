#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from resource_registry_common import write_json

FORBIDDEN_CLAIM_MARKERS = {
    "alpha",
    "live_trading",
    "live execution",
    "statistical significance",
    "statistically significant",
    "investment advice",
}

ALLOWED_STATUSES = {"supported", "gated", "planned", "not_supported"}


def _claim_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("claims"), list):
        rows = payload["claims"]
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError("Claims matrix must be a list or an object with a claims list.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every claim row must be an object.")
    return rows


def validate_claims(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        claim = str(row.get("claim", "")).strip()
        status = str(row.get("status", "")).strip()
        evidence_gate = str(row.get("evidence_gate", "")).strip()
        if not claim:
            errors.append(f"row {index}: claim is required")
        if status not in ALLOWED_STATUSES:
            errors.append(f"row {index}: invalid status {status!r}")
        lowered = " ".join([claim, str(row.get("notes", "")), str(row.get("claim_type", ""))]).lower()
        if any(marker in lowered for marker in FORBIDDEN_CLAIM_MARKERS) and status != "not_supported":
            errors.append(f"row {index}: unsupported alpha/live-trading/statistical-significance claim must be not_supported")
        if status == "supported" and not evidence_gate:
            errors.append(f"row {index}: supported claim requires evidence_gate")
    return errors


def build_summary(path: Path) -> dict[str, Any]:
    rows = _claim_rows(yaml.safe_load(path.read_text(encoding="utf-8")))
    errors = validate_claims(rows)
    return {"status": "valid" if not errors else "invalid", "path": str(path), "row_count": len(rows), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Signal Engine claim support/gating matrix.")
    parser.add_argument("--path", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "row_count": 0, "errors": [str(exc)]}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if summary["errors"]:
        print(f"Claims matrix validation failed: {summary['row_count']} row(s), {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1
    print(f"Claims matrix validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
