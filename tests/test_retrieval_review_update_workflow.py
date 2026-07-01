from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from signal_engine.retrieval.bakeoff import BAKEOFF_STATUS_LABEL
from signal_engine.retrieval.review_updates import (
    REVIEW_WORKSHEET_COLUMNS,
    export_review_worksheet,
    import_review_updates,
)
from tools.plan_retrieval_bakeoff import plan_retrieval_bakeoff
from tools.validate_retrieval_reviewed_query_set import validate_retrieval_reviewed_query_set


OBJECTS_PATH = Path("data/retrieval/retrieval_object_metadata.jsonl")
FIRST20_QUERY_SET_PATH = Path("data/retrieval/retrieval_reviewed_query_set.first20.jsonl")
FIRST20_MANIFEST_PATH = Path("configs/retrieval_bakeoff.first20_review_pending.example.yml")

FORBIDDEN_WORKSHEET_COLUMNS = {
    "raw_text",
    "raw_transcript_text",
    "transcript_text",
    "asr_text",
    "audio_text",
    "chunk_text",
    "chunk_body_text",
    "evidence_text",
    "answer",
    "answer_text",
    "expected_answer",
    "gold_label",
    "gold_labels",
    "adjudication",
    "adjudication_row",
    "training_label",
    "promotion_row",
    "embedding",
    "embeddings",
    "vector",
    "vectors",
    "vector_db",
}


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _export_worksheet(tmp_path: Path) -> Path:
    worksheet_path = tmp_path / "worksheet.csv"
    export_review_worksheet(
        query_set_path=FIRST20_QUERY_SET_PATH,
        objects_path=OBJECTS_PATH,
        out_path=worksheet_path,
    )
    return worksheet_path


