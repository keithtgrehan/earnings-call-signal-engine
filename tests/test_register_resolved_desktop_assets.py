from __future__ import annotations

import csv
from pathlib import Path

from tools.register_resolved_desktop_assets import register_resolved_assets


def test_register_resolved_assets_writes_path_hash_only(tmp_path: Path) -> None:
    workspace = tmp_path / "desktop"
    transcript = workspace / "JPM" / "jpm_2025_q4" / "transcript" / "transcript.txt"
    audio = workspace / "JPM" / "jpm_2025_q4" / "audio" / "call.mp3"
    transcript.parent.mkdir(parents=True)
    audio.parent.mkdir(parents=True)
    transcript.write_text("Operator: welcome\nQuestion-and-Answer\n", encoding="utf-8")
    audio.write_bytes(b"audio")
    log = workspace / "_audit" / "resolved_download_log.csv"
    log.parent.mkdir(parents=True)
    fields = ["case_id", "ticker", "company_name", "asset_type", "source_url", "local_path", "download_status", "sha256", "provenance_path", "commit_allowed", "training_allowed", "eval_allowed", "approval_ref"]
    with log.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"case_id": "jpm_2025_q4", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "asset_type": "transcript", "source_url": "https://ir.example.com/q4.txt", "local_path": str(transcript), "download_status": "downloaded", "sha256": "", "provenance_path": "", "commit_allowed": "false", "training_allowed": "false", "eval_allowed": "true", "approval_ref": "approval://test"})
        writer.writerow({"case_id": "jpm_2025_q4", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "asset_type": "audio", "source_url": "https://ir.example.com/q4.mp3", "local_path": str(audio), "download_status": "downloaded", "sha256": "", "provenance_path": "", "commit_allowed": "false", "training_allowed": "false", "eval_allowed": "true", "approval_ref": "approval://test"})

    summary = register_resolved_assets(workspace=workspace, download_log=log, transcript_out=tmp_path / "transcripts.csv", audio_out=tmp_path / "audio.csv")

    transcript_rows = list(csv.DictReader((tmp_path / "transcripts.csv").open(newline="", encoding="utf-8")))
    audio_rows = list(csv.DictReader((tmp_path / "audio.csv").open(newline="", encoding="utf-8")))
    assert summary["registered_transcripts"] == 1
    assert summary["registered_audio"] == 1
    assert transcript_rows[0]["local_path"] == str(transcript)
    assert transcript_rows[0]["sha256"].startswith("sha256:")
    assert transcript_rows[0]["commit_allowed"] == "false"
    assert audio_rows[0]["training_allowed"] == "false"
