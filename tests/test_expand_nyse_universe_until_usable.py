from __future__ import annotations

from tools.expand_nyse_universe_until_usable import expand_nyse_universe


def test_expansion_keeps_only_verified_nyse_recent_first_and_tracks_extra_companies() -> None:
    existing = [{"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "sector": "banking"}]
    candidates = [
        {"ticker": "ABC", "company_name": "ABC Corp", "exchange": "NASDAQ", "sector": "tech", "rank": "1"},
        {"ticker": "XOM", "company_name": "Exxon Mobil", "exchange": "NYSE", "sector": "energy", "rank": "2"},
        {"ticker": "LLY", "company_name": "Eli Lilly", "exchange": "NYSE", "sector": "healthcare", "rank": "3"},
    ]

    rows, summary = expand_nyse_universe(existing_companies=existing, candidate_companies=candidates, usable_pairs=0, target_pairs=2)

    assert [row["ticker"] for row in rows] == ["XOM", "LLY"]
    assert summary["extra_nyse_companies_selected"] == 2
    assert summary["excluded_non_nyse"] == 1


def test_expansion_is_noop_when_target_already_met() -> None:
    rows, summary = expand_nyse_universe(existing_companies=[], candidate_companies=[{"ticker": "XOM", "exchange": "NYSE"}], usable_pairs=100, target_pairs=100)

    assert rows == []
    assert summary["status"] == "target_pairs_already_met"
