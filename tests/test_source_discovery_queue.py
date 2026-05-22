from __future__ import annotations

from signal_engine.data_sources.discovery_queue import build_candidate, validate_candidate


def test_youtube_discovery_blocks_raw_media_by_default() -> None:
    row = build_candidate(
        source_url="https://www.youtube.com/watch?v=demo",
        source_type="youtube_metadata",
        rights_tier="publicly_available",
        raw_audio_allowed=True,
    )
    assert "YouTube candidates must be metadata-only by default" in validate_candidate(row)


def test_licensed_vendor_discovery_blocks_raw_body() -> None:
    row = build_candidate(
        source_url="vendor://demo",
        source_type="licensed_vendor",
        rights_tier="restricted",
        raw_body_allowed=True,
        blocked_reason="blocked",
    )
    errors = validate_candidate(row)
    assert "licensed vendor raw body is blocked by default" in errors
    assert "restricted/paywalled/vendor raw body is blocked by default" in errors


def test_sec_candidate_requires_fair_access_note() -> None:
    row = build_candidate(
        source_url="https://www.sec.gov/Archives/demo",
        source_type="sec_edgar",
        rights_tier="public_domain",
        fair_access_rate_limit_per_second=10,
    )
    assert "SEC/EDGAR candidates require fair_access_note" in validate_candidate(row)
