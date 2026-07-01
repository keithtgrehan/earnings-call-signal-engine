#!/usr/bin/env python3
"""Validate first100 promotion manifests with hard anti-contamination gates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "review" / "staging" / "first100_promotion_manifest.jsonl"
REPORT_PATH = ROOT / "reports" / "review" / "first100_promotion_manifest_validation.md"
JSON_REPORT_PATH = ROOT / "reports" / "review" / "first100_promotion_manifest_validation.json"
ALLOWED_FINAL_LABELS = {
    "guidance_revision",
    "guidance_statement",
    "analyst_pressure",
    "management_hedging",
    "uncertainty",
    "reassurance",
    "answer_shift",
    "neutral/no_signal",
    "reject_candidate",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _looks_like_repo_raw_text(value: Any) -> bool:
    text = str(value or "")
    if not text:
        return False
    if text.startswith("sha256:"):
        return False
    if text.startswith("/Users/keith/Desktop/"):
        return False
    return len(text.split()) > 3 or "\n" in text


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    label_ids: list[str] = []
    provenance_hashes: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in ("adjudicator", "adjudicated_at", "final_label", "source_file", "source_sha256", "normalized_transcript_hash", "provenance_hash"):
            if not row.get(field):
                errors.append(f"row {index}: missing {field}")
        if not row.get("candidate_id"):
            errors.append(f"row {index}: missing candidate_id; copy the exact candidate_id from the adjudicated review row")
        final_label = str(row.get("final_label", "")).strip()
        if final_label and final_label not in ALLOWED_FINAL_LABELS:
            errors.append(f"row {index}: invalid final_label {final_label!r}; use a supported first100 review label")
        if row.get("review_status") != "adjudicated":
            errors.append(f"row {index}: review_status must be adjudicated")
        if row.get("gold_status") != "promotion_candidate":
            errors.append(f"row {index}: attempted promotion without manifest readiness; gold_status must be promotion_candidate only in a reviewed promotion manifest")
        if not (row.get("final_evidence_text_hash") or row.get("final_evidence_text_ref") or row.get("final_evidence_text")):
            errors.append(f"row {index}: missing final_evidence_text proof")
        if _looks_like_repo_raw_text(row.get("final_evidence_text")):
            errors.append(f"row {index}: final_evidence_text appears to contain raw text in repo output")
        if row.get("source_type") == "external_dataset":
            errors.append(f"row {index}: external_dataset sources cannot be promoted")
        if row.get("weak_label_only") is True or str(row.get("weak_label_only", "")).lower() == "true":
            errors.append(f"row {index}: weak_label_only rows cannot be promoted")
        unresolved = row.get("unresolved_contamination_flags", [])
        if isinstance(unresolved, str):
            unresolved = [flag for flag in unresolved.split(";") if flag]
        if unresolved:
            errors.append(f"row {index}: unresolved contamination flags remain")
        label_id = str(row.get("label_id") or row.get("candidate_id") or "")
        if not label_id:
            errors.append(f"row {index}: missing label_id or candidate_id")
        label_ids.append(label_id)
        provenance_hash = str(row.get("provenance_hash") or "")
        provenance_hashes.append(provenance_hash)
        if row.get("final_label") and row.get("final_label") == row.get("suggested_label") and not row.get("rationale"):
            errors.append(f"row {index}: machine suggestion copied as final label without rationale")
        training_requested = str(row.get("training_export_requested", "")).lower() == "true"
        training_allowed = str(row.get("training_allowed", "false")).lower() == "true"
        if training_requested and not training_allowed:
            errors.append(f"row {index}: unsupported training-rights claim; training_allowed false but training export requested")
    duplicate_label_ids = [item for item, count in Counter(label_ids).items() if item and count > 1]
    duplicate_provenance = [item for item, count in Counter(provenance_hashes).items() if item and count > 1]
    errors.extend(f"duplicate label_id {item}" for item in duplicate_label_ids)
    errors.extend(f"duplicate provenance_hash {item}" for item in duplicate_provenance)
    return errors


def validate(path: Path = DEFAULT_MANIFEST, out_path: Path = REPORT_PATH, json_out_path: Path = JSON_REPORT_PATH) -> dict[str, Any]:
    if not path.exists():
        summary = {
            "status": "NOT_READY",
            "manifest_exists": False,
            "rows": 0,
            "valid": False,
            "error_count": 1,
            "errors": ["promotion manifest missing; human adjudication has not been supplied"],
            "gold_promoted": 0,
            "training_ready": False,
        }
        write_reports(summary, out_path, json_out_path)
        return summary
    rows = read_jsonl(path)
    errors = validate_rows(rows)
    summary = {
        "status": "PROMOTION_READY" if rows and not errors else "NOT_READY",
        "manifest_exists": True,
        "rows": len(rows),
        "valid": bool(rows) and not errors,
        "error_count": len(errors),
        "errors": errors[:200],
        "gold_promoted": 0,
        "training_ready": False,
    }
    write_reports(summary, out_path, json_out_path)
    return summary


def write_reports(summary: dict[str, Any], out_path: Path, json_out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Promotion Manifest Validation",
        "",
        f"- Status: {summary['status']}",
        f"- Manifest exists: {str(summary['manifest_exists']).lower()}",
        f"- Rows: {summary['rows']}",
        f"- Valid: {str(summary['valid']).lower()}",
        f"- Error count: {summary['error_count']}",
        "- Gold promoted: 0",
        "- Training ready: false",
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
    parser = argparse.ArgumentParser(description="Validate first100 promotion manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_REPORT_PATH)
    args = parser.parse_args(argv)
    summary = validate(args.manifest, args.out, args.json_out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "NOT_READY" and not summary["manifest_exists"] else (0 if summary["valid"] else 1)


if __name__ == "__main__":
    raise SystemExit(main())
