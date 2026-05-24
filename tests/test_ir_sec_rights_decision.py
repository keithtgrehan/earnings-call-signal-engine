from __future__ import annotations

from signal_engine.ir_sec_acquisition import (
    build_asset_availability,
    build_permitted_ingest_queue,
    classify_source_type,
    decide_source_use,
    make_provenance_hash,
    normalize_candidate,
)


def _candidate(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "candidate_id": "cand_1",
        "case_id": "case_jpm_2026_q1",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "exchange": "NYSE",
        "fiscal_period": "2026_Q1",
        "source_type": "official_ir_metadata",
        "source_url_or_ref": "official-ir://JPM/quarterly_results/2026_Q1",
        "source_domain": "review-required",
        "source_terms_url": "",
        "robots_url": "",
        "rights_status": "unknown",
        "rights_tier": "publicly_available",
        "source_terms_checked": False,
        "robots_checked": False,
        "paywall_or_login_required": False,
        "raw_transcript_allowed": False,
        "raw_audio_allowed": False,
        "raw_video_allowed": False,
        "raw_slides_allowed": False,
        "commit_allowed": False,
        "eval_allowed": False,
        "training_allowed": False,
        "metadata_only": True,
        "blocked_reason_code": "source_terms_not_checked",
        "manual_action": "review official IR source terms and robots",
        "last_checked_at": "2026-05-23T00:00:00+00:00",
    }
    row.update(overrides)
    row["provenance_hash"] = make_provenance_hash(row)
    return row


def test_unknown_rights_blocks_raw_use() -> None:
    candidate = normalize_candidate(
        _candidate(
            source_type="official_ir_permitted_raw",
            metadata_only=False,
            raw_transcript_allowed=True,
            rights_status="unknown",
            source_terms_checked=True,
            robots_checked=True,
            blocked_reason_code="",
        )
    )

    decision = decide_source_use(candidate, {"unknown_rights_default": "blocked"})

    assert decision["decision"] == "blocked"
    assert decision["blocked_reason_code"] == "unknown_rights"


def test_official_ir_raw_without_terms_check_is_blocked() -> None:
    candidate = normalize_candidate(
        _candidate(
            source_type="official_ir_permitted_raw",
            metadata_only=False,
            rights_status="approved",
            rights_tier="official_public_terms_checked",
            raw_transcript_allowed=True,
            source_terms_checked=False,
            robots_checked=True,
            blocked_reason_code="",
        )
    )

    decision = decide_source_use(candidate, {"require_source_terms_check": True, "require_robots_check": True})

    assert decision["decision"] == "blocked"
    assert decision["blocked_reason_code"] == "source_terms_not_checked"


def test_official_ir_metadata_only_is_allowed_as_metadata_only() -> None:
    candidate = normalize_candidate(_candidate())

    decision = decide_source_use(candidate, {"unknown_rights_default": "blocked"})

    assert decision["decision"] == "metadata_only"
    assert decision["metadata_only"] is True


def test_youtube_raw_media_is_blocked_without_authorization() -> None:
    candidate = normalize_candidate(
        _candidate(
            source_type="blocked_restricted",
            source_url_or_ref="https://www.youtube.com/watch?v=metadata_only",
            source_domain="youtube.com",
            rights_status="approved",
            source_terms_checked=True,
            robots_checked=True,
            metadata_only=False,
            raw_audio_allowed=True,
            blocked_reason_code="",
        )
    )

    decision = decide_source_use(candidate, {})

    assert classify_source_type(str(candidate["source_url_or_ref"])) == "blocked_restricted"
    assert decision["decision"] == "blocked"
    assert decision["blocked_reason_code"] == "youtube_raw_media_blocked_without_authorization"


def test_vendor_raw_is_blocked_without_license_config() -> None:
    candidate = normalize_candidate(
        _candidate(
            source_type="blocked_restricted",
            source_url_or_ref="licensed-vendor://provider/JPM/2026_Q1",
            rights_status="approved",
            source_terms_checked=True,
            robots_checked=True,
            metadata_only=False,
            raw_transcript_allowed=True,
            blocked_reason_code="",
        )
    )

    decision = decide_source_use(candidate, {})

    assert decision["decision"] == "blocked"
    assert decision["blocked_reason_code"] == "licensed_vendor_without_license_config"


def test_manual_local_path_hash_stays_separate_from_ir_sec_candidates() -> None:
    manual = normalize_candidate(
        _candidate(
            source_type="manual_local",
            source_url_or_ref="/operator/local/JPM_2026_Q1.txt",
            source_domain="local",
            rights_status="manual_registered",
            rights_tier="manual_supplied",
            metadata_only=True,
            manual_local_registered=True,
            source_sha256="sha256:" + "a" * 64,
            blocked_reason_code="",
        )
    )
    official = normalize_candidate(_candidate(candidate_id="cand_2"))

    availability = build_asset_availability([manual, official])
    queue = build_permitted_ingest_queue([manual, official], {})

    assert availability["case_jpm_2026_q1"]["manual_local_registered"] is True
    assert availability["case_jpm_2026_q1"]["official_ir_candidate"] is True
    assert queue == []
    assert make_provenance_hash(manual).startswith("sha256:")
