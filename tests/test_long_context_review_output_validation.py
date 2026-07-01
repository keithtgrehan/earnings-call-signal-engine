from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from signal_engine.retrieval.long_context_review_output import (
    LONG_CONTEXT_REVIEW_OUTPUT_STATUS_LABEL,
    REVIEW_OUTPUT_VALIDATION_INDEX_STATUS_LABEL,
    REVIEW_OUTPUT_VALIDATION_STATUS_LABEL,
    batch_validate_long_context_review_outputs,
    validate_long_context_review_output_file,
)
from tools.validate_long_context_review_output import main as review_output_cli


BUNDLE_PATH = Path("reports/case_bundles/hd_2025_q4.case_review_bundle.json")
PROMPT_PACK_PATH = Path("reports/long_context/hd_2025_q4.prompt_pack.json")
SAMPLE_ABSTAIN_PATH = Path("data/retrieval/long_context_review_output.sample_abstain.json")
SAMPLE_METADATA_PATH = Path("data/retrieval/long_context_review_output.sample_metadata_only.json")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(tmp_path: Path, payload: dict[str, Any], name: str = "candidate.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def test_valid_abstention_sample_passes_and_writes_honest_report(tmp_path: Path) -> None:
    md_out = tmp_path / "HD_2025_Q4.review_output_validation.md"
    json_out = tmp_path / "HD_2025_Q4.review_output_validation.json"

    summary = validate_long_context_review_output_file(
        review_output_path=SAMPLE_ABSTAIN_PATH,
        prompt_pack_path=PROMPT_PACK_PATH,
        bundle_path=BUNDLE_PATH,
        out_path=md_out,
        json_out_path=json_out,
    )

    assert summary["status_label"] == REVIEW_OUTPUT_VALIDATION_STATUS_LABEL
    assert summary["review_output_status_label"] == LONG_CONTEXT_REVIEW_OUTPUT_STATUS_LABEL
    assert summary["validation_status"] == "passed"
    assert summary["case_id"] == "hd_2025_q4"
    assert summary["record_count"] == 1
    assert summary["cited_object_count"] == 0
    assert summary["cited_provenance_count"] == 0
    assert summary["abstention_count"] == 1
    assert summary["unsupported_claim_count"] == 0
    assert summary["raw_text_risk"] is False
    assert summary["provider_execution"] is False
    assert summary["llm_called_by_this_tool"] is False
    assert summary["evaluated_model_quality"] is False
    assert summary["benchmark_complete"] is False
    assert summary["production_claims"] is False
    assert md_out.exists()
    assert json_out.exists()


def test_valid_metadata_only_output_passes_with_citations() -> None:
    summary = validate_long_context_review_output_file(
        review_output_path=SAMPLE_METADATA_PATH,
        prompt_pack_path=PROMPT_PACK_PATH,
        bundle_path=BUNDLE_PATH,
    )

    assert summary["validation_status"] == "passed"
    assert summary["cited_object_count"] == 1
    assert summary["cited_provenance_count"] == 1
    assert summary["abstention_count"] == 0


def test_missing_cited_object_ref_fails(tmp_path: Path) -> None:
    payload = _load_json(SAMPLE_METADATA_PATH)
    payload["cited_object_refs"] = ["rom_evidence_0000000000000000"]
    payload["conclusions"][0]["cited_object_refs"] = ["rom_evidence_0000000000000000"]

    with pytest.raises(ValueError, match="unknown cited_object_ref"):
        validate_long_context_review_output_file(
            review_output_path=_write_payload(tmp_path, payload),
            prompt_pack_path=PROMPT_PACK_PATH,
            bundle_path=BUNDLE_PATH,
        )


def test_missing_provenance_ref_fails(tmp_path: Path) -> None:
    payload = _load_json(SAMPLE_METADATA_PATH)
    payload["cited_provenance_refs"] = ["missing/provenance/ref.json"]
    payload["conclusions"][0]["cited_provenance_refs"] = ["missing/provenance/ref.json"]

    with pytest.raises(ValueError, match="unknown cited_provenance_ref"):
        validate_long_context_review_output_file(
            review_output_path=_write_payload(tmp_path, payload),
            prompt_pack_path=PROMPT_PACK_PATH,
            bundle_path=BUNDLE_PATH,
        )


def test_uncited_conclusion_fails(tmp_path: Path) -> None:
    payload = _load_json(SAMPLE_METADATA_PATH)
    payload["conclusions"][0]["cited_object_refs"] = []
    payload["conclusions"][0]["cited_provenance_refs"] = []

    with pytest.raises(ValueError, match="uncited conclusion"):
        validate_long_context_review_output_file(
            review_output_path=_write_payload(tmp_path, payload),
            prompt_pack_path=PROMPT_PACK_PATH,
            bundle_path=BUNDLE_PATH,
        )


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("raw_text", "forbidden"),
        ("provider_response", "provider/model output key"),
        ("chain_of_thought", "chain-of-thought"),
    ],
)
def test_raw_provider_and_chain_of_thought_fields_fail(tmp_path: Path, field: str, message: str) -> None:
    payload = _load_json(SAMPLE_METADATA_PATH)
    payload[field] = "blocked"

    with pytest.raises(ValueError, match=message):
        validate_long_context_review_output_file(
            review_output_path=_write_payload(tmp_path, payload),
            prompt_pack_path=PROMPT_PACK_PATH,
            bundle_path=BUNDLE_PATH,
        )


