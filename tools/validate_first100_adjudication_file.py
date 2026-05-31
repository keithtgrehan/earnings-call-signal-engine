#!/usr/bin/env python3
"""Validate first100 human adjudication JSONL without promoting labels."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADJUDICATION = ROOT / "data" / "review" / "staging" / "first100_adjudication_draft.jsonl"
REPORT_PATH = ROOT / "reports" / "review" / "first100_adjudication_file_validation.md"
JSON_REPORT_PATH = ROOT / "reports" / "review" / "first100_adjudication_file_validation.json"

ALLOWED_LABELS = {
    "guidance_revision",
    "guidance_statement",
    "analyst_pressure",
    "management_hedging",
    "uncertainty",
    "reassurance",
    "answer_shift",
    "neutral/no_signal",
    "reject_candidate",
    "needs_source_review",
    "needs_adjudication",
}
REVIEWER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{2,}$")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _is_sha256(value: Any) -> bool:
    return str(value or "").startswith("sha256:")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except (OSError, ValueError):
        return str(path)


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            errors.append(f"row {index}: missing candidate_id; copy the exact candidate_id from the first100 review packet")

        label = str(row.get("adjudicated_label") or row.get("final_label") or "").strip()
        if label not in ALLOWED_LABELS:
            errors.append(
                f"row {index}: invalid adjudicated_label {label!r}; use one of {', '.join(sorted(ALLOWED_LABELS))}"
            )

        reviewer = str(row.get("reviewer", "")).strip()
        if not REVIEWER_RE.match(reviewer):
            errors.append("row {index}: invalid reviewer; use a stable reviewer id with at least 3 letters/numbers".format(index=index))

        has_evidence_ref = bool(row.get("evidence_object_id") or row.get("chunk_id"))
        has_hashes = _is_sha256(row.get("source_sha256")) and _is_sha256(row.get("normalized_transcript_hash")) and _is_sha256(row.get("provenance_hash"))
        if not has_evidence_ref or not has_hashes:
            errors.append(
                f"row {index}: missing evidence/provenance reference; include evidence_object_id or chunk_id plus source_sha256, normalized_transcript_hash, and provenance_hash"
            )

        promotion_decision = str(row.get("promotion_decision", "not_requested")).strip()
        if promotion_decision not in {"not_requested", "defer_to_promotion_manifest"}:
            errors.append(
                f"row {index}: attempted promotion without manifest readiness; adjudication files must use promotion_decision=not_requested"
            )
        if row.get("gold_status") not in {"", "not_gold", None}:
            errors.append(f"row {index}: attempted promotion without manifest readiness; adjudication file gold_status must stay not_gold")

        training_requested = _as_bool(row.get("training_export_requested", False))
        training_allowed = _as_bool(row.get("training_allowed", False))
        explicit_rights = str(row.get("explicit_training_rights_ref", "")).strip()
        if training_requested or training_allowed or explicit_rights:
            errors.append(
                f"row {index}: unsupported training-rights claim; first100 adjudication drafts cannot request training export or assert training rights"
            )

        for raw_field in ("evidence_text", "raw_text", "snippet", "quote", "final_evidence_text"):
            if raw_field in row:
                errors.append(f"row {index}: raw text field {raw_field} is not allowed in adjudication JSONL")
    return errors


def validate_adjudication_file(
    path: Path = DEFAULT_ADJUDICATION,
    out_path: Path = REPORT_PATH,
    json_out_path: Path = JSON_REPORT_PATH,
) -> dict[str, Any]:
    if not path.exists():
        summary = {
            "status": "NOT_READY",
            "manifest_exists": False,
            "adjudicated_rows": 0,
            "valid": False,
            "error_count": 1,
            "errors": [f"adjudication file missing: {_display_path(path)}"],
            "promotion_ready": False,
            "training_ready": False,
            "gold_labels_created": 0,
        }
        write_reports(summary, out_path, json_out_path)
        return summary
    rows = read_jsonl(path)
    errors = validate_rows(rows)
    summary = {
        "status": "ADJUDICATION_DRAFT_VALID" if rows and not errors else "NOT_READY",
        "manifest_exists": True,
        "adjudicated_rows": len(rows),
        "valid": bool(rows) and not errors,
        "error_count": len(errors),
        "errors": errors[:200],
        "promotion_ready": False,
        "training_ready": False,
        "gold_labels_created": 0,
    }
    write_reports(summary, out_path, json_out_path)
    return summary


def write_reports(summary: dict[str, Any], out_path: Path, json_out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Adjudication File Validation",
        "",
        f"- Status: {summary['status']}",
        f"- Adjudication file exists: {str(summary['manifest_exists']).lower()}",
        f"- Adjudicated rows: {summary['adjudicated_rows']}",
        f"- Valid: {str(summary['valid']).lower()}",
        f"- Error count: {summary['error_count']}",
        "- Promotion ready: false",
        "- Training ready: false",
        "- Gold labels created: 0",
        "",
        "## Errors",
        "",
    ]
    errors = summary.get("errors") or []
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    json_out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate first100 adjudication draft JSONL without promotion.")
    parser.add_argument("--adjudication", type=Path, default=DEFAULT_ADJUDICATION)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_REPORT_PATH)
    args = parser.parse_args(argv)
    summary = validate_adjudication_file(args.adjudication, args.out, args.json_out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
