#!/usr/bin/env python3
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

from signal_engine.agent5_acquisition import validate_manual_local_registry


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_readiness(*, registry_path: Path) -> dict[str, Any]:
    if not registry_path.exists():
        return {
            "state": "NOT_READY",
            "manual_local_registry_exists": False,
            "registered_transcript_count": 0,
            "valid_source_hash_count": 0,
            "eligible_case_count": 0,
            "can_generate_real_candidates": False,
            "missing_fields": ["manual_local_registry.jsonl is missing"],
            "validation_errors": [],
        }
    rows = _load_jsonl(registry_path)
    errors = validate_manual_local_registry(rows)
    transcript_rows = [row for row in rows if row.get("media_type") == "transcript"]
    valid_hash_rows = [row for row in transcript_rows if str(row.get("source_sha256", "")).startswith("sha256:")]
    eligible_cases = sorted({str(row.get("case_id", "")) for row in valid_hash_rows if row.get("case_id")})
    missing_fields: list[str] = []
    if not transcript_rows:
        missing_fields.append("no transcript media_type rows")
    if not valid_hash_rows:
        missing_fields.append("no transcript rows with sha256 source hash")
    state = "READY_FOR_AGENT1_DETERMINISTIC_CANDIDATES" if not errors and valid_hash_rows else "NOT_READY"
    return {
        "state": state,
        "manual_local_registry_exists": True,
        "registered_transcript_count": len(transcript_rows),
        "valid_source_hash_count": len(valid_hash_rows),
        "eligible_case_count": len(eligible_cases),
        "can_generate_real_candidates": state == "READY_FOR_AGENT1_DETERMINISTIC_CANDIDATES",
        "missing_fields": missing_fields,
        "validation_errors": errors,
    }


def _write_report(path: Path, readiness: dict[str, Any]) -> None:
    lines = [
        "# Agent 1 Candidate Generation Readiness",
        "",
        f"- State: `{readiness['state']}`",
        f"- Manual-local registry exists: `{str(readiness['manual_local_registry_exists']).lower()}`",
        f"- Registered transcript count: `{readiness['registered_transcript_count']}`",
        f"- Valid source hash count: `{readiness['valid_source_hash_count']}`",
        f"- Eligible case count: `{readiness['eligible_case_count']}`",
        f"- Agent 1 can generate real candidates: `{str(readiness['can_generate_real_candidates']).lower()}`",
        "",
        "## Missing Fields",
        "",
    ]
    missing = readiness.get("missing_fields") or []
    lines.extend(f"- {item}" for item in missing)
    if not missing:
        lines.append("- none")
    errors = readiness.get("validation_errors") or []
    lines.extend(["", "## Validation Errors", ""])
    lines.extend(f"- {item}" for item in errors)
    if not errors:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report whether Agent 1 can generate real deterministic candidates from manual-local transcript registrations.")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--report", default="reports/agent1_candidate_generation_readiness.md")
    parser.add_argument("--json", default="reports/agent1_candidate_generation_readiness.json")
    args = parser.parse_args(argv)
    readiness = build_readiness(registry_path=Path(args.registry))
    _write_report(Path(args.report), readiness)
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Agent 1 candidate readiness: {readiness['state']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
