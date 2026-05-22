from __future__ import annotations

from signal_engine.corpus.nyse_universe import build_case_from_metadata, validate_nyse_case, validate_nyse_universe


def test_nyse_universe_unknown_rights_blocks_raw_ingest() -> None:
    row = build_case_from_metadata(
        case_id="nyse_demo_q1",
        ticker="ACM",
        company_name="ACME",
        fiscal_period="FY2023_Q1",
        call_date="2023-05-04",
        call_datetime="2023-05-04T21:00:00Z",
    )
    row["raw_transcript_allowed"] = True
    errors = validate_nyse_case(row)
    assert "unknown or restricted rights cannot request raw ingest" in errors


def test_nyse_universe_example_shape_is_valid() -> None:
    row = build_case_from_metadata(
        case_id="nyse_demo_q2",
        ticker="MNL",
        company_name="Manual Local Example",
        fiscal_period="FY2024_Q2",
        call_date="2024-08-07",
        call_datetime="2024-08-07T20:30:00Z",
    )
    assert validate_nyse_universe([row]) == []
