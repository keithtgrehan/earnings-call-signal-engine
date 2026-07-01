from __future__ import annotations

from pathlib import Path

from tools.apply_agent_s1_transcript_replacements import apply_agent_s1_transcript_replacements
from tools.first30_transcript_common import FIRST30_INGESTION_FIELDS, read_csv, write_csv
from tools.resolve_first30_missing_transcript_urls import REPLACEMENT_FIELDS


def _row(case_id: str, ticker: str = "JPM") -> dict[str, str]:
    return {
        "candidate_id": f"first30_{case_id}",
        "priority_rank": "1",
        "case_id": case_id,
        "ticker": ticker,
        "company_name": "Example Corp.",
        "exchange": "NYSE",
        "fiscal_year": "2025" if "_2025_" in case_id else "2024",
        "fiscal_quarter": "Q1",
        "event_date": "2025-01-01",
        "source_url": "https://example.com/ir",
        "source_domain": "example.com",
        "source_type": "official_ir",
        "expected_format": "pdf",
        "source_url_kind": "landing_or_metadata",
        "rights_status": "metadata_only_rights_review",
        "approval_required": "true",
        "rights_review_required": "true",
        "download_allowed": "false",
        "blocked_reason": "direct_transcript_url_required",
        "raw_text_committed": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
        "explicit_training_rights_ref": "",
        "license_config_ref": "",
        "control_fixture": "false",
        "qna_expected": "true",
        "source_relation": "transcript_canonical",
        "approval_ref": "",
        "next_action": "resolve_direct_transcript_url",
        "notes": "",
    }


def test_agent_s1_replacements_keep_raw_guardrails(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    replacements = tmp_path / "replacements.csv"
    audit = tmp_path / "_audit"
    write_csv(manifest, [_row("jpm_2025_q2"), _row("cat_2025_q3", "CAT")], FIRST30_INGESTION_FIELDS)
    write_csv(replacements, [], REPLACEMENT_FIELDS)

    summary = apply_agent_s1_transcript_replacements(
        manifest_path=manifest,
        replacements_path=replacements,
        audit_dir=audit,
        probe_network=False,
        probe_content=False,
    )

    rows = {row["case_id"]: row for row in read_csv(manifest)}
    assert summary["applied_replacements"] == 2
    assert rows["jpm_2025_q2"]["download_allowed"] == "true"
    assert rows["jpm_2025_q2"]["commit_allowed"] == "false"
    assert rows["jpm_2025_q2"]["training_allowed"] == "false"
    assert rows["cat_2025_q3"]["source_domain"] == "s25.q4cdn.com"
    assert rows["cat_2025_q3"]["rights_review_required"] == "true"
    assert (audit / "first30_transcript_url_replacements.csv").exists()


def test_agent_s1_can_queue_cdn_when_policy_disabled(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    replacements = tmp_path / "replacements.csv"
    audit = tmp_path / "_audit"
    write_csv(manifest, [_row("cat_2025_q2", "CAT")], FIRST30_INGESTION_FIELDS)
    write_csv(replacements, [], REPLACEMENT_FIELDS)

    apply_agent_s1_transcript_replacements(
        manifest_path=manifest,
        replacements_path=replacements,
        audit_dir=audit,
        probe_network=False,
        probe_content=False,
        official_ir_cdn_assessment=False,
    )

    row = read_csv(manifest)[0]
    replacement = read_csv(replacements)[0]
    assert row["download_allowed"] == "false"
    assert replacement["blocked_reason"] == "official_ir_cdn_review_queue_only"
    assert replacement["rights_review_required"] == "true"
