#!/usr/bin/env python3
"""Validate manually reviewed NYSE 100 source approval CSVs before promotion."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.source_rights_common import (
    PERMITTED_SOURCE_TYPES,
    QUEUE_FIELDS,
    VENDOR_SOURCE_TYPES,
    as_bool,
    is_youtube_url,
)

DEFAULT_INPUT = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"
DEFAULT_JSON_REPORT = ROOT / "reports" / "acquisition" / "source_approval_validation.json"
DEFAULT_MD_REPORT = ROOT / "reports" / "acquisition" / "source_approval_validation.md"
DOWNLOAD_ALLOWED_RIGHTS = {"safe_to_download", "rights_cleared"}
BOOL_FIELDS = {
    "allow_download",
    "allow_eval_use",
    "allow_training_use",
    "commit_allowed",
    "manual_approval_required",
    "source_terms_checked",
    "robots_checked",
}
MEDIA_ASSET_TYPES = {"audio", "video", "video_metadata"}


def _read_csv_with_headers(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def _valid_bool(value: str) -> bool:
    return str(value).strip().lower() in {"", "true", "false", "1", "0", "yes", "no", "y", "n"}


def validate_approval_rows(rows: list[dict[str, str]], headers: list[str] | None = None) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    headers = headers or list(rows[0].keys()) if rows else headers or []
    missing_headers = [field for field in QUEUE_FIELDS if field not in headers]
    if missing_headers:
        errors.append(f"missing required headers: {', '.join(missing_headers)}")
    extra_headers = [field for field in headers if field not in QUEUE_FIELDS]
    if extra_headers:
        warnings.append(f"unexpected extra headers: {', '.join(extra_headers)}")

    approved_downloads = 0
    training_uses = 0
    for index, row in enumerate(rows, start=1):
        prefix = f"row {index}"
        for field in ("case_id", "ticker", "asset_type", "source_url"):
            if not str(row.get(field, "")).strip():
                errors.append(f"{prefix}: {field} is required")
        for field in BOOL_FIELDS:
            if not _valid_bool(row.get(field, "")):
                errors.append(f"{prefix}: {field} must be true/false or empty")
        if as_bool(row.get("commit_allowed")):
            errors.append(f"{prefix}: commit_allowed must remain false")

        allow_download = as_bool(row.get("allow_download"))
        allow_training = as_bool(row.get("allow_training_use"))
        if allow_download:
            approved_downloads += 1
            for field in ("approval_ref", "approved_by", "approved_at"):
                if not str(row.get(field, "")).strip():
                    errors.append(f"{prefix}: allow_download=true requires {field}")
            if row.get("rights_status") not in DOWNLOAD_ALLOWED_RIGHTS:
                errors.append(f"{prefix}: allow_download=true requires rights_status in {sorted(DOWNLOAD_ALLOWED_RIGHTS)}")
            if row.get("source_type") not in PERMITTED_SOURCE_TYPES:
                errors.append(f"{prefix}: allow_download=true uses non-permitted source_type {row.get('source_type')!r}")
            for field in ("source_terms_checked", "robots_checked"):
                if not as_bool(row.get(field)):
                    errors.append(f"{prefix}: allow_download=true requires {field}=true")
            blocked_reason = str(row.get("blocked_reason", "")).strip().lower()
            if blocked_reason and blocked_reason not in {"resolved", "none", "approved"}:
                errors.append(f"{prefix}: allow_download=true requires blocked_reason to be empty or resolved")
            if row.get("source_type") in VENDOR_SOURCE_TYPES and not str(row.get("license_config_ref", "")).strip():
                errors.append(f"{prefix}: vendor raw ingest requires license_config_ref")

        if allow_training:
            training_uses += 1
            if not str(row.get("explicit_training_rights_ref", "")).strip():
                errors.append(f"{prefix}: allow_training_use=true requires explicit_training_rights_ref")
        if is_youtube_url(row.get("source_url", "")) and row.get("asset_type") in MEDIA_ASSET_TYPES and allow_download:
            errors.append(f"{prefix}: YouTube media rows cannot allow_download=true")

    summary = {
        "rows": len(rows),
        "approved_download_rows": approved_downloads,
        "training_use_rows": training_uses,
        "valid": not errors,
    }
    return errors, warnings, summary


def write_reports(*, json_path: Path, markdown_path: Path, errors: list[str], warnings: list[str], summary: dict[str, Any]) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"valid": not errors, "errors": errors, "warnings": warnings, "summary": summary}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Source Approval Validation", "", f"- Valid: {str(not errors).lower()}"]
    lines.extend(f"- {key}: {value}" for key, value in summary.items() if key != "valid")
    if errors:
        lines.extend(["", "## Errors", *[f"- {error}" for error in errors]])
    if warnings:
        lines.extend(["", "## Warnings", *[f"- {warning}" for warning in warnings]])
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate manually reviewed NYSE 100 source approval CSV guardrails.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MD_REPORT)
    args = parser.parse_args(argv)
    headers, rows = _read_csv_with_headers(args.input)
    errors, warnings, summary = validate_approval_rows(rows, headers)
    write_reports(json_path=args.json_out, markdown_path=args.markdown_out, errors=errors, warnings=warnings, summary=summary)
    print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings, "summary": summary}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
