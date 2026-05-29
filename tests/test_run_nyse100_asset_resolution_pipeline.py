from __future__ import annotations

import csv
from pathlib import Path

from tools.run_nyse100_asset_resolution_pipeline import run_asset_resolution_pipeline


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_pipeline_ranks_candidates_and_builds_permitted_direct_download_manifest(tmp_path: Path) -> None:
    workspace = tmp_path / "desktop"
    inputs = tmp_path / "repo" / "data" / "acquisition"
    _write_csv(
        inputs / "nyse_100_company_universe.csv",
        [{"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "sector": "banking"}],
    )
    _write_csv(
        inputs / "nyse_100_5y_call_targets.csv",
        [{"case_id": "jpm_2025_q4", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "fiscal_year": "2025", "fiscal_quarter": "Q4", "event_date": "2025-12-31"}],
    )
    _write_csv(
        inputs / "nyse_100_source_rights_review_queue.csv",
        [{"case_id": "jpm_2025_q4", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "fiscal_year": "2025", "fiscal_quarter": "Q4", "source_url": "https://ir.example.com/events", "source_type": "official_ir", "asset_type": "transcript"}],
    )
    transcript = {
        "candidate_id": "c1",
        "case_id": "jpm_2025_q4",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "fiscal_period": "2025 Q4",
        "event_date": "2025-12-31",
        "asset_type": "transcript_text",
        "source_type": "official_ir",
        "source_url": "https://ir.example.com/events",
        "resolved_asset_url": "https://ir.example.com/q4.txt",
        "asset_url_domain": "ir.example.com",
        "file_ext": ".txt",
        "content_type_hint": "text/plain",
        "confidence": "0.95",
        "confidence_reason": "direct transcript",
        "rights_status": "user_authorized_public_direct",
        "download_allowed": "true",
        "approval_ref": "approval://test",
        "license_config_ref": "",
        "blocked_reason": "",
        "next_action": "download",
        "provenance_hash": "sha256:" + "a" * 64,
    }
    audio = dict(transcript, candidate_id="c2", asset_type="audio_mp3", resolved_asset_url="https://ir.example.com/q4.mp3", file_ext=".mp3", content_type_hint="audio/mpeg")

    summary = run_asset_resolution_pipeline(
        acquisition_dir=inputs,
        workspace=workspace,
        target_pairs=1,
        official_resolver=lambda _rows: [transcript, audio],
        sec_resolver=lambda _rows: [],
        provider_resolver=lambda _rows: [],
        direct_detector=lambda row: row,
    )

    permitted = list(csv.DictReader((inputs / "nyse_100_user_authorized_permitted_downloads.csv").open(newline="", encoding="utf-8")))
    ranked = list(csv.DictReader((inputs / "nyse_100_ranked_asset_candidates.csv").open(newline="", encoding="utf-8")))
    assert summary["usable_candidate_pairs"] == 1
    assert [row["asset_type"] for row in ranked[:2]] == ["transcript_text", "audio_mp3"]
    assert len(permitted) == 2
    assert permitted[0]["commit_allowed"] == "false"
    assert (workspace / "_audit" / "ranked_asset_candidates.csv").exists()
