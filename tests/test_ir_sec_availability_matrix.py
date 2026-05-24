from __future__ import annotations

from signal_engine.ir_sec_acquisition import build_asset_availability
from scripts.build_ir_sec_availability_matrix import build_availability_rows
from scripts.build_official_ir_candidate_map import build_official_ir_candidate_map
from scripts.build_sec_metadata_queue import build_sec_metadata_queue


def test_ir_sec_availability_matrix_combines_official_ir_and_sec_candidates() -> None:
    targets = [{"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "fiscal_periods": ["2026_Q1"]}]
    official_rows = build_official_ir_candidate_map(targets)
    sec_rows = build_sec_metadata_queue(
        targets,
        {"sec": {"target_forms": ["8-K"], "max_requests_per_second": 10, "user_agent": "SignalEngine/IR-SEC metadata discovery contact@example.com"}},
    )

    availability = build_asset_availability([*official_rows, *sec_rows])
    rows = build_availability_rows(availability)

    assert len(rows) == 1
    row = rows[0]
    assert row["case_id"] == "irsec_jpm_2026_q1"
    assert row["event_identity_status"] == "source_candidate_found"
    assert row["official_ir_candidate"] is True
    assert row["sec_candidate"] is True
    assert row["manual_local_registered"] is False
    assert row["permitted_ingest_available"] is False
    assert row["provenance_complete"] is False
