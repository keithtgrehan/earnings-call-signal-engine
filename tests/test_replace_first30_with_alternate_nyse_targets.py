from __future__ import annotations

from pathlib import Path

import tools.replace_first30_with_alternate_nyse_targets as alternates
from tools.first30_transcript_common import FIRST30_INGESTION_FIELDS, read_csv, write_csv


def _blocked_row(case_id: str) -> dict[str, str]:
    return {
        "candidate_id": f"first30_{case_id}",
        "priority_rank": "10",
        "case_id": case_id,
        "ticker": "DOW",
        "company_name": "Dow Inc.",
        "exchange": "NYSE",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q4",
        "event_date": "2025-12-31",
        "source_url": "https://investors.example.com",
        "source_domain": "investors.example.com",
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


def test_alternates_append_only_clean_nyse_rows(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.csv"
    out = tmp_path / "alternates.csv"
    audit = tmp_path / "_audit"
    write_csv(manifest, [_blocked_row("dow_2025_q4")], FIRST30_INGESTION_FIELDS)
    monkeypatch.setattr(
        alternates,
        "ALTERNATES",
        [
            {
                "case_id": "f_2025_q1",
                "ticker": "F",
                "company_name": "Ford Motor Company",
                "fiscal_year": "2025",
                "fiscal_quarter": "Q1",
                "event_date": "2025-05-05",
                "source_url": "https://s205.q4cdn.com/882619693/files/doc_financials/2025/q1/Ford-Q1-2025-Earnings-Call-Transcript-5-5-25.pdf",
                "replacement_for_blocked_case": "dow_2025_q4",
            }
        ],
    )
    monkeypatch.setattr(alternates, "probe_transcript_url", lambda row, candidate, probe_content=True: (True, "content_clean:test", "test"))

    summary = alternates.replace_first30_with_alternate_nyse_targets(
        manifest_path=manifest,
        out_path=out,
        audit_dir=audit,
        probe_content=False,
    )

    rows = read_csv(manifest)
    added = rows[1]
    assert summary["alternates_added_to_manifest"] == 1
    assert added["case_id"] == "f_2025_q1"
    assert added["exchange"] == "NYSE"
    assert added["download_allowed"] == "true"
    assert added["commit_allowed"] == "false"
    assert added["training_allowed"] == "false"
    assert added["rights_review_required"] == "true"
    assert (audit / "first30_alternate_replacement_candidates.csv").exists()


def test_alternates_skip_when_original_blocker_is_resolved(tmp_path: Path, monkeypatch) -> None:
    row = _blocked_row("dow_2025_q4")
    row["download_allowed"] = "true"
    row["blocked_reason"] = ""
    manifest = tmp_path / "manifest.csv"
    out = tmp_path / "alternates.csv"
    audit = tmp_path / "_audit"
    write_csv(manifest, [row], FIRST30_INGESTION_FIELDS)
    monkeypatch.setattr(alternates, "probe_transcript_url", lambda row, candidate, probe_content=True: (True, "content_clean:test", "test"))

    summary = alternates.replace_first30_with_alternate_nyse_targets(
        manifest_path=manifest,
        out_path=out,
        audit_dir=audit,
        probe_content=False,
    )

    assert summary["alternates_added_to_manifest"] == 0
    assert len(read_csv(manifest)) == 1
