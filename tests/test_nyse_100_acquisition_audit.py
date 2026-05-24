from __future__ import annotations

import csv
from pathlib import Path

from signal_engine.acquisition.nyse100 import AUDIT_FIELDS, build_call_targets, build_company_universe, populate_desktop_workspace
from scripts.validate_nyse_100_acquisition_audit import validate_audit_rows


def test_acquisition_audit_has_required_fields_and_metadata_only_rows(tmp_path: Path) -> None:
    targets = build_call_targets(build_company_universe()[:1], start_year=2025, years_back=1)
    populate_desktop_workspace(targets, output_root=tmp_path, checkpoint_interval=25)
    audit_path = tmp_path / "_audit" / "nyse_earnings_call_audit.csv"
    rows = list(csv.DictReader(audit_path.open(newline="", encoding="utf-8")))

    assert list(rows[0].keys()) == AUDIT_FIELDS
    assert validate_audit_rows(rows, audit_path=audit_path) == []
    assert rows[0]["rights_status"] == "metadata_only"
    assert rows[0]["transcript_local_path"].endswith("/transcript")
    assert rows[0]["audio_local_path"].endswith("/audio")
    assert rows[0]["video_local_path"].endswith("/video")


def test_audit_validation_requires_blocked_reason_for_blocked_rows(tmp_path: Path) -> None:
    rows = [
        {field: "" for field in AUDIT_FIELDS}
        | {
            "case_id": "jpm_2025_q4",
            "ticker_symbol": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "exchange": "NYSE",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q4",
            "calendar_year": "2025",
            "rights_status": "blocked",
            "priority_tier": "4",
            "local_paths_created": "false",
            "provenance_hash": "sha256:" + "a" * 64,
        }
    ]

    errors = validate_audit_rows(rows, audit_path=tmp_path / "audit.csv")

    assert any("blocked rows require blocked_reason" in error for error in errors)
