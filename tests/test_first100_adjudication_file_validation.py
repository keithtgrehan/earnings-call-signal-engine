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
        "reviewed_at": "2026-05-31T12:00:00Z",
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


def _write_candidate_metadata(path: Path, candidate_id: str = "fake_candidate_001") -> None:
    path.write_text(
        json.dumps(
            {
                "candidate_id": candidate_id,
                "case_id": "fake_2025_q4",
                "ticker": "FAKE",
                "fiscal_period": "2025 Q4",
            }
        )
        + "\n",
        encoding="utf-8",
    )


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
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates)

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

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
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates)

    exit_code = main(
        [
            str(path),
            "--candidates",
            str(candidates),
            "--out",
            str(tmp_path / "report.md"),
            "--json-out",
            str(tmp_path / "report.json"),
        ]
    )

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
        "reviewed_at",
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


def test_manual_operator_checklist_documents_safe_local_workflow() -> None:
    checklist = (validator.ROOT / "docs" / "review" / "first100_manual_operator_checklist.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "reports/review/first100_reviewer_packet.md",
        "data/review/staging/first100_signal_candidates.jsonl",
        "data/review/staging/first100_adjudication_draft.jsonl",
        "No transcript quotes are pasted",
        "No `quote`, `snippet`, `raw_text`, `evidence_text`, or `final_evidence_text` field is present",
        "`promotion_ready=false`",
        "`training_ready=false`",
        "PYENV_VERSION=3.11.3 python tools/validate_first100_adjudication.py --draft data/review/staging/first100_adjudication_draft.jsonl --mode staging",
        "PYENV_VERSION=3.11.3 python tools/build_first100_reviewer_packet.py",
        "PYENV_VERSION=3.11.3 python tools/build_review_readiness_dashboard.py",
        "scripts/check_restricted_artifacts.py",
    ):
        assert required in checklist


def test_malformed_jsonl_fails_with_line_number(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps(_row()) + "\n" + '{"candidate_id": \n', encoding="utf-8")

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json")

    assert summary["valid"] is False
    assert summary["status"] == "NOT_READY"
    assert any("line 2: malformed JSON" in error for error in summary["errors"])
    assert summary["promotion_ready"] is False
    assert summary["training_ready"] is False


def test_missing_required_field_fails_clearly(tmp_path: Path) -> None:
    row = _row()
    row.pop("case_id")
    path = tmp_path / "missing.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates)

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

    assert any("missing required field case_id" in error for error in summary["errors"])


def test_unknown_candidate_id_fails_when_candidate_metadata_exists(tmp_path: Path) -> None:
    path = tmp_path / "unknown.jsonl"
    path.write_text(json.dumps(_row()) + "\n", encoding="utf-8")
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates, "other_candidate")

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

    assert any("candidate_id fake_candidate_001 not found" in error for error in summary["errors"])


def test_non_empty_rows_fail_closed_when_candidate_metadata_absent(tmp_path: Path) -> None:
    path = tmp_path / "draft.jsonl"
    path.write_text(json.dumps(_row()) + "\n", encoding="utf-8")

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", tmp_path / "missing_candidates.jsonl")

    assert any("candidate metadata missing" in error for error in summary["errors"])
    assert summary["promotion_ready"] is False
    assert summary["training_ready"] is False


def test_duplicate_candidate_id_fails(tmp_path: Path) -> None:
    path = tmp_path / "dupe.jsonl"
    path.write_text(json.dumps(_row()) + "\n" + json.dumps(_row()) + "\n", encoding="utf-8")
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates)

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

    assert any("duplicate candidate_id fake_candidate_001" in error for error in summary["errors"])


def test_invalid_review_status_gold_status_and_training_values_fail(tmp_path: Path) -> None:
    row = _row()
    row["review_status"] = "pending_human_review"
    row["gold_status"] = "promotion_candidate"
    row["promotion_decision"] = "promote"
    row["training_allowed"] = True
    row["training_export_requested"] = True
    row["explicit_training_rights_ref"] = "rights_ref"
    path = tmp_path / "bad_status.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates)

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

    assert any("review_status must be adjudicated" in error for error in summary["errors"])
    assert any("gold_status must stay not_gold" in error for error in summary["errors"])
    assert any("promotion_decision must be absent or not_requested" in error for error in summary["errors"])
    assert any("unsupported training-rights claim" in error for error in summary["errors"])


def test_rejection_reason_required_and_validated(tmp_path: Path) -> None:
    missing = _row()
    missing["candidate_id"] = "missing_reason"
    missing["adjudicated_label"] = "reject_candidate"
    invalid = _row()
    invalid["candidate_id"] = "invalid_reason"
    invalid["adjudicated_label"] = "needs_source_review"
    invalid["rejection_reason"] = "because"
    path = tmp_path / "rejections.jsonl"
    path.write_text(json.dumps(missing) + "\n" + json.dumps(invalid) + "\n", encoding="utf-8")
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates, "missing_reason")
    with candidates.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"candidate_id": "invalid_reason"}) + "\n")

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

    assert any("missing rejection_reason" in error for error in summary["errors"])
    assert any("invalid rejection_reason 'because'" in error for error in summary["errors"])


def test_missing_or_invalid_reviewer_metadata_fails(tmp_path: Path) -> None:
    missing = _row()
    missing["candidate_id"] = "missing_reviewer"
    missing["reviewer"] = ""
    invalid_time = _row()
    invalid_time["candidate_id"] = "invalid_time"
    invalid_time["reviewed_at"] = "2026-05-31 12:00:00"
    path = tmp_path / "reviewer.jsonl"
    path.write_text(json.dumps(missing) + "\n" + json.dumps(invalid_time) + "\n", encoding="utf-8")
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates, "missing_reviewer")
    with candidates.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"candidate_id": "invalid_time"}) + "\n")

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

    assert any("invalid reviewer" in error for error in summary["errors"])
    assert any("reviewed_at must be ISO-8601 UTC" in error for error in summary["errors"])


def test_unknown_and_raw_text_fields_fail(tmp_path: Path) -> None:
    row = _row()
    row["surprise"] = "nope"
    row["quote"] = "raw transcript words"
    path = tmp_path / "unknown.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    candidates = tmp_path / "candidates.jsonl"
    _write_candidate_metadata(candidates)

    summary = validate_adjudication_file(path, tmp_path / "report.md", tmp_path / "report.json", candidates)

    assert any("unknown field surprise" in error for error in summary["errors"])
    assert any("raw text field quote is not allowed" in error for error in summary["errors"])


def test_safe_cli_wrapper_validates_empty_staging_draft(tmp_path: Path) -> None:
    from tools.validate_first100_adjudication import main as wrapper_main

    draft = tmp_path / "draft.jsonl"
    draft.write_text("\n", encoding="utf-8")
    exit_code = wrapper_main(
        [
            "--draft",
            str(draft),
            "--mode",
            "staging",
            "--out",
            str(tmp_path / "report.md"),
            "--json-out",
            str(tmp_path / "report.json"),
        ]
    )

    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["status"] == "NOT_READY"
    assert report["adjudicated_rows"] == 0
    assert report["promotion_ready"] is False
    assert report["training_ready"] is False
