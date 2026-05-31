from __future__ import annotations

import json
from pathlib import Path

import tools.validate_first100_adjudication_file as validator
from tools.validate_first100_adjudication_file import main, validate_adjudication_file, validate_rows


def _row() -> dict[str, object]:
    return {
        "candidate_id": "fake_candidate_001",
        "case_id": "fake_2025_q4",
        "ticker": "FAKE",
        "fiscal_period": "2025 Q4",
        "suggested_label": "guidance_statement",
        "adjudicated_label": "guidance_statement",
        "review_status": "adjudicated",
        "gold_status": "not_gold",
        "reviewer": "reviewer_1",
        "rationale": "Metadata and Desktop source were reviewed.",
        "source_file": "/Users/keith/Desktop/earnings calls 100 samples/fake/source.txt",
        "source_sha256": "sha256:" + "a" * 64,
        "normalized_transcript_hash": "sha256:" + "b" * 64,
        "text_hash": "sha256:" + "c" * 64,
        "provenance_hash": "sha256:" + "d" * 64,
        "evidence_object_id": "evidence_fake",
        "chunk_id": "chunk_fake",
        "promotion_decision": "not_requested",
        "training_export_requested": False,
        "training_allowed": False,
        "explicit_training_rights_ref": "",
    }


def test_adjudication_validator_explains_common_reviewer_mistakes() -> None:
    bad = _row()
    bad["candidate_id"] = ""
    bad["adjudicated_label"] = "bullish"
    bad["reviewer"] = "?"
    bad["source_sha256"] = ""
    bad["promotion_decision"] = "promote"
    bad["training_export_requested"] = True

    errors = validate_rows([bad])

    assert any("missing candidate_id" in error for error in errors)
    assert any("invalid adjudicated_label" in error for error in errors)
    assert any("invalid reviewer" in error for error in errors)
    assert any("missing evidence/provenance reference" in error for error in errors)
    assert any("attempted promotion without manifest readiness" in error for error in errors)
    assert any("unsupported training-rights claim" in error for error in errors)


def test_adjudication_validator_accepts_metadata_only_non_promotional_row(tmp_path: Path) -> None:
    path = tmp_path / "adjudication.jsonl"
    path.write_text(json.dumps(_row()) + "\n", encoding="utf-8")

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json")

    assert summary["valid"] is True
    assert summary["adjudicated_rows"] == 1
    assert summary["promotion_ready"] is False
    assert summary["training_ready"] is False


def test_empty_adjudication_draft_is_not_ready_without_errors(tmp_path: Path) -> None:
    path = tmp_path / "first100_adjudication_draft.jsonl"
    path.write_text("\n", encoding="utf-8")

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json")

    assert summary["manifest_exists"] is True
    assert summary["valid"] is False
    assert summary["status"] == "NOT_READY"
    assert summary["adjudicated_rows"] == 0
    assert summary["error_count"] == 0
    assert summary["promotion_ready"] is False
    assert summary["training_ready"] is False


def test_adjudication_validator_accepts_positional_path(tmp_path: Path) -> None:
    path = tmp_path / "adjudication.jsonl"
    path.write_text(json.dumps(_row()) + "\n", encoding="utf-8")

    exit_code = main([str(path), "--out", str(tmp_path / "report.md"), "--json-out", str(tmp_path / "report.json")])

    assert exit_code == 0


def test_documentation_template_cannot_be_used_as_real_adjudication_data() -> None:
    template_path = validator.ROOT / "docs" / "review" / "first100_adjudication_row_template.json"

    template = json.loads(template_path.read_text(encoding="utf-8"))
    errors = validate_rows([template])

    assert "data/review/staging" not in str(template_path)
    assert template["candidate_id"] == "<candidate_id>"
    assert template["adjudicated_label"] == "<adjudicated_label>"
    assert template["gold_status"] == "not_gold"
    assert template["promotion_decision"] == "not_requested"
    assert template["training_export_requested"] is False
    assert template["training_allowed"] is False
    assert errors
    assert any("invalid adjudicated_label" in error for error in errors)


def test_documentation_template_cannot_trigger_readiness(tmp_path: Path) -> None:
    template_path = validator.ROOT / "docs" / "review" / "first100_adjudication_row_template.json"
    draft_path = tmp_path / "template-as-draft.jsonl"
    template = json.loads(template_path.read_text(encoding="utf-8"))
    draft_path.write_text(json.dumps(template) + "\n", encoding="utf-8")

    summary = validate_adjudication_file(draft_path, tmp_path / "report.md", tmp_path / "report.json")

    assert summary["valid"] is False
    assert summary["status"] == "NOT_READY"
    assert summary["promotion_ready"] is False
    assert summary["training_ready"] is False
    assert summary["gold_labels_created"] == 0


def test_manual_adjudication_guide_documents_required_fields_and_blockers() -> None:
    guide = (validator.ROOT / "docs" / "review" / "first100_manual_adjudication_guide.md").read_text(encoding="utf-8")

    for required in (
        "candidate_id",
        "adjudicated_label",
        "reviewer",
        "rationale",
        "source_sha256",
        "normalized_transcript_hash",
        "text_hash",
        "provenance_hash",
        "gold_status",
        "promotion_decision",
        "training_export_requested",
        "training_allowed",
        "explicit_training_rights_ref",
    ):
        assert f"`{required}`" in guide
    for label in validator.ALLOWED_LABELS:
        assert f"`{label}`" in guide
    for blocker in ("Do not guess", "No raw transcript text", "Promotion remains blocked", "Training remains blocked"):
        assert blocker in guide
