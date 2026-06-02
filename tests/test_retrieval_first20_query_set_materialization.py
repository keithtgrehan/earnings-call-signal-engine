from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from signal_engine.retrieval.bakeoff import BAKEOFF_STATUS_LABEL, load_bakeoff_manifest
from signal_engine.retrieval.reviewed_query_set import REVIEWED_QUERY_SET_QUERY_TYPES
from signal_engine.retrieval.reviewed_query_set import validate_reviewed_query_set_rows
from tools.plan_retrieval_bakeoff import plan_retrieval_bakeoff
from tools.validate_retrieval_bakeoff_manifest import main as validate_bakeoff_cli
from tools.validate_retrieval_reviewed_query_set import validate_retrieval_reviewed_query_set


OBJECTS_PATH = Path("data/retrieval/retrieval_object_metadata.jsonl")
FIRST20_QUERY_SET_PATH = Path("data/retrieval/retrieval_reviewed_query_set.first20.jsonl")
FIRST20_MANIFEST_PATH = Path("configs/retrieval_bakeoff.first20_review_pending.example.yml")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _object_rows_by_id() -> dict[str, dict[str, Any]]:
    return {row["object_id"]: row for row in _jsonl(OBJECTS_PATH)}


def test_first20_query_types_are_supported_by_schema_and_validator() -> None:
    schema = json.loads(Path("schemas/retrieval_reviewed_query_set.schema.json").read_text(encoding="utf-8"))
    expected_types = {
        "guidance_revision_lookup",
        "uncertainty_language_lookup",
        "analyst_pressure_lookup",
        "topic_lookup",
        "evidence_object_lookup",
        "case_comparison_lookup",
    }

    assert expected_types <= REVIEWED_QUERY_SET_QUERY_TYPES
    assert expected_types <= set(schema["properties"]["query_type"]["enum"])


def test_first20_candidate_validates_without_template_allowance() -> None:
    summary = validate_retrieval_reviewed_query_set(
        query_set_path=FIRST20_QUERY_SET_PATH,
        objects_path=OBJECTS_PATH,
    )

    assert summary["query_count"] == 20
    assert summary["query_status_counts"] == {"review_pending": 20}
    assert summary["reviewed_eligible_query_count"] == 0
    assert summary["benchmark_threshold_met"] is False
    assert summary["benchmark_ready_query_set"] is False
    assert summary["query_set_readiness_status"] == "review_pending_blocked"
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False


def test_first20_candidate_contains_no_raw_text_like_fields() -> None:
    rows = _jsonl(FIRST20_QUERY_SET_PATH)
    forbidden_keys = {
        "raw_text",
        "transcript_text",
        "asr_text",
        "audio_text",
        "chunk_text",
        "evidence_text",
        "answer",
        "answer_text",
        "expected_answer",
        "gold_label",
        "adjudication",
        "training_label",
        "promotion_row",
        "embedding",
        "vector",
    }

    for row in rows:
        assert not (set(row) & forbidden_keys)
        encoded = json.dumps(row, sort_keys=True).lower()
        assert "operator:" not in encoded
        assert "management:" not in encoded
        assert "analyst:" not in encoded
        assert "raw transcript" not in encoded
        assert "chunk text" not in encoded
        assert "evidence text" not in encoded


def test_first20_candidate_references_known_objects_and_matching_provenance() -> None:
    rows = _jsonl(FIRST20_QUERY_SET_PATH)
    objects = _object_rows_by_id()

    assert len(rows) == 20
    assert len({row["query_id"] for row in rows}) == 20
    for row in rows:
        assert row["expected_object_ids"]
        assert row["provenance_refs"]
        for object_id in row["expected_object_ids"]:
            obj = objects[object_id]
            assert obj["case_id"] == row["case_id"]
            assert obj["object_type"] in row["expected_object_types"]
            assert obj["provenance_ref"] in row["provenance_refs"]
        for object_id in row["evidence_object_id_refs"]:
            assert objects[object_id]["object_type"] == "evidence_object_metadata"


def test_first20_candidate_rejects_extra_provenance_ref() -> None:
    rows = _jsonl(FIRST20_QUERY_SET_PATH)
    rows[0]["provenance_refs"].append("/safe/unrelated/provenance.json")

    errors = validate_reviewed_query_set_rows(rows, list(_object_rows_by_id().values()))

    assert any("provenance_refs must exactly match" in error for error in errors)


def test_first20_candidate_rejects_cross_case_evidence_ref() -> None:
    rows = _jsonl(FIRST20_QUERY_SET_PATH)
    rows[0]["evidence_object_id_refs"] = [rows[1]["expected_object_ids"][0]]

    errors = validate_reviewed_query_set_rows(rows, list(_object_rows_by_id().values()))

    assert any("does not match case_id" in error for error in errors)


def test_first20_candidate_remains_review_pending_and_not_eligible() -> None:
    rows = _jsonl(FIRST20_QUERY_SET_PATH)

    assert {row["review_status"] for row in rows} == {"review_pending"}
    assert all(row["benchmark_eligible"] is False for row in rows)
    assert all(row["reviewer"] == "" for row in rows)
    assert all(row["reviewed_at"] == "" for row in rows)


def test_first20_manifest_validates_and_is_review_pending_not_smoke_only() -> None:
    manifest = load_bakeoff_manifest(FIRST20_MANIFEST_PATH, root=Path("."))

    assert manifest.payload["status_label"] == BAKEOFF_STATUS_LABEL
    assert manifest.payload["reviewed_query_set"]["path"] == str(FIRST20_QUERY_SET_PATH)
    assert manifest.payload["reviewed_query_set"]["review_stage"] == "review_pending"
    assert manifest.payload["reviewed_query_set"]["smoke_only"] is False
    assert manifest.payload["reviewed_query_set"]["reviewed"] is False
    assert validate_bakeoff_cli(["--manifest", str(FIRST20_MANIFEST_PATH)]) == 0


def test_bakeoff_planner_consumes_first20_candidate_safely(tmp_path: Path) -> None:
    manifest = yaml.safe_load(FIRST20_MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["plan_outputs"] = {
        "json_report": str(tmp_path / "first20_plan.json"),
        "markdown_report": str(tmp_path / "first20_plan.md"),
    }
    manifest_path = tmp_path / "first20_manifest.yml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    summary = plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)
    report_json = (tmp_path / "first20_plan.json").read_text(encoding="utf-8")
    report_md = (tmp_path / "first20_plan.md").read_text(encoding="utf-8")

    assert summary["status_label"] == BAKEOFF_STATUS_LABEL
    assert summary["query_count"] == 20
    assert summary["query_status_counts"] == {"review_pending": 20}
    assert summary["reviewed_eligible_query_count"] == 0
    assert summary["benchmark_threshold_met"] is False
    assert summary["benchmark_ready_query_set"] is False
    assert summary["real_benchmark_allowed"] is False
    assert summary["network_calls"] is False
    assert summary["embeddings_generated"] is False
    assert summary["vector_db_generated"] is False
    assert summary["provider_benchmark_complete"] is False
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False
    assert '"raw_text"' not in report_json
    assert '"chunk_text"' not in report_json
    assert '"provider_response"' not in report_json
    assert "benchmark_threshold_met: `false`" in report_md
