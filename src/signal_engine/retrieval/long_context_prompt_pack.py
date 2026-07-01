from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from signal_engine.retrieval.case_bundle import (
    CASE_BUNDLE_STATUS_LABEL,
    STABLE_GENERATED_AT,
    validate_case_review_bundle_file,
)
from signal_engine.retrieval.evaluate import (
    validate_claim_safety_text,
    validate_no_forbidden_payload_keys,
    validate_no_raw_text_like_values,
)
from signal_engine.retrieval.providers.safety import validate_provider_output_payload
from signal_engine.retrieval.reviewed_query_set import OVERCLAIM_TEXT_RE

LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL = "long_context_case_prompt_pack_scaffold_only"
LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL = "long_context_prompt_pack_index_scaffold_only"
EXPECTED_OUTPUT_SCHEMA_REF = "schemas/long_context_case_review_output.schema.json"

FORBIDDEN_PROMPT_PACK_OUTPUT_NAME_RE = re.compile(
    r"(embedding|embeddings|vector|vectors|indexstore|faiss|chroma|lancedb|provider_artifact|model_output)",
    re.IGNORECASE,
)
FORBIDDEN_PROVIDER_MODEL_KEYS = {
    "provider_response",
    "provider_output",
    "provider_outputs",
    "model_output",
    "model_outputs",
    "llm_response",
    "llm_output",
    "completion",
    "completion_text",
    "response_text",
    "generated_answer",
}
PROMPT_PACK_REQUIRED_FIELDS = {
    "prompt_pack_id",
    "generated_at",
    "status_label",
    "case_id",
    "source_case_bundle_path",
    "source_bundle_id",
    "allowed_input_refs",
    "blocked_input_types",
    "reviewer_instruction_sections",
    "expected_output_schema_ref",
    "citation_requirements",
    "faithfulness_checks",
    "overclaim_guardrails",
    "readiness_flags",
    "blocked_reasons",
    "provider_execution",
    "llm_called",
    "model_output_present",
    "evaluated_model_quality",
    "production_claims",
}
PROMPT_PACK_INDEX_REQUIRED_FIELDS = {
    "generated_at",
    "status_label",
    "prompt_pack_count",
    "case_count",
    "cases",
    "blocked_reasons",
    "provider_execution",
    "llm_called",
    "model_outputs_present",
    "evaluated_model_quality",
    "production_claims",
}


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _validate_output_path(path: Path, *, suffixes: set[str], role: str) -> None:
    if path.suffix.lower() not in suffixes:
        raise ValueError(f"{role} output must use one of: {', '.join(sorted(suffixes))}")
    if FORBIDDEN_PROMPT_PACK_OUTPUT_NAME_RE.search(path.name):
        raise ValueError(f"{role} output filename suggests generated provider/model/vector artifacts: {path.name}")


