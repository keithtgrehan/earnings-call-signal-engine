#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def fetch_json(url: str, *, user_agent: str) -> Any:
    request = Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_cik(cik: str | int) -> str:
    return str(cik).strip().lstrip("0").zfill(10)


def resolve_ticker(ticker: str, *, user_agent: str) -> dict[str, str]:
    tickers = fetch_json(COMPANY_TICKERS_URL, user_agent=user_agent)
    target = ticker.upper()
    for item in tickers.values():
        if str(item.get("ticker", "")).upper() == target:
            return {
                "ticker": target,
                "cik": normalize_cik(item["cik_str"]),
                "company_name": str(item.get("title", "")),
            }
    raise ValueError(f"Ticker not found in SEC company ticker metadata: {ticker}")


def recent_8k_filings(*, ticker: str, cik: str, company_name: str, user_agent: str, limit: int) -> list[dict[str, Any]]:
    submissions = fetch_json(SUBMISSIONS_URL.format(cik=normalize_cik(cik)), user_agent=user_agent)
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])

    filings: list[dict[str, Any]] = []
    cik_no_zeros = str(int(normalize_cik(cik)))
    for form, filing_date, accession, primary_document in zip(forms, filing_dates, accessions, primary_documents):
        if form != "8-K":
            continue
        accession_no_dash = str(accession).replace("-", "")
        filings.append(
            {
                "ticker": ticker.upper(),
                "cik": normalize_cik(cik),
                "company_name": company_name,
                "form": form,
                "filing_date": filing_date,
                "accession_number": accession,
                "primary_document": primary_document,
                "filing_detail_url": (
                    f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/"
                    f"{accession_no_dash}/{primary_document}"
                ),
                "metadata_only": True,
            }
        )
        if len(filings) >= limit:
            break
    return filings


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ticker",
        "cik",
        "company_name",
        "form",
        "filing_date",
        "accession_number",
        "primary_document",
        "filing_detail_url",
        "metadata_only",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch small SEC 8-K filing metadata only; no transcript scraping.")
    parser.add_argument("--ticker", help="Company ticker to resolve through SEC company_tickers metadata.")
    parser.add_argument("--cik", help="Company CIK. If omitted, --ticker is required.")
    parser.add_argument("--company-name", default="", help="Optional company name when using --cik directly.")
    parser.add_argument("--user-agent", required=True, help="Required SEC-compliant user agent, e.g. name email.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum recent 8-K metadata rows to save.")
    parser.add_argument("--json-out", help="Optional JSON output path.")
    parser.add_argument("--csv-out", help="Optional CSV output path.")
    args = parser.parse_args(argv)

    if not args.ticker and not args.cik:
        parser.error("provide --ticker or --cik")
    if args.limit < 1:
        parser.error("--limit must be >= 1")
    if not args.json_out and not args.csv_out:
        parser.error("provide --json-out and/or --csv-out")

    if args.ticker and not args.cik:
        resolved = resolve_ticker(args.ticker, user_agent=args.user_agent)
    else:
        resolved = {
            "ticker": (args.ticker or "").upper(),
            "cik": normalize_cik(args.cik or ""),
            "company_name": args.company_name,
        }

    filings = recent_8k_filings(
        ticker=resolved["ticker"],
        cik=resolved["cik"],
        company_name=resolved["company_name"],
        user_agent=args.user_agent,
        limit=args.limit,
    )
    payload = {
        "schema_version": "signal_engine_sec_8k_index_0.1",
        "source": "SEC EDGAR submissions metadata",
        "metadata_only": True,
        "notes": "Metadata only. No transcripts, exhibits, PDFs, audio, video, or paid/API outputs fetched.",
        "filings": filings,
    }

    if args.json_out:
        write_json(Path(args.json_out), payload)
    if args.csv_out:
        write_csv(Path(args.csv_out), filings)
    print(f"Fetched {len(filings)} 8-K metadata row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
