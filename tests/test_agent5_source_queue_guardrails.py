from __future__ import annotations

from signal_engine.agent5_acquisition import build_nyse_30_targets, build_source_queue, validate_source_queue


def test_source_queue_is_metadata_only() -> None:
    rows = build_source_queue(build_nyse_30_targets())
    assert len(rows) == 150
    assert not validate_source_queue(rows)
    assert all(row["stores_body"] is False for row in rows)
    assert all(row["stores_transcript_text"] is False for row in rows)
    assert all(row["stores_media"] is False for row in rows)
    assert all(str(row["provenance_hash"]).startswith("sha256:") for row in rows)


def test_youtube_and_vendor_raw_ingest_blocked() -> None:
    rows = build_source_queue(build_nyse_30_targets()[:1])
    youtube = next(row for row in rows if row["source_type"] == "youtube_metadata_only")
    vendor = next(row for row in rows if row["source_type"] == "licensed_vendor_blocked")
    assert youtube["raw_audio_allowed"] is False
    assert youtube["raw_video_allowed"] is False
    assert vendor["raw_body_allowed"] is False
    youtube["raw_video_allowed"] = True
    vendor["raw_body_allowed"] = True
    errors = validate_source_queue(rows)
    assert any("youtube_metadata_only must keep raw_video_allowed=false" in error for error in errors)
    assert any("licensed_vendor_blocked must keep raw_body_allowed=false" in error for error in errors)


def test_sec_candidates_include_fair_access_metadata() -> None:
    rows = build_source_queue(build_nyse_30_targets()[:1])
    sec = next(row for row in rows if row["source_type"] == "sec_edgar_metadata_candidate")
    assert sec["fair_access_rate_limit_per_second"] == 10
    sec["fair_access_note"] = ""
    assert any("fair_access_note" in error for error in validate_source_queue(rows))
