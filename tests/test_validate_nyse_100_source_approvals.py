from __future__ import annotations

from scripts.validate_nyse_100_source_approvals import validate_approval_rows
from tools.source_rights_common import QUEUE_FIELDS


def _row(**overrides: str) -> dict[str, str]:
    row = {field: "" for field in QUEUE_FIELDS}
    row.update(
        {
            "source_id": "src_1",
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "asset_type": "transcript",
            "source_type": "official_ir",
            "source_url": "https://ir.example.com/transcript",
            "source_domain": "ir.example.com",
            "rights_status": "safe_to_download",
            "allow_download": "true",
            "allow_eval_use": "true",
            "allow_training_use": "false",
            "commit_allowed": "false",
            "manual_approval_required": "true",
            "approval_ref": "approval://jpm-q4",
            "approved_by": "Keith",
            "approved_at": "2026-05-28T00:00:00+00:00",
            "source_terms_checked": "true",
            "robots_checked": "true",
        }
    )
    row.update(overrides)
    return row


def test_complete_source_approval_is_valid() -> None:
    errors, warnings, summary = validate_approval_rows([_row()], QUEUE_FIELDS)

    assert errors == []
    assert warnings == []
    assert summary["approved_download_rows"] == 1


def test_download_requires_approval_identity() -> None:
    errors, _, _ = validate_approval_rows([_row(approval_ref="")], QUEUE_FIELDS)

    assert any("approval_ref" in error for error in errors)


def test_unknown_rights_fail_closed_for_download() -> None:
    errors, _, _ = validate_approval_rows([_row(rights_status="unknown")], QUEUE_FIELDS)

    assert any("rights_status" in error for error in errors)


def test_manual_local_review_only_does_not_unlock_download() -> None:
    errors, _, _ = validate_approval_rows([_row(rights_status="manual_local_review_only")], QUEUE_FIELDS)

    assert any("rights_status" in error for error in errors)


def test_youtube_audio_download_is_rejected() -> None:
    errors, _, _ = validate_approval_rows(
        [_row(asset_type="audio", source_type="official_ir_webcast", source_url="https://www.youtube.com/watch?v=abc")],
        QUEUE_FIELDS,
    )

    assert any("YouTube media" in error for error in errors)


def test_training_requires_explicit_rights_ref() -> None:
    errors, _, _ = validate_approval_rows([_row(allow_training_use="true")], QUEUE_FIELDS)

    assert any("explicit_training_rights_ref" in error for error in errors)
