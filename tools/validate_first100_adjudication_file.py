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
DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
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
ALLOWED_REJECTION_REASONS = {
    "safe_harbor_or_non_gaap",
    "operator_or_vendor_disclaimer",
    "generic_optimism",
    "historical_only",
    "analyst_only_unpaired_question",
    "unsupported_guidance_comparator",
    "wrong_case_or_period",
    "missing_source_or_hash",
    "duplicate_candidate",
    "source_needs_review",
    "not_a_signal",
}
REQUIRED_FIELDS = {
    "candidate_id",
    "case_id",
    "ticker",
    "fiscal_period",
    "adjudicated_label",
    "review_status",
    "gold_status",
    "reviewer",
    "reviewed_at",
    "rationale",
    "source_sha256",
    "normalized_transcript_hash",
    "text_hash",
    "provenance_hash",
}
OPTIONAL_FIELDS = {
    "suggested_label",
    "source_file",
    "evidence_object_id",
    "chunk_id",
    "rejection_reason",
    "unresolved_contamination_flags",
    "weak_label_only",
    "promotion_decision",
    "training_export_requested",
    "training_allowed",
    "explicit_training_rights_ref",
}
ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
RAW_TEXT_FIELDS = {"evidence_text", "raw_text", "snippet", "quote", "final_evidence_text"}
REVIEWER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{2,}$")
REVIEWED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows, errors = read_jsonl_with_errors(path)
    if errors:
        raise ValueError("; ".join(errors))
    return rows


def read_jsonl_with_errors(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: malformed JSON: {exc.msg}")
            continue
        if not isinstance(parsed, dict):
            errors.append(f"line {line_number}: JSONL row must be an object")
            continue
        rows.append(parsed)
    return rows, errors


def _is_sha256(value: Any) -> bool:
    return str(value or "").startswith("sha256:")


def _is_blocked_or_false(value: Any) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, bool):
        return False
    return str(value).strip().lower() in {"", "false", "0", "blocked", "not_allowed", "not_configured"}


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except (OSError, ValueError):
        return str(path)


def load_candidate_ids(candidates_path: Path) -> tuple[bool, set[str], list[str]]:
    if not candidates_path.exists():
        return False, set(), []
    rows, parse_errors = read_jsonl_with_errors(candidates_path)
    candidate_ids = {str(row.get("candidate_id", "")).strip() for row in rows if str(row.get("candidate_id", "")).strip()}
    errors = [f"candidate metadata {error}" for error in parse_errors]
    return True, candidate_ids, errors


