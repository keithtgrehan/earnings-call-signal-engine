from __future__ import annotations

from signal_engine.acquisition.nyse100 import build_call_targets, build_company_universe


def test_call_targets_start_2025_and_work_backward_five_years() -> None:
    rows = build_call_targets(build_company_universe(), start_year=2025, years_back=5)

    assert len(rows) == 500
    assert len({row["case_id"] for row in rows}) == 500
    assert {row["target_year"] for row in rows} == {"2025", "2024", "2023", "2022", "2021"}
    assert rows[0]["target_year"] == "2025"
    assert rows[99]["target_year"] == "2025"
    assert rows[100]["target_year"] == "2024"
    assert all(row["fiscal_quarter"] == "Q4" for row in rows)
    assert all(row["exchange"] == "NYSE" for row in rows)


def test_call_targets_do_not_claim_undiscovered_events() -> None:
    rows = build_call_targets(build_company_universe()[:2], start_year=2025, years_back=2)

    assert len(rows) == 4
    assert all(row["event_identity_status"] == "target_placeholder_period_end_date" for row in rows)
    assert all(row["source_status"] == "metadata_discovery_pending" for row in rows)
    assert all("not a discovered earnings-call date" in row["notes"] for row in rows)
