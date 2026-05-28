#!/usr/bin/env python3
"""Build a deterministic source-rights review priority report."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import json
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.source_rights_common import VENDOR_SOURCE_TYPES, as_bool, is_youtube_url, read_csv

DEFAULT_QUEUE = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"
DEFAULT_JSON = ROOT / "reports" / "acquisition" / "source_rights_priority_summary.json"
DEFAULT_MD = ROOT / "reports" / "acquisition" / "source_rights_priority_summary.md"
PREFERRED_SOURCE_TYPES = {"company_ir", "official_ir", "official_ir_transcript"}


def quarter_number(value: str) -> int:
    cleaned = str(value).upper().replace("Q", "").strip()
    return int(cleaned) if cleaned.isdigit() else 0


def metadata_completeness(row: dict[str, str]) -> int:
    fields = ("case_id", "ticker", "company_name", "asset_type", "source_type", "source_url", "source_domain", "rights_status")
    return sum(1 for field in fields if str(row.get(field, "")).strip())


def exclude_reason(row: dict[str, str]) -> str:
    asset_type = row.get("asset_type", "")
    source_type = row.get("source_type", "")
    if not row.get("ticker") or not row.get("case_id"):
        return "missing_nyse_identity"
    if is_youtube_url(row.get("source_url", "")) and asset_type in {"audio", "video", "video_metadata"}:
        return "exclude_youtube_media"
    if source_type in VENDOR_SOURCE_TYPES and not (as_bool(row.get("allow_download")) and row.get("license_config_ref")):
        return "exclude_unlicensed_vendor_raw"
    return ""


def sort_key(row: dict[str, str]) -> tuple[Any, ...]:
    source_rank = 0 if row.get("source_type") in PREFERRED_SOURCE_TYPES else 1
    asset_rank = 0 if row.get("asset_type") == "transcript" else 1
    blocker_rank = 0 if str(row.get("blocked_reason", "")).strip().lower() in {"", "none", "resolved", "approved"} else 1
    completeness = metadata_completeness(row)
    fiscal_year = int(row.get("fiscal_year") or 0) if str(row.get("fiscal_year", "")).isdigit() else 0
    return (source_rank, asset_rank, blocker_rank, -completeness, -fiscal_year, -quarter_number(row.get("fiscal_quarter", "")), row.get("ticker", ""), row.get("case_id", ""))


def prioritize_rows(rows: list[dict[str, str]], *, limit: int = 50) -> tuple[list[dict[str, Any]], Counter[str]]:
    exclusions: Counter[str] = Counter()
    eligible: list[dict[str, str]] = []
    for row in rows:
        reason = exclude_reason(row)
        if reason:
            exclusions[reason] += 1
            continue
        eligible.append(row)
    prioritized: list[dict[str, Any]] = []
    for rank, row in enumerate(sorted(eligible, key=sort_key)[:limit], start=1):
        prioritized.append(
            {
                "rank": rank,
                "case_id": row.get("case_id", ""),
                "ticker": row.get("ticker", ""),
                "asset_type": row.get("asset_type", ""),
                "source_type": row.get("source_type", ""),
                "source_domain": row.get("source_domain", ""),
                "rights_status": row.get("rights_status", ""),
                "blocked_reason": row.get("blocked_reason", ""),
                "metadata_completeness": metadata_completeness(row),
                "next_action": row.get("next_action", ""),
            }
        )
    return prioritized, exclusions


def write_reports(*, rows: list[dict[str, str]], prioritized: list[dict[str, Any]], exclusions: Counter[str], json_path: Path, markdown_path: Path) -> None:
    summary = {
        "queue_rows": len(rows),
        "prioritized_rows": len(prioritized),
        "excluded_rows": sum(exclusions.values()),
        "exclusions": dict(exclusions),
        "top_priorities": prioritized,
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Source Rights Priority Summary",
        "",
        f"- Queue rows: {len(rows)}",
        f"- Prioritized rows: {len(prioritized)}",
        f"- Excluded rows: {sum(exclusions.values())}",
        "",
        "| rank | ticker | case_id | asset_type | source_type | source_domain | rights_status |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in prioritized:
        lines.append(
            f"| {row['rank']} | {row['ticker']} | {row['case_id']} | {row['asset_type']} | {row['source_type']} | {row['source_domain']} | {row['rights_status']} |"
        )
    if exclusions:
        lines.extend(["", "## Exclusions"])
        lines.extend(f"- {reason}: {count}" for reason, count in sorted(exclusions.items()))
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prioritize NYSE 100 source-rights queue rows for manual review.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)
    rows = read_csv(args.queue)
    prioritized, exclusions = prioritize_rows(rows, limit=args.limit)
    write_reports(rows=rows, prioritized=prioritized, exclusions=exclusions, json_path=args.json_out, markdown_path=args.markdown_out)
    print(json.dumps({"queue_rows": len(rows), "prioritized_rows": len(prioritized), "excluded_rows": sum(exclusions.values())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
