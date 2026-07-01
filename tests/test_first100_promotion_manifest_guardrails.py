from __future__ import annotations

import json
from pathlib import Path

from tools.validate_first100_promotion_manifest import validate, validate_rows


def test_missing_promotion_manifest_is_not_ready(tmp_path: Path) -> None:
    summary = validate(tmp_path / "missing.jsonl", tmp_path / "report.md", tmp_path / "report.json")

    assert summary["status"] == "NOT_READY"
    assert summary["manifest_exists"] is False
    assert summary["valid"] is False


def test_promotion_manifest_rejects_raw_final_evidence_text() -> None:
    rows = [
        {
            "candidate_id": "cand1",
            "label_id": "label1",
            "adjudicator": "reviewer",
            "adjudicated_at": "2026-05-31T00:00:00Z",
            "review_status": "adjudicated",
            "gold_status": "promotion_candidate",
            "final_label": "guidance_statement",
            "suggested_label": "guidance_statement",
            "rationale": "",
            "final_evidence_text": "management said guidance was improving",
            "source_file": "/Users/keith/Desktop/source.txt",
            "source_sha256": "sha256:" + "a" * 64,
            "normalized_transcript_hash": "sha256:" + "b" * 64,
            "provenance_hash": "sha256:" + "c" * 64,
            "weak_label_only": False,
        }
    ]

    errors = validate_rows(rows)

    assert any("raw text" in error for error in errors)
    assert any("without rationale" in error for error in errors)


def test_promotion_manifest_error_messages_are_reviewer_actionable() -> None:
    errors = validate_rows(
        [
            {
                "candidate_id": "",
                "label_id": "",
                "adjudicator": "",
                "review_status": "pending_human_review",
                "gold_status": "not_gold",
                "final_label": "bullish",
                "training_export_requested": True,
                "training_allowed": False,
            }
        ]
    )

    assert any("missing candidate_id" in error for error in errors)
    assert any("invalid final_label" in error for error in errors)
    assert any("attempted promotion without manifest readiness" in error for error in errors)
    assert any("unsupported training-rights claim" in error for error in errors)


def test_promotion_manifest_validates_metadata_evidence_hash(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "candidate_id": "cand1",
                "label_id": "label1",
                "adjudicator": "reviewer",
                "adjudicated_at": "2026-05-31T00:00:00Z",
                "review_status": "adjudicated",
                "gold_status": "promotion_candidate",
                "final_label": "guidance_statement",
                "suggested_label": "uncertainty",
                "rationale": "Reviewer checked the source and selected a different final label.",
                "final_evidence_text_hash": "sha256:" + "d" * 64,
                "source_file": "/Users/keith/Desktop/source.txt",
                "source_sha256": "sha256:" + "a" * 64,
                "normalized_transcript_hash": "sha256:" + "b" * 64,
                "provenance_hash": "sha256:" + "c" * 64,
                "weak_label_only": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = validate(manifest, tmp_path / "report.md", tmp_path / "report.json")

    assert summary["valid"] is True
    assert summary["status"] == "PROMOTION_READY"
