from __future__ import annotations

import csv
from pathlib import Path

from scripts.validate_source_rights_review_queue import validate_queue
from tools.build_source_rights_review_queue import build_queue
from tools.source_rights_common import QUEUE_FIELDS


AUDIT_FIELDS = [
    "case_id",
    "ticker_symbol",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "calendar_year",
    "earnings_call_date",
    "transcript_source_url",
    "audio_source_url",
    "video_source_url",
    "transcript_availability",
    "audio_availability",
    "video_availability",
    "source_type",
    "rights_status",
    "priority_tier",
    "local_paths_created",
    "notes",
    "source_domain",
    "discovered_timestamp",
    "acquisition_method",
    "provenance_hash",
    "transcript_local_path",
    "audio_local_path",
    "video_local_path",
    "blocked_reason",
    "next_action",
]


def _write_audit(workspace: Path) -> None:
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    audit.parent.mkdir(parents=True)
    with audit.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "case_id": "jpm_2025_q4",
                "ticker_symbol": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "exchange": "NYSE",
                "fiscal_year": "2025",
                "fiscal_quarter": "Q4",
                "calendar_year": "2025",
                "earnings_call_date": "2025-12-31",
                "transcript_source_url": "https://ir.example.com/transcript",
                "audio_source_url": "https://ir.example.com/audio.mp3",
                "video_source_url": "",
                "source_type": "official_ir",
                "rights_status": "metadata_only",
                "source_domain": "ir.example.com",
                "blocked_reason": "metadata_only_no_raw_download",
            }
        )


def test_review_queue_defaults_fail_closed(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    _write_audit(workspace)
    monkeypatch.setattr("tools.build_source_rights_review_queue.REPORT_DIR", tmp_path / "reports")
    rows = build_queue(workspace=workspace, out_path=tmp_path / "queue.csv")

    assert len(rows) == 2
    assert list(rows[0].keys()) == QUEUE_FIELDS
    assert {row["allow_download"] for row in rows} == {"false"}
    assert {row["allow_eval_use"] for row in rows} == {"false"}
    assert {row["allow_training_use"] for row in rows} == {"false"}
    assert {row["commit_allowed"] for row in rows} == {"false"}
    assert validate_queue(tmp_path / "queue.csv") == []


def test_validator_rejects_training_without_explicit_rights(tmp_path: Path) -> None:
    path = tmp_path / "queue.csv"
    row = {field: "" for field in QUEUE_FIELDS}
    row.update(
        {
            "source_id": "src_1",
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "asset_type": "transcript",
            "source_type": "official_ir",
            "source_url": "https://ir.example.com/transcript",
            "allow_download": "false",
            "allow_training_use": "true",
            "commit_allowed": "false",
            "manual_approval_required": "true",
        }
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)

    assert any("explicit_training_rights_ref" in error for error in validate_queue(path))
