#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import build_call_targets, build_company_universe, build_ir_source_candidates, write_csv

def main() -> None:
    rows = build_ir_source_candidates(build_call_targets(build_company_universe(), start_year=2025, years_back=5))
    write_csv(
        ROOT / "data/acquisition/nyse_100_ir_source_candidates.csv",
        rows,
        [
            "case_id",
            "ticker",
            "company_name",
            "fiscal_year",
            "fiscal_quarter",
            "official_ir_url",
            "source_domain",
            "candidate_type",
            "network_fetch_enabled",
            "source_status",
            "rights_status",
            "notes",
        ],
    )
    print({"ir_source_candidates": len(rows)})


if __name__ == "__main__":
    main()
