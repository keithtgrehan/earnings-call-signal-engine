from __future__ import annotations

import csv
from pathlib import Path

from tools.chunk_user_authorized_transcripts import chunk_user_authorized_transcripts
from tools.register_user_authorized_desktop_assets import register_user_authorized_assets


DOWNLOAD_LOG_FIELDS = [
    "source_id",
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "source_type",
    "source_url",
    "download_status",
    "blocked_reason",
    "local_path",
    "sha256",
    "bytes",
    "content_type",
    "commit_allowed",
    "training_allowed",
    "eval_allowed",
    "approval_ref",
    "provenance_path",
]


def _write_download_log(path: Path, transcript: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DOWNLOAD_LOG_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "source_id": "src_1",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "asset_type": "transcript",
                "source_type": "official_ir_transcript",
                "source_url": "file://fixture",
                "download_status": "downloaded",
                "local_path": str(transcript),
                "sha256": "sha256:" + "a" * 64,
                "commit_allowed": "false",
                "training_allowed": "false",
                "eval_allowed": "true",
                "approval_ref": "approval://keith/test",
            }
        )


def test_registers_and_chunks_transcript_text_desktop_only(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    transcript = workspace / "JPM_JPMorgan_Chase_Co" / "2025-12-31_FY2025_Q4" / "transcript" / "call.txt"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("Operator: welcome to the call. Prepared remarks. Question-and-answer. " * 80, encoding="utf-8")
    log = workspace / "_audit" / "user_authorized_download_log.csv"
    _write_download_log(log, transcript)
    monkeypatch.setattr("tools.register_user_authorized_desktop_assets.REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr("tools.chunk_user_authorized_transcripts.REPORT_DIR", tmp_path / "reports")

    transcript_registry = tmp_path / "manual_local_transcript_registry.csv"
    audio_registry = tmp_path / "manual_local_audio_registry.csv"
    registry_summary = register_user_authorized_assets(
        workspace=workspace,
        download_log=log,
        transcript_out=transcript_registry,
        audio_out=audio_registry,
    )
    chunk_summary = chunk_user_authorized_transcripts(
        registry_path=transcript_registry,
        workspace=workspace,
        out_path=tmp_path / "repo_manifest.csv",
        chunk_chars=120,
        overlap_chars=20,
    )

    assert registry_summary["registered_transcripts"] == 1
    assert chunk_summary["transcript_chunks"] > 1
    rows = list(csv.DictReader((tmp_path / "repo_manifest.csv").open(newline="", encoding="utf-8")))
    assert "Operator: welcome" not in (tmp_path / "repo_manifest.csv").read_text(encoding="utf-8")
    assert all(Path(row["local_chunk_path"]).exists() for row in rows)
    assert all(workspace in Path(row["local_chunk_path"]).parents for row in rows)
    assert all(row["raw_text_committed"] == "false" for row in rows)
