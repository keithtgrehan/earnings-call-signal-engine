from __future__ import annotations

from pathlib import Path

from tools.first30_transcript_common import FIRST30_INGESTION_FIELDS, read_csv, write_csv
from tools.resolve_first30_missing_transcript_urls import REPLACEMENT_FIELDS
import tools.resolve_remaining_first30_transcripts as resolver


def _manifest_row(case_id: str = "f_2025_q4") -> dict[str, str]:
    return {
        "candidate_id": f"first30_{case_id}",
        "priority_rank": "1",
        "case_id": case_id,
        "ticker": "F",
        "company_name": "Ford Motor Company",
        "exchange": "NYSE",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q4",
        "event_date": "2025-12-31",
        "source_url": "https://shareholder.ford.com/investors/financials/quarterly-results/default.aspx",
        "source_domain": "shareholder.ford.com",
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


def test_remaining_resolver_applies_clean_official_feed_url(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.csv"
    replacements = tmp_path / "replacements.csv"
    out = tmp_path / "remaining.csv"
    audit = tmp_path / "_audit"
    url = "https://s205.q4cdn.com/882619693/files/doc_financials/2025/q4/Ford-Q4-2025-Earnings-Call-Transcript.pdf"
    write_csv(manifest, [_manifest_row()], FIRST30_INGESTION_FIELDS)
    write_csv(replacements, [], REPLACEMENT_FIELDS)
    monkeypatch.setattr(resolver, "candidate_urls_for_row", lambda row: [url])
    monkeypatch.setattr(resolver, "probe_transcript_url", lambda row, candidate, probe_content=True: (True, "content_clean:test", "test"))

    summary = resolver.resolve_remaining_first30_transcripts(
        manifest_path=manifest,
        replacements_path=replacements,
        out_path=out,
        audit_dir=audit,
        probe_content=False,
    )

    row = read_csv(manifest)[0]
    replacement = read_csv(out)[0]
    assert summary["applied_replacements"] == 1
    assert row["download_allowed"] == "true"
    assert row["commit_allowed"] == "false"
    assert row["training_allowed"] == "false"
    assert row["source_url"] == url
    assert row["rights_review_required"] == "true"
    assert replacement["download_allowed"] == "true"
    assert (audit / "remaining_first30_transcript_url_replacements.csv").exists()


def test_remaining_resolver_blocks_vendor_marked_candidate(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.csv"
    replacements = tmp_path / "replacements.csv"
    out = tmp_path / "remaining.csv"
    audit = tmp_path / "_audit"
    write_csv(manifest, [_manifest_row("rf_2025_q4")], FIRST30_INGESTION_FIELDS)
    write_csv(replacements, [], REPLACEMENT_FIELDS)
    monkeypatch.setattr(resolver, "candidate_urls_for_row", lambda row: ["https://s202.q4cdn.com/example/transcript.pdf"])
    monkeypatch.setattr(resolver, "probe_transcript_url", lambda row, candidate, probe_content=True: (False, "vendor_copyright_marker_detected", "pypdf_memory"))

    summary = resolver.resolve_remaining_first30_transcripts(
        manifest_path=manifest,
        replacements_path=replacements,
        out_path=out,
        audit_dir=audit,
        probe_content=False,
    )

    row = read_csv(manifest)[0]
    replacement = read_csv(out)[0]
    assert summary["vendor_marker_blocked"] == 1
    assert row["download_allowed"] == "false"
    assert replacement["blocked_reason"] == "vendor_copyright_marker_detected"
