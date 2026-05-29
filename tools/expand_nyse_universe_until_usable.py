#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import read_csv, write_csv

DEFAULT_EXISTING = ROOT / "data" / "acquisition" / "nyse_100_company_universe.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_expanded_candidate_universe.csv"
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "nyse_expansion_status.md"

EXPANSION_FIELDS = ["ticker", "company_name", "exchange", "sector", "industry", "rank", "selection_reason", "exchange_status", "notes"]


def expand_nyse_universe(
    *,
    existing_companies: list[dict[str, str]],
    candidate_companies: list[dict[str, str]],
    usable_pairs: int,
    target_pairs: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if usable_pairs >= target_pairs:
        return [], {"status": "target_pairs_already_met", "extra_nyse_companies_selected": 0, "excluded_non_nyse": 0}
    existing_tickers = {row.get("ticker", "") for row in existing_companies}
    selected: list[dict[str, str]] = []
    seen_sectors: set[str] = set()
    excluded_non_nyse = 0
    for row in sorted(candidate_companies, key=lambda item: int(str(item.get("rank") or 999999))):
        if str(row.get("exchange", "")).upper() != "NYSE":
            excluded_non_nyse += 1
            continue
        if row.get("ticker", "") in existing_tickers:
            continue
        selected.append({field: str(row.get(field, "")) for field in EXPANSION_FIELDS})
        seen_sectors.add(row.get("sector", ""))
        if usable_pairs + len(selected) >= target_pairs:
            break
    return selected, {
        "status": "expanded" if selected else "configured_nyse_candidate_universe_exhausted",
        "extra_nyse_companies_selected": len(selected),
        "excluded_non_nyse": excluded_non_nyse,
        "sectors_selected": len(seen_sectors),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# NYSE Expansion Status\n\n"
        f"- Status: {summary['status']}\n"
        f"- Extra NYSE companies selected: {summary['extra_nyse_companies_selected']}\n"
        f"- Excluded non-NYSE rows: {summary['excluded_non_nyse']}\n"
        f"- Sectors selected: {summary.get('sectors_selected', 0)}\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Expand beyond NYSE 100 when usable transcript/audio pairs are below target.")
    parser.add_argument("--existing", type=Path, default=DEFAULT_EXISTING)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_EXISTING)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--usable-pairs", type=int, default=0)
    parser.add_argument("--target-pairs", type=int, default=100)
    args = parser.parse_args(argv)
    rows, summary = expand_nyse_universe(existing_companies=read_csv(args.existing), candidate_companies=read_csv(args.candidates), usable_pairs=args.usable_pairs, target_pairs=args.target_pairs)
    write_csv(args.out, rows, EXPANSION_FIELDS)
    write_report(DEFAULT_REPORT, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
