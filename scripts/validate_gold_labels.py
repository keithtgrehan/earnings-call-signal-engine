#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "case_id",
    "label_id",
    "signal_type",
    "direction",
    "speaker_role",
    "evidence_text",
    "evidence_start",
    "evidence_end",
    "confidence",
    "notes",
)

ENUMS = {
    "signal_type": {
        "guidance_revision",
        "analyst_pressure",
        "management_hedging",
        "uncertainty",
        "opportunity_commitment",
        "risk_friction",
        "neutral",
    },
    "direction": {"positive", "negative", "mixed", "neutral", "unknown"},
    "speaker_role": {"management", "analyst", "operator", "unknown"},
    "confidence": {"low", "medium", "high"},
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"line {line_number}: expected JSON object")
        rows.append(row)
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        if not str(row.get("case_id", "")).strip():
            errors.append(f"row {index}: case_id is required")
        if not str(row.get("label_id", "")).strip():
            errors.append(f"row {index}: label_id is required")
        for field, valid_values in ENUMS.items():
            if field in row and row[field] not in valid_values:
                errors.append(f"row {index}: invalid {field} {row[field]!r}")
        signal_type = row.get("signal_type")
        evidence_text = str(row.get("evidence_text", ""))
        if signal_type != "neutral" and not evidence_text.strip():
            errors.append(f"row {index}: evidence_text is required for non-neutral labels")
    return errors


def build_summary(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    errors = validate_rows(rows)
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "row_count": len(rows),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Signal Engine gold label JSONL.")
    parser.add_argument("--path", required=True, help="Gold label JSONL path to validate.")
    parser.add_argument("--json-out", help="Optional path for machine-readable validation summary.")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "row_count": 0, "errors": [str(exc)]}

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if summary["errors"]:
        print(f"Gold label validation failed: {summary['row_count']} row(s), {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1
    print(f"Gold label validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
