from __future__ import annotations

import csv
from pathlib import Path

from scripts.build_manual_local_batch_from_discovery import build_batch_rows
from scripts.discover_approved_local_transcripts import discover_approved_transcripts
from scripts.register_manual_local_batch import load_batch_rows, register_batch_rows


def test_discovery_writes_path_hash_only_and_blocks_unapproved_dirs(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    blocked = tmp_path / "blocked"
    approved.mkdir()
    blocked.mkdir()
    transcript = approved / "JPM_2026_Q1.txt"
    transcript.write_text("Operator: welcome\n", encoding="utf-8")
    pdf = approved / "JPM_2026_Q1_slides.pdf"
    pdf.write_bytes(b"%PDF-1.4\nmetadata only\n")
    outside = blocked / "BAC_2026_Q1.txt"
    outside.write_text("Operator: welcome\n", encoding="utf-8")

    out_path = tmp_path / "candidates.jsonl"
    report_path = tmp_path / "report.md"
    rows = discover_approved_transcripts(
        search_dirs=[approved, blocked],
        approved_dirs=[approved],
        out_path=out_path,
        report_path=report_path,
    )

    by_name = {Path(str(row["path_ref"])).name: row for row in rows}
    assert by_name["JPM_2026_Q1.txt"]["status"] == "candidate_metadata_only"
    assert str(by_name["JPM_2026_Q1.txt"]["sha256"]).startswith("sha256:")
    assert by_name["JPM_2026_Q1.txt"]["body_parsed"] is False
    assert by_name["JPM_2026_Q1_slides.pdf"]["ocr_run"] is False
    assert by_name["JPM_2026_Q1_slides.pdf"]["body_parsed"] is False
    assert by_name["BAC_2026_Q1.txt"]["status"] == "blocked_outside_approved_directories"
    assert "Operator:" not in out_path.read_text(encoding="utf-8")
    assert "Files copied: `0`" in report_path.read_text(encoding="utf-8")


def test_batch_builder_and_registration_keep_unknown_rights_closed(tmp_path: Path) -> None:
    transcript = tmp_path / "JPM_2026_Q1.txt"
    transcript.write_text("Operator: welcome\n", encoding="utf-8")
    discovery_rows = [
        {
            "path_ref": str(transcript),
            "sha256": "sha256:placeholder",
            "candidate_case_id": "jpm_2026_q1",
            "status": "candidate_metadata_only",
            "rights_status": "unknown",
        }
    ]

    batch_rows = build_batch_rows(discovery_rows)

    assert batch_rows[0]["local_path"] == str(transcript)
    assert batch_rows[0]["rights_tier"] == "unknown"
    assert batch_rows[0]["eval_allowed"] == "false"
    assert batch_rows[0]["training_allowed"] == "false"
    assert batch_rows[0]["commit_allowed"] == "false"

    batch_csv = tmp_path / "batch.csv"
    fieldnames = list(batch_rows[0])
    with batch_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        blocked = dict(batch_rows[0])
        blocked["eval_allowed"] = "true"
        writer.writerow(blocked)

    loaded = load_batch_rows(batch_csv)
    registered, errors = register_batch_rows(loaded, operator="tester")

    assert registered == []
    assert any("unknown/restricted manual-local rights cannot allow commit/training/eval" in error for error in errors)


def test_valid_manual_local_batch_registers_path_and_hash_only(tmp_path: Path) -> None:
    transcript = tmp_path / "JPM_2026_Q1.txt"
    transcript.write_text("Operator: welcome\nManagement: prepared remarks\n", encoding="utf-8")
    rows = [
        {
            "case_id": "jpm_2026_q1",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "fiscal_period": "2026_Q1",
            "local_path": str(transcript),
            "source_url": "https://example.com/jpm-q1",
            "source_type": "manual_local",
            "rights_tier": "manual_supplied",
            "operator": "tester",
            "eval_allowed": "false",
            "training_allowed": "false",
            "commit_allowed": "false",
            "notes": "path/hash only",
        }
    ]

    registered, errors = register_batch_rows(rows, operator="tester")

    assert errors == []
    assert len(registered) == 1
    record = registered[0]
    assert record["source_path_ref"] == str(transcript)
    assert str(record["source_sha256"]).startswith("sha256:")
    assert record["raw_file_copied_into_repo"] is False
    assert "raw_text" not in record
    assert "Operator:" not in str(record)
