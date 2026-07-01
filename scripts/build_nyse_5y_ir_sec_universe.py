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

from signal_engine.ir_sec_acquisition import case_id_for, read_yaml, target_rows_from_payload, write_text, write_yaml


def build_universe_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        ticker = str(target["ticker"]).upper()
        for fiscal_period in target.get("fiscal_periods", []):
            rows.append(
                {
                    "case_id": case_id_for(ticker, str(fiscal_period)),
                    "ticker": ticker,
                    "company_name": target["company_name"],
                    "exchange": target.get("exchange", "NYSE"),
                    "sector": target.get("sector", ""),
                    "fiscal_period": str(fiscal_period),
                    "event_identity_status": "target_only",
                    "metadata_only": True,
                    "proof_of_event_existence": False,
                    "rights_status": "unknown",
                    "raw_transcript_allowed": False,
                    "raw_audio_allowed": False,
                    "raw_video_allowed": False,
                    "raw_slides_allowed": False,
                    "manual_action": "link target to reviewed official IR or SEC metadata candidate",
                }
            )
    return rows


def build_report(rows: list[dict[str, Any]]) -> str:
    tickers = sorted({str(row["ticker"]) for row in rows})
    periods = sorted({str(row["fiscal_period"]) for row in rows})
    return f"""# NYSE 5-Year IR/SEC Universe

Status: target-only metadata universe.

- Tickers: {len(tickers)}
- Fiscal periods: {len(periods)}
- Target cases: {len(rows)}
- Network used: no
- Proof of event existence claimed: no

Exact call dates are left as source-candidate or manual-verification work. The universe is a planning surface for official IR and SEC/EDGAR metadata discovery.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the NYSE 5-year IR/SEC metadata target universe.")
    parser.add_argument("--targets", default="configs/nyse_5y_ir_sec_targets.example.yml")
    parser.add_argument("--policy", default="configs/ir_sec_acquisition_policy.example.yml")
    parser.add_argument("--out", default="data/corpus/nyse_5y_ir_sec_universe.yml")
    parser.add_argument("--report", default="reports/agent5/nyse_5y_ir_sec_universe.md")
    args = parser.parse_args(argv)

    policy = read_yaml(ROOT / args.policy)
    targets = target_rows_from_payload(read_yaml(ROOT / args.targets), lookback_years=int(policy.get("lookback_years", 5)))
    rows = build_universe_rows(targets)
    write_yaml(ROOT / args.out, {"status": "target_only", "network_used": False, "events": rows})
    write_text(ROOT / args.report, build_report(rows))
    print(f"NYSE 5-year IR/SEC universe written: {len(rows)} target case(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
