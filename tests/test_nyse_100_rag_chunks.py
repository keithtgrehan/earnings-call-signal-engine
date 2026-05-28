from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.build_nyse_100_rag_chunks as chunk_module


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


def _audit_row(workspace: Path, transcript: Path, **overrides: str) -> dict[str, str]:
    row = {
        "asset_id": "jpm_2025_q1_transcript",
        "case_id": "jpm_2025_q1",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "exchange": "NYSE",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "calendar_year": "2025",
        "earnings_call_date": "2025-04-14",
        "asset_type": "transcript",
        "source_url": "file://fixture",
        "source_type": "company_ir",
        "rights_status": "safe_to_download",
        "availability": "available",
        "download_status": "downloaded",
        "blocked_reason": "",
        "local_path": str(transcript),
        "transcript_local_path": str(transcript),
        "audio_local_path": "",
        "sha256": "sha256:" + "c" * 64,
        "content_type": "text/plain",
        "bytes": "10",
        "created_at": "2026-05-24T00:00:00+00:00",
        "provenance_hash": "sha256:" + "d" * 64,
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


def test_chunker_processes_only_allowed_transcripts(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    call_folder = workspace / "JPM_JPMorgan_Chase_Co" / "2025-04-14_FY2025_Q1"
    transcript_dir = call_folder / "transcript"
    transcript_dir.mkdir(parents=True)
    transcript = transcript_dir / "jpm_2025_q1_transcript.txt"
    transcript.write_text(("allowed transcript text " * 200), encoding="utf-8")

    blocked_transcript = transcript_dir / "blocked_transcript.txt"
    blocked_transcript.write_text("blocked text should not be chunked", encoding="utf-8")

    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    _write_audit(
        audit,
        [
            _audit_row(workspace, transcript),
            _audit_row(
                workspace,
                blocked_transcript,
                asset_id="jpm_2025_q1_blocked",
                rights_status="unknown",
                download_status="blocked",
                blocked_reason="unknown_rights_blocked",
            ),
        ],
    )

    out_manifest = tmp_path / "repo" / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
    desktop_index = workspace / "_audit" / "rag_chunk_index.csv"
    monkeypatch.setattr(chunk_module, "REPORT_DIR", tmp_path / "repo_reports")
    exit_code = chunk_module.main(
        [
            "--workspace",
            str(workspace),
            "--audit",
            str(audit),
            "--out-manifest",
            str(out_manifest),
            "--desktop-index",
            str(desktop_index),
            "--chunk-chars",
            "120",
            "--overlap-chars",
            "20",
        ]
    )

    assert exit_code == 0
    with out_manifest.open(newline="", encoding="utf-8") as handle:
        manifest_rows = list(csv.DictReader(handle))
    assert manifest_rows
    assert {row["rights_status"] for row in manifest_rows} == {"safe_to_download"}
    assert all(Path(row["local_chunk_path"]).exists() for row in manifest_rows)
    assert "allowed transcript text" not in out_manifest.read_text(encoding="utf-8")
    assert desktop_index.exists()


def test_chunk_manifest_stores_hashes_and_paths_only(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    call_folder = workspace / "JPM_JPMorgan_Chase_Co" / "2025-04-14_FY2025_Q1"
    transcript = call_folder / "transcript" / "jpm_2025_q1_transcript.txt"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("sensitive transcript sentence. " * 40, encoding="utf-8")
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    _write_audit(audit, [_audit_row(workspace, transcript)])

    out_manifest = tmp_path / "repo" / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
    monkeypatch.setattr(chunk_module, "REPORT_DIR", tmp_path / "repo_reports")
    exit_code = chunk_module.main(
        [
            "--workspace",
            str(workspace),
            "--audit",
            str(audit),
            "--out-manifest",
            str(out_manifest),
            "--desktop-index",
            str(workspace / "_audit" / "rag_chunk_index.csv"),
        ]
    )

    assert exit_code == 0
    manifest_text = out_manifest.read_text(encoding="utf-8")
    assert "sensitive transcript sentence" not in manifest_text
    with out_manifest.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["text_sha256"].startswith("sha256:")
    assert row["source_sha256"].startswith("sha256:")
    assert row["raw_text_committed"] == "false"


def test_event_markers_produce_event_aligned_chunk_types(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    call_folder = workspace / "JPM_JPMorgan_Chase_Co" / "2025-04-14_FY2025_Q1"
    transcript = call_folder / "transcript" / "jpm_2025_q1_transcript.txt"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "Prepared Remarks\n"
        "Management: SYNTHETIC PREPARED PHRASE.\n"
        "Question-and-Answer\n"
        "Analyst: SYNTHETIC QUESTION PHRASE?\n"
        "Management: SYNTHETIC ANSWER PHRASE.\n",
        encoding="utf-8",
    )
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    _write_audit(audit, [_audit_row(workspace, transcript)])

    out_manifest = tmp_path / "repo" / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
    monkeypatch.setattr(chunk_module, "REPORT_DIR", tmp_path / "repo_reports")
    exit_code = chunk_module.main(
        [
            "--workspace",
            str(workspace),
            "--audit",
            str(audit),
            "--out-manifest",
            str(out_manifest),
            "--desktop-index",
            str(workspace / "_audit" / "rag_chunk_index.csv"),
            "--chunk-chars",
            "80",
            "--overlap-chars",
            "0",
        ]
    )

    assert exit_code == 0
    with out_manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["chunk_type"] for row in rows} & {"prepared_remarks", "qa_question", "qa_answer", "qa_pair"}
    manifest_text = out_manifest.read_text(encoding="utf-8")
    assert "SYNTHETIC PREPARED PHRASE" not in manifest_text
    assert "SYNTHETIC QUESTION PHRASE" not in manifest_text
    assert "SYNTHETIC ANSWER PHRASE" not in manifest_text
