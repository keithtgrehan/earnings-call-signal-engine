from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.discover_nyse_earnings_media import (
    build_candidate_calls,
    classify_rights_status,
    priority_tier_for,
    run_discovery,
)


AS_OF_DATE = date(2026, 5, 24)


def test_build_candidate_calls_recent_first_and_nyse_only() -> None:
    rows, exclusions = build_candidate_calls(target_count=12, years_back=5, as_of_date=AS_OF_DATE)

    assert len(rows) == 12
    assert all(row["exchange"] == "NYSE" for row in rows)
    assert [row["fiscal_year"] for row in rows[:3]] == ["2026", "2026", "2026"]
    assert {row["ticker_symbol"] for row in rows}.isdisjoint({"HON", "PEP", "UAL"})
    assert {row["ticker_symbol"] for row in exclusions} == {"HON", "PEP", "UAL"}


def test_priority_tier_prefers_transcript_then_audio_then_video() -> None:
    assert priority_tier_for("available", "available", "available") == "1"
    assert priority_tier_for("available", "available", "unknown") == "2"
    assert priority_tier_for("available", "unknown", "unknown") == "3"
    assert priority_tier_for("unknown", "available", "available") == "4"


def test_rights_classification_blocks_youtube_media_and_vendor_raw() -> None:
    youtube = classify_rights_status(
        source_type="youtube_metadata_only",
        metadata_only=True,
        raw_requested=True,
        license_config_ref="",
    )
    vendor = classify_rights_status(
        source_type="earnings_platform",
        metadata_only=False,
        raw_requested=True,
        license_config_ref="",
    )

    assert youtube["rights_status"] == "blocked"
    assert "YouTube" in youtube["notes"]
    assert vendor["rights_status"] == "blocked"
    assert "license" in vendor["notes"]


def test_run_discovery_creates_workspace_manifest_and_provenance(tmp_path: Path) -> None:
    output_root = tmp_path / "earnings calls 100 samples"
    manifest = tmp_path / "manifest.csv"
    registry = tmp_path / "registry.csv"
    targets = tmp_path / "targets.csv"
    reports_dir = tmp_path / "reports"

    summary = run_discovery(
        target_count=4,
        years_back=5,
        output_root=output_root,
        manifest_path=manifest,
        source_registry_path=registry,
        targets_path=targets,
        reports_dir=reports_dir,
        metadata_only=True,
        max_workers=2,
        checkpoint_interval=2,
        dry_run=False,
        as_of_date=AS_OF_DATE,
    )

    assert summary["total_candidates_found"] == 4
    assert summary["tier_counts"] == {"1": 0, "2": 0, "3": 0, "4": 4}
    assert manifest.exists()
    assert registry.exists()
    assert targets.exists()
    assert (reports_dir / "nyse_100_media_progress_002.md").exists()
    assert (reports_dir / "nyse_100_media_corpus_status.json").exists()

    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    first = rows[0]
    assert first["local_paths_created"] == "true"
    assert first["rights_status"] == "metadata_only"
    assert first["priority_tier"] == "4"

    call_folder = Path(first["call_folder"])
    assert (call_folder / "transcript").is_dir()
    assert (call_folder / "audio").is_dir()
    assert (call_folder / "video").is_dir()
    assert (call_folder / "metadata" / "manifest.json").is_file()
    assert (call_folder / "provenance" / "provenance.json").is_file()

    manifest_payload = json.loads((call_folder / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    provenance_payload = json.loads((call_folder / "provenance" / "provenance.json").read_text(encoding="utf-8"))
    assert manifest_payload["ticker_symbol"] == first["ticker_symbol"]
    assert provenance_payload["provenance_hash"].startswith("sha256:")


def test_metadata_only_mode_never_marks_raw_media_safe(tmp_path: Path) -> None:
    summary = run_discovery(
        target_count=3,
        years_back=5,
        output_root=tmp_path / "workspace",
        manifest_path=tmp_path / "manifest.csv",
        source_registry_path=tmp_path / "registry.csv",
        targets_path=tmp_path / "targets.csv",
        reports_dir=tmp_path / "reports",
        metadata_only=True,
        max_workers=1,
        checkpoint_interval=25,
        dry_run=False,
        as_of_date=AS_OF_DATE,
    )

    assert summary["safe_download_candidates"] == 0
    with (tmp_path / "registry.csv").open(newline="", encoding="utf-8") as handle:
        registry_rows = list(csv.DictReader(handle))
    assert registry_rows
    assert all(row["raw_download_allowed"] == "false" for row in registry_rows)
