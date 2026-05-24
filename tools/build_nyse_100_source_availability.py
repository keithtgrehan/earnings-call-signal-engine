#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import build_call_targets, build_company_universe, build_source_availability, build_source_candidates, write_csv

def main() -> None:
    targets = build_call_targets(build_company_universe(), start_year=2025, years_back=5)
    rights_rows = build_source_candidates(targets)
    rows = build_source_availability(targets, rights_rows)
    write_csv(
        ROOT / "data/acquisition/nyse_100_source_availability.csv",
        rows,
        [
            "case_id",
            "ticker",
            "company_name",
            "exchange",
            "fiscal_year",
            "fiscal_quarter",
            "event_identity_status",
            "official_ir_status",
            "sec_status",
            "transcript_status",
            "audio_status",
            "video_status",
            "safe_download_candidates",
            "blocked_source_count",
            "next_action",
        ],
    )
    print({"source_availability_rows": len(rows)})


if __name__ == "__main__":
    main()