@pytest.mark.parametrize(
    "unsafe_statement",
    [
        "This supports a buy recommendation.",
        "This creates alpha.",
        "This has statistical significance.",
        "This is production RAG.",
        "This proves evaluated model quality.",
    ],
)
def test_unsafe_claim_wording_fails(tmp_path: Path, unsafe_statement: str) -> None:
    payload = _load_json(SAMPLE_METADATA_PATH)
    payload["conclusions"][0]["statement"] = unsafe_statement

    with pytest.raises(ValueError, match="unsupported claim"):
        validate_long_context_review_output_file(
            review_output_path=_write_payload(tmp_path, payload),
            prompt_pack_path=PROMPT_PACK_PATH,
            bundle_path=BUNDLE_PATH,
        )


def test_wrong_case_id_fails(tmp_path: Path) -> None:
    payload = _load_json(SAMPLE_METADATA_PATH)
    payload["case_id"] = "wrong_case"

    with pytest.raises(ValueError, match="case_id must match"):
        validate_long_context_review_output_file(
            review_output_path=_write_payload(tmp_path, payload),
            prompt_pack_path=PROMPT_PACK_PATH,
            bundle_path=BUNDLE_PATH,
        )


def test_batch_validation_index_builds_and_stays_scaffold_only(tmp_path: Path) -> None:
    index = batch_validate_long_context_review_outputs(
        samples_dir=Path("data/retrieval"),
        prompt_pack_dir=Path("reports/long_context"),
        bundle_dir=Path("reports/case_bundles"),
        out_dir=tmp_path,
    )

    assert index["status_label"] == REVIEW_OUTPUT_VALIDATION_INDEX_STATUS_LABEL
    assert index["validation_status"] == "passed"
    assert index["sample_validation_count"] == 2
    assert index["passed_count"] == 2
    assert index["provider_execution"] is False
    assert index["llm_called_by_this_tool"] is False
    assert index["model_output_present"] is False
    assert index["evaluated_model_quality"] is False
    assert index["benchmark_complete"] is False
    assert index["production_claims"] is False
    assert (tmp_path / "long_context_review_output_validation_index.json").exists()
    assert (tmp_path / "long_context_review_output_validation_index.md").exists()


def test_cli_single_and_batch_modes_accept_uppercase_case_paths(tmp_path: Path) -> None:
    single_md = tmp_path / "HD_2025_Q4.review_output_validation.md"
    single_json = tmp_path / "HD_2025_Q4.review_output_validation.json"
    assert (
        review_output_cli(
            [
                "--review-output",
                str(SAMPLE_ABSTAIN_PATH),
                "--prompt-pack",
                "reports/long_context/HD_2025_Q4.prompt_pack.json",
                "--bundle",
                "reports/case_bundles/HD_2025_Q4.case_review_bundle.json",
                "--out",
                str(single_md),
                "--json-out",
                str(single_json),
            ]
        )
        == 0
    )
    assert review_output_cli(
        [
            "--all-samples",
            "data/retrieval",
            "--prompt-pack-dir",
            "reports/long_context",
            "--bundle-dir",
            "reports/case_bundles",
            "--out-dir",
            str(tmp_path / "batch"),
        ]
    ) == 0

    generated_names = {path.name.lower() for path in (tmp_path / "batch").iterdir()}
    assert not any("embedding" in name for name in generated_names)
    assert not any("vector" in name for name in generated_names)
    assert not any("provider_artifact" in name for name in generated_names)
