from __future__ import annotations

from signal_engine.acquisition.matched_pair_resolver import classify_ir_platform_url


def test_choruscall_is_webcast_player_only() -> None:
    assert classify_ir_platform_url("https://event.choruscall.com/mediaframe/webcast.html?webcastid=hLub2smn") == "webcast_player_only"


def test_youtube_is_blocked_media() -> None:
    assert classify_ir_platform_url("https://www.youtube.com/watch?v=abc") == "youtube_media_blocked"


def test_transcript_pdf_and_audio_are_direct_assets() -> None:
    assert classify_ir_platform_url("https://ir.example.com/q4-transcript.pdf") == "direct_transcript"
    assert classify_ir_platform_url("https://ir.example.com/q4-call.mp3") == "direct_audio"
