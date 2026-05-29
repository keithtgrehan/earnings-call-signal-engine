from __future__ import annotations

import csv
from pathlib import Path

from tools.download_resolved_earnings_assets import download_resolved_assets


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_downloader_writes_transcript_audio_and_provenance_under_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "desktop"
    manifest = tmp_path / "manifest.csv"
    base = {
        "candidate_id": "c1",
        "case_id": "jpm_2025_q4",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "fiscal_period": "2025 Q4",
        "asset_type": "transcript_text",
        "source_type": "official_ir",
        "source_url": "https://ir.example.com/events",
        "resolved_asset_url": "https://ir.example.com/q4.txt",
        "download_allowed": "true",
        "approval_ref": "approval://test",
        "commit_allowed": "false",
        "training_allowed": "false",
        "eval_allowed": "true",
        "blocked_reason": "",
    }
    audio = dict(base, candidate_id="c2", asset_type="audio_mp3", resolved_asset_url="https://ir.example.com/q4.mp3")
    _write_manifest(manifest, [base, audio])

    def fetcher(url: str) -> tuple[int, str, bytes]:
        if url.endswith(".mp3"):
            return 200, "audio/mpeg", b"audio bytes"
        return 200, "text/plain", b"Operator: welcome\nQuestion-and-Answer\nAnalyst: question\n"

    summary = download_resolved_assets(manifest=manifest, workspace=workspace, fetcher=fetcher)

    assert summary["transcript_successes"] == 1
    assert summary["audio_successes"] == 1
    log_rows = list(csv.DictReader((workspace / "_audit" / "resolved_download_log.csv").open(newline="", encoding="utf-8")))
    assert len(log_rows) == 2
    assert all(Path(row["local_path"]).is_relative_to(workspace) for row in log_rows)
    assert all(row["commit_allowed"] == "false" and row["training_allowed"] == "false" for row in log_rows)
    assert all(Path(row["provenance_path"]).exists() for row in log_rows)


def test_downloader_blocks_signed_urls_without_writing_raw(tmp_path: Path) -> None:
    workspace = tmp_path / "desktop"
    manifest = tmp_path / "manifest.csv"
    _write_manifest(
        manifest,
        [
            {
                "candidate_id": "c1",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "asset_type": "audio_mp3",
                "resolved_asset_url": "https://ir.example.com/q4.mp3?token=secret",
                "download_allowed": "true",
                "commit_allowed": "false",
                "training_allowed": "false",
                "eval_allowed": "true",
            }
        ],
    )

    summary = download_resolved_assets(manifest=manifest, workspace=workspace, fetcher=lambda _url: (200, "audio/mpeg", b"audio"))

    assert summary["audio_successes"] == 0
    assert summary["blocked"] == 1
    assert not list(workspace.glob("**/*.mp3"))
