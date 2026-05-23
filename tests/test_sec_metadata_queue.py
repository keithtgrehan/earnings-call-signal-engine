from __future__ import annotations

from scripts.build_sec_metadata_queue import build_sec_metadata_queue


def test_sec_metadata_queue_is_metadata_first_and_rate_limited() -> None:
    targets = [{"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "fiscal_periods": ["2026_Q1"]}]
    policy = {
        "sec": {
            "target_forms": ["8-K", "10-Q", "10-K"],
            "max_requests_per_second": 10,
            "user_agent": "SignalEngine/IR-SEC metadata discovery contact@example.com",
            "raw_filing_body_downloads": False,
        }
    }

    rows = build_sec_metadata_queue(targets, policy)

    assert len(rows) == 1
    row = rows[0]
    assert row["cik_lookup_required"] is True
    assert row["target_forms"] == ["8-K", "10-Q", "10-K"]
    assert row["max_requests_per_second"] == 10
    assert row["user_agent_required"] is True
    assert row["raw_body_allowed"] is False
    assert row["metadata_only"] is True
    assert row["blocked_reason_code"] == "sec_metadata_only"
    assert str(row["provenance_hash"]).startswith("sha256:")
