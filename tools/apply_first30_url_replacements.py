#!/usr/bin/env python3
"""Apply approved first30 transcript URL replacements to the ingestion manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import (  # noqa: E402
    APPROVAL_REF,
    AUDIT_DIR,
    FIRST30_INGESTION_FIELDS,
    FIRST30_INGESTION_MANIFEST_PATH,
    domain_for_url,
    is_direct_text_url,
    is_official_cdn_domain,
    read_csv,
    write_csv,
)
from tools.resolve_first30_missing_transcript_urls import OUT_PATH as REPLACEMENTS_PATH  # noqa: E402

REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_url_replacement_apply_status.md"


def _source_url_kind(url: str) -> str:
    domain = domain_for_url(url)
    if is_official_cdn_domain(domain) and is_direct_text_url(url):
        return "official_ir_cdn_direct"
    if is_direct_text_url(url):
        return "official_direct"
    return "landing_or_metadata"


def _apply_one(row: dict[str, str], replacement: dict[str, str]) -> dict[str, str]:
    if replacement.get("download_allowed") != "true" or not replacement.get("replacement_source_url"):
        return row
    url = replacement["replacement_source_url"]
    updated = dict(row)
    updated["source_url"] = url
    updated["source_domain"] = domain_for_url(url)
    updated["source_type"] = replacement.get("source_type") or row.get("source_type", "official_ir")
    updated["expected_format"] = replacement.get("expected_format") or row.get("expected_format", "")
    updated["source_url_kind"] = _source_url_kind(url)
    updated["rights_review_required"] = replacement.get("rights_review_required", "false")
    updated["download_allowed"] = "true"
    updated["blocked_reason"] = ""
    updated["raw_text_committed"] = "false"
    updated["commit_allowed"] = "false"
    updated["training_allowed"] = "false"
    updated["approval_ref"] = replacement.get("approval_ref") or APPROVAL_REF
    updated["next_action"] = "download_desktop_only"
    note = f"Replacement applied: {replacement.get('replacement_reason', '')}".strip()
    updated["notes"] = (row.get("notes", "") + " " + note).strip()
    return updated


def apply_replacements(
    *,
    manifest_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    replacements_path: Path = REPLACEMENTS_PATH,
    audit_dir: Path = AUDIT_DIR,
) -> dict[str, Any]:
    rows = read_csv(manifest_path)
    replacements = {row.get("case_id", ""): row for row in read_csv(replacements_path)}
    applied: list[str] = []
    final_rows: list[dict[str, str]] = []
    for row in rows:
        replacement = replacements.get(row.get("case_id", ""))
        updated = _apply_one(row, replacement or {})
        if updated != row:
            applied.append(row.get("case_id", ""))
        final_rows.append(updated)
    write_csv(manifest_path, final_rows, FIRST30_INGESTION_FIELDS)
    write_csv(audit_dir / "first30_transcript_ingestion_manifest.csv", final_rows, FIRST30_INGESTION_FIELDS)
    summary = {
        "manifest_rows": len(final_rows),
        "replacement_rows": len(replacements),
        "applied_replacements": len(applied),
        "applied_case_ids": applied,
        "download_allowed_rows": sum(1 for row in final_rows if row.get("download_allowed") == "true"),
        "out_manifest": str(manifest_path),
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 URL Replacement Apply Status",
        "",
        f"- Manifest rows: {summary['manifest_rows']}",
        f"- Replacement rows: {summary['replacement_rows']}",
        f"- Applied replacements: {summary['applied_replacements']}",
        f"- Download-allowed rows after apply: {summary['download_allowed_rows']}",
        "- Commit allowed for raw assets: false",
        "- Training allowed: false",
        "",
        "## Applied Cases",
        "",
    ]
    if summary["applied_case_ids"]:
        lines.extend(f"- `{case_id}`" for case_id in summary["applied_case_ids"])
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply approved first30 transcript URL replacements.")
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--replacements", type=Path, default=REPLACEMENTS_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    args = parser.parse_args(argv)
    print(json.dumps(apply_replacements(manifest_path=args.manifest, replacements_path=args.replacements, audit_dir=args.audit_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
