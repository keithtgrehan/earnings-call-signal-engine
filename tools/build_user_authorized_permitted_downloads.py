#!/usr/bin/env python3
"""Build a user-authorized permitted-download manifest from source-rights rows."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import (
    DEFAULT_WORKSPACE,
    USER_AUTHORIZED_PERMITTED_FIELDS,
    as_bool,
    hard_barrier_reason,
    normalize_source_type,
    now_iso,
    read_csv,
    read_policy,
    stable_hash,
    write_csv,
)

REPORT_DIR = ROOT / "reports" / "acquisition"
DEFAULT_POLICY = ROOT / "configs" / "nyse_100_user_authorized_ingest_policy.yml"
DEFAULT_QUEUE = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_permitted_downloads.csv"


def _eligible_asset(row: dict[str, str]) -> bool:
    return row.get("asset_type") in {"transcript", "audio"}


def _eligible_rights(row: dict[str, str], policy: dict[str, Any]) -> bool:
    rights = str(row.get("rights_status", "")).strip()
    if rights in {"blocked", "restricted"}:
        return False
    if rights in {"metadata_only", "unknown", "unknown_fail_closed", "", "safe_to_download", "rights_cleared", "manual_local_review_only"}:
        return as_bool(policy.get("enabled"))
    return as_bool(policy.get("enabled"))


def _permitted_row(row: dict[str, str], policy: dict[str, Any], approved_at: str) -> dict[str, str]:
    source_type = normalize_source_type(row)
    approval_ref = str(
        policy.get("authorization_ref")
        or "Keith user-authorized acquisition for Signal Engine 2.0 assessment; raw files Desktop-only; no git raw commit"
    )
    payload = {
        "source_id": row.get("source_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "fiscal_year": row.get("fiscal_year", ""),
        "fiscal_quarter": row.get("fiscal_quarter", ""),
        "asset_type": row.get("asset_type", ""),
        "source_type": source_type,
        "source_url": row.get("source_url", ""),
        "source_domain": row.get("source_domain", ""),
        "rights_status": "safe_to_download",
        "allow_download": "true",
        "allow_eval_use": "true",
        "allow_training_use": "false",
        "commit_allowed": "false",
        "approval_ref": approval_ref,
        "approved_by": "Keith",
        "approved_at": approved_at,
        "license_config_ref": row.get("license_config_ref", ""),
        "youtube_written_authorization_ref": row.get("youtube_written_authorization_ref", ""),
        "explicit_training_rights_ref": row.get("explicit_training_rights_ref", ""),
        "blocked_reason": "",
    }
    payload["provenance_hash"] = stable_hash(payload)
    return {field: payload.get(field, "") for field in USER_AUTHORIZED_PERMITTED_FIELDS}


def build_permitted_downloads(
    *,
    queue_path: Path,
    policy_path: Path,
    out_path: Path,
    desktop_out: Path | None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    policy = read_policy(policy_path)
    queue_rows = read_csv(queue_path)
    approved_at = now_iso()
    allowed_types = set(policy.get("allowed_source_types") or [])
    promoted: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    for row in queue_rows:
        candidate = dict(row)
        candidate["source_type"] = normalize_source_type(candidate)
        reason = ""
        if not as_bool(policy.get("enabled")):
            reason = "user_authorization_policy_disabled"
        elif not _eligible_asset(candidate):
            reason = "asset_type_not_promoted"
        elif not _eligible_rights(candidate, policy):
            reason = f"rights_status_not_eligible:{candidate.get('rights_status', '')}"
        else:
            reason = hard_barrier_reason(candidate, policy)
            if not reason and candidate["source_type"] not in allowed_types:
                reason = f"source_type_not_allowed:{candidate['source_type']}"
        if reason:
            blocked.append({**candidate, "blocked_reason": reason})
            continue
        promoted.append(_permitted_row(candidate, policy, approved_at))

    write_csv(out_path, promoted, USER_AUTHORIZED_PERMITTED_FIELDS)
    if desktop_out is not None:
        write_csv(desktop_out, promoted, USER_AUTHORIZED_PERMITTED_FIELDS)
    write_report(promoted, blocked, out_path=out_path)
    return promoted, blocked


def write_report(promoted: list[dict[str, str]], blocked: list[dict[str, str]], *, out_path: Path) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    blocked_reasons = Counter(row.get("blocked_reason", "") for row in blocked)
    lines = [
        "# User-Authorized Permitted Downloads",
        "",
        f"- Permitted download rows: {len(promoted)}",
        f"- Blocked/not promoted rows: {len(blocked)}",
        f"- Output: `{out_path}`",
        "- Approved by: Keith",
        "- commit_allowed: false",
        "- allow_training_use: false",
        "",
        "## Blocked Reasons",
        "",
    ]
    if blocked_reasons:
        lines.extend(f"- `{reason}`: {count}" for reason, count in blocked_reasons.most_common())
    else:
        lines.append("- none")
    (REPORT_DIR / "user_authorized_permitted_downloads.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_preflight(queue_path: Path, policy_path: Path, workspace: Path) -> None:
    rows = read_csv(queue_path)
    official_transcripts = sum(1 for row in rows if row.get("asset_type") == "transcript" and normalize_source_type(row) in {"official_ir_transcript", "company_ir"})
    official_audio = sum(1 for row in rows if row.get("asset_type") == "audio" and normalize_source_type(row) in {"official_ir_webcast", "official_ir_audio", "company_ir"})
    sec = sum(1 for row in rows if "sec" in normalize_source_type(row))
    youtube = sum(1 for row in rows if "youtube" in normalize_source_type(row) or "youtube" in row.get("source_url", "").lower())
    vendor = sum(1 for row in rows if "vendor" in normalize_source_type(row) or row.get("source_url", "").startswith("licensed-vendor://"))
    blocked = sum(1 for row in rows if hard_barrier_reason({**row, "source_type": normalize_source_type(row)}, read_policy(policy_path)))
    lines = [
        "# User-Authorized Ingest Preflight",
        "",
        f"- Workspace: `{workspace}`",
        f"- Source rows found: {len(rows)}",
        f"- Official/company transcript candidates: {official_transcripts}",
        f"- Official/company audio/webcast candidates: {official_audio}",
        f"- SEC candidates: {sec}",
        f"- YouTube rows: {youtube}",
        f"- Vendor rows: {vendor}",
        f"- Hard-blocked rows: {blocked}",
        f"- Rows eligible for user-authorized promotion: {len(rows) - blocked}",
    ]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "user_authorized_ingest_preflight.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build user-authorized permitted-download manifest.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--desktop-out", type=Path)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args(argv)
    write_preflight(args.queue, args.policy, args.workspace)
    promoted, blocked = build_permitted_downloads(queue_path=args.queue, policy_path=args.policy, out_path=args.out, desktop_out=args.desktop_out)
    print({"permitted_download_rows": len(promoted), "blocked_rows": len(blocked), "out": str(args.out)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
