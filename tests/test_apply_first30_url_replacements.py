from __future__ import annotations

from pathlib import Path

from tools.apply_first30_url_replacements import apply_replacements
from tools.first30_transcript_common import FIRST30_INGESTION_FIELDS, write_csv
from tools.resolve_first30_missing_transcript_urls import REPLACEMENT_FIELDS


def test_apply_replacements_updates_only_download_allowed_rows(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    replacements = tmp_path / "replacements.csv"
    audit = tmp_path / "audit"
    write_csv(
        manifest,
        [
            {
                "candidate_id": "first30_jpm_2025_q1",
                "case_id": "jpm_2025_q1",
                "ticker": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "exchange": "NYSE",
                "fiscal_year": "2025",
                "fiscal_quarter": "Q1",
                "source_url": "https://www.jpmorganchase.com/ir",
                "source_domain": "www.jpmorganchase.com",
                "source_type": "official_ir",
                "expected_format": "pdf",
                "source_url_kind": "landing_or_metadata",
                "rights_status": "safe_to_download",
                "approval_required": "true",
                "rights_review_required": "false",
                "download_allowed": "false",
                "blocked_reason": "direct_transcript_url_required",
                "raw_text_committed": "false",
                "commit_allowed": "false",
                "training_allowed": "false",
                "control_fixture": "false",
                "source_relation": "transcript_canonical",
            }
        ],
        FIRST30_INGESTION_FIELDS,
    )
    write_csv(
        replacements,
        [
            {
                "case_id": "jpm_2025_q1",
                "replacement_source_url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/1st-quarter/1q25-earnings-transcript.pdf",
                "source_type": "official_ir",
                "expected_format": "pdf",
                "download_allowed": "true",
                "rights_review_required": "false",
                "approval_ref": "user_authorized_project_assessment",
                "replacement_reason": "official_same_domain_or_ir_cdn",
            }
        ],
        REPLACEMENT_FIELDS,
    )
    summary = apply_replacements(manifest_path=manifest, replacements_path=replacements, audit_dir=audit)
    assert summary["applied_replacements"] == 1
    rows = manifest.read_text(encoding="utf-8")
    assert "download_desktop_only" in rows
    assert "direct_transcript_url_required" not in rows
