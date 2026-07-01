from __future__ import annotations

from scripts.build_official_ir_candidate_map import OFFICIAL_IR_SECTIONS, build_official_ir_candidate_map


def test_official_ir_candidate_map_is_metadata_only() -> None:
    targets = [
        {
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "exchange": "NYSE",
            "fiscal_periods": ["2026_Q1"],
        }
    ]

    rows = build_official_ir_candidate_map(targets)

    assert len(rows) == len(OFFICIAL_IR_SECTIONS)
    assert {row["source_type"] for row in rows} == {"official_ir_metadata"}
    assert all(row["metadata_only"] is True for row in rows)
    assert all(row["raw_transcript_allowed"] is False for row in rows)
    assert all(row["raw_audio_allowed"] is False for row in rows)
    assert all(row["raw_video_allowed"] is False for row in rows)
    assert all(row["raw_slides_allowed"] is False for row in rows)
    assert all(row["blocked_reason_code"] == "source_terms_not_checked" for row in rows)
    assert all("review official IR source terms/robots" in row["manual_action"] for row in rows)
    assert all(str(row["provenance_hash"]).startswith("sha256:") for row in rows)
