from __future__ import annotations

import csv
from pathlib import Path

from tools.download_user_authorized_earnings_assets import download_user_authorized_assets
from tools.user_authorized_ingest_common import USER_AUTHORIZED_PERMITTED_FIELDS


def _write_policy(path: Path, workspace: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "enabled: true",
                "authorization_ref: Keith test authorization",
                f"workspace_root: {workspace}",
                "allow_transcript_downloads: true",
                "allow_audio_downloads: true",
                "allow_youtube_audio_video: false",
                "allow_vendor_raw_without_license: false",
                "allow_paywall_login_bypass: false",
                "allow_drm_bypass: false",
                "allow_signed_session_url_bypass: false",
                "store_raw_only_on_desktop: true",
                "commit_raw_to_git: false",
                "allow_eval_use: true",
                "allow_training_use: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_manifest(path: Path, source_url: str, **overrides: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=USER_AUTHORIZED_PERMITTED_FIELDS, lineterminator="\n")
        writer.writeheader()
        row = {field: "" for field in USER_AUTHORIZED_PERMITTED_FIELDS}
        row.update(
            {
                "source_id": "src_1",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "fiscal_year": "2025",
                "fiscal_quarter": "Q4",
                "asset_type": "transcript",
                "source_type": "official_ir_transcript",
                "source_url": source_url,
                "source_domain": "ir.example.com",
                "rights_status": "safe_to_download",
                "allow_download": "true",
                "allow_eval_use": "true",
                "allow_training_use": "false",
                "commit_allowed": "false",
                "approval_ref": "approval://keith/test",
                "approved_by": "Keith",
                "approved_at": "2026-05-24T00:00:00+00:00",
                "provenance_hash": "sha256:" + "a" * 64,
            }
        )
        row.update(overrides)
        writer.writerow(row)


def test_transcript_download_writes_to_desktop_workspace_only(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    source = tmp_path / "source_transcript.txt"
    source.write_text("Operator: welcome.\nPrepared remarks.\nQuestion-and-answer session.\n" * 30, encoding="utf-8")
    manifest = tmp_path / "manifest.csv"
    policy = tmp_path / "policy.yml"
    _write_policy(policy, workspace)
    _write_manifest(manifest, source.as_uri())
    monkeypatch.setattr("tools.download_user_authorized_earnings_assets.REPORT_DIR", tmp_path / "reports")

    summary = download_user_authorized_assets(manifest_path=manifest, policy_path=policy, workspace=workspace)

    assert summary["transcript_downloads_succeeded"] == 1
    log = workspace / "_audit" / "user_authorized_download_log.csv"
    rows = list(csv.DictReader(log.open(newline="", encoding="utf-8")))
    local_path = Path(rows[0]["local_path"])
    assert rows[0]["download_status"] == "downloaded"
    assert workspace in local_path.parents
    assert local_path.suffix == ".txt"


def test_download_blocks_youtube_signed_and_repo_paths(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    policy = tmp_path / "policy.yml"
    _write_policy(policy, workspace)
    manifest = tmp_path / "manifest.csv"
    _write_manifest(manifest, "https://youtube.com/watch?v=abc", asset_type="audio", source_type="official_ir_webcast")
    monkeypatch.setattr("tools.download_user_authorized_earnings_assets.REPORT_DIR", tmp_path / "reports")

    summary = download_user_authorized_assets(manifest_path=manifest, policy_path=policy, workspace=workspace)

    assert summary["audio_downloads_succeeded"] == 0
    rows = list(csv.DictReader((workspace / "_audit" / "user_authorized_download_log.csv").open(newline="", encoding="utf-8")))
    assert rows[0]["download_status"] == "blocked"
    assert "youtube" in rows[0]["blocked_reason"]


def test_incomplete_manual_approval_does_not_download_in_legacy_tool() -> None:
    from tools.acquire_nyse_100_assets import download_decision

    status, reason = download_decision(
        source={"source_type": "company_ir", "rights_status": "metadata_only", "availability": "available", "raw_download_allowed": "false"},
        asset_type="transcript",
        source_url="file:///tmp/example.txt",
        policy={
            "enabled": True,
            "allow_transcript_downloads": False,
            "allowed_source_types_for_transcript_download": ["company_ir"],
            "blocked_source_types": [],
        },
        approval={"allow_download": "true"},
        run_mode="permitted-only",
    )

    assert status == "blocked"
    assert reason == "manual_approval_incomplete"
