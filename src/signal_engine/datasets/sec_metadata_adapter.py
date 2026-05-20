from __future__ import annotations

from typing import Any


def normalize_sec_metadata_row(row: dict[str, Any]) -> dict[str, str]:
    """Normalize metadata-only SEC/EDGAR rows without downloading filings."""
    accession = str(row.get("accession_number") or row.get("accession") or "").strip()
    ticker = str(row.get("ticker") or "").strip().upper()
    filing_type = str(row.get("filing_type") or row.get("form") or "").strip().upper()
    filed_at = str(row.get("filed_at") or row.get("filing_date") or "").strip()
    source_url = str(row.get("source_url") or row.get("url") or "").strip()
    return {
        "accession_number": accession,
        "ticker": ticker,
        "filing_type": filing_type,
        "filed_at": filed_at,
        "source_url": source_url,
        "source_type": "sec_metadata",
    }
