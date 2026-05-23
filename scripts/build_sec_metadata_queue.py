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
    candidate_id_for,
    case_id_for,
    make_provenance_hash,
    read_yaml,
    target_rows_from_payload,
    validate_policy,
    write_text,
    write_yaml,
)


def build_sec_metadata_queue(targets: list[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    sec_policy = policy.get("sec", {}) if isinstance(policy.get("sec", {}), dict) else {}
    target_forms = list(sec_policy.get("target_forms", ["8-K", "10-Q", "10-K"]))
    max_rps = int(sec_policy.get("max_requests_per_second", 10))
    rows: list[dict[str, Any]] = []
    for target in targets:
        ticker = str(target["ticker"]).upper()
        company_name = str(target["company_name"])
        exchange = str(target.get("exchange", "NYSE"))
        for fiscal_period in target.get("fiscal_periods", []):
            period = str(fiscal_period)
            case_id = case_id_for(ticker, period)
            row = {
                "candidate_id": candidate_id_for(case_id, "sec_edgar_metadata", "cik_lookup"),
                "case_id": case_id,
                "ticker": ticker,
                "company_name": company_name,
                "exchange": exchange,
                "fiscal_period": period,
                "source_type": "sec_edgar_metadata",
                "source_url_or_ref": f"sec-edgar://CIK_LOOKUP_REQUIRED/{ticker}/{period}",
                "source_domain": "sec.gov",
                "source_terms_url": "https://www.sec.gov/privacy.htm",
                "robots_url": "https://www.sec.gov/robots.txt",
                "rights_status": "metadata_only",
                "rights_tier": "public_domain",
                "source_terms_checked": True,
                "robots_checked": True,
                "paywall_or_login_required": False,
                "raw_transcript_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "raw_slides_allowed": False,
                "commit_allowed": False,
                "eval_allowed": False,
                "training_allowed": False,
                "metadata_only": True,
                "blocked_reason_code": "sec_metadata_only",
                "manual_action": "optional later SEC metadata fetch after enabling policy",
                "last_checked_at": "",
                "cik_lookup_required": True,
                "target_forms": list(target_forms),
                "lookback_year": period.split("_", maxsplit=1)[0],
                "max_requests_per_second": max_rps,
                "user_agent_required": True,
                "raw_body_allowed": False,
                "exhibit_metadata_candidate": True,
                "fair_access_note": "SEC automated access must remain at or below 10 requests/second with a descriptive User-Agent.",
            }
            row["provenance_hash"] = make_provenance_hash(row)
            rows.append(row)
    return rows


def build_report(rows: list[dict[str, Any]], policy: dict[str, Any]) -> str:
    tickers = sorted({str(row["ticker"]) for row in rows})
    cases = sorted({str(row["case_id"]) for row in rows})
    sec_policy = policy.get("sec", {}) if isinstance(policy.get("sec", {}), dict) else {}
    return f"""# SEC Metadata Queue

Status: metadata-first queue.

- Tickers: {len(tickers)}
- Target cases: {len(cases)}
- Queue rows: {len(rows)}
- Target forms: {', '.join(sec_policy.get('target_forms', ['8-K', '10-Q', '10-K']))}
- Maximum request rate: {sec_policy.get('max_requests_per_second', 10)} requests/second
- Descriptive User-Agent configured: {'yes' if str(sec_policy.get('user_agent', '')).strip() else 'no'}
- Filing body downloads: no
- Network used: no

The queue can identify candidate filings, event timing, releases, and exhibits after policy-enabled metadata access. It does not guarantee full earnings-call transcript availability.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a metadata-only SEC/EDGAR queue.")
    parser.add_argument("--targets", default="configs/nyse_5y_ir_sec_targets.example.yml")
    parser.add_argument("--policy", default="configs/ir_sec_acquisition_policy.example.yml")
    parser.add_argument("--out", default="data/corpus/sec_metadata_queue.yml")
    parser.add_argument("--report", default="reports/agent5/sec_metadata_queue.md")
    args = parser.parse_args(argv)

    policy = read_yaml(ROOT / args.policy)
    errors = validate_policy(policy)
    if errors:
        raise SystemExit("Policy validation failed: " + "; ".join(errors))
    if policy.get("network_enabled") is True:
        raise SystemExit("SEC metadata queue builder is network-free; enable a separate fetch step only after policy review.")
    targets = target_rows_from_payload(read_yaml(ROOT / args.targets), lookback_years=int(policy.get("lookback_years", 5)))
    rows = build_sec_metadata_queue(targets, policy)
    write_yaml(ROOT / args.out, {"status": "metadata_only", "network_used": False, "queue": rows})
    write_text(ROOT / args.report, build_report(rows, policy))
    print(f"SEC metadata queue written: {len(rows)} metadata-only row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
