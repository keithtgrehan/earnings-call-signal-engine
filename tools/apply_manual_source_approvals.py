#!/usr/bin/env python3
"""Promote reviewed source rows into a permitted-download manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.source_rights_common import (
    PERMITTED_DOWNLOAD_FIELDS,
    PERMITTED_SOURCE_TYPES,
    VENDOR_SOURCE_TYPES,
    as_bool,
    is_youtube_url,
    read_csv,
    write_csv,
)

REPORT_DIR = ROOT / "reports" / "acquisition"
DEFAULT_QUEUE = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_permitted_downloads.csv"


def promotion_errors(row: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if not as_bool(row.get("allow_download")):
        errors.append("allow_download must be true")
    for field in ("approval_ref", "approved_by", "approved_at", "source_url"):
        if not str(row.get(field, "")).strip():
            errors.append(f"{field} is required")
    if row.get("source_type") not in PERMITTED_SOURCE_TYPES:
        errors.append("source_type is not permitted for approved download")
    blocked_reason = str(row.get("blocked_reason", "")).strip().lower()
    if blocked_reason and blocked_reason not in {"resolved", "none", "approved"}:
        errors.append("blocked_reason must be empty or resolved")
    if as_bool(row.get("commit_allowed")):
        errors.append("commit_allowed must remain false")
    if is_youtube_url(row.get("source_url", "")) and row.get("asset_type") in {"audio", "video", "video_metadata"}:
        errors.append("YouTube audio/video download is blocked")
    if row.get("source_type") in VENDOR_SOURCE_TYPES and not row.get("license_config_ref"):
        errors.append("vendor raw requires license_config_ref")
    if as_bool(row.get("allow_training_use")) and not row.get("explicit_training_rights_ref"):
        errors.append("training use requires explicit_training_rights_ref")
    return errors


def apply_approvals(*, input_path: Path, out_path: Path) -> tuple[list[dict[str, str]], dict[str, list[str]]]:
    rows = read_csv(input_path)
    permitted: list[dict[str, str]] = []
    rejected: dict[str, list[str]] = {}
    for row in rows:
        errors = promotion_errors(row)
        if errors:
            rejected[row.get("source_id") or row.get("case_id", "<unknown>")] = errors
            continue
        permitted.append(
            {
                "case_id": row.get("case_id", ""),
                "ticker": row.get("ticker", ""),
                "company_name": row.get("company_name", ""),
                "asset_type": row.get("asset_type", ""),
                "source_type": row.get("source_type", ""),
                "source_url": row.get("source_url", ""),
                "rights_status": "safe_to_download",
                "license_config_ref": row.get("license_config_ref", ""),
                "authorization_ref": row.get("approval_ref", ""),
                "approval_ref": row.get("approval_ref", ""),
                "approved_by": row.get("approved_by", ""),
                "approved_at": row.get("approved_at", ""),
                "allow_eval_use": str(as_bool(row.get("allow_eval_use"))).lower(),
                "allow_training_use": str(as_bool(row.get("allow_training_use"))).lower(),
                "provenance_hash": row.get("provenance_hash", ""),
            }
        )
    write_csv(out_path, permitted, PERMITTED_DOWNLOAD_FIELDS)
    write_reports(permitted, rejected, out_path=out_path)
    return permitted, rejected


def write_reports(permitted: list[dict[str, str]], rejected: dict[str, list[str]], *, out_path: Path) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Permitted Downloads After Manual Approval",
        "",
        f"- Approved download rows: {len(permitted)}",
        f"- Rejected/non-approved rows: {len(rejected)}",
        f"- Output: `{out_path}`",
        "- Raw commits allowed: false",
        "- YouTube media download: blocked",
    ]
    if not permitted:
        lines.append("- Status: 0 approved downloads")
    (REPORT_DIR / "permitted_downloads_after_manual_approval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORT_DIR / "legal_download_unlock_status.md").write_text(
        "# Legal Download Unlock Status\n\n"
        f"- Approved downloads unlocked: {len(permitted)}\n"
        "- Unknown rights fail closed: true\n"
        "- Vendor raw requires license_config_ref: true\n"
        "- Training remains separately gated: true\n",
        encoding="utf-8",
    )
    (REPORT_DIR / "nyse_100_download_and_rag_status.md").write_text(
        "# NYSE 100 Download and RAG Status\n\n"
        f"- Approved download rows: {len(permitted)}\n"
        "- Downloader rerun required only when approved rows are present.\n"
        "- RAG manifest remains metadata/hash/path only; no embeddings or vector DB created.\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply manual source approvals to produce a safe permitted-download manifest.")
    parser.add_argument("--input", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    permitted, rejected = apply_approvals(input_path=args.input, out_path=args.out)
    print({"approved_download_rows": len(permitted), "rejected_or_pending_rows": len(rejected), "out": str(args.out)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
