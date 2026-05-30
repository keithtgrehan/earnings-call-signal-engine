from __future__ import annotations

import time
from datetime import date
from typing import Any

from .asset_resolver import make_candidate


def _accession_path(cik: str, accession: str, document: str) -> str:
    clean_cik = str(int(cik)) if str(cik).isdigit() else str(cik).lstrip("0")
    clean_accession = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{clean_cik}/{clean_accession}/{document}"


def _within_past_five_years(filing_date: str, current_year: int | None = None) -> bool:
    current_year = current_year or date.today().year
    try:
        year = int(str(filing_date)[:4])
    except ValueError:
        return False
    return current_year - 5 <= year <= current_year


def _is_nyse(row: dict[str, str]) -> bool:
    return str(row.get("exchange", "NYSE")).upper() == "NYSE"


def _is_transcript_like(value: str) -> bool:
    lower = value.lower()
    return "transcript" in lower and ("call" in lower or "conference" in lower or "earnings" in lower)


def _is_earnings_release(value: str) -> bool:
    lower = value.lower()
    return "99.1" in lower or "earnings release" in lower or "results" in lower


def resolve_sec_assets_for_rows(
    rows: list[dict[str, str]],
    *,
    ticker_ciks: dict[str, str],
    submissions_by_ticker: dict[str, list[dict[str, Any]]],
    current_year: int | None = None,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for row in rows:
        if not _is_nyse(row) or not _within_past_five_years(str(row.get("fiscal_year") or row.get("event_date", "")), current_year=current_year):
            continue
        ticker = row.get("ticker") or row.get("ticker_symbol") or ""
        cik = ticker_ciks.get(ticker)
        if not cik:
            continue
        for filing in submissions_by_ticker.get(ticker, []):
            form = str(filing.get("form", ""))
            filing_date = str(filing.get("filingDate", ""))
            if form not in {"8-K", "10-Q", "10-K"} or not _within_past_five_years(filing_date, current_year=current_year):
                continue
            items = str(filing.get("items", ""))
            accession = str(filing.get("accessionNumber", ""))
            primary_doc = str(filing.get("primaryDocument", ""))
            exhibits = filing.get("exhibits") or []
            if "2.02" in items or form == "8-K":
                for exhibit in exhibits:
                    document = str(exhibit.get("document", ""))
                    description = str(exhibit.get("description", ""))
                    if not document:
                        continue
                    url = _accession_path(cik, accession, document)
                    transcript_like = _is_transcript_like(description + " " + document)
                    release_like = _is_earnings_release(description + " " + document)
                    if not transcript_like and not release_like:
                        continue
                    candidates.append(
                        make_candidate(
                            row,
                            asset_type="transcript_html" if transcript_like else "sec_exhibit",
                            source_type="sec_edgar",
                            source_url=_accession_path(cik, accession, primary_doc) if primary_doc else url,
                            resolved_asset_url=url,
                            confidence=0.88 if transcript_like else 0.74,
                            confidence_reason=("explicit earnings call transcript exhibit" if transcript_like else "8-K Item 2.02 / Exhibit 99.1 earnings release metadata"),
                            rights_status="user_authorized_public_direct" if transcript_like else "metadata_only",
                            download_allowed=transcript_like,
                            next_action="download" if transcript_like else "metadata_review",
                            content_type_hint="text/html",
                        )
                    )
    return candidates


class SecMetadataClient:
    def __init__(self, *, user_agent: str, min_delay_sec: float = 0.11) -> None:
        self.user_agent = user_agent
        self.min_delay_sec = min_delay_sec
        self._last_request = 0.0

    def throttle(self) -> None:
        remaining = self.min_delay_sec - (time.time() - self._last_request)
        if remaining > 0:
            time.sleep(remaining)
        self._last_request = time.time()
