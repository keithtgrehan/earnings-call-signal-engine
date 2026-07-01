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
from signal_engine.retrieval.long_context_prompt_pack import (
    LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL,
    validate_long_context_prompt_pack_file,
)
from signal_engine.retrieval.providers.safety import validate_provider_output_payload
from signal_engine.retrieval.reviewed_query_set import OVERCLAIM_TEXT_RE

LONG_CONTEXT_REVIEW_OUTPUT_STATUS_LABEL = "long_context_review_output_candidate_metadata_only"
REVIEW_OUTPUT_VALIDATION_STATUS_LABEL = "long_context_review_output_validation_only"
REVIEW_OUTPUT_VALIDATION_INDEX_STATUS_LABEL = "long_context_review_output_validation_index_only"

ALLOWED_REVIEWER_CONFIDENCE = {"low", "medium", "high"}
REVIEW_OUTPUT_REQUIRED_FIELDS = {
    "review_output_id",
    "generated_at",
    "status_label",
    "case_id",
    "reviewer_model_slot",
    "reviewed_bundle_id",
    "source_prompt_pack_id",
    "summary",
    "conclusions",
    "cited_object_refs",
    "cited_provenance_refs",
    "detected_issues",
    "uncertainty_flags",
    "extraction_disagreements",
    "hallucination_risk_notes",
    "reviewer_confidence",
    "abstentions",
    "cannot_answer_reasons",
    "provider_execution",
    "llm_called_by_this_tool",
    "model_output_present",
    "evaluated_model_quality",
    "benchmark_complete",
    "production_claims",
    "sample_only",
}
CONCLUSION_REQUIRED_FIELDS = {
    "conclusion_id",
    "statement",
    "cited_object_refs",
    "cited_provenance_refs",
    "abstained",
}
ABSTENTION_REQUIRED_FIELDS = {"abstention_id", "reason", "cited_object_refs", "cited_provenance_refs"}
FORBIDDEN_REVIEW_OUTPUT_KEYS = {
    "provider_response",
    "provider_output",
    "provider_outputs",
    "raw_provider_response",
    "model_output",
    "model_outputs",
    "raw_model_output",
    "llm_response",
    "llm_output",
    "completion",
    "completion_text",
    "generated_answer",
    "prompt_text",
    "system_prompt",
    "user_prompt",
    "chain_of_thought",
    "cot",
    "reasoning_trace",
    "scratchpad",
    "tool_trace",
}
OVERCLAIM_VALUE_RE = re.compile(
    r"\b(production\s+rag|evaluated\s+rag|production\s+retrieval|benchmark\s+result|benchmark\s+score|"
    r"provider\s+ranking|evaluated\s+model\s+quality|model-quality\s+claim|production\s+model)\b",
    re.IGNORECASE,
)
FORBIDDEN_REVIEW_OUTPUT_NAME_RE = re.compile(
    r"(embedding|embeddings|vector|vectors|indexstore|faiss|chroma|lancedb|provider_artifact|model_output)",
    re.IGNORECASE,
)


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def resolve_existing_path(path: Path) -> Path:
    if path.exists():
        return path
    lower_name = path.with_name(path.name.lower())
    if lower_name.exists():
        return lower_name
    raise ValueError(f"path does not exist: {path}")


def _validate_output_path(path: Path, *, suffixes: set[str], role: str) -> None:
    if path.suffix.lower() not in suffixes:
        raise ValueError(f"{role} output must use one of: {', '.join(sorted(suffixes))}")
    if FORBIDDEN_REVIEW_OUTPUT_NAME_RE.search(path.name):
        raise ValueError(f"{role} output filename suggests generated provider/model/vector artifacts: {path.name}")