def validate_rows(
    rows: list[dict[str, Any]],
    candidate_ids: set[str] | None = None,
    candidate_metadata_exists: bool | None = None,
    candidate_metadata_errors: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    if candidate_metadata_errors:
        errors.extend(candidate_metadata_errors)
    if rows and candidate_metadata_exists is False:
        errors.append("candidate metadata missing; non-empty adjudication rows cannot be validated fail-closed")
    for index, row in enumerate(rows, start=1):
        unknown_fields = sorted(set(row) - ALLOWED_FIELDS)
        for field in unknown_fields:
            errors.append(f"row {index}: unknown field {field}; remove unsupported fields before validation")

        for raw_field in RAW_TEXT_FIELDS:
            if raw_field in row:
                errors.append(f"row {index}: raw text field {raw_field} is not allowed in adjudication JSONL")

        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            errors.append(f"row {index}: missing candidate_id; copy the exact candidate_id from the first100 review packet")
        elif candidate_id in seen_candidate_ids:
            errors.append(f"row {index}: duplicate candidate_id {candidate_id}; keep one adjudication row per candidate")
        else:
            seen_candidate_ids.add(candidate_id)
        if candidate_id and candidate_ids is not None and candidate_id not in candidate_ids:
            errors.append(f"row {index}: candidate_id {candidate_id} not found in first100 candidate metadata")

        for field in sorted(REQUIRED_FIELDS):
            if not str(row.get(field, "")).strip():
                errors.append(f"row {index}: missing required field {field}")

        label = str(row.get("adjudicated_label") or row.get("final_label") or "").strip()
        if label not in ALLOWED_LABELS:
            errors.append(
                f"row {index}: invalid adjudicated_label {label!r}; use one of {', '.join(sorted(ALLOWED_LABELS))}"
            )

        review_status = str(row.get("review_status", "")).strip()
        if review_status != "adjudicated":
            errors.append(f"row {index}: review_status must be adjudicated")

        if row.get("gold_status") != "not_gold":
            errors.append(f"row {index}: gold_status must stay not_gold")

        reviewer = str(row.get("reviewer", "")).strip()
        if not REVIEWER_RE.match(reviewer):
            errors.append("row {index}: invalid reviewer; use a stable reviewer id with at least 3 letters/numbers".format(index=index))

        reviewed_at = str(row.get("reviewed_at", "")).strip()
        if not REVIEWED_AT_RE.match(reviewed_at):
            errors.append(f"row {index}: reviewed_at must be ISO-8601 UTC with trailing Z, e.g. 2026-05-31T12:00:00Z")

        has_evidence_ref = bool(row.get("evidence_object_id") or row.get("chunk_id"))
        has_hashes = (
            _is_sha256(row.get("source_sha256"))
            and _is_sha256(row.get("normalized_transcript_hash"))
            and _is_sha256(row.get("text_hash"))
            and _is_sha256(row.get("provenance_hash"))
        )
        if not has_evidence_ref or not has_hashes:
            errors.append(
                f"row {index}: missing evidence/provenance reference; include evidence_object_id or chunk_id plus source_sha256, normalized_transcript_hash, text_hash, and provenance_hash"
            )

        promotion_decision = str(row.get("promotion_decision", "not_requested")).strip()
        if promotion_decision != "not_requested":
            errors.append(
                f"row {index}: promotion_decision must be absent or not_requested; attempted promotion without manifest readiness"
            )

        training_requested = not _is_blocked_or_false(row.get("training_export_requested", False))
        training_allowed = not _is_blocked_or_false(row.get("training_allowed", False))
        explicit_rights = str(row.get("explicit_training_rights_ref", "")).strip()
        if training_requested or training_allowed or not _is_blocked_or_false(explicit_rights):
            errors.append(
                f"row {index}: unsupported training-rights claim; first100 adjudication drafts cannot request training export or assert training rights"
            )

        rejection_reason = str(row.get("rejection_reason", "")).strip()
        if label in {"reject_candidate", "needs_source_review"} and not rejection_reason:
            errors.append(f"row {index}: missing rejection_reason for adjudicated_label={label}")
        if rejection_reason and rejection_reason not in ALLOWED_REJECTION_REASONS:
            errors.append(
                f"row {index}: invalid rejection_reason {rejection_reason!r}; use one of {', '.join(sorted(ALLOWED_REJECTION_REASONS))}"
            )
    return errors


def validate_adjudication_file(
    path: Path = DEFAULT_ADJUDICATION,
    out_path: Path = REPORT_PATH,
    json_out_path: Path = JSON_REPORT_PATH,
    candidates_path: Path = DEFAULT_CANDIDATES,
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
    rows, parse_errors = read_jsonl_with_errors(path)
    candidate_metadata_exists, candidate_ids, candidate_metadata_errors = load_candidate_ids(candidates_path)
    errors = parse_errors
    if not parse_errors:
        errors = validate_rows(
            rows,
            candidate_ids=candidate_ids if candidate_metadata_exists else None,
            candidate_metadata_exists=candidate_metadata_exists if rows else None,
            candidate_metadata_errors=candidate_metadata_errors,
        )
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
    parser.add_argument(
        "adjudication_path",
        nargs="?",
        type=Path,
        help="Optional positional path to the adjudication draft JSONL.",
    )
    parser.add_argument("--adjudication", type=Path, default=DEFAULT_ADJUDICATION)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_REPORT_PATH)
    args = parser.parse_args(argv)
    adjudication_path = args.adjudication_path or args.adjudication
    summary = validate_adjudication_file(adjudication_path, args.out, args.json_out, args.candidates)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
