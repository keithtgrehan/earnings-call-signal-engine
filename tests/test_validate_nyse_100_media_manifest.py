from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_nyse_100_media_manifest import (
    MANIFEST_FIELDS,
    build_summary,
    validate_manifest_rows,
)


AS_OF_DATE = date(2026, 5, 24)


def _valid_row(tmp_path: Path, **overrides: str) -> dict[str, str]:
    call_folder = tmp_path / "JPM_JPMorgan_Chase_Co" / "2026-04-14_FY2026_Q1"
    for child in ("transcript", "audio", "video", "metadata", "provenance"):
        (call_folder / child).mkdir(parents=True, exist_ok=True)
    row = {
        "case_id": "jpm_2026_q1",
        "ticker_symbol": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "exchange": "NYSE",
        "fiscal_year": "2026",
        "fiscal_quarter": "Q1",
        "calendar_year": "2026",
        "earnings_call_date": "2026-04-14",
        "transcript_source_url": "https://www.jpmorganchase.com/ir",
        "audio_source_url": "https://www.jpmorganchase.com/ir/events",
        "video_source_url": "https://www.jpmorganchase.com/ir/events",
        "transcript_availability": "available",
        "audio_availability": "unknown",
        "video_availability": "unknown",
        "source_type": "company_ir",
        "rights_status": "metadata_only",
        "priority_tier": "3",
        "local_paths_created": "true",
        "notes": "Metadata-only candidate; manual review required before raw use.",
        "source_domain": "jpmorganchase.com",
        "discovered_timestamp": "2026-05-24T10:00:00+00:00",
        "acquisition_method": "rights_aware_metadata_discovery",
        "provenance_hash": "sha256:" + "a" * 64,
        "call_folder": str(call_folder),
    }
    row.update(overrides)
    return row


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_valid_manifest_passes_and_counts_tiers(tmp_path: Path) -> None:
    rows = [
        _valid_row(tmp_path, case_id="jpm_2026_q1", priority_tier="3"),
        _valid_row(
            tmp_path,
            case_id="wmt_2026_q1",
            ticker_symbol="WMT",
            company_name="Walmart Inc.",
            priority_tier="4",
            transcript_availability="unknown",
        ),
    ]

    errors = validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path)
    summary = build_summary(rows, errors)

    assert errors == []
    assert summary["total_rows"] == 2
    assert summary["tier_counts"] == {"1": 0, "2": 0, "3": 1, "4": 1}


def test_invalid_exchange_fails(tmp_path: Path) -> None:
    rows = [_valid_row(tmp_path, exchange="NASDAQ")]

    errors = validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path)

    assert any("exchange must equal NYSE" in error for error in errors)


def test_stale_dates_fail(tmp_path: Path) -> None:
    rows = [_valid_row(tmp_path, earnings_call_date="2020-01-01", calendar_year="2020", fiscal_year="2020")]

    errors = validate_manifest_rows(rows, years_back=5, as_of_date=AS_OF_DATE, repo_root=tmp_path)

    assert any("outside the 5-year lookback" in error for error in errors)


def test_duplicate_rows_fail(tmp_path: Path) -> None:
    row = _valid_row(tmp_path)
    rows = [dict(row), dict(row)]

    errors = validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path)

    assert any("duplicate manifest identity" in error for error in errors)


def test_available_media_requires_url(tmp_path: Path) -> None:
    rows = [_valid_row(tmp_path, audio_availability="available", audio_source_url="")]

    errors = validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path)

    assert any("audio_source_url is required when audio_availability=available" in error for error in errors)


def test_blocked_sources_require_notes(tmp_path: Path) -> None:
    rows = [_valid_row(tmp_path, transcript_availability="blocked", notes="")]

    errors = validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path)

    assert any("blocked or paywalled availability requires notes" in error for error in errors)


def test_missing_local_folder_fails(tmp_path: Path) -> None:
    rows = [_valid_row(tmp_path, call_folder=str(tmp_path / "missing"), local_paths_created="true")]

    errors = validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path)

    assert any("local folder missing" in error for error in errors)


def test_repo_tracked_raw_media_fails(tmp_path: Path) -> None:
    rows = [_valid_row(tmp_path)]
    raw_path = tmp_path / "data" / "raw" / "call.mp3"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_bytes(b"raw media")

    errors = validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path, tracked_paths=[raw_path])

    assert any("repo-tracked raw media path is not allowed" in error for error in errors)


def test_cli_reads_manifest_file(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    _write_manifest(manifest, [_valid_row(tmp_path)])

    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert validate_manifest_rows(rows, as_of_date=AS_OF_DATE, repo_root=tmp_path) == []
