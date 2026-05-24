from __future__ import annotations

import csv
from pathlib import Path

from tools.apply_manual_source_approvals import apply_approvals
from tools.source_rights_common import QUEUE_FIELDS


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            payload = {field: "" for field in QUEUE_FIELDS}
            payload.update(row)
            writer.writerow(payload)


def test_pending_rows_do_not_promote(tmp_path: Path, monkeypatch) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue(
        queue,
        [
            {
                "source_id": "src_pending",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "asset_type": "transcript",
                "source_type": "official_ir",
                "source_url": "https://ir.example.com/transcript",
                "allow_download": "false",
                "commit_allowed": "false",
            }
        ],
    )
    monkeypatch.setattr("tools.apply_manual_source_approvals.REPORT_DIR", tmp_path / "reports")
    permitted, rejected = apply_approvals(input_path=queue, out_path=tmp_path / "permitted.csv")

    assert permitted == []
    assert rejected
    assert (tmp_path / "permitted.csv").read_text(encoding="utf-8").count("\n") == 1


def test_complete_manual_approval_promotes_download_but_not_commit(tmp_path: Path, monkeypatch) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue(
        queue,
        [
            {
                "source_id": "src_approved",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "asset_type": "transcript",
                "source_type": "official_ir",
                "source_url": "https://ir.example.com/transcript",
                "blocked_reason": "",
                "allow_download": "true",
                "allow_eval_use": "true",
                "allow_training_use": "false",
                "commit_allowed": "false",
                "approval_ref": "approval://keith/jpm-q4",
                "approved_by": "Keith",
                "approved_at": "2026-05-24T00:00:00+00:00",
                "provenance_hash": "sha256:" + "a" * 64,
            }
        ],
    )
    monkeypatch.setattr("tools.apply_manual_source_approvals.REPORT_DIR", tmp_path / "reports")
    permitted, rejected = apply_approvals(input_path=queue, out_path=tmp_path / "permitted.csv")

    assert rejected == {}
    assert len(permitted) == 1
    assert permitted[0]["rights_status"] == "safe_to_download"
    assert permitted[0]["authorization_ref"] == "approval://keith/jpm-q4"


def test_youtube_audio_never_promotes(tmp_path: Path, monkeypatch) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue(
        queue,
        [
            {
                "source_id": "src_youtube",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "asset_type": "audio",
                "source_type": "official_ir_webcast",
                "source_url": "https://www.youtube.com/watch?v=abc",
                "allow_download": "true",
                "commit_allowed": "false",
                "approval_ref": "approval://keith/jpm-q4",
                "approved_by": "Keith",
                "approved_at": "2026-05-24T00:00:00+00:00",
            }
        ],
    )
    monkeypatch.setattr("tools.apply_manual_source_approvals.REPORT_DIR", tmp_path / "reports")
    permitted, rejected = apply_approvals(input_path=queue, out_path=tmp_path / "permitted.csv")

    assert permitted == []
    assert any("YouTube" in error for errors in rejected.values() for error in errors)