def _write_updates(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_worksheet_export_contains_metadata_only_fields_and_matching_row_count(tmp_path: Path) -> None:
    worksheet_path = tmp_path / "worksheet.csv"

    summary = export_review_worksheet(
        query_set_path=FIRST20_QUERY_SET_PATH,
        objects_path=OBJECTS_PATH,
        out_path=worksheet_path,
    )
    rows = _csv_rows(worksheet_path)

    assert summary["row_count"] == 20
    assert summary["query_set_readiness_status"] == "review_pending_blocked"
    assert list(rows[0]) == REVIEW_WORKSHEET_COLUMNS
    assert not (set(rows[0]) & FORBIDDEN_WORKSHEET_COLUMNS)
    assert len(rows) == len(_jsonl(FIRST20_QUERY_SET_PATH)) == 20
    encoded = json.dumps(rows, sort_keys=True).lower()
    assert "operator:" not in encoded
    assert "management:" not in encoded
    assert "analyst:" not in encoded
    assert '"raw_text"' not in encoded
    assert '"chunk_text"' not in encoded


def test_worksheet_export_uses_lf_line_endings_for_git_diff_check(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)

    assert b"\r\n" not in worksheet_path.read_bytes()


def test_import_preserves_immutable_fields_and_outputs_valid_pending_candidate(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)
    out_path = tmp_path / "reviewed_candidate.jsonl"

    summary = import_review_updates(
        query_set_path=FIRST20_QUERY_SET_PATH,
        review_updates_path=worksheet_path,
        objects_path=OBJECTS_PATH,
        out_path=out_path,
        summary_json_path=tmp_path / "summary.json",
        summary_md_path=tmp_path / "summary.md",
    )

    base_rows = _jsonl(FIRST20_QUERY_SET_PATH)
    candidate_rows = _jsonl(out_path)
    immutable_fields = {
        "query_id",
        "case_id",
        "query_type",
        "query_text_or_safe_query_label",
        "expected_object_ids",
        "expected_object_types",
        "expected_topics",
        "evidence_object_id_refs",
        "provenance_refs",
    }
    assert len(candidate_rows) == len(base_rows) == 20
    for base_row, candidate_row in zip(base_rows, candidate_rows, strict=True):
        assert {field: candidate_row[field] for field in immutable_fields} == {
            field: base_row[field] for field in immutable_fields
        }
    assert summary["total_rows"] == 20
    assert summary["reviewed_rows"] == 0
    assert summary["approved_rows"] == 0
    assert summary["benchmark_eligible_rows"] == 0
    assert summary["benchmark_threshold_met"] is False
    assert summary["provider_execution"] is False
    assert summary["embeddings_generated"] is False
    assert summary["vector_db_generated"] is False
    assert validate_retrieval_reviewed_query_set(query_set_path=out_path, objects_path=OBJECTS_PATH)["query_count"] == 20


def test_import_rejects_changed_object_ids_or_provenance_refs(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)
    rows = _csv_rows(worksheet_path)
    rows[0]["expected_object_ids"] = json.dumps(["rom_evidence_ffffffffffffffff"])
    _write_updates(worksheet_path, rows)

    with pytest.raises(ValueError, match="immutable field expected_object_ids changed"):
        import_review_updates(
            query_set_path=FIRST20_QUERY_SET_PATH,
            review_updates_path=worksheet_path,
            objects_path=OBJECTS_PATH,
            out_path=tmp_path / "candidate.jsonl",
        )

    rows = _csv_rows(_export_worksheet(tmp_path))
    rows[0]["provenance_refs"] = json.dumps(["/safe/changed/provenance.json"])
    _write_updates(worksheet_path, rows)
    with pytest.raises(ValueError, match="immutable field provenance_refs changed"):
        import_review_updates(
            query_set_path=FIRST20_QUERY_SET_PATH,
            review_updates_path=worksheet_path,
            objects_path=OBJECTS_PATH,
            out_path=tmp_path / "candidate.jsonl",
        )


def test_import_rejects_raw_text_columns_and_answer_leakage(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)
    rows = _csv_rows(worksheet_path)
    rows[0]["raw_text"] = "blocked"
    with worksheet_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="unexpected worksheet column raw_text"):
        import_review_updates(
            query_set_path=FIRST20_QUERY_SET_PATH,
            review_updates_path=worksheet_path,
            objects_path=OBJECTS_PATH,
            out_path=tmp_path / "candidate.jsonl",
        )

    worksheet_path = _export_worksheet(tmp_path)
    rows = _csv_rows(worksheet_path)
    rows[0]["reviewer_notes"] = "expected answer should never be pasted here"
    _write_updates(worksheet_path, rows)
    with pytest.raises(ValueError, match="answer leakage"):
        import_review_updates(
            query_set_path=FIRST20_QUERY_SET_PATH,
            review_updates_path=worksheet_path,
            objects_path=OBJECTS_PATH,
            out_path=tmp_path / "candidate.jsonl",
        )


def test_import_rejects_eligibility_without_reviewed_status(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)
    rows = _csv_rows(worksheet_path)
    rows[0]["benchmark_eligible"] = "true"
    rows[0]["reviewer_decision"] = "approved"
    rows[0]["reviewer"] = "reviewer_r9"
    rows[0]["reviewed_at"] = "2026-06-02T15:00:00Z"
    _write_updates(worksheet_path, rows)

    with pytest.raises(ValueError, match="benchmark_eligible=true requires review_status=reviewed"):
        import_review_updates(
            query_set_path=FIRST20_QUERY_SET_PATH,
            review_updates_path=worksheet_path,
            objects_path=OBJECTS_PATH,
            out_path=tmp_path / "candidate.jsonl",
        )


def test_import_rejects_reviewed_status_without_reviewer_and_reviewed_at(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)
    rows = _csv_rows(worksheet_path)
    rows[0]["review_status"] = "reviewed"
    rows[0]["reviewer_decision"] = "approved"
    _write_updates(worksheet_path, rows)

    with pytest.raises(ValueError, match="reviewer must be present"):
        import_review_updates(
            query_set_path=FIRST20_QUERY_SET_PATH,
            review_updates_path=worksheet_path,
            objects_path=OBJECTS_PATH,
            out_path=tmp_path / "candidate.jsonl",
        )


