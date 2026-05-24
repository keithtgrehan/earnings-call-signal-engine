from __future__ import annotations

from signal_engine.acquisition.rights import decide_rights, validate_permitted_download_row


def test_unknown_rights_fail_closed_for_raw_use() -> None:
    decision = decide_rights({"source_type": "official_ir", "rights_status": "unknown", "raw_requested": True})

    assert decision["rights_status"] == "unknown_fail_closed"
    assert decision["blocked_reason"] == "rights_unknown"
    assert decision["download_allowed"] is False


def test_youtube_media_is_metadata_only_without_authorization() -> None:
    decision = decide_rights(
        {
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/watch?v=abc",
            "asset_type": "audio",
            "raw_requested": True,
        }
    )

    assert decision["rights_status"] == "metadata_only"
    assert decision["blocked_reason"] == "youtube_media_blocked"
    assert decision["download_allowed"] is False


def test_vendor_raw_requires_license_config_ref() -> None:
    decision = decide_rights({"source_type": "vendor", "source_url": "licensed-vendor://demo", "raw_requested": True})

    assert decision["rights_status"] == "license_required"
    assert decision["blocked_reason"] == "vendor_license_missing"
    assert decision["download_allowed"] is False


def test_official_ir_raw_requires_terms_robots_and_allow_flag() -> None:
    blocked = decide_rights(
        {
            "source_type": "official_ir",
            "rights_status": "safe_to_download",
            "raw_requested": True,
            "terms_checked": True,
            "robots_checked": False,
        }
    )
    allowed = decide_rights(
        {
            "source_type": "official_ir",
            "rights_status": "safe_to_download",
            "raw_requested": True,
            "terms_checked": True,
            "robots_checked": True,
            "allowed_storage": True,
            "source_url": "file:///tmp/source.txt",
        }
    )

    assert blocked["rights_status"] == "blocked"
    assert blocked["blocked_reason"] == "robots_blocked"
    assert allowed["download_allowed"] is True


def test_validate_permitted_download_row_rejects_unsafe_sources() -> None:
    errors = validate_permitted_download_row(
        {
            "case_id": "jpm_2025_q4",
            "source_type": "youtube",
            "rights_status": "safe_to_download",
            "source_url": "https://youtube.com/watch?v=abc",
        }
    )

    assert any("YouTube" in error for error in errors)

    safe_errors = validate_permitted_download_row(
        {
            "case_id": "jpm_2025_q4",
            "asset_type": "transcript",
            "source_type": "manually_approved_source",
            "rights_status": "safe_to_download",
            "source_url": "file:///tmp/transcript.txt",
        }
    )

    assert safe_errors == []
