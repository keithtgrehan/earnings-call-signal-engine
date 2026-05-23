from __future__ import annotations

from signal_engine.ir_sec_acquisition import build_permitted_ingest_queue, make_provenance_hash, normalize_candidate
from scripts.build_official_ir_candidate_map import build_official_ir_candidate_map


def test_default_permitted_ingest_queue_is_empty() -> None:
    targets = [{"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "fiscal_periods": ["2026_Q1"]}]
    rows = build_official_ir_candidate_map(targets)

    queue = build_permitted_ingest_queue(rows, {})

    assert queue == []


def test_permitted_ingest_requires_explicit_raw_and_approval_flags() -> None:
    row = normalize_candidate(
        {
            "candidate_id": "cand_allowed",
            "case_id": "irsec_jpm_2026_q1",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "exchange": "NYSE",
            "fiscal_period": "2026_Q1",
            "source_type": "official_ir_permitted_raw",
            "source_url_or_ref": "https://investor.example.com/jpm/transcript",
            "source_domain": "investor.example.com",
            "source_terms_url": "https://investor.example.com/terms",
            "robots_url": "https://investor.example.com/robots.txt",
            "rights_status": "approved",
            "rights_tier": "official_public_terms_checked",
            "source_terms_checked": True,
            "robots_checked": True,
            "paywall_or_login_required": False,
            "raw_transcript_allowed": True,
            "raw_audio_allowed": False,
            "raw_video_allowed": False,
            "raw_slides_allowed": False,
            "commit_allowed": False,
            "eval_allowed": True,
            "training_allowed": False,
            "metadata_only": False,
            "blocked_reason_code": "",
            "manual_action": "",
            "approval_ref": "approval://operator/jpm_2026_q1_transcript",
            "last_checked_at": "2026-05-23T00:00:00+00:00",
        }
    )
    row["provenance_hash"] = make_provenance_hash(row)

    queue = build_permitted_ingest_queue(
        [row],
        {
            "require_manual_approval_for_raw": True,
            "allow_raw_transcript_ingest": True,
            "official_ir": {"raw_body_allowed": True, "source_terms_checked": True, "robots_checked": True},
        },
    )

    assert len(queue) == 1
    assert queue[0]["asset_type"] == "transcript"
    assert queue[0]["allowed_commit"] is False
    assert queue[0]["allowed_eval_use"] is True
    assert queue[0]["allowed_training_use"] is False
    assert queue[0]["blocked_if_missing"] is True
