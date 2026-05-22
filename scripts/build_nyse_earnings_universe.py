#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

from resource_registry_common import read_structured, write_json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.corpus.nyse_universe import build_case_from_metadata, validate_nyse_universe


def _from_ticker_csv(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for item in csv.DictReader(handle):
            rows.append(
                build_case_from_metadata(
                    case_id=item.get("case_id") or f"nyse_{item['ticker'].lower()}_{item['fiscal_period'].lower()}",
                    ticker=item["ticker"],
                    company_name=item.get("company_name", ""),
                    fiscal_period=item.get("fiscal_period", "unknown_period"),
                    call_date=item.get("call_date", "2023-01-01"),
                    call_datetime=item.get("call_datetime", "2023-01-01T00:00:00Z"),
                )
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build NYSE target-universe metadata without network calls.")
    parser.add_argument("--ticker-csv", help="Optional user-supplied ticker metadata CSV.")
    parser.add_argument("--example-config", default="configs/nyse_earnings_universe.example.yml")
    parser.add_argument("--out", help="Optional JSON output path. Nothing is written by default.")
    args = parser.parse_args(argv)

    if args.ticker_csv:
        rows = _from_ticker_csv(Path(args.ticker_csv))
    else:
        payload = read_structured(Path(args.example_config))
        rows = payload.get("cases", []) if isinstance(payload, dict) else []
    errors = validate_nyse_universe(rows)
    summary = {"status": "valid" if not errors else "invalid", "row_count": len(rows), "errors": errors, "cases": rows}
    if args.out:
        write_json(Path(args.out), summary)
    if errors:
        print(f"NYSE universe build blocked: {len(errors)} validation error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"NYSE universe build dry-run passed: {len(rows)} metadata row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
