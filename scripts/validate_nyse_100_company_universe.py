#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import COMPANY_FIELDS

def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if len(rows) != 100:
        errors.append(f"company universe must contain 100 rows, found {len(rows)}")
    tickers: set[str] = set()
    for index, row in enumerate(rows, start=1):
        for field in COMPANY_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing {field}")
        ticker = row.get("ticker", "")
        if ticker in tickers:
            errors.append(f"row {index}: duplicate ticker {ticker}")
        tickers.add(ticker)
        if row.get("exchange") != "NYSE":
            errors.append(f"row {index}: exchange must be NYSE")
        if not row.get("exchange_status", "").startswith("verified"):
            errors.append(f"row {index}: exchange_status must be verified")
    return errors


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=ROOT / "data/acquisition/nyse_100_company_universe.csv")
    args = parser.parse_args()
    errors = validate_rows(read_rows(args.path))
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"NYSE 100 company universe validation passed: {args.path}")


if __name__ == "__main__":
    main()
