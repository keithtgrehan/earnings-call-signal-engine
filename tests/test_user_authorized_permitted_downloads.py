from __future__ import annotations

import csv
from pathlib import Path

from tools.build_user_authorized_permitted_downloads import build_permitted_downloads
from tools.user_authorized_ingest_common import USER_AUTHORIZED_QUEUE_FIELDS


def _write_policy(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "enabled: true",
                "authorization_mode: user_asserted_project_authorization",
                "authorization_ref: Keith test authorization",
                "workspace_root: /tmp/desktop",
                "allow_transcript_downloads: true",
                "allow_audio_downloads: true",
                "allow_video_downloads: false",
                "allow_youtube_audio_video: false",
                "allow_vendor_raw_without_license: false",
                "allow_paywall_login_bypass: false",
                "allow_drm_bypass: false",
                "allow_signed_session_url_bypass: false",
                "store_raw_only_on_desktop: true",
                "commit_raw_to_git: false",
                "allow_eval_use: true",
                "allow_training_use: false",
                "allowed_source_types:",
                "  - company_ir",
                "  - official_ir_transcript",
                "  - official_ir_audio",
                "  - official_ir_webcast",
                "  - official_ir_event",
                "  - sec_allowed_exhibit",
                "  - sec_edgar",
                "  - manual_local_transcript",
                "  - manual_local_audio",
                "  - manually_approved_public_source",
                "blocked_source_types:",
                "  - youtube_metadata_only",
                "  - licensed_vendor_blocked",
                "  - paywalled",
                "youtube_requires:",
                "  youtube_written_authorization_ref: true",
                "vendor_requires:",
                "  license_config_ref: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=USER_AUTHORIZED_QUEUE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            payload = {field: "" for field in USER_AUTHORIZED_QUEUE_FIELDS}
            payload.update(
                {
                    "source_id": "src_1",
                    "case_id": "jpm_2025_q4",
                    "ticker": "JPM",
                    "company_name": "JPMorgan Chase & Co.",
                    "fiscal_year": "2025",
                    "fiscal_quarter": "Q4",
                    "asset_type": "transcript",
                    "source_type": "official_ir",
                    "source_url": "https://ir.example.com/transcript",
                    "source_domain": "ir.example.com",
                    "rights_status": "metadata_only",
                    "blocked_reason": "metadata_only_no_raw_download",
                    "commit_allowed": "false",
                    "manual_approval_required": "true",
                }
            )
            payload.update(row)
            writer.writerow(payload)


def test_user_authorization_promotes_official_ir_transcript(tmp_path: Path, monkeypatch) -> None:
    policy = tmp_path / "policy.yml"
    queue = tmp_path / "queue.csv"
    out = tmp_path / "permitted.csv"
    _write_policy(policy)
    _write_queue(queue, [{}])
    monkeypatch.setattr("tools.build_user_authorized_permitted_downloads.REPORT_DIR", tmp_path / "reports")

    promoted, blocked = build_permitted_downloads(queue_path=queue, policy_path=policy, out_path=out, desktop_out=None)

    assert len(promoted) == 1
    assert blocked == []
    row = promoted[0]
    assert row["allow_download"] == "true"
    assert row["allow_eval_use"] == "true"
    assert row["allow_training_use"] == "false"
    assert row["commit_allowed"] == "false"
    assert row["approved_by"] == "Keith"
    assert row["source_type"] == "official_ir_transcript"


def test_unknown_public_official_row_promotes_only_with_enabled_policy(tmp_path: Path, monkeypatch) -> None:
    policy = tmp_path / "policy.yml"
    queue = tmp_path / "queue.csv"
    _write_policy(policy)
    _write_queue(queue, [{"rights_status": "unknown", "source_type": "official_ir"}])
    monkeypatch.setattr("tools.build_user_authorized_permitted_downloads.REPORT_DIR", tmp_path / "reports")

    promoted, _ = build_permitted_downloads(queue_path=queue, policy_path=policy, out_path=tmp_path / "enabled.csv", desktop_out=None)
    assert len(promoted) == 1

    disabled = policy.read_text(encoding="utf-8").replace("enabled: true", "enabled: false")
    policy.write_text(disabled, encoding="utf-8")
    promoted, blocked = build_permitted_downloads(queue_path=queue, policy_path=policy, out_path=tmp_path / "disabled.csv", desktop_out=None)
    assert promoted == []
    assert blocked[0]["blocked_reason"] == "user_authorization_policy_disabled"


def test_youtube_vendor_and_hard_barriers_do_not_promote(tmp_path: Path, monkeypatch) -> None:
    policy = tmp_path / "policy.yml"
    queue = tmp_path / "queue.csv"
    _write_policy(policy)
    _write_queue(
        queue,
        [
            {"source_id": "youtube", "asset_type": "audio", "source_type": "youtube_metadata_only", "source_url": "https://youtube.com/watch?v=abc"},
            {"source_id": "vendor", "source_type": "licensed_vendor_blocked", "source_url": "licensed-vendor://demo"},
            {"source_id": "signed", "source_url": "https://ir.example.com/call.mp3?token=abc", "blocked_reason": ""},
            {"source_id": "paywall", "source_url": "https://ir.example.com/login/transcript", "blocked_reason": ""},
            {"source_id": "commit", "commit_allowed": "true"},
            {"source_id": "training", "allow_training_use": "true", "blocked_reason": ""},
        ],
    )
    monkeypatch.setattr("tools.build_user_authorized_permitted_downloads.REPORT_DIR", tmp_path / "reports")

    promoted, blocked = build_permitted_downloads(queue_path=queue, policy_path=policy, out_path=tmp_path / "permitted.csv", desktop_out=None)

    assert promoted == []
    reasons = {row["blocked_reason"] for row in blocked}
    assert "youtube_audio_video_requires_written_authorization" in reasons
    assert "vendor_raw_requires_license_config_ref" in reasons
    assert "signed_or_session_url_blocked" in reasons
    assert "paywall_or_login_blocked" in reasons
    assert "commit_allowed_must_be_false" in reasons
    assert "training_use_requires_explicit_training_rights_ref" in reasons