def _compact_key(value: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return re.sub(r"[^a-z0-9]", "", snake)


def _provider_model_key_errors(payload: Any, *, context: str) -> list[str]:
    errors: list[str] = []
    forbidden = {_compact_key(key) for key in FORBIDDEN_PROVIDER_MODEL_KEYS}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                if _compact_key(str(key)) in forbidden:
                    errors.append(f"{context}: forbidden provider/model output key {key_path}")
                visit(nested, key_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")
    return errors


def _payload_safety_errors(payload: dict[str, Any], *, context: str) -> list[str]:
    errors = validate_provider_output_payload(payload, context=context)
    errors.extend(validate_no_forbidden_payload_keys(payload, context=context))
    errors.extend(validate_no_raw_text_like_values(payload, context=context))
    errors.extend(_provider_model_key_errors(payload, context=context))

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)
        elif isinstance(value, str):
            errors.extend(validate_claim_safety_text(value))
            if OVERCLAIM_TEXT_RE.search(value):
                errors.append(f"{context}: production or benchmark overclaim wording is not allowed")

    visit(payload)
    return errors


def _load_case_bundle(bundle_path: Path) -> dict[str, Any]:
    if not bundle_path.exists():
        raise ValueError(f"bundle path does not exist: {bundle_path}")
    summary = validate_case_review_bundle_file(bundle_path)
    if summary["status_label"] != CASE_BUNDLE_STATUS_LABEL:
        raise ValueError("prompt packs must be built from a single case bundle JSON")
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("case bundle must contain a JSON object")
    return payload


def _allowed_input_refs(bundle: dict[str, Any], *, bundle_path: Path) -> dict[str, Any]:
    return {
        "case_bundle": {
            "bundle_id": bundle["bundle_id"],
            "case_id": bundle["case_id"],
            "path": _display_path(bundle_path),
            "status_label": bundle["status_label"],
        },
        "retrieval_object_refs": [
            {
                "object_id": ref["object_id"],
                "object_type": ref["object_type"],
                "case_id": ref["case_id"],
                "source_hash": ref["source_hash"],
                "text_hash": ref["text_hash"],
                "provenance_hash": ref["provenance_hash"],
                "provenance_ref": ref["provenance_ref"],
                "section_label": ref["section_label"],
                "speaker_role": ref["speaker_role"],
                "topic": ref["topic"],
            }
            for ref in bundle["retrieval_object_refs"]
        ],
        "reviewed_query_refs": [
            {
                "query_id": ref["query_id"],
                "query_type": ref["query_type"],
                "case_id": ref["case_id"],
                "expected_object_ids": ref["expected_object_ids"],
                "evidence_object_id_refs": ref["evidence_object_id_refs"],
                "provenance_refs": ref["provenance_refs"],
                "review_status": ref["review_status"],
                "benchmark_eligible": ref["benchmark_eligible"],
            }
            for ref in bundle["reviewed_query_refs"]
        ],
        "provenance_refs": bundle["provenance_refs"],
        "safe_report_refs": bundle["safe_report_refs"],
    }


def _reviewer_instruction_sections() -> list[dict[str, Any]]:
    return [
        {
            "section_id": "scope",
            "title": "Scope",
            "instructions": [
                "Use only the provided metadata references.",
                "Treat deterministic extraction and provenance references as canonical routing inputs.",
            ],
        },
        {
            "section_id": "citations",
            "title": "Citation Requirements",
            "instructions": [
                "Every conclusion must cite at least one object_id.",
                "Every conclusion must cite at least one provenance_ref.",
            ],
        },
        {
            "section_id": "abstention",
            "title": "Abstention",
            "instructions": [
                "Return cannot_answer_reasons when the provided refs do not support a conclusion.",
                "Do not infer from missing or unsafe evidence.",
            ],
        },
        {
            "section_id": "claim_boundaries",
            "title": "Claim Boundaries",
            "instructions": [
                "Do not make market action recommendations.",
                "Do not make return-edge or unsupported quantitative-validity claims.",
                "Do not describe this packet as deployment-grade evidence.",
            ],
        },
    ]


def _readiness_flags(bundle: dict[str, Any]) -> dict[str, bool]:
    return {
        "has_case_bundle": True,
        "has_allowed_input_refs": bool(bundle["retrieval_object_refs"]),
        "has_provenance_refs": bool(bundle["provenance_refs"]),
        "has_reviewed_query_refs": bool(bundle["reviewed_query_refs"]),
        "prompt_template_only": True,
        "provider_ready": False,
        "llm_review_ready": False,
        "benchmark_ready": False,
    }


def _blocked_reasons(bundle: dict[str, Any]) -> list[str]:
    reasons = set(bundle.get("blocked_reasons", []))
    reasons.update(
        {
            "prompt_pack_scaffold_only",
            "provider_execution_disabled",
            "llm_execution_disabled",
            "model_output_absent",
            "evaluated_model_quality_false",
        }
    )
    return sorted(reasons)


def _build_prompt_pack_from_bundle(bundle: dict[str, Any], *, bundle_path: Path) -> dict[str, Any]:
    pack = {
        "prompt_pack_id": f"long_context_prompt_pack:{bundle['case_id']}",
        "generated_at": STABLE_GENERATED_AT,
        "status_label": LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL,
        "case_id": bundle["case_id"],
        "source_case_bundle_path": _display_path(bundle_path),
        "source_bundle_id": bundle["bundle_id"],
        "allowed_input_refs": _allowed_input_refs(bundle, bundle_path=bundle_path),
        "blocked_input_types": [
            "raw_transcript_text",
            "raw_chunk_text",
            "raw_evidence_text",
            "provider_outputs",
            "model_outputs",
            "embeddings",
            "vector_store_artifacts",
            "labels_or_adjudication_rows",
        ],
        "reviewer_instruction_sections": _reviewer_instruction_sections(),
        "expected_output_schema_ref": EXPECTED_OUTPUT_SCHEMA_REF,
        "citation_requirements": [
            "cite_object_id_for_each_conclusion",
            "cite_provenance_ref_for_each_conclusion",
            "abstain_when_refs_are_missing_or_insufficient",
        ],
        "faithfulness_checks": [
            "all_claims_have_object_refs",
            "all_claims_have_provenance_refs",
            "no_conclusion_from_missing_metadata",
            "deterministic_extraction_remains_canonical",
        ],
        "overclaim_guardrails": [
            "no_market_action_recommendations",
            "no_return_edge_claims",
            "no_unsupported_quantitative_validity_claims",
            "no_production_quality_claims",
        ],
        "readiness_flags": _readiness_flags(bundle),
        "blocked_reasons": _blocked_reasons(bundle),
        "provider_execution": False,
        "llm_called": False,
        "model_output_present": False,
        "evaluated_model_quality": False,
        "production_claims": False,
    }
    errors = validate_long_context_prompt_pack_payload(pack)
    if errors:
        raise ValueError("; ".join(errors))
    return pack


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _write_pack_markdown(path: Path, pack: dict[str, Any]) -> None:
    _validate_output_path(path, suffixes={".md"}, role="prompt pack Markdown")
    lines = [
        f"# Long-Context Prompt Pack: {pack['case_id']}",
        "",
        "## Status",
        f"- status: `{pack['status_label']}`",
        f"- provider execution: `{str(pack['provider_execution']).lower()}`",
        f"- LLM called: `{str(pack['llm_called']).lower()}`",
        f"- model output present: `{str(pack['model_output_present']).lower()}`",
        f"- evaluated model quality: `{str(pack['evaluated_model_quality']).lower()}`",
        f"- production claims: `{str(pack['production_claims']).lower()}`",
        "",
        "## Inputs",
        f"- source bundle: `{pack['source_case_bundle_path']}`",
        f"- retrieval object refs: `{len(pack['allowed_input_refs']['retrieval_object_refs'])}`",
        f"- reviewed query refs: `{len(pack['allowed_input_refs']['reviewed_query_refs'])}`",
        f"- provenance refs: `{len(pack['allowed_input_refs']['provenance_refs'])}`",
        "",
        "## Citation Requirements",
    ]
    lines.extend(f"- `{item}`" for item in pack["citation_requirements"])
    lines.extend(
        [
            "",
            "## Blocked Reasons",
        ]
    )
    lines.extend(f"- `{reason}`" for reason in pack["blocked_reasons"])
    lines.extend(
        [
            "",
            "## Reviewer Note",
            "This prompt pack is a metadata-only scaffold for future bounded review. It is not a provider call, model output, benchmark, or quality claim.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_long_context_prompt_pack(*, bundle_path: Path, out_path: Path, report_path: Path) -> dict[str, Any]:
    _validate_output_path(out_path, suffixes={".json"}, role="prompt pack JSON")
    bundle = _load_case_bundle(bundle_path)
    pack = _build_prompt_pack_from_bundle(bundle, bundle_path=bundle_path)
    _write_json(out_path, pack)
    _write_pack_markdown(report_path, pack)
    return pack


def _pack_summary(pack: dict[str, Any], *, pack_path: Path, report_path: Path) -> dict[str, Any]:
    return {
        "case_id": pack["case_id"],
        "prompt_pack_id": pack["prompt_pack_id"],
        "prompt_pack_path": _display_path(pack_path),
        "report_path": _display_path(report_path),
        "readiness_status": "prompt_pack_scaffold_only",
        "blocked_reasons": pack["blocked_reasons"],
        "llm_called": False,
        "model_output_present": False,
        "provider_execution": False,
    }


def _write_index_markdown(path: Path, index: dict[str, Any]) -> None:
    _validate_output_path(path, suffixes={".md"}, role="prompt pack index Markdown")
    lines = [
        "# Long-Context Prompt Pack Index",
        "",
        "## Status",
        f"- status: `{index['status_label']}`",
        f"- prompt pack count: `{index['prompt_pack_count']}`",
        f"- case count: `{index['case_count']}`",
        f"- provider execution: `{str(index['provider_execution']).lower()}`",
        f"- LLM called: `{str(index['llm_called']).lower()}`",
        f"- model outputs present: `{str(index['model_outputs_present']).lower()}`",
        f"- evaluated model quality: `{str(index['evaluated_model_quality']).lower()}`",
        f"- production claims: `{str(index['production_claims']).lower()}`",
        "",
        "## Cases",
    ]
    for case in index["cases"]:
        lines.append(
            f"- `{case['case_id']}` readiness=`{case['readiness_status']}` "
            f"llm_called=`{str(case['llm_called']).lower()}` model_output=`{str(case['model_output_present']).lower()}`"
        )
    lines.extend(
        [
            "",
            "## Blocked Reasons",
        ]
    )
    lines.extend(f"- `{reason}`" for reason in index["blocked_reasons"])
    lines.extend(
        [
            "",
            "## Reviewer Note",
            "The index lists prompt-pack scaffolds only. It does not contain model outputs or benchmark results.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_all_long_context_prompt_packs(*, bundles_dir: Path, out_dir: Path) -> dict[str, Any]:
    if not bundles_dir.exists():
        raise ValueError(f"bundle directory does not exist: {bundles_dir}")
    bundle_paths = sorted(path for path in bundles_dir.glob("*.case_review_bundle.json") if path.is_file())
    if not bundle_paths:
        raise ValueError(f"no case review bundles found in {bundles_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    cases: list[dict[str, Any]] = []
    blocked_reasons: set[str] = set()
    for bundle_path in bundle_paths:
        bundle = _load_case_bundle(bundle_path)
        out_path = out_dir / f"{bundle['case_id']}.prompt_pack.json"
        report_path = out_dir / f"{bundle['case_id']}.prompt_pack.md"
        pack = _build_prompt_pack_from_bundle(bundle, bundle_path=bundle_path)
        _write_json(out_path, pack)
        _write_pack_markdown(report_path, pack)
        cases.append(_pack_summary(pack, pack_path=out_path, report_path=report_path))
        blocked_reasons.update(pack["blocked_reasons"])
    index = {
        "generated_at": STABLE_GENERATED_AT,
        "status_label": LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL,
        "prompt_pack_count": len(cases),
        "case_count": len(cases),
        "cases": cases,
        "blocked_reasons": sorted(blocked_reasons),
        "provider_execution": False,
        "llm_called": False,
        "model_outputs_present": False,
        "evaluated_model_quality": False,
        "production_claims": False,
    }
    errors = validate_long_context_prompt_pack_index_payload(index)
    if errors:
        raise ValueError("; ".join(errors))
    _write_json(out_dir / "long_context_prompt_pack_index.json", index)
    _write_index_markdown(out_dir / "long_context_prompt_pack_index.md", index)
    return index


def validate_long_context_prompt_pack_payload(payload: dict[str, Any]) -> list[str]:
    errors = _payload_safety_errors(payload, context="long-context prompt pack")
    keys = set(payload)
    for field in sorted(PROMPT_PACK_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - PROMPT_PACK_REQUIRED_FIELDS):
        errors.append(f"unexpected field {field}")
    if errors:
        return errors
    if payload.get("status_label") != LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL:
        errors.append(f"status_label must be {LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL}")
    if payload.get("expected_output_schema_ref") != EXPECTED_OUTPUT_SCHEMA_REF:
        errors.append(f"expected_output_schema_ref must be {EXPECTED_OUTPUT_SCHEMA_REF}")
    for field in ("provider_execution", "llm_called", "model_output_present", "evaluated_model_quality", "production_claims"):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    allowed_input_refs = payload.get("allowed_input_refs")
    if not isinstance(allowed_input_refs, dict):
        errors.append("allowed_input_refs must be an object")
        allowed_input_refs = {}
    provenance_refs = allowed_input_refs.get("provenance_refs")
    if not isinstance(provenance_refs, list) or not provenance_refs:
        errors.append("allowed_input_refs.provenance_refs must not be empty")
    if not isinstance(allowed_input_refs.get("retrieval_object_refs"), list) or not allowed_input_refs.get("retrieval_object_refs"):
        errors.append("allowed_input_refs.retrieval_object_refs must not be empty")
    citation_requirements = payload.get("citation_requirements")
    if not isinstance(citation_requirements, list) or not citation_requirements:
        errors.append("citation_requirements must not be empty")
    reviewer_sections = payload.get("reviewer_instruction_sections")
    if not isinstance(reviewer_sections, list) or not reviewer_sections:
        errors.append("reviewer_instruction_sections must not be empty")
    readiness_flags = payload.get("readiness_flags")
    if not isinstance(readiness_flags, dict):
        errors.append("readiness_flags must be an object")
    else:
        for key, value in readiness_flags.items():
            if not isinstance(value, bool):
                errors.append(f"readiness_flags.{key} must be a boolean")
        for key in ("provider_ready", "llm_review_ready", "benchmark_ready"):
            if readiness_flags.get(key) is not False:
                errors.append(f"readiness_flags.{key} must be false")
    return errors


def validate_long_context_prompt_pack_index_payload(payload: dict[str, Any]) -> list[str]:
    errors = _payload_safety_errors(payload, context="long-context prompt pack index")
    keys = set(payload)
    for field in sorted(PROMPT_PACK_INDEX_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - PROMPT_PACK_INDEX_REQUIRED_FIELDS):
        errors.append(f"unexpected field {field}")
    if errors:
        return errors
    if payload.get("status_label") != LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL:
        errors.append(f"status_label must be {LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL}")
    for field in ("provider_execution", "llm_called", "model_outputs_present", "evaluated_model_quality", "production_claims"):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be an array")
        cases = []
    if payload.get("case_count") != len(cases):
        errors.append("case_count must equal cases length")
    if payload.get("prompt_pack_count") != len(cases):
        errors.append("prompt_pack_count must equal cases length")
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        if case.get("llm_called") is not False:
            errors.append(f"cases[{index}].llm_called must be false")
        if case.get("model_output_present") is not False:
            errors.append(f"cases[{index}].model_output_present must be false")
    return errors


def validate_long_context_prompt_pack_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("prompt-pack file must contain a JSON object")
    status = payload.get("status_label")
    if status == LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL:
        errors = validate_long_context_prompt_pack_payload(payload)
        if errors:
            raise ValueError("; ".join(errors))
        return {
            "status_label": LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL,
            "case_id": payload["case_id"],
            "provider_execution": False,
            "llm_called": False,
            "model_output_present": False,
            "evaluated_model_quality": False,
        }
    if status == LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL:
        errors = validate_long_context_prompt_pack_index_payload(payload)
        if errors:
            raise ValueError("; ".join(errors))
        return {
            "status_label": LONG_CONTEXT_PROMPT_PACK_INDEX_STATUS_LABEL,
            "prompt_pack_count": payload["prompt_pack_count"],
            "case_count": payload["case_count"],
            "provider_execution": False,
            "llm_called": False,
            "model_outputs_present": False,
            "evaluated_model_quality": False,
        }
    raise ValueError(f"unsupported prompt-pack status_label {status!r}")
