from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import intake_high_signal_transcripts as intake  # noqa: E402
import prepare_manual_transcript_sources as manual_sources  # noqa: E402


VALID_TRANSCRIPT = """
Tesla Q4 2025 Earnings Call
Operator: Good afternoon and welcome to the earnings call.
Prepared remarks
CEO: We expect revenue to improve next quarter and will discuss product demand.
Question-and-Answer
Analyst: Can you discuss Q4 demand, margin outlook, and guidance?
CFO: We expect revenue to grow and conference call questions will cover analysts.
""" + ("Management answer with earnings call detail and analyst discussion. " * 120)


def write_manual_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manual_sources.MANUAL_SOURCE_FIELDS))
        writer.writeheader()
        writer.writerows(rows)


def base_row(local_file: Path | None = None) -> dict[str, str]:
    return {
        "case_id": "TSLA_2025_Q4",
        "ticker": "TSLA",
        "company_name": "Tesla, Inc.",
        "fiscal_year": "2025",
        "quarter": "Q4",
        "source_url": "https://ir.example.com/tsla-q4-transcript",
        "local_file_path": str(local_file or ""),
        "source_type": "txt",
        "source_license_notes": "Manually saved from a public investor relations transcript page.",
        "public_source_confirmed": "true",
        "notes": "fixture",
    }


def row_obj(row: dict[str, str], *, confirmed: bool | None = None) -> manual_sources.ManualSourceRow:
    return manual_sources.ManualSourceRow(
        case_id=row["case_id"],
        ticker=row["ticker"],
        company_name=row["company_name"],
        fiscal_year=row["fiscal_year"],
        quarter=row["quarter"],
        source_url=row["source_url"],
        local_file_path=row["local_file_path"],
        source_type=row["source_type"],
        source_license_notes=row["source_license_notes"],
        public_source_confirmed=manual_sources.parse_bool(row["public_source_confirmed"]) if confirmed is None else confirmed,
        notes=row["notes"],
    )


def test_manual_source_csv_validation_header_and_rows(tmp_path: Path) -> None:
    transcript = tmp_path / "tsla.txt"
    transcript.write_text(VALID_TRANSCRIPT, encoding="utf-8")
    source_csv = tmp_path / "manual_sources.csv"
    write_manual_csv(source_csv, [base_row(transcript)])

    rows = manual_sources.read_manual_rows(source_csv)

    assert rows[0].case_id == "TSLA_2025_Q4"
    assert rows[0].public_source_confirmed is True
    assert rows[0].source_license_notes


def test_missing_provenance_rejected_without_manifest_row(tmp_path: Path) -> None:
    transcript = tmp_path / "tsla.txt"
    transcript.write_text(VALID_TRANSCRIPT, encoding="utf-8")
    row = base_row(transcript)
    row["public_source_confirmed"] = "false"
    row["source_license_notes"] = ""
    result = manual_sources.validate_local_file(
        row_obj(row, confirmed=False),
        min_chars=500,
        require_markers=True,
    )

    assert result.status == "rejected"
    assert result.rejection_reason == "public_source_not_confirmed"


def test_local_transcript_file_validation_and_manifest_writing(tmp_path: Path) -> None:
    transcript = tmp_path / "tsla.md"
    transcript.write_text(VALID_TRANSCRIPT, encoding="utf-8")
    source_row = base_row(transcript)
    result = manual_sources.validate_local_file(
        row_obj(source_row),
        min_chars=500,
        require_markers=True,
    )
    manifest = tmp_path / "manual_transcript_file_manifest.csv"

    manual_sources.write_file_manifest(manifest, [result])

    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    assert result.status == "verified"
    assert rows[0]["case_id"] == "TSLA_2025_Q4"
    assert rows[0]["source_type"] == "manual_file"
    assert int(rows[0]["transcript_char_estimate"]) >= 500


def test_intake_from_local_transcript_file_preserves_provenance(tmp_path: Path) -> None:
    transcript = tmp_path / "tsla.txt"
    transcript.write_text(VALID_TRANSCRIPT, encoding="utf-8")
    case = intake.PlannedCase(
        case_id="TSLA_2025_Q4",
        ticker="TSLA",
        fiscal_year="2025",
        quarter="Q4",
        source_url="https://ir.example.com/tsla-q4-transcript",
        source_type="manual_file",
        company_name="Tesla, Inc.",
        notes="fixture local source",
        local_file_path=str(transcript),
        source_license_notes="Manually saved from a public investor relations transcript page.",
        public_source_confirmed=True,
    )

    row = intake.write_case_outputs(
        case=case,
        output_root=tmp_path / "cases",
        overwrite=False,
        min_chars=500,
        require_markers=True,
        timeout=5,
    )

    case_dir = tmp_path / "cases" / "TSLA_2025_Q4"
    provenance = json.loads((case_dir / "metadata" / "provenance.json").read_text(encoding="utf-8"))
    assert row["status"] == "valid"
    assert provenance["web_downloaded"] is False
    assert provenance["manual_source_file_path"] == str(transcript)
    assert provenance["source_license_notes"]
    assert (case_dir / "raw" / "transcript.txt").read_text(encoding="utf-8").startswith("Tesla Q4 2025")
    assert (case_dir / "labels" / "human_labeling_packet.md").exists()
    assert not (tmp_path / "cases" / "gold_labels.jsonl").exists()


def test_raw_overwrite_protection_for_manual_file(tmp_path: Path) -> None:
    transcript = tmp_path / "tsla.txt"
    transcript.write_text(VALID_TRANSCRIPT, encoding="utf-8")
    raw_dir = tmp_path / "cases" / "TSLA_2025_Q4" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "transcript.txt").write_text("existing immutable raw", encoding="utf-8")
    case = intake.PlannedCase(
        case_id="TSLA_2025_Q4",
        ticker="TSLA",
        fiscal_year="2025",
        quarter="Q4",
        source_url="",
        source_type="manual_file",
        local_file_path=str(transcript),
        source_license_notes="Public transcript saved manually.",
        public_source_confirmed=True,
    )

    with pytest.raises(intake.IntakeError, match="overwrite is false"):
        intake.write_case_outputs(
            case=case,
            output_root=tmp_path / "cases",
            overwrite=False,
            min_chars=500,
            require_markers=True,
            timeout=5,
        )