def test_approved_reviewed_rows_can_become_benchmark_eligible_in_temp_fixture(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)
    rows = _csv_rows(worksheet_path)
    for row in rows:
        row["review_status"] = "reviewed"
        row["benchmark_eligible"] = "true"
        row["reviewer"] = "reviewer_r9_temp_fixture"
        row["reviewed_at"] = "2026-06-02T15:00:00Z"
        row["reviewer_decision"] = "approved"
    _write_updates(worksheet_path, rows)
    out_path = tmp_path / "reviewed_candidate.jsonl"

    summary = import_review_updates(
        query_set_path=FIRST20_QUERY_SET_PATH,
        review_updates_path=worksheet_path,
        objects_path=OBJECTS_PATH,
        out_path=out_path,
        summary_json_path=tmp_path / "summary.json",
        summary_md_path=tmp_path / "summary.md",
    )

    assert summary["total_rows"] == 20
    assert summary["reviewed_rows"] == 20
    assert summary["approved_rows"] == 20
    assert summary["rejected_rows"] == 0
    assert summary["benchmark_eligible_rows"] == 20
    assert summary["benchmark_threshold_met"] is True
    validated = validate_retrieval_reviewed_query_set(query_set_path=out_path, objects_path=OBJECTS_PATH)
    assert validated["benchmark_ready_query_set"] is True
    assert validated["evaluated_retrieval_quality"] is False


def test_bakeoff_planner_can_consume_temp_reviewed_candidate_without_running_providers(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)
    rows = _csv_rows(worksheet_path)
    for row in rows:
        row["review_status"] = "reviewed"
        row["benchmark_eligible"] = "true"
        row["reviewer"] = "reviewer_r9_temp_fixture"
        row["reviewed_at"] = "2026-06-02T15:00:00Z"
        row["reviewer_decision"] = "approved"
    _write_updates(worksheet_path, rows)
    candidate_path = tmp_path / "reviewed_candidate.jsonl"
    import_review_updates(
        query_set_path=FIRST20_QUERY_SET_PATH,
        review_updates_path=worksheet_path,
        objects_path=OBJECTS_PATH,
        out_path=candidate_path,
    )
    manifest = yaml.safe_load(FIRST20_MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["reviewed_query_set"] = {
        "path": str(candidate_path),
        "reviewed": True,
        "smoke_only": False,
        "review_stage": "reviewed",
        "reviewer": "reviewer_r9_temp_fixture",
        "approval_id": "temp_fixture_only",
        "notes": "Temporary reviewed-query import fixture for planner gating tests.",
    }
    manifest["plan_outputs"] = {
        "json_report": str(tmp_path / "reviewed_plan.json"),
        "markdown_report": str(tmp_path / "reviewed_plan.md"),
    }
    manifest_path = tmp_path / "reviewed_manifest.yml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    summary = plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)

    assert summary["status_label"] == BAKEOFF_STATUS_LABEL
    assert summary["benchmark_ready_query_set"] is True
    assert summary["benchmark_threshold_met"] is True
    assert summary["real_benchmark_allowed"] is False
    assert summary["network_calls"] is False
    assert summary["embeddings_generated"] is False
    assert summary["vector_db_generated"] is False
    assert summary["provider_benchmark_complete"] is False
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False


def test_import_does_not_create_embedding_vector_or_provider_artifacts(tmp_path: Path) -> None:
    worksheet_path = _export_worksheet(tmp_path)

    import_review_updates(
        query_set_path=FIRST20_QUERY_SET_PATH,
        review_updates_path=worksheet_path,
        objects_path=OBJECTS_PATH,
        out_path=tmp_path / "candidate.jsonl",
        summary_json_path=tmp_path / "summary.json",
        summary_md_path=tmp_path / "summary.md",
    )

    generated_names = {path.name.lower() for path in tmp_path.iterdir()}
    assert not any("embedding" in name for name in generated_names)
    assert not any("vector" in name for name in generated_names)
    assert not any("provider_artifact" in name for name in generated_names)
