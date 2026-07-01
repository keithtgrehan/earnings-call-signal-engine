from __future__ import annotations

from signal_engine.ir_sec_acquisition import validate_policy


def _policy(**overrides: object) -> dict[str, object]:
    policy: dict[str, object] = {
        "enabled": False,
        "network_enabled": False,
        "exchange": "NYSE",
        "lookback_years": 5,
        "default_mode": "metadata_only",
        "unknown_rights_default": "blocked",
        "require_source_terms_check": True,
        "require_robots_check": True,
        "require_manual_approval_for_raw": True,
        "allow_raw_transcript_ingest": False,
        "allow_raw_audio_ingest": False,
        "allow_raw_video_ingest": False,
        "allow_raw_slides_ingest": False,
        "commit_raw_assets": False,
        "sec": {
            "enabled": False,
            "max_requests_per_second": 10,
            "user_agent": "SignalEngine/IR-SEC metadata discovery contact@example.com",
            "cache_dir": ".cache/sec_metadata",
            "raw_filing_body_downloads": False,
            "target_forms": ["8-K", "10-Q", "10-K"],
        },
        "official_ir": {
            "enabled": False,
            "max_requests_per_second_per_domain": 1,
            "domain_allowlist": [],
            "raw_body_allowed": False,
            "source_terms_checked": False,
            "robots_checked": False,
        },
        "output": {"write_metadata_reports": True, "write_raw_assets": False},
    }
    policy.update(overrides)
    return policy


def test_default_policy_is_valid_and_network_disabled() -> None:
    errors = validate_policy(_policy())

    assert errors == []


def test_sec_queue_rate_above_10_fails() -> None:
    policy = _policy(sec={**_policy()["sec"], "enabled": True, "max_requests_per_second": 11})

    errors = validate_policy(policy)

    assert "sec.max_requests_per_second must be <= 10" in errors


def test_sec_raw_body_downloads_true_fails_default_policy() -> None:
    policy = _policy(sec={**_policy()["sec"], "raw_filing_body_downloads": True})

    errors = validate_policy(policy)

    assert "sec.raw_filing_body_downloads must remain false for this metadata-first tool" in errors


def test_missing_user_agent_fails_if_sec_enabled() -> None:
    policy = _policy(sec={**_policy()["sec"], "enabled": True, "user_agent": ""})

    errors = validate_policy(policy)

    assert "sec.user_agent is required when SEC metadata discovery is enabled" in errors


def test_official_ir_raw_disabled_unless_terms_and_robots_checked() -> None:
    policy = _policy(
        official_ir={**_policy()["official_ir"], "raw_body_allowed": True, "source_terms_checked": True, "robots_checked": False}
    )

    errors = validate_policy(policy)

    assert "official_ir.raw_body_allowed requires source_terms_checked and robots_checked" in errors
