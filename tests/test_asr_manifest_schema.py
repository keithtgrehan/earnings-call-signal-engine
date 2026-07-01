from __future__ import annotations

from signal_engine.audio.asr_manifest import build_asr_manifest_row


def test_asr_manifest_is_local_and_metadata_only() -> None:
    row = build_asr_manifest_row(case_id="case1", audio_sha256="sha256:" + "a" * 64)

    assert row["cloud_upload"] is False
    assert row["raw_asr_text_committed"] is False
