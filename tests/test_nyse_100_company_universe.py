from __future__ import annotations

from collections import Counter

from signal_engine.acquisition.nyse100 import build_company_universe


def test_company_universe_has_100_verified_nyse_companies() -> None:
    rows = build_company_universe()

    assert len(rows) == 100
    assert len({row["ticker"] for row in rows}) == 100
    assert all(row["exchange"] == "NYSE" for row in rows)
    assert all(row["exchange_status"].startswith("verified") for row in rows)
    assert {row["ticker"] for row in rows}.isdisjoint({"WMT", "KMB", "PLTR", "SHOP"})


def test_company_universe_covers_required_industries() -> None:
    rows = build_company_universe()
    sectors = {row["sector"] for row in rows}
    industries = " ".join(row["industry"] for row in rows).lower()
    counts = Counter(row["sector"] for row in rows)

    assert {
        "banking",
        "industrials",
        "healthcare",
        "consumer",
        "telecom",
        "energy",
        "aerospace",
        "insurance",
        "payments",
        "retail",
        "logistics",
        "financial_infrastructure",
        "technology",
    }.issubset(sectors)
    assert "rating" in industries
    assert "exchange" in industries
    assert counts["banking"] >= 10
    assert counts["healthcare"] >= 10
    assert counts["consumer"] >= 8
