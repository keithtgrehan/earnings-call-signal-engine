from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_nyse_100_asset_acquisition import validate_acquisition
import tools.build_nyse_100_audio_rag_manifest as audio_module


AUDIT_FIELDS = [
    "asset_id",
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "calendar_year",
    "earnings_call_date",
    "asset_type",
    "source_url",
    "source_type",
    "rights_status",
    "availability",
    "download_status",
    "blocked_reason",
    "local_path",
    "transcript_local_path",
    "audio_local_path",
    "sha256",
    "content_type",
    "bytes",
    "created_at",
    "provenance_hash",
    "metadata_path",
    "provenance_path",
    "raw_git_committed",
    "license_config_ref",
    "manual_approval_ref",
    "allow_eval_use",
    "allow_training_use",
    "source_domain",
    "folder_path",
]


def _write_audit(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _audio_row(workspace: Path, audio_path: Path, **overrides: str) -> dict[str, str]:
    row = {
        "asset_id": "jpm_2025_q1_audio",
        "case_id": "jpm_2025_q1",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "exchange": "NYSE",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "calendar_year": "2025",
        "earnings_call_date": "2025-04-14",
        "asset_type": "audio",
        "source_url": "file://fixture",
        "source_type": "official_ir_webcast",
        "rights_status": "safe_to_download",
        "availability": "available",
        "download_status": "downloaded",
        "blocked_reason": "",
        "local_path": str(audio_path),
        "transcript_local_path": "",
        "audio_local_path": str(audio_path),
        "sha256": "sha256:" + "e" * 64,
        "content_type": "audio/mpeg",
        "bytes": "16",
        "created_at": "2026-05-24T00:00:00+00:00",
        "provenance_hash": "sha256:" + "f" * 64,
        "metadata_path": "",
        "provenance_path": "",
        "raw_git_committed": "false",
        "license_config_ref": "",
        "manual_approval_ref": "",
        "allow_eval_use": "true",
        "allow_training_use": "false",
        "source_domain": "ir.example.com",
        "folder_path": str(workspace / "JPM_JPMorgan_Chase_Co" / "2025-04-14_FY2025_Q1"),
    }
    row.update(overrides)
    return row


def test_audio_rag_manifest_is_todo_when_asr_disabled(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    audio_path = workspace / "JPM_JPMorgan_Chase_Co" / "2025-04-14_FY2025_Q1" / "audio" / "call.mp3"
    audio_path.parent.mkdir(parents=True)
    audio_path.write_bytes(b"ID3synthetic-audio")
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    _write_audit(audit, [_audio_row(workspace, audio_path)])

    out = tmp_path / "repo" / "data" / "acquisition" / "nyse_100_audio_rag_manifest.csv"
    monkeypatch.setattr(audio_module, "REPORT_DIR", tmp_path / "repo_reports")
    exit_code = audio_module.main(["--workspace", str(workspace), "--audit", str(audit), "--out", str(out)])

    assert exit_code == 0
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["asr_status"] == "todo_asr_disabled"
    assert rows[0]["raw_text_committed"] == "false"


def test_validator_catches_raw_asset_path_inside_repo(tmp_path: Path) -> None:
    workspace = tmp_path / "desktop"
    repo_root = tmp_path / "repo"
    raw_transcript = repo_root / "data" / "raw" / "transcript.txt"
    raw_transcript.parent.mkdir(parents=True)
    raw_transcript.write_text("raw transcript should not be in repo", encoding="utf-8")
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    _write_audit(
        audit,
        [
            _audio_row(
                workspace,
                raw_transcript,
                asset_type="transcript",
                local_path=str(raw_transcript),
                transcript_local_path=str(raw_transcript),
                audio_local_path="",
                content_type="text/plain",
            )
        ],
    )

    result = validate_acquisition(workspace=workspace, audit_path=audit, repo_root=repo_root, target_count=1)

    assert any("raw asset local_path is inside repo" in error for error in result.errors)