def _compact_key(value: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return re.sub(r"[^a-z0-9]", "", snake)


def _walk_strings(value: Any, *, path: str = "") -> list[tuple[str, str]]:
    strings: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            strings.extend(_walk_strings(nested, path=f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            strings.extend(_walk_strings(nested, path=f"{path}[{index}]"))
    elif isinstance(value, str):
        strings.append((path, value))
    return strings


def _forbidden_review_output_key_errors(payload: Any, *, context: str) -> list[str]:
    errors: list[str] = []
    forbidden = {_compact_key(key) for key in FORBIDDEN_REVIEW_OUTPUT_KEYS}
    chain_keys = {"chainofthought", "cot", "reasoningtrace", "scratchpad", "tooltrace"}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                compact = _compact_key(str(key))
                if compact in chain_keys:
                    errors.append(f"{context}: chain-of-thought or trace field is not allowed at {key_path}")
                elif compact in forbidden:
                    errors.append(f"{context}: forbidden provider/model output key {key_path}")
                visit(nested, key_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")
    return errors


def _payload_safety_errors(payload: Any, *, context: str) -> list[str]:
    errors = validate_provider_output_payload(payload, context=context)
    errors.extend(validate_no_forbidden_payload_keys(payload, context=context))
    errors.extend(validate_no_raw_text_like_values(payload, context=context))
    errors.extend(_forbidden_review_output_key_errors(payload, context=context))
    for path, value in _walk_strings(payload):
        claim_errors = validate_claim_safety_text(value)
        if claim_errors or OVERCLAIM_TEXT_RE.search(value) or OVERCLAIM_VALUE_RE.search(value):
            errors.append(f"{context}: unsupported claim at {path}")
    return errors


def _load_review_output_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"review output path does not exist: {path}")
    if path.suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            records.append(payload)
        if not records:
            raise ValueError(f"{path}: no review output records found")
        return records
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        if not payload:
            raise ValueError(f"{path}: no review output records found")
        return payload
    raise ValueError(f"{path}: expected JSON object, JSON array of objects, or JSONL objects")


def _load_context(*, prompt_pack_path: Path, bundle_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt_summary = validate_long_context_prompt_pack_file(prompt_pack_path)
    if prompt_summary["status_label"] != LONG_CONTEXT_PROMPT_PACK_STATUS_LABEL:
        raise ValueError("review output validation requires a single prompt-pack JSON")
    bundle_summary = validate_case_review_bundle_file(bundle_path)
    if bundle_summary["status_label"] != CASE_BUNDLE_STATUS_LABEL:
        raise ValueError("review output validation requires a single case bundle JSON")
    prompt_pack = json.loads(prompt_pack_path.read_text(encoding="utf-8"))
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if prompt_pack["case_id"] != bundle["case_id"]:
        raise ValueError("prompt pack case_id must match bundle case_id")
    if prompt_pack["source_bundle_id"] != bundle["bundle_id"]:
        raise ValueError("prompt pack source_bundle_id must match bundle bundle_id")
    return prompt_pack, bundle


def _string_list(payload: dict[str, Any], field: str, errors: list[str], *, context: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{context}.{field} must be an array of strings")
        return []
    return value


def _validate_ref_list(
    refs: list[str],
    *,
    known_refs: set[str],
    label: str,
    context: str,
    errors: list[str],
) -> None:
    for ref in refs:
        if ref not in known_refs:
            errors.append(f"{context}: unknown {label} {ref}")


def _validate_conclusions(
    payload: dict[str, Any],
    *,
    known_object_ids: set[str],
    known_provenance_refs: set[str],
    errors: list[str],
) -> int:
    conclusions = payload.get("conclusions")
    if not isinstance(conclusions, list):
        errors.append("conclusions must be an array")
        return 0
    uncited_count = 0
    for index, conclusion in enumerate(conclusions, start=1):
        context = f"conclusions[{index}]"
        if not isinstance(conclusion, dict):
            errors.append(f"{context} must be an object")
            continue
        keys = set(conclusion)
        for field in sorted(CONCLUSION_REQUIRED_FIELDS - keys):
            errors.append(f"{context}: missing required field {field}")
        for field in sorted(keys - CONCLUSION_REQUIRED_FIELDS):
            errors.append(f"{context}: unexpected field {field}")
        if errors and not CONCLUSION_REQUIRED_FIELDS <= keys:
            continue
        statement = conclusion.get("statement")
        if not isinstance(statement, str):
            errors.append(f"{context}.statement must be a string")
            statement = ""
        object_refs = _string_list(conclusion, "cited_object_refs", errors, context=context)
        provenance_refs = _string_list(conclusion, "cited_provenance_refs", errors, context=context)
        abstained = conclusion.get("abstained")
        if not isinstance(abstained, bool):
            errors.append(f"{context}.abstained must be a boolean")
            abstained = False
        _validate_ref_list(
            object_refs,
            known_refs=known_object_ids,
            label="cited_object_ref",
            context=context,
            errors=errors,
        )
        _validate_ref_list(
            provenance_refs,
            known_refs=known_provenance_refs,
            label="cited_provenance_ref",
            context=context,
            errors=errors,
        )
        if statement.strip() and not abstained and (not object_refs or not provenance_refs):
            uncited_count += 1
            errors.append(f"{context}: uncited conclusion requires object and provenance citations")
    return uncited_count


def _validate_abstentions(
    payload: dict[str, Any],
    *,
    known_object_ids: set[str],
    known_provenance_refs: set[str],
    errors: list[str],
) -> int:
    abstentions = payload.get("abstentions")
    if not isinstance(abstentions, list):
        errors.append("abstentions must be an array")
        return 0
    for index, abstention in enumerate(abstentions, start=1):
        context = f"abstentions[{index}]"
        if not isinstance(abstention, dict):
            errors.append(f"{context} must be an object")
            continue
        keys = set(abstention)
        for field in sorted(ABSTENTION_REQUIRED_FIELDS - keys):
            errors.append(f"{context}: missing required field {field}")
        for field in sorted(keys - ABSTENTION_REQUIRED_FIELDS):
            errors.append(f"{context}: unexpected field {field}")
        if not ABSTENTION_REQUIRED_FIELDS <= keys:
            continue
        if not isinstance(abstention.get("abstention_id"), str) or not abstention["abstention_id"].strip():
            errors.append(f"{context}.abstention_id must be a non-empty string")
        if not isinstance(abstention.get("reason"), str) or not abstention["reason"].strip():
            errors.append(f"{context}.reason must be a non-empty string")
        object_refs = _string_list(abstention, "cited_object_refs", errors, context=context)
        provenance_refs = _string_list(abstention, "cited_provenance_refs", errors, context=context)
        _validate_ref_list(
            object_refs,
            known_refs=known_object_ids,
            label="cited_object_ref",
            context=context,
            errors=errors,
        )
        _validate_ref_list(
            provenance_refs,
            known_refs=known_provenance_refs,
            label="cited_provenance_ref",
            context=context,
            errors=errors,
        )
    return len(abstentions)


def validate_review_output_record(
    payload: dict[str, Any],
    *,
    prompt_pack: dict[str, Any],
    bundle: dict[str, Any],
) -> tuple[list[str], dict[str, int]]:
    errors = _payload_safety_errors(payload, context="long-context review output")
    keys = set(payload)
    for field in sorted(REVIEW_OUTPUT_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - REVIEW_OUTPUT_REQUIRED_FIELDS):
        errors.append(f"unexpected field {field}")
    if errors:
        return errors, {"abstention_count": 0, "uncited_conclusion_count": 0}

    for field in (
        "review_output_id",
        "generated_at",
        "status_label",
        "case_id",
        "reviewer_model_slot",
        "reviewed_bundle_id",
        "source_prompt_pack_id",
        "summary",
    ):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if payload.get("status_label") != LONG_CONTEXT_REVIEW_OUTPUT_STATUS_LABEL:
        errors.append(f"status_label must be {LONG_CONTEXT_REVIEW_OUTPUT_STATUS_LABEL}")
    if payload.get("case_id") != bundle["case_id"] or payload.get("case_id") != prompt_pack["case_id"]:
        errors.append("case_id must match prompt pack and bundle")
    if payload.get("reviewed_bundle_id") != bundle["bundle_id"]:
        errors.append("reviewed_bundle_id must match bundle_id")
    if payload.get("source_prompt_pack_id") != prompt_pack["prompt_pack_id"]:
        errors.append("source_prompt_pack_id must match prompt_pack_id")
    if payload.get("reviewer_confidence") not in ALLOWED_REVIEWER_CONFIDENCE:
        errors.append("reviewer_confidence must be one of: high, low, medium")
    for field in (
        "provider_execution",
        "llm_called_by_this_tool",
        "model_output_present",
        "evaluated_model_quality",
        "benchmark_complete",
        "production_claims",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    if payload.get("sample_only") is not True:
        errors.append("sample_only must be true for committed sample outputs")

    known_object_ids = {ref["object_id"] for ref in bundle["retrieval_object_refs"]}
    known_provenance_refs = set(bundle["provenance_refs"])
    cited_object_refs = _string_list(payload, "cited_object_refs", errors, context="review output")
    cited_provenance_refs = _string_list(payload, "cited_provenance_refs", errors, context="review output")
    _validate_ref_list(
        cited_object_refs,
        known_refs=known_object_ids,
        label="cited_object_ref",
        context="review output",
        errors=errors,
    )
    _validate_ref_list(
        cited_provenance_refs,
        known_refs=known_provenance_refs,
        label="cited_provenance_ref",
        context="review output",
        errors=errors,
    )
    for field in (
        "detected_issues",
        "uncertainty_flags",
        "extraction_disagreements",
        "hallucination_risk_notes",
        "cannot_answer_reasons",
    ):
        _string_list(payload, field, errors, context="review output")
    uncited_count = _validate_conclusions(
        payload,
        known_object_ids=known_object_ids,
        known_provenance_refs=known_provenance_refs,
        errors=errors,
    )
    abstention_count = _validate_abstentions(
        payload,
        known_object_ids=known_object_ids,
        known_provenance_refs=known_provenance_refs,
        errors=errors,
    )
    if not payload.get("conclusions") and abstention_count == 0:
        errors.append("review output must include conclusions or explicit abstentions")
    if abstention_count > 0 and not payload.get("cannot_answer_reasons"):
        errors.append("cannot_answer_reasons must be present when abstentions are present")
    return errors, {"abstention_count": abstention_count, "uncited_conclusion_count": uncited_count}


def _summary_for_records(
    *,
    records: list[dict[str, Any]],
    prompt_pack: dict[str, Any],
    bundle: dict[str, Any],
    review_output_path: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    abstention_count = 0
    unsupported_claim_count = 0
    for index, record in enumerate(records, start=1):
        record_errors, counters = validate_review_output_record(record, prompt_pack=prompt_pack, bundle=bundle)
        for error in record_errors:
            if "unsupported claim" in error:
                unsupported_claim_count += 1
            errors.append(f"record {index}: {error}")
        abstention_count += counters["abstention_count"]
    cited_object_refs = sorted(
        {
            ref
            for record in records
            for ref in record.get("cited_object_refs", [])
            if isinstance(ref, str)
        }
    )
    cited_provenance_refs = sorted(
        {
            ref
            for record in records
            for ref in record.get("cited_provenance_refs", [])
            if isinstance(ref, str)
        }
    )
    base_summary = {
        "generated_at": STABLE_GENERATED_AT,
        "status_label": REVIEW_OUTPUT_VALIDATION_STATUS_LABEL,
        "review_output_status_label": LONG_CONTEXT_REVIEW_OUTPUT_STATUS_LABEL,
        "validation_status": "passed" if not errors else "failed",
        "review_output_path": _display_path(review_output_path),
        "case_id": bundle["case_id"],
        "reviewed_bundle_id": bundle["bundle_id"],
        "prompt_pack_id": prompt_pack["prompt_pack_id"],
        "record_count": len(records),
        "cited_object_count": len(cited_object_refs),
        "cited_provenance_count": len(cited_provenance_refs),
        "abstention_count": abstention_count,
        "unsupported_claim_count": unsupported_claim_count,
        "raw_text_risk": False,
        "provider_execution": False,
        "llm_called_by_this_tool": False,
        "model_output_present": False,
        "evaluated_model_quality": False,
        "benchmark_complete": False,
        "production_claims": False,
        "errors": errors,
    }
    report_errors = _payload_safety_errors(base_summary, context="long-context review output validation summary")
    if report_errors:
        raise ValueError("; ".join(report_errors))
    return base_summary


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _validate_output_path(path, suffixes={".json"}, role="review output validation JSON")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    _validate_output_path(path, suffixes={".md"}, role="review output validation Markdown")
    lines = [
        f"# Long-Context Review Output Validation: {payload['case_id']}",
        "",
        "## Status",
        f"- validation status: `{payload['validation_status']}`",
        f"- status label: `{payload['status_label']}`",
        f"- review output status: `{payload['review_output_status_label']}`",
        f"- provider execution: `{str(payload['provider_execution']).lower()}`",
        f"- LLM called by this tool: `{str(payload['llm_called_by_this_tool']).lower()}`",
        f"- model output present: `{str(payload['model_output_present']).lower()}`",
        f"- evaluated model quality: `{str(payload['evaluated_model_quality']).lower()}`",
        f"- benchmark complete: `{str(payload['benchmark_complete']).lower()}`",
        f"- production claims: `{str(payload['production_claims']).lower()}`",
        "",
        "## Counts",
        f"- records: `{payload['record_count']}`",
        f"- cited objects: `{payload['cited_object_count']}`",
        f"- cited provenance refs: `{payload['cited_provenance_count']}`",
        f"- abstentions: `{payload['abstention_count']}`",
        f"- unsupported claims: `{payload['unsupported_claim_count']}`",
        f"- raw text risk: `{str(payload['raw_text_risk']).lower()}`",
        "",
        "## Errors",
    ]
    if payload["errors"]:
        lines.extend(f"- `{error}`" for error in payload["errors"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundary",
            "This report validates sanitized reviewer-output structure only. It is not an LLM call, raw model output, benchmark, or quality claim.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_long_context_review_output_file(
    *,
    review_output_path: Path,
    prompt_pack_path: Path,
    bundle_path: Path,
    out_path: Path | None = None,
    json_out_path: Path | None = None,
) -> dict[str, Any]:
    review_output_path = resolve_existing_path(review_output_path)
    prompt_pack_path = resolve_existing_path(prompt_pack_path)
    bundle_path = resolve_existing_path(bundle_path)
    prompt_pack, bundle = _load_context(prompt_pack_path=prompt_pack_path, bundle_path=bundle_path)
    records = _load_review_output_records(review_output_path)
    summary = _summary_for_records(
        records=records,
        prompt_pack=prompt_pack,
        bundle=bundle,
        review_output_path=review_output_path,
    )
    if summary["errors"]:
        raise ValueError("; ".join(summary["errors"]))
    if json_out_path is not None:
        _write_json(json_out_path, summary)
    if out_path is not None:
        _write_markdown(out_path, summary)
    return summary


def _case_id_from_records(path: Path) -> str:
    records = _load_review_output_records(path)
    case_ids = {record.get("case_id") for record in records if isinstance(record.get("case_id"), str)}
    if len(case_ids) != 1:
        raise ValueError(f"{path}: expected exactly one case_id across review output records")
    return str(next(iter(case_ids)))


def _write_index_markdown(path: Path, payload: dict[str, Any]) -> None:
    _validate_output_path(path, suffixes={".md"}, role="review output validation index Markdown")
    lines = [
        "# Long-Context Review Output Validation Index",
        "",
        "## Status",
        f"- validation status: `{payload['validation_status']}`",
        f"- status label: `{payload['status_label']}`",
        f"- sample validations: `{payload['sample_validation_count']}`",
        f"- provider execution: `{str(payload['provider_execution']).lower()}`",
        f"- LLM called by this tool: `{str(payload['llm_called_by_this_tool']).lower()}`",
        f"- model output present: `{str(payload['model_output_present']).lower()}`",
        f"- evaluated model quality: `{str(payload['evaluated_model_quality']).lower()}`",
        f"- benchmark complete: `{str(payload['benchmark_complete']).lower()}`",
        f"- production claims: `{str(payload['production_claims']).lower()}`",
        "",
        "## Samples",
    ]
    for sample in payload["samples"]:
        lines.append(
            f"- `{sample['review_output_path']}` case=`{sample['case_id']}` status=`{sample['validation_status']}` "
            f"abstentions=`{sample['abstention_count']}`"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def batch_validate_long_context_review_outputs(
    *,
    samples_dir: Path,
    prompt_pack_dir: Path,
    bundle_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    samples_dir = resolve_existing_path(samples_dir)
    prompt_pack_dir = resolve_existing_path(prompt_pack_dir)
    bundle_dir = resolve_existing_path(bundle_dir)
    sample_paths = sorted(samples_dir.glob("long_context_review_output.sample_*.json")) + sorted(
        samples_dir.glob("long_context_review_output.sample_*.jsonl")
    )
    if not sample_paths:
        raise ValueError(f"no long-context review output samples found in {samples_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    samples: list[dict[str, Any]] = []
    errors: list[str] = []
    for sample_path in sample_paths:
        case_id = _case_id_from_records(sample_path)
        prompt_pack_path = prompt_pack_dir / f"{case_id}.prompt_pack.json"
        bundle_path = bundle_dir / f"{case_id}.case_review_bundle.json"
        stem = sample_path.name.removesuffix(".json").removesuffix(".jsonl")
        json_out = out_dir / f"{stem}.validation.json"
        md_out = out_dir / f"{stem}.validation.md"
        try:
            summary = validate_long_context_review_output_file(
                review_output_path=sample_path,
                prompt_pack_path=prompt_pack_path,
                bundle_path=bundle_path,
                out_path=md_out,
                json_out_path=json_out,
            )
            samples.append(summary)
        except ValueError as exc:
            errors.append(f"{sample_path}: {exc}")
    index = {
        "generated_at": STABLE_GENERATED_AT,
        "status_label": REVIEW_OUTPUT_VALIDATION_INDEX_STATUS_LABEL,
        "validation_status": "passed" if not errors else "failed",
        "sample_validation_count": len(samples),
        "passed_count": len(samples),
        "failed_count": len(errors),
        "samples": samples,
        "errors": errors,
        "provider_execution": False,
        "llm_called_by_this_tool": False,
        "model_output_present": False,
        "evaluated_model_quality": False,
        "benchmark_complete": False,
        "production_claims": False,
    }
    report_errors = _payload_safety_errors(index, context="long-context review output validation index")
    if report_errors:
        raise ValueError("; ".join(report_errors))
    if errors:
        raise ValueError("; ".join(errors))
    _write_json(out_dir / "long_context_review_output_validation_index.json", index)
    _write_index_markdown(out_dir / "long_context_review_output_validation_index.md", index)
    return index
