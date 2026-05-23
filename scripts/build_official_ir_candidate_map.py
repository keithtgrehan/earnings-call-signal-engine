#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.ir_sec_acquisition import (
    OFFICIAL_IR_SECTIONS,
    candidate_id_for,
    case_id_for,
    make_provenance_hash,
    read_yaml,
    write_text,
    write_yaml,
)


def build_official_ir_candidate_map(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        ticker = str(target["ticker"]).upper()
        company_name = str(target["company_name"])
        exchange = str(target.get("exchange", "NYSE"))
        for fiscal_period in target.get("fiscal_periods", []):
            case_id = case_id_for(ticker, str(fiscal_period))
            for section in OFFICIAL_IR_SECTIONS:
                row = {
                    "candidate_id": candidate_id_for(case_id, "official_ir_metadata", section),
                    "case_id": case_id,
                    "ticker": ticker,
                    "company_name": company_name,
                    "exchange": exchange,
                    "fiscal_period": str(fiscal_period),
                    "source_type": "official_ir_metadata",
                    "source_url_or_ref": f"official-ir://{ticker}/{section}/{fiscal_period}",
                    "source_domain": "review-required",
                    "source_terms_url": "",
                    "robots_url": "",
                    "rights_status": "unknown",
                    "rights_tier": "publicly_available",
                    "source_terms_checked": False,
                    "robots_checked": False,
                    "paywall_or_login_required": False,
                    "raw_transcript_allowed": False,
                    "raw_audio_allowed": False,
                    "raw_video_allowed": False,
                    "raw_slides_allowed": False,
                    "commit_allowed": False,
                    "eval_allowed": False,
                    "training_allowed": False,
                    "metadata_only": True,
                    "blocked_reason_code": "source_terms_not_checked",
                    "manual_action": "review official IR source terms/robots and confirm whether raw transcript use is allowed",
                    "last_checked_at": "",
                    "ir_section": section,
                    "availability_claimed": False,
                }
                row["provenance_hash"] = make_provenance_hash(row)
                rows.append(row)
    return rows


def build_report(rows: list[dict[str, Any]]) -> str:
    tickers = sorted({str(row["ticker"]) for row in rows})
    cases = sorted({str(row["case_id"]) for row in rows})
    return f"""# Official IR Candidate Map

Status: metadata-only candidate map.

- Tickers: {len(tickers)}
- Target cases: {len(cases)}
- Candidate rows: {len(rows)}
- IR sections per case: {len(OFFICIAL_IR_SECTIONS)}
- Network used: no
- Raw assets written: no

Each row is a placeholder for source-rights review. The map does not claim that a company hosts a transcript, webcast, presentation, or release at the placeholder reference.

Manual action: review official IR source terms/robots and confirm whether raw transcript use is allowed before any permitted acquisition queue entry can exist.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a metadata-only official IR candidate map.")
    parser.add_argument("--targets", default="configs/nyse_5y_ir_sec_targets.example.yml")
    parser.add_argument("--policy", default="configs/ir_sec_acquisition_policy.example.yml")
    parser.add_argument("--out", default="data/corpus/official_ir_candidate_map.yml")
    parser.add_argument("--report", default="reports/agent5/official_ir_candidate_map.md")
    args = parser.parse_args(argv)

    policy = read_yaml(ROOT / args.policy)
    if policy.get("network_enabled") is True:
        raise SystemExit("Official IR candidate mapping does not use network access.")
    payload = read_yaml(ROOT / args.targets)
    raw_targets = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(raw_targets, list):
        raise SystemExit("target config must contain a targets list")
    targets = [{**target, "fiscal_periods": target.get("fiscal_periods", ["rolling_5y"])} for target in raw_targets]
    rows = build_official_ir_candidate_map(targets)
    write_yaml(ROOT / args.out, {"status": "metadata_only", "network_used": False, "candidates": rows})
    write_text(ROOT / args.report, build_report(rows))
    print(f"Official IR candidate map written: {len(rows)} metadata-only candidate(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
