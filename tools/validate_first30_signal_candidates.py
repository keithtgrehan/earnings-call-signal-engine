#!/usr/bin/env python3
"""Validate first30 signal candidates remain metadata-only and not gold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.first30_extraction import validate_candidate_rows

DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first30_signal_candidates.jsonl"
REPORT_PATH = ROOT / "reports" / "extraction" / "first30_signal_candidate_validation.md"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate(path: Path = DEFAULT_CANDIDATES, out_path: Path = REPORT_PATH) -> dict[str, Any]:
    rows = read_jsonl(path)
    errors = validate_candidate_rows(rows)
    summary = {
        "candidate_rows": len(rows),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors[:100],
        "gold_labels_created": 0,
        "raw_text_committed": False,
    }
    write_report(summary, out_path)
    return summary


def write_report(summary: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Signal Candidate Validation",
        "",
        f"- Candidate rows: {summary['candidate_rows']}",
        f"- Valid: {str(summary['valid']).lower()}",
        f"- Error count: {summary['error_count']}",
        "- Gold labels created: 0",
        "- Raw evidence text committed: false",
        "",
        "## Errors",
        "",
    ]
    errors = summary.get("errors") or []
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate first30 signal candidate guardrails.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    summary = validate(args.candidates, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
