from __future__ import annotations

from signal_engine.audio.asr_manifest import build_asr_manifest_row


def test_asr_manifest_missing_dependency_does_not_crash() -> None:
    row = build_asr_manifest_row(case_id="vz_2024_q4", audio_asset_id="vz_2024_q4_audio", audio_sha256="sha256:" + "a" * 64, engine="missing-backend")
    assert row["cloud_upload"] is False
    assert row["raw_asr_committed"] is False
    assert row["dependency_status"] == "dependency_missing"
