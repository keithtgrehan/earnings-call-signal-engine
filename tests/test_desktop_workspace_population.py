from __future__ import annotations

import csv
import json
from pathlib import Path

from signal_engine.acquisition.nyse100 import build_call_targets, build_company_universe, populate_desktop_workspace


def test_metadata_only_population_creates_call_folders_and_audit(tmp_path: Path) -> None:
    companies = build_company_universe()[:2]
    targets = build_call_targets(companies, start_year=2025, years_back=1)
    summary = populate_desktop_workspace(targets, output_root=tmp_path, checkpoint_interval=1)

    assert summary["total_companies_selected"] == 2
    assert summary["total_call_folders_created"] == 2
    assert summary["total_transcript_files_downloaded"] == 0
    assert summary["total_audio_files_downloaded"] == 0
    assert summary["total_metadata_only_calls"] == 2

    audit_path = tmp_path / "_audit" / "nyse_earnings_call_audit.csv"
    assert audit_path.exists()
    rows = list(csv.DictReader(audit_path.open(newline="", encoding="utf-8")))
    assert len(rows) == 2
    assert all(row["rights_status"] == "metadata_only" for row in rows)

    call_folder = Path(rows[0]["transcript_local_path"]).parent
    for child in ("transcript", "audio", "video", "metadata", "provenance", "chunks"):
        assert (call_folder / child).is_dir()

    metadata = json.loads((call_folder / "metadata" / "call_metadata.json").read_text(encoding="utf-8"))
    rights = json.loads((call_folder / "provenance" / "rights_decision.json").read_text(encoding="utf-8"))
    assert metadata["ticker_symbol"] == rows[0]["ticker_symbol"]
    assert metadata["acquisition_method"] == "metadata-first discovery"
    assert rights["rights_status"] == "metadata_only"
    assert rights["download_allowed"] is False


def test_population_records_blocked_sources_and_zero_permitted_downloads(tmp_path: Path) -> None:
    targets = build_call_targets(build_company_universe()[:1], start_year=2025, years_back=1)
    populate_desktop_workspace(targets, output_root=tmp_path, checkpoint_interval=25)

    blocked = list(csv.DictReader((tmp_path / "_audit" / "blocked_sources.csv").open(newline="", encoding="utf-8")))
    permitted = list(csv.DictReader((tmp_path / "_audit" / "permitted_downloads.csv").open(newline="", encoding="utf-8")))

    assert {row["blocked_reason"] for row in blocked} >= {"youtube_media_blocked", "vendor_license_missing"}
    assert permitted == []
