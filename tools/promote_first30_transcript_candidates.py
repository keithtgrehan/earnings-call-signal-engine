#!/usr/bin/env python3
"""Promote first-30 transcript candidates into a Desktop-only ingestion manifest."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import (  # noqa: E402
    AUDIT_DIR,
    DESKTOP_WORKSPACE,
    FIRST30_CANDIDATE_PATH,
    FIRST30_INGESTION_FIELDS,
    FIRST30_INGESTION_MANIFEST_PATH,
    FIRST30_INGESTION_PLAN_PATH,
    FIRST30_RIGHTS_QUEUE_PATH,
    build_promotion_rows,
    read_csv,
    write_csv,
)


def _bool_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if row.get(field, "").lower() == "true")


def write_plan(rows: list[dict[str, str]], out_path: Path = FIRST30_INGESTION_PLAN_PATH) -> None:
    blocker_counts = Counter(row.get("blocked_reason") or "download_allowed" for row in rows)
    allowed = [row for row in rows if row.get("download_allowed") == "true"]
    lines = [
        "# First30 Transcript Ingestion Plan",
        "",
        "- Scope: NYSE first-30 transcript candidates plus the registered HD control fixture.",
        "- Storage: raw PDFs/HTML/TXT and parsed transcript text stay under the Desktop workspace only.",
        "- Repo policy: metadata manifests only; `commit_allowed=false`, `training_allowed=false`, `raw_text_committed=false`.",
        "",
        "## Counts",
        "",
        f"- Candidate rows: {len(rows)}",
        f"- Download-allowed rows: {len(allowed)}",
        f"- Rights-review-required rows: {_bool_count(rows, 'rights_review_required')}",
        f"- Q4CDN/CloudFront rows: {sum(1 for row in rows if row.get('source_url_kind') == 'official_ir_cdn_direct')}",
        f"- Control fixture rows: {_bool_count(rows, 'control_fixture')}",
        "",
        "## Download Order",
        "",
    ]
    for row in sorted(allowed, key=lambda item: int(item.get("priority_rank", "999"))):
        review = " review_required" if row.get("rights_review_required") == "true" else ""
        lines.append(f"- {row['priority_rank']}. `{row['case_id']}` `{row['ticker']}` {row['source_url_kind']}{review}")
    lines.extend(["", "## Blockers", ""])
    for reason, count in sorted(blocker_counts.items()):
        lines.append(f"- `{reason}`: {count}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_rights_queue(rows: list[dict[str, str]], out_path: Path = FIRST30_RIGHTS_QUEUE_PATH) -> None:
    needs_review = [row for row in rows if row.get("rights_review_required") == "true" or row.get("download_allowed") != "true"]
    lines = [
        "# First30 Source Rights Queue",
        "",
        "Rows here require either post-download source review, direct transcript URL resolution, or explicit replacement.",
        "",
    ]
    if not needs_review:
        lines.append("- none")
    for row in needs_review:
        lines.append(
            f"- `{row.get('case_id')}` `{row.get('ticker')}`: {row.get('blocked_reason') or 'rights_review_required'}; "
            f"download_allowed={row.get('download_allowed')}; source={row.get('source_url')}"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def promote_first30_transcripts(
    *,
    candidates_path: Path = FIRST30_CANDIDATE_PATH,
    out_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    workspace: Path = DESKTOP_WORKSPACE,
) -> dict[str, Any]:
    candidates = read_csv(candidates_path)
    rows = build_promotion_rows(candidates)
    write_csv(out_path, rows, FIRST30_INGESTION_FIELDS)
    write_csv(workspace / "_audit" / "first30_transcript_ingestion_manifest.csv", rows, FIRST30_INGESTION_FIELDS)
    write_plan(rows)
    write_rights_queue(rows)
    summary = {
        "candidate_rows": len(candidates),
        "manifest_rows": len(rows),
        "download_allowed": _bool_count(rows, "download_allowed"),
        "rights_review_required": _bool_count(rows, "rights_review_required"),
        "q4cdn_or_cloudfront_rows": sum(1 for row in rows if row.get("source_url_kind") == "official_ir_cdn_direct"),
        "desktop_audit": str(AUDIT_DIR / "first30_transcript_ingestion_manifest.csv"),
        "out_manifest": str(out_path),
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote first30 transcript candidates into a safe ingestion manifest.")
    parser.add_argument("--candidates", type=Path, default=FIRST30_CANDIDATE_PATH)
    parser.add_argument("--out", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    args = parser.parse_args(argv)
    summary = promote_first30_transcripts(candidates_path=args.candidates, out_path=args.out, workspace=args.workspace)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
