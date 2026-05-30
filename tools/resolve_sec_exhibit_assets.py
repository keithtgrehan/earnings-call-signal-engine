#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import RESOLVED_ASSET_FIELDS, read_csv, write_csv, write_resolution_report
from signal_engine.acquisition.sec_resolver import resolve_sec_assets_for_rows

DEFAULT_TARGETS = ROOT / "data" / "acquisition" / "nyse_100_5y_call_targets.csv"
DEFAULT_SEC_INDEX = ROOT / "data" / "acquisition" / "nyse_100_sec_event_index.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_sec_resolved_assets.csv"
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "sec_exhibit_resolution.md"


def _offline_submissions(sec_rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, list[dict[str, object]]]]:
    ticker_ciks: dict[str, str] = {}
    submissions: dict[str, list[dict[str, object]]] = {}
    for row in sec_rows:
        ticker = row.get("ticker", "")
        if not ticker:
            continue
        ticker_ciks[ticker] = row.get("sec_company_ref", "0000000000").replace("CIK", "").zfill(10)
        filing_url = row.get("filing_url", "")
        if not filing_url:
            continue
        submissions.setdefault(ticker, []).append(
            {
                "form": "8-K",
                "filingDate": row.get("event_date") or row.get("fiscal_year", ""),
                "accessionNumber": row.get("accession_number", ""),
                "items": "2.02" if row.get("item_202_or_exhibit_991") in {"true", "True", "1"} else "",
                "primaryDocument": Path(filing_url).name,
                "exhibits": [
                    {
                        "document": Path(filing_url).name,
                        "description": "EX-99.1 earnings release metadata",
                    }
                ],
            }
        )
    return ticker_ciks, submissions


def run(targets: Path, sec_index: Path, out: Path, report: Path) -> dict[str, int | str]:
    user_agent = os.environ.get("SEC_USER_AGENT", "SignalEngine/2.0 keithtgrehan project assessment contact")
    target_rows = read_csv(targets)
    ticker_ciks, submissions = _offline_submissions(read_csv(sec_index))
    candidates = resolve_sec_assets_for_rows(target_rows, ticker_ciks=ticker_ciks, submissions_by_ticker=submissions)
    write_csv(out, candidates, RESOLVED_ASSET_FIELDS)
    write_resolution_report(report, candidates, title="SEC Exhibit Resolution")
    return {"target_rows": len(target_rows), "candidate_rows": len(candidates), "sec_user_agent": user_agent}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve SEC 8-K / Exhibit metadata to asset candidates.")
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--sec-index", type=Path, default=DEFAULT_SEC_INDEX)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.targets, args.sec_index, args.out, args.report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
