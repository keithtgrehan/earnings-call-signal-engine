from __future__ import annotations

from signal_engine.acquisition.matched_pair_resolver import classify_ir_platform_url, resolve_matched_pair_status, validate_matched_pair_row


def test_vz_direct_mp3_is_approval_gated() -> None:
    row = {
        "candidate_id": "mp_vz_2024_q4",
        "case_id": "vz_2024_q4",
        "ticker": "VZ",
        "company_name": "Verizon",
        "exchange": "NYSE",
        "fiscal_year": "2024",
        "fiscal_quarter": "Q4",
        "event_date": "2025-01-24",
        "transcript_url": "https://www.verizon.com/transcript.pdf",
        "prepared_transcript_url": "",
        "audio_url": "https://www.verizon.com/audio.mp3",
        "webcast_url": "",
        "source_type": "official_ir",
        "status": "strong_candidate",
        "blocker": "source terms review needed",
        "source_relation": "prepared_audio_vs_full_transcript",
        "review_required": "true",
        "prepared_audio_label": "prepared_earnings_audio",
        "asr_ready": "true",
        "license_config_ref": "",
        "approval_required": "true",
        "transcript_download_allowed": "false",
        "audio_download_allowed": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
        "pair_status": "candidate",
        "next_action": "source_rights_review",
        "notes": "",
    }
    assert classify_ir_platform_url(row["audio_url"]) == "direct_audio"
    assert validate_matched_pair_row(row) == []


def test_prepared_audio_pair_requires_review_after_match() -> None:
    status = resolve_matched_pair_status(
        {"case_id": "vz_2024_q4", "blocker": "none", "review_required": "true", "source_relation": "prepared_audio_vs_full_transcript"},
        transcript_registered=True,
        audio_registered=True,
    )
    assert status["pair_status"] == "matched_review_required"
    assert status["review_required"] == "true"
