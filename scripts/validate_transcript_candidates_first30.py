#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "event_date",
    "source_url",
    "source_domain",
    "source_type",
    "expected_format",
    "rights_status",
    "approval_required",
    "download_allowed",
    "raw_text_committed",
    "commit_allowed",
    "training_allowed",
    "control_fixture",
    "normalization_risk",
    "qna_expected",
    "next_action",
    "notes",
]
RIGHTS = {
    "official_ir_public_linked",
    "official_ir_hosted_third_party_transcript_possible",
    "metadata_only_rights_review",
    "control_fixture_registered",
}
FORMATS = {"pdf", "html", "txt"}
RISKS = {"low", "medium", "high"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate_row(row: dict[str, str], *, repo_root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for field in FIELDS:
        if field not in row:
            errors.append(f"missing required column {field}")
    if errors:
        return errors
    if row["case_id"] != row["case_id"].lower():
        errors.append("case_id must be lowercase")
    try:
        date.fromisoformat(row["event_date"])
    except ValueError:
        errors.append("event_date must be ISO date")
    if row["expected_format"] not in FORMATS:
        errors.append("expected_format enum invalid")
    if row["normalization_risk"] not in RISKS:
        errors.append("normalization_risk enum invalid")
    if row["qna_expected"] not in {"true", "false"}:
        errors.append("qna_expected must be boolean string")
    if not row["source_url"]:
        errors.append("source_url must be non-empty")
    if row["rights_status"] not in RIGHTS:
        errors.append("rights_status enum invalid")
    for field in ("approval_required", "download_allowed", "raw_text_committed", "commit_allowed", "training_allowed", "control_fixture"):
        if row[field] not in {"true", "false"}:
            errors.append(f"{field} must be boolean string")
    if row["download_allowed"] != "false":
        errors.append("download_allowed defaults false until approval promotion")
    if row["raw_text_committed"] != "false" or row["commit_allowed"] != "false":
        errors.append("raw text and commit flags must be false")
    if row["training_allowed"] != "false":
        errors.append("training_allowed must be false")
    path = Path(row["source_url"])
    if path.is_absolute():
        try:
            path.resolve().relative_to(repo_root.resolve())
            errors.append("source_url must not be a raw local path inside repo")
        except (OSError, ValueError):
            pass
    if urlparse(row["source_url"]).netloc.lower() != row["source_domain"]:
        errors.append("source_domain must match source_url host")
    return errors


def validate_file(path: Path) -> dict[str, object]:
    rows = read_rows(path)
    errors: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=2):
        for error in validate_row(row):
            errors.append({"row": index, "case_id": row.get("case_id", ""), "error": error})
    target_rows = [row for row in rows if row.get("control_fixture") != "true"]
    control_rows = [row for row in rows if row.get("control_fixture") == "true"]
    return {"rows": len(rows), "target_rows": len(target_rows), "control_rows": len(control_rows), "errors": errors}


def write_report(summary: dict[str, object]) -> None:
    path = ROOT / "reports" / "acquisition" / "first30_transcript_ingestion_status.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First-30 Transcript Ingestion Status",
        "",
        f"- Manifest rows: {summary['rows']}",
        f"- First-30 target rows: {summary['target_rows']}",
        f"- Control fixture rows: {summary['control_rows']}",
        f"- Validation errors: {len(summary['errors'])}",
        "- Downloads allowed by default: false",
        "- Raw PDF/text committed: false",
        "- Training allowed: false",
    ]
    if summary["errors"]:
        lines.append("")
        lines.append("## Errors")
        for error in summary["errors"]:
            lines.append(f"- row {error.get('row')}: {error.get('case_id', '')} {error.get('error')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate first-30 transcript candidate metadata.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    summary = validate_file(args.path)
    write_report(summary)
    print(f"transcript_candidates_first30 rows={summary['rows']} errors={len(summary['errors'])}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
