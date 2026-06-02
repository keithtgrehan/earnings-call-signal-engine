from __future__ import annotations

import json
from pathlib import Path

from signal_engine.retrieval.bakeoff import BAKEOFF_STATUS_LABEL, load_bakeoff_manifest
from signal_engine.retrieval.long_context_review_output import REVIEW_OUTPUT_VALIDATION_STATUS_LABEL
from signal_engine.retrieval.reviewed_query_set import validate_and_summarize_reviewed_query_set
from tools.plan_retrieval_bakeoff import plan_retrieval_bakeoff
from tools.validate_long_context_review_output import validate_long_context_review_output_file
from tools.validate_retrieval_bakeoff_manifest import main as validate_bakeoff_cli


ROOT = Path(".")
OBJECTS_PATH = Path("data/retrieval/retrieval_object_metadata.jsonl")
REVIEWED_QUERY_SET_PATH = Path("data/retrieval/retrieval_reviewed_query_set.first20.reviewed_candidate.jsonl")
REVIEWED_INPUTS_MANIFEST_PATH = Path("configs/retrieval_bakeoff.first20_reviewed_inputs.example.yml")
PLAN_JSON = Path("reports/retrieval/retrieval_bakeoff_first20_reviewed_inputs_plan.json")
PLAN_MD = Path("reports/retrieval/retrieval_bakeoff_first20_reviewed_inputs_plan.md")
LONG_CONTEXT_SAMPLE = Path("data/retrieval/long_context_review_output.sample_abstain.json")
LONG_CONTEXT_PROMPT_PACK = Path("reports/long_context/hd_2025_q4.prompt_pack.json")
LONG_CONTEXT_BUNDLE = Path("reports/case_bundles/hd_2025_q4.case_review_bundle.json")


def test_reviewed_candidate_validates_as_benchmark_ready_inputs_only() -> None:
    summary = validate_and_summarize_reviewed_query_set(
        query_set_path=REVIEWED_QUERY_SET_PATH,
        objects_path=OBJECTS_PATH,
    )

    assert summary["query_count"] == 20
    assert summary["query_status_counts"] == {"reviewed": 20}
    assert summary["reviewed_eligible_query_count"] == 20
    assert summary["benchmark_threshold_met"] is True
    assert summary["query_set_readiness_status"] == "benchmark_ready_inputs_only"
    assert summary["benchmark_ready_query_set"] is True
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False
    assert summary["production_rag_claim"] is False


def test_reviewed_inputs_manifest_validates_and_points_to_reviewed_candidate() -> None:
    assert validate_bakeoff_cli(["--manifest", str(REVIEWED_INPUTS_MANIFEST_PATH)]) == 0

    manifest = load_bakeoff_manifest(REVIEWED_INPUTS_MANIFEST_PATH, root=ROOT)
    reviewed_gate = manifest.payload["reviewed_query_set"]

    assert manifest.payload["status_label"] == BAKEOFF_STATUS_LABEL
    assert reviewed_gate["path"] == str(REVIEWED_QUERY_SET_PATH)
    assert reviewed_gate["reviewed"] is True
    assert reviewed_gate["smoke_only"] is False
    assert reviewed_gate["review_stage"] == "reviewed"
    assert manifest.payload["provider_slots"] == ["local_stub"]
    assert manifest.payload["network_allowed"] is False
    assert manifest.payload["reviewer_approval"]["approved"] is False


def test_planner_reports_reviewed_inputs_ready_without_benchmark_or_provider_execution() -> None:
    summary = plan_retrieval_bakeoff(manifest_path=REVIEWED_INPUTS_MANIFEST_PATH, dry_run=True)

    assert summary["query_count"] == 20
    assert summary["reviewed_eligible_query_count"] == 20
    assert summary["benchmark_threshold_met"] is True
    assert summary["query_set_readiness_status"] == "benchmark_ready_inputs_only"
    assert summary["benchmark_ready_query_set"] is True
    assert summary["real_benchmark_allowed"] is False
    assert summary["provider_slots"] == ["local_stub"]
    assert summary["network_calls"] is False
    assert summary["embeddings_generated"] is False
    assert summary["vector_db_generated"] is False
    assert summary["benchmark_complete"] is False
    assert summary["provider_benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False
    assert summary["production_rag_claim"] is False
    assert PLAN_JSON.exists()
    assert PLAN_MD.exists()


def test_reviewed_inputs_plan_report_contains_honest_gate_wording() -> None:
    plan_retrieval_bakeoff(manifest_path=REVIEWED_INPUTS_MANIFEST_PATH, dry_run=True)

    report_md = PLAN_MD.read_text(encoding="utf-8")
    report_json = json.loads(PLAN_JSON.read_text(encoding="utf-8"))

    assert "- reviewed eligible query rows: `20`" in report_md
    assert "- benchmark_threshold_met: `true`" in report_md
    assert "- benchmark-ready inputs only: `true`" in report_md
    assert "- real_benchmark_allowed: `false`" in report_md
    assert "- benchmark complete: `false`" in report_md
    assert "- evaluated retrieval quality: `false`" in report_md
    assert report_json["reviewed_eligible_query_count"] == 20
    assert report_json["benchmark_ready_query_set"] is True
    assert report_json["benchmark_complete"] is False
    assert report_json["evaluated_retrieval_quality"] is False


def test_reviewed_inputs_plan_contains_no_provider_vector_or_model_artifacts() -> None:
    plan_retrieval_bakeoff(manifest_path=REVIEWED_INPUTS_MANIFEST_PATH, dry_run=True)
    combined = PLAN_JSON.read_text(encoding="utf-8") + "\n" + PLAN_MD.read_text(encoding="utf-8")

    forbidden_terms = [
        '"raw_text"',
        '"chunk_text"',
        '"transcript_text"',
        '"provider_response"',
        '"model_output"',
        '"embedding"',
        '"embeddings"',
        '"vector"',
        '"vectors"',
        '"vector_db"',
    ]
    for term in forbidden_terms:
        assert term not in combined


def test_long_context_review_output_validation_remains_validation_only(tmp_path: Path) -> None:
    summary = validate_long_context_review_output_file(
        review_output_path=LONG_CONTEXT_SAMPLE,
        prompt_pack_path=LONG_CONTEXT_PROMPT_PACK,
        bundle_path=LONG_CONTEXT_BUNDLE,
        out_path=tmp_path / "review_output_validation.md",
        json_out_path=tmp_path / "review_output_validation.json",
    )

    assert summary["status_label"] == REVIEW_OUTPUT_VALIDATION_STATUS_LABEL
    assert summary["validation_status"] == "passed"
    assert summary["provider_execution"] is False
    assert summary["llm_called_by_this_tool"] is False
    assert summary["evaluated_model_quality"] is False
    assert summary["benchmark_complete"] is False
    assert summary["production_claims"] is False
