from __future__ import annotations

import json

from earnings_call_sentiment.corpus import CorpusCase, build_manifest_validation_summary


def test_corpus_case_serializes_to_manifest_row() -> None:
    row = CorpusCase(
        case_id="TEST_2026_Q1_call01",
        company="Test Co",
        ticker="TEST",
        fiscal_period="Q1_2026",
        event_date="2026-01-30",
        transcript_local_path="data/corpus/raw/transcripts/TEST_2026_Q1_call01.txt",
        transcript_verified=True,
        audio_verified=False,
        video_verified=False,
        transcript_source_type="local_asr_transcript",
        transcript_parse_status="timed_segments_available",
        audio_fetch_status="not_available",
        video_fetch_status="not_available",
        provenance={"source": "unit_test"},
    ).to_manifest_row()

    assert row["case_id"] == "TEST_2026_Q1_call01"
    assert row["transcript_verified"] == "true"
    assert json.loads(row["provenance_json"]) == {"source": "unit_test"}


def test_manifest_validation_flags_invalid_rows() -> None:
    summary = build_manifest_validation_summary(
        [
            {
                "case_id": "BROKEN",
                "company": "",
                "ticker": "BROK",
                "fiscal_period": "Q1_2026",
                "event_date": "2026-01-01",
                "transcript_verified": "true",
                "audio_verified": "false",
                "video_verified": "false",
                "transcript_source_type": "",
                "transcript_parse_status": "bad_status",
                "audio_fetch_status": "missing",
                "video_fetch_status": "missing",
                "transcript_local_path": "",
                "transcript_url": "",
                "audio_local_path": "",
                "video_local_path": "",
                "provenance_json": "",
            }
        ]
    )

    assert summary["errors"]
    assert any("missing company" in message for message in summary["errors"])
    assert any("invalid transcript_parse_status" in message for message in summary["errors"])
