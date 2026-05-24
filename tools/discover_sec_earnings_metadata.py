#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import build_call_targets, build_company_universe, build_sec_event_index, write_csv

def main() -> None:
    parser = argparse.ArgumentParser(description="Write SEC/EDGAR metadata-first target index.")
    parser.add_argument("--user-agent", default="Signal Engine 2.0 metadata-first discovery contact keithtgrehan@example.com")
    parser.add_argument("--max-requests-per-second", type=float, default=10.0)
    args = parser.parse_args()
    if args.max_requests_per_second > 10:
        raise SystemExit("SEC max requests per second must be <=10")
    if not args.user_agent.strip():
        raise SystemExit("SEC User-Agent is required")
    rows = build_sec_event_index(build_call_targets(build_company_universe(), start_year=2025, years_back=5))
    write_csv(
        ROOT / "data/acquisition/nyse_100_sec_event_index.csv",
        rows,
        [
            "case_id",
            "ticker",
            "company_name",
            "fiscal_year",
            "fiscal_quarter",
            "target_forms",
            "sec_company_ref",
            "accession_number",
            "filing_url",
            "item_202_or_exhibit_991",
            "rights_status",
            "blocked_reason",
            "notes",
        ],
    )
    print({"sec_event_index_rows": len(rows), "max_requests_per_second": args.max_requests_per_second})


if __name__ == "__main__":
    main()
