from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from signal_engine.retrieval.long_context_prompt_pack import (
    LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL,
    LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL,
    build_all_long_context_prompt_packs,
    build_long_context_prompt_pack,
    validate_long_context_prompt_pack_file,
)
from tools.build_long_context_prompt_pack import main as prompt_pack_cli


CASE_BUNDLE_PATH = Path("reports/case_bundles/hd_2025_q4.case_review_bundle.json")
CASE_BUNDLE_DIR = Path("reports/case_bundles")
PROMPT_TEMPLATE_PATHS = [
    Path("docs/prompts/long_context_case_review_system_prompt.md"),
    Path("docs/prompts/long_context_case_review_user_prompt_template.md"),
    Path("docs/prompts/long_context_case_review_output_rubric.md"),
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_single_prompt_pack_builds_from_case_bundle_metadata_only(tmp_path: Path) -> None:
    out_path = tmp_path / "HD_2025_Q4.prompt_pack.json"
    report_path = tmp_path / "HD_2025_Q4.prompt_pack.md"

    pack = build_long_context_prompt_pack(
        bundle_path=CASE_BUNDLE_PATH,
        out_path=out_path,
        report_path=report_path,
    )

    assert pack["status_label"] == LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL
    assert pack["case_id"] == "hd_2025_q4"
    assert pack["source_case_bundle_path"] == str(CASE_BUNDLE_PATH)
    assert pack["expected_output_schema_ref"] == "schemas/long_context_case_review_output.schema.json"
    assert len(pack["allowed_input_refs"]["retrieval_object_refs"]) == 22
    assert len(pack["allowed_input_refs"]["reviewed_query_refs"]) == 1
    assert pack["readiness_flags"]["has_case_bundle"] is True
    assert pack["readiness_flags"]["has_provenance_refs"] is True
    assert pack["readiness_flags"]["llm_review_ready"] is False
    assert pack["readiness_flags"]["provider_ready"] is False
    assert pack["readiness_flags"]["benchmark_ready"] is False
    assert pack["provider_execution"] is False
    assert pack["llm_called"] is False
    assert pack["model_output_present"] is False
    assert pack["evaluated_model_quality"] is False
    assert pack["production_claims"] is False
    assert "model_output_absent" in pack["blocked_reasons"]
    assert "llm_execution_disabled" in pack["blocked_reasons"]
    assert out_path.exists()
    assert report_path.exists()
    encoded = json.dumps(pack, sort_keys=True).lower()
    assert '"raw_text"' not in encoded
    assert '"chunk_text"' not in encoded
    assert '"provider_response"' not in encoded
    assert '"model_output"' not in encoded


def test_all_prompt_pack_index_builds_one_pack_per_case_bundle(tmp_path: Path) -> None:
    index = build_all_long_context_prompt_packs(
        bundles_dir=CASE_BUNDLE_DIR,
        out_dir=tmp_path,
    )

    assert index["status_label"] == LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL
    assert index["case_count"] == 31
    assert index["prompt_pack_count"] == 31
    assert index["provider_execution"] is False
    assert index["llm_called"] is False
    assert index["model_outputs_present"] is False
    assert index["evaluated_model_quality"] is False
    assert index["production_claims"] is False
    assert (tmp_path / "long_context_prompt_pack_index.json").exists()
    assert (tmp_path / "long_context_prompt_pack_index.md").exists()
    assert len(list(tmp_path.glob("*.prompt_pack.json"))) == 31
    hd_summary = next(case for case in index["cases"] if case["case_id"] == "hd_2025_q4")
    assert hd_summary["readiness_status"] == "prompt_pack_scaffold_only"
    assert hd_summary["llm_called"] is False
    assert hd_summary["model_output_present"] is False


def test_missing_bundle_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bundle path does not exist"):
        build_long_context_prompt_pack(
            bundle_path=tmp_path / "missing.case_review_bundle.json",
            out_path=tmp_path / "missing.prompt_pack.json",
            report_path=tmp_path / "missing.prompt_pack.md",
        )


def test_prompt_pack_validation_accepts_valid_pack_and_index(tmp_path: Path) -> None:
    pack_path = tmp_path / "HD_2025_Q4.prompt_pack.json"
    build_long_context_prompt_pack(
        bundle_path=CASE_BUNDLE_PATH,
        out_path=pack_path,
        report_path=tmp_path / "HD_2025_Q4.prompt_pack.md",
    )
    build_all_long_context_prompt_packs(
        bundles_dir=CASE_BUNDLE_DIR,
        out_dir=tmp_path / "all",
    )

    pack_summary = validate_long_context_prompt_pack_file(pack_path)
    index_summary = validate_long_context_prompt_pack_file(tmp_path / "all" / "long_context_prompt_pack_index.json")

    assert pack_summary["status_label"] == LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL
    assert pack_summary["case_id"] == "hd_2025_q4"
    assert index_summary["status_label"] == LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL
    assert index_summary["prompt_pack_count"] == 31


def test_prompt_pack_validation_rejects_raw_provider_model_and_overclaim_payloads(tmp_path: Path) -> None:
    pack_path = tmp_path / "HD_2025_Q4.prompt_pack.json"
    build_long_context_prompt_pack(
        bundle_path=CASE_BUNDLE_PATH,
        out_path=pack_path,
        report_path=tmp_path / "HD_2025_Q4.prompt_pack.md",
    )

    raw_payload = _load_json(pack_path)
    raw_payload["allowed_input_refs"]["retrieval_object_refs"][0]["raw_text"] = "blocked"
    raw_path = tmp_path / "raw.prompt_pack.json"
    raw_path.write_text(json.dumps(raw_payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden"):
        validate_long_context_prompt_pack_file(raw_path)

    provider_payload = _load_json(pack_path)
    provider_payload["provider_response"] = {"status": "blocked"}
    provider_path = tmp_path / "provider.prompt_pack.json"
    provider_path.write_text(json.dumps(provider_payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="provider/model output key"):
        validate_long_context_prompt_pack_file(provider_path)

    model_payload = _load_json(pack_path)
    model_payload["model_output"] = "blocked"
    model_path = tmp_path / "model.prompt_pack.json"
    model_path.write_text(json.dumps(model_payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="provider/model output key"):
        validate_long_context_prompt_pack_file(model_path)

    overclaim = _load_json(pack_path)
    overclaim["evaluated_model_quality"] = True
    overclaim["readiness_flags"]["llm_review_ready"] = True
    overclaim_path = tmp_path / "overclaim.prompt_pack.json"
    overclaim_path.write_text(json.dumps(overclaim, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="evaluated_model_quality must be false"):
        validate_long_context_prompt_pack_file(overclaim_path)


def test_missing_citation_requirements_and_provenance_are_rejected(tmp_path: Path) -> None:
    pack_path = tmp_path / "HD_2025_Q4.prompt_pack.json"
    build_long_context_prompt_pack(
        bundle_path=CASE_BUNDLE_PATH,
        out_path=pack_path,
        report_path=tmp_path / "HD_2025_Q4.prompt_pack.md",
    )

    payload = _load_json(pack_path)
    payload["citation_requirements"] = []
    payload["allowed_input_refs"]["provenance_refs"] = []
    bad_path = tmp_path / "missing_citations.prompt_pack.json"
    bad_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError, match="citation_requirements must not be empty"):
        validate_long_context_prompt_pack_file(bad_path)


def test_prompt_templates_include_citation_abstention_and_claim_guardrails() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in PROMPT_TEMPLATE_PATHS)

    assert "abstain" in combined
    assert "object_id" in combined
    assert "provenance" in combined
    assert "citation" in combined
    assert "trading" in combined
    assert "alpha" in combined
    assert "statistical significance" in combined
    assert "do not paste raw transcript text" in combined


def test_prompt_pack_cli_modes_build_and_validate_without_llm_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "prompt_packs"
    assert (
        prompt_pack_cli(
            [
                "--all-bundles",
                str(CASE_BUNDLE_DIR),
                "--out-dir",
                str(out_dir),
            ]
        )
        == 0
    )
    assert prompt_pack_cli(["--validate", str(out_dir / "long_context_prompt_pack_index.json")]) == 0

    generated_names = {path.name.lower() for path in out_dir.iterdir()}
    assert not any("embedding" in name for name in generated_names)
    assert not any("vector" in name for name in generated_names)
    assert not any("provider_artifact" in name for name in generated_names)
    index = _load_json(out_dir / "long_context_prompt_pack_index.json")
    assert index["provider_execution"] is False
    assert index["llm_called"] is False
    assert index["model_outputs_present"] is False
    assert index["evaluated_model_quality"] is False
