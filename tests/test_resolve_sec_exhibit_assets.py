from __future__ import annotations

from signal_engine.acquisition.sec_resolver import resolve_sec_assets_for_rows


def test_sec_resolver_prioritizes_8k_item_202_exhibit_991_without_calling_release_a_transcript() -> None:
    rows = [
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "exchange": "NYSE",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q4",
            "event_date": "2025-12-31",
        }
    ]
    ticker_ciks = {"JPM": "0000019617"}
    submissions = {
        "JPM": [
            {
                "form": "8-K",
                "filingDate": "2025-10-14",
                "accessionNumber": "0000019617-25-000123",
                "items": "2.02",
                "primaryDocument": "jpm-20251014.htm",
                "description": "Current report",
                "exhibits": [
                    {"document": "ex991.htm", "description": "EX-99.1 Earnings release"},
                    {"document": "ex992.htm", "description": "EX-99.2 Earnings call transcript"},
                ],
            }
        ]
    }

    candidates = resolve_sec_assets_for_rows(rows, ticker_ciks=ticker_ciks, submissions_by_ticker=submissions)

    release = next(row for row in candidates if row["resolved_asset_url"].endswith("ex991.htm"))
    transcript = next(row for row in candidates if row["resolved_asset_url"].endswith("ex992.htm"))
    assert release["asset_type"] == "sec_exhibit"
    assert "earnings release" in release["confidence_reason"].lower()
    assert transcript["asset_type"] == "transcript_html"
    assert transcript["download_allowed"] == "true"
    assert transcript["source_type"] == "sec_edgar"


def test_sec_resolver_skips_non_nyse_rows_and_old_filings() -> None:
    rows = [
        {"case_id": "abc_2025_q4", "ticker": "ABC", "exchange": "NASDAQ", "fiscal_year": "2025", "fiscal_quarter": "Q4"},
        {"case_id": "xyz_2019_q4", "ticker": "XYZ", "exchange": "NYSE", "fiscal_year": "2019", "fiscal_quarter": "Q4"},
    ]

    candidates = resolve_sec_assets_for_rows(rows, ticker_ciks={"ABC": "1", "XYZ": "2"}, submissions_by_ticker={})

    assert candidates == []
