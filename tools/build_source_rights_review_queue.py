#!/usr/bin/env python3
"""Build a fail-closed source-rights review queue from NYSE 100 metadata."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.source_rights_common import QUEUE_FIELDS, read_csv, source_domain, stable_hash, write_csv

REPORT_DIR = ROOT / "reports" / "acquisition"
DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
DEFAULT_AUDIT = DEFAULT_WORKSPACE / "_audit" / "nyse_earnings_call_audit.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"


def _audit_candidates(workspace: Path) -> list[dict[str, str]]:
    audit_rows = read_csv(workspace / "_audit" / "nyse_earnings_call_audit.csv")
    rows: list[dict[str, str]] = []
    for audit in audit_rows:
        for asset_type, url_field in (("transcript", "transcript_source_url"), ("audio", "audio_source_url")):
            source_url = str(audit.get(url_field, "")).strip()
            if not source_url:
                continue
            rows.append(
                {
                    "case_id": audit.get("case_id", ""),
                    "ticker": audit.get("ticker_symbol") or audit.get("ticker", ""),
                    "company_name": audit.get("company_name", ""),
                    "fiscal_year": audit.get("fiscal_year", ""),
                    "fiscal_quarter": audit.get("fiscal_quarter", ""),
                    "asset_type": asset_type,
                    "source_type": audit.get("source_type") or "official_ir",
                    "source_url": source_url,
                    "source_domain": audit.get("source_domain") or source_domain(source_url),
                    "rights_status": audit.get("rights_status") or "metadata_only",
                    "blocked_reason": audit.get("blocked_reason") or "source_terms_and_robots_not_reviewed",
                }
            )
    return rows


def _repo_candidates() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in read_csv(ROOT / "data" / "acquisition" / "nyse_100_rights_decisions.csv"):
        if source.get("asset_type") not in {"transcript", "audio"}:
            continue
        rows.append(
            {
                "case_id": source.get("case_id", ""),
                "ticker": source.get("ticker", ""),
                "company_name": source.get("company_name", ""),
                "fiscal_year": "",
                "fiscal_quarter": "",
                "asset_type": source.get("asset_type", ""),
                "source_type": source.get("source_type", ""),
                "source_url": source.get("source_url", ""),
                "source_domain": source.get("source_domain") or source_domain(source.get("source_url", "")),
                "rights_status": source.get("rights_status") or "metadata_only",
                "blocked_reason": source.get("blocked_reason") or "source_terms_and_robots_not_reviewed",
            }
        )
    return rows


def build_queue(*, workspace: Path, out_path: Path) -> list[dict[str, str]]:
    candidates = _audit_candidates(workspace) or _repo_candidates()
    seen: set[tuple[str, str, str, str]] = set()
    rows: list[dict[str, str]] = []
    for candidate in candidates:
        key = (
            candidate.get("case_id", ""),
            candidate.get("ticker", "").upper(),
            candidate.get("asset_type", ""),
            candidate.get("source_url", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        source_id = stable_hash({"key": key})[:24].replace("sha256:", "src_")
        payload = {
            "source_id": source_id,
            **candidate,
            "allow_download": "false",
            "allow_eval_use": "false",
            "allow_training_use": "false",
            "commit_allowed": "false",
            "manual_approval_required": "true",
            "approval_ref": "",
            "approved_by": "",
            "approved_at": "",
            "license_config_ref": "",
            "explicit_training_rights_ref": "",
            "source_terms_checked": "false",
            "robots_checked": "false",
            "review_priority": "1" if candidate.get("asset_type") == "transcript" else "2",
            "next_action": "Review source terms, robots policy, event identity, and storage/evaluation rights before any raw download.",
        }
        payload["provenance_hash"] = stable_hash({key: payload.get(key, "") for key in QUEUE_FIELDS if key != "provenance_hash"})
        rows.append({field: str(payload.get(field, "")) for field in QUEUE_FIELDS})
    write_csv(out_path, rows, QUEUE_FIELDS)
    write_reports(rows, workspace=workspace, out_path=out_path)
    return rows


def write_reports(rows: list[dict[str, str]], *, workspace: Path, out_path: Path) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    by_asset = Counter(row["asset_type"] for row in rows)
    by_domain = Counter(row["source_domain"] for row in rows if row["source_domain"])
    created = datetime.now(UTC).replace(microsecond=0).isoformat()
    (REPORT_DIR / "source_rights_review_queue.md").write_text(
        "\n".join(
            [
                "# Source Rights Review Queue",
                "",
                f"- Created at: {created}",
                f"- Workspace: `{workspace}`",
                f"- Queue rows: {len(rows)}",
                f"- Transcript rows: {by_asset.get('transcript', 0)}",
                f"- Audio rows: {by_asset.get('audio', 0)}",
                f"- Output: `{out_path}`",
                "- Default allow_download: false",
                "- Default allow_eval_use: false",
                "- Default allow_training_use: false",
                "- Default commit_allowed: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    action_lines = [
        "# Top 50 Source Rights Review Actions",
        "",
        "| rank | source_domain | rows | next_action |",
        "| --- | --- | ---: | --- |",
    ]
    for rank, (domain, count) in enumerate(by_domain.most_common(50), start=1):
        action_lines.append(f"| {rank} | {domain} | {count} | Review source terms/robots and record approval refs before raw download. |")
    if not by_domain:
        action_lines.append("| 1 | none | 0 | No source rows available. |")
    (REPORT_DIR / "top50_source_rights_review_actions.md").write_text("\n".join(action_lines) + "\n", encoding="utf-8")
    audit_dir = workspace / "_audit"
    if audit_dir.exists():
        write_csv(audit_dir / "source_rights_review_queue.csv", rows, QUEUE_FIELDS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build source-rights review queue with fail-closed defaults.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    rows = build_queue(workspace=args.workspace, out_path=args.out)
    print({"queue_rows": len(rows), "out": str(args.out)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
