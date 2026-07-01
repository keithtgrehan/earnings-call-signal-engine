from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from signal_engine.retrieval.bakeoff import BAKEOFF_STATUS_LABEL
from signal_engine.retrieval.reviewed_query_set import (
    MIN_REVIEWED_ELIGIBLE_QUERIES,
    REVIEWED_QUERY_SET_REQUIRED_FIELDS,
    REVIEWED_QUERY_SET_STATUSES,
    REVIEWED_QUERY_SET_STATUS_BENCHMARK_READY_INPUTS_ONLY,
    REVIEWED_QUERY_SET_STATUS_TEMPLATE_ONLY,
    load_reviewed_query_set,
    summarize_reviewed_query_set,
    validate_reviewed_query_set_rows,
)
from tools.plan_retrieval_bakeoff import plan_retrieval_bakeoff
from tools.validate_retrieval_reviewed_query_set import main as reviewed_query_set_cli
from tools.validate_retrieval_reviewed_query_set import validate_retrieval_reviewed_query_set


ROOT = Path(".")
OBJECTS_PATH = Path("data/retrieval/retrieval_object_metadata.jsonl")
TEMPLATE_QUERY_SET_PATH = Path("data/retrieval/retrieval_reviewed_query_set.template.jsonl")


def _object_rows() -> list[dict[str, Any]]:
    return [json.loads(line) for line in OBJECTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def _object_row(case_id: str = "hd_2025_q4") -> dict[str, Any]:
    for row in _object_rows():
        if row["case_id"] == case_id:
            return row
    raise AssertionError(f"missing object row for {case_id}")


def _reviewed_row(**overrides: Any) -> dict[str, Any]:
    obj = _object_row()
    row: dict[str, Any] = {
        "query_id": "rq_hd_2025_q4_prepared_remarks_001",
        "case_id": obj["case_id"],
        "query_type": "positive_evidence_lookup",
        "query_text_or_safe_query_label": "SAFE_LABEL: hd_2025_q4 prepared remarks management evidence object",
        "expected_object_ids": [obj["object_id"]],
        "expected_object_types": [obj["object_type"]],
        "expected_topics": [obj["topic"]],
        "evidence_object_id_refs": [obj["object_id"]],
        "provenance_refs": [obj["provenance_ref"]],
        "reviewer": "reviewer_r7",
        "reviewed_at": "2026-06-02T12:00:00Z",
        "review_status": "reviewed",
        "benchmark_eligible": True,
        "notes": "Metadata-only reviewed row for future retrieval-input readiness.",
    }
    row.update(overrides)
    return row


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _example_manifest() -> dict[str, Any]:
    return yaml.safe_load(Path("configs/retrieval_bakeoff.example.yml").read_text(encoding="utf-8"))


def test_reviewed_query_set_schema_is_metadata_only() -> None:
    schema = json.loads(Path("schemas/retrieval_reviewed_query_set.schema.json").read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == REVIEWED_QUERY_SET_REQUIRED_FIELDS
    assert set(schema["properties"]["review_status"]["enum"]) == REVIEWED_QUERY_SET_STATUSES
    for forbidden in ("raw_text", "chunk_text", "evidence_text", "answer", "gold_label", "embedding", "vector"):
        assert forbidden not in schema["properties"]


def test_valid_template_query_set_passes_with_allow_template() -> None:
    summary = validate_retrieval_reviewed_query_set(
        query_set_path=TEMPLATE_QUERY_SET_PATH,
        objects_path=OBJECTS_PATH,
        allow_template=True,
    )

    assert summary["query_set_readiness_status"] == REVIEWED_QUERY_SET_STATUS_TEMPLATE_ONLY
    assert summary["benchmark_ready_query_set"] is False
    assert summary["reviewed_eligible_query_count"] == 0
    assert summary["evaluated_retrieval_quality"] is False


def test_reviewed_query_set_cli_accepts_template_with_allow_template() -> None:
    exit_code = reviewed_query_set_cli(
        [
            "--query-set",
            str(TEMPLATE_QUERY_SET_PATH),
            "--objects",
            str(OBJECTS_PATH),
            "--allow-template",
        ]
    )

    assert exit_code == 0


def test_template_query_set_requires_allow_template() -> None:
    rows = load_reviewed_query_set(TEMPLATE_QUERY_SET_PATH)

    errors = validate_reviewed_query_set_rows(rows, _object_rows(), allow_template=False)

    assert any("template_only rows require --allow-template" in error for error in errors)


def test_duplicate_query_id_rejected() -> None:
    row = _reviewed_row()

    errors = validate_reviewed_query_set_rows([row, dict(row)], _object_rows(), allow_template=False)

    assert any("duplicate query_id" in error for error in errors)


def test_invalid_review_status_rejected() -> None:
    row = _reviewed_row(review_status="benchmark_complete")

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any("invalid review_status" in error for error in errors)


def test_unknown_object_id_rejected() -> None:
    row = _reviewed_row(expected_object_ids=["rom_evidence_deadbeefdeadbeef"])

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any("unknown expected_object_id" in error for error in errors)


def test_missing_provenance_ref_rejected() -> None:
    row = _reviewed_row(provenance_refs=[])

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any("provenance_refs must not be empty" in error for error in errors)


@pytest.mark.parametrize("forbidden_key", ["raw_text", "chunkText", "evidence_text", "answer_text", "gold_label", "embedding"])
def test_raw_text_and_answer_leakage_keys_rejected(forbidden_key: str) -> None:
    row = _reviewed_row()
    row[forbidden_key] = "blocked"

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any(forbidden_key in error for error in errors)


def test_answer_leakage_value_rejected() -> None:
    row = _reviewed_row(notes="expected answer should not be stored in query rows")

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any("answer leakage" in error for error in errors)


@pytest.mark.parametrize("unsafe_label", ["buy signal", "sell setup", "short idea", "alpha proof", "statistical significance"])
def test_unsafe_claim_wording_rejected(unsafe_label: str) -> None:
    row = _reviewed_row(query_text_or_safe_query_label=unsafe_label)

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any("unsafe market claim" in error for error in errors)


def test_benchmark_eligible_requires_reviewed_status() -> None:
    row = _reviewed_row(review_status="review_pending", benchmark_eligible=True, reviewer="", reviewed_at="")

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any("benchmark_eligible=true requires review_status=reviewed" in error for error in errors)


@pytest.mark.parametrize("field", ["reviewer", "reviewed_at"])
def test_reviewed_status_requires_reviewer_and_reviewed_at(field: str) -> None:
    row = _reviewed_row(**{field: ""})

    errors = validate_reviewed_query_set_rows([row], _object_rows(), allow_template=False)

    assert any(field in error for error in errors)


def test_smoke_only_set_blocks_benchmark_status() -> None:
    row = _reviewed_row(review_status="smoke_only", benchmark_eligible=False, reviewer="", reviewed_at="")

    summary = summarize_reviewed_query_set([row], object_rows=_object_rows())

    assert summary["query_set_readiness_status"] == "smoke_only_blocked"
    assert summary["benchmark_ready_query_set"] is False
    assert summary["has_reviewed_eligible_queries"] is False


def test_reviewed_eligible_set_unlocks_future_input_readiness_only() -> None:
    obj_rows = _object_rows()
    reviewed_rows = []
    for index, obj in enumerate(obj_rows[:MIN_REVIEWED_ELIGIBLE_QUERIES], start=1):
        reviewed_rows.append(
            _reviewed_row(
                query_id=f"rq_reviewed_ready_{index:03d}",
                case_id=obj["case_id"],
                expected_object_ids=[obj["object_id"]],
                expected_object_types=[obj["object_type"]],
                expected_topics=[obj["topic"]],
                evidence_object_id_refs=[obj["object_id"]],
                provenance_refs=[obj["provenance_ref"]],
            )
        )

    summary = summarize_reviewed_query_set(reviewed_rows, object_rows=obj_rows)

    assert summary["query_set_readiness_status"] == REVIEWED_QUERY_SET_STATUS_BENCHMARK_READY_INPUTS_ONLY
    assert summary["benchmark_ready_query_set"] is True
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False


def test_bakeoff_planner_reflects_template_query_set_readiness(tmp_path: Path) -> None:
    payload = _example_manifest()
    payload["reviewed_query_set"]["path"] = str(TEMPLATE_QUERY_SET_PATH)
    payload["reviewed_query_set"]["reviewed"] = False
    payload["reviewed_query_set"]["smoke_only"] = True
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "bakeoff_plan.json"),
        "markdown_report": str(tmp_path / "bakeoff_plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    summary = plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)

    assert summary["status_label"] == BAKEOFF_STATUS_LABEL
    assert summary["query_set_readiness_status"] == REVIEWED_QUERY_SET_STATUS_TEMPLATE_ONLY
    assert summary["benchmark_ready_query_set"] is False
    assert summary["real_benchmark_allowed"] is False
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False


def test_bakeoff_planner_does_not_turn_ready_inputs_into_results(tmp_path: Path) -> None:
    obj_rows = _object_rows()
    reviewed_rows = []
    for index, obj in enumerate(obj_rows[:MIN_REVIEWED_ELIGIBLE_QUERIES], start=1):
        reviewed_rows.append(
            _reviewed_row(
                query_id=f"rq_plan_ready_{index:03d}",
                case_id=obj["case_id"],
                expected_object_ids=[obj["object_id"]],
                expected_object_types=[obj["object_type"]],
                expected_topics=[obj["topic"]],
                evidence_object_id_refs=[obj["object_id"]],
                provenance_refs=[obj["provenance_ref"]],
            )
        )
    query_set_path = tmp_path / "reviewed_queries.jsonl"
    _write_jsonl(query_set_path, reviewed_rows)

    payload = _example_manifest()
    payload["reviewed_query_set"]["path"] = str(query_set_path)
    payload["reviewed_query_set"]["reviewed"] = True
    payload["reviewed_query_set"]["smoke_only"] = False
    payload["reviewed_query_set"]["review_stage"] = "reviewed"
    payload["reviewed_query_set"]["reviewer"] = "reviewer_r7"
    payload["reviewed_query_set"]["approval_id"] = "approval_pending_fixture"
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "bakeoff_plan.json"),
        "markdown_report": str(tmp_path / "bakeoff_plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    summary = plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)

    assert summary["query_set_readiness_status"] == REVIEWED_QUERY_SET_STATUS_BENCHMARK_READY_INPUTS_ONLY
    assert summary["benchmark_ready_query_set"] is True
    assert summary["provider_slots"] == ["local_stub"]
    assert summary["real_benchmark_allowed"] is False
    assert summary["provider_benchmark_complete"] is False
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False


def test_no_raw_text_in_reviewed_query_reports(tmp_path: Path) -> None:
    payload = _example_manifest()
    payload["reviewed_query_set"]["path"] = str(TEMPLATE_QUERY_SET_PATH)
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "bakeoff_plan.json"),
        "markdown_report": str(tmp_path / "bakeoff_plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)
    report_json = (tmp_path / "bakeoff_plan.json").read_text(encoding="utf-8")
    report_md = (tmp_path / "bakeoff_plan.md").read_text(encoding="utf-8")

    forbidden_terms = ["raw_text", "chunk_text", "evidence_text", "answer_text", "embedding_values", "provider_response"]
    for term in forbidden_terms:
        assert f'"{term}"' not in report_json
        assert f"{term}:" not in report_md
