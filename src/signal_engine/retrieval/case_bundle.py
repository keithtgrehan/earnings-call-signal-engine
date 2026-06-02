from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from signal_engine.retrieval.evaluate import (
    validate_claim_safety_text,
    validate_no_forbidden_payload_keys,
    validate_no_raw_text_like_values,
)
from signal_engine.retrieval.object_metadata import validate_retrieval_object_metadata_rows
from signal_engine.retrieval.providers.safety import validate_provider_output_payload
from signal_engine.retrieval.reviewed_query_set import (
    OVERCLAIM_TEXT_RE,
    read_jsonl,
    validate_reviewed_query_set_rows,
)

CASE_BUNDLE_STATUS_LABEL = "case_review_bundle_metadata_only"
CASE_BUNDLE_INDEX_STATUS_LABEL = "case_review_bundle_index_metadata_only"
STABLE_GENERATED_AT = "1970-01-01T00:00:00Z"

FORBIDDEN_CASE_BUNDLE_OUTPUT_NAME_RE = re.compile(
    r"(embedding|embeddings|vector|vectors|indexstore|faiss|chroma|lancedb|provider_artifact)",
    re.IGNORECASE,
)
SAFE_REPORT_CANDIDATES = (
    ("retrieval_object_metadata_export", "reports/retrieval/retrieval_object_metadata_export.md"),
    ("first20_review_packet", "reports/retrieval/retrieval_reviewed_query_set_first20_packet.md"),
    ("first20_bakeoff_plan", "reports/retrieval/retrieval_bakeoff_first20_review_pending_plan.md"),
    ("review_import_summary", "reports/retrieval/retrieval_review_import_summary.md"),
)
BUNDLE_REQUIRED_FIELDS = {
    "bundle_id",
    "generated_at",
    "status_label",
    "case_id",
    "ticker",
    "company",
    "fiscal_period",
    "object_count",
    "reviewed_query_count",
    "reviewed_eligible_query_count",
    "retrieval_object_refs",
    "reviewed_query_refs",
    "provenance_refs",
    "safe_report_refs",
    "readiness_flags",
    "blocked_reasons",
    "no_raw_text",
    "provider_execution",
    "embeddings_generated",
    "vector_db_generated",
    "evaluated_retrieval_quality",
    "production_claims",
}
INDEX_REQUIRED_FIELDS = {
    "generated_at",
    "status_label",
    "case_count",
    "bundle_count",
    "object_count",
    "reviewed_query_count",
    "reviewed_eligible_query_count",
    "cases",
    "blocked_reasons",
    "no_raw_text",
    "provider_execution",
    "embeddings_generated",
    "vector_db_generated",
    "evaluated_retrieval_quality",
    "production_claims",
}


def normalize_case_id(case_id: str) -> str:
    return case_id.strip().lower()


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _validate_output_path(path: Path, *, suffixes: set[str], role: str) -> None:
    if path.suffix.lower() not in suffixes:
        raise ValueError(f"{role} output must use one of: {', '.join(sorted(suffixes))}")
    if FORBIDDEN_CASE_BUNDLE_OUTPUT_NAME_RE.search(path.name):
        raise ValueError(f"{role} output filename suggests generated provider/vector artifacts: {path.name}")


def _load_validated_inputs(
    *,
    objects_path: Path,
    query_set_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    object_rows = read_jsonl(objects_path)
    object_errors = validate_retrieval_object_metadata_rows(object_rows)
    if object_errors:
        raise ValueError("; ".join(f"retrieval object metadata: {error}" for error in object_errors))
    query_rows = read_jsonl(query_set_path)
    query_errors = validate_reviewed_query_set_rows(query_rows, object_rows)
    if query_errors:
        raise ValueError("; ".join(query_errors))
    return object_rows, query_rows


def _safe_report_refs() -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for report_type, path_text in SAFE_REPORT_CANDIDATES:
        path = Path(path_text)
        refs.append({"report_type": report_type, "path": path_text, "exists": path.exists()})
    return refs


def _object_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "object_id": row["object_id"],
        "object_type": row["object_type"],
        "case_id": row["case_id"],
        "source_type": row["source_type"],
        "source_hash": row["source_hash"],
        "text_hash": row["text_hash"],
        "normalized_transcript_hash": row["normalized_transcript_hash"],
        "provenance_hash": row["provenance_hash"],
        "provenance_ref": row["provenance_ref"],
        "section_label": row["section_label"],
        "speaker_role": row["speaker_role"],
        "topic": row["topic"],
        "retrieval_priority": row["retrieval_priority"],
        "content_included": False,
        "embeddings_included": False,
        "vector_db_included": False,
    }


def _query_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_id": row["query_id"],
        "case_id": row["case_id"],
        "query_type": row["query_type"],
        "query_text_or_safe_query_label": row["query_text_or_safe_query_label"],
        "expected_object_ids": row["expected_object_ids"],
        "expected_object_types": row["expected_object_types"],
        "evidence_object_id_refs": row["evidence_object_id_refs"],
        "provenance_refs": row["provenance_refs"],
        "review_status": row["review_status"],
        "benchmark_eligible": row["benchmark_eligible"],
    }


def _case_metadata(case_objects: list[dict[str, Any]]) -> dict[str, str]:
    first = case_objects[0]
    return {
        "ticker": str(first.get("ticker", "")),
        "company": str(first.get("company", "")),
        "fiscal_period": str(first.get("fiscal_period", "")),
    }


def _readiness_flags(
    *,
    object_count: int,
    query_count: int,
    reviewed_eligible_count: int,
    pending_count: int,
) -> dict[str, bool]:
    return {
        "has_retrieval_objects": object_count > 0,
        "has_reviewed_query_rows": query_count > 0,
        "has_reviewed_eligible_query_rows": reviewed_eligible_count > 0,
        "review_pending": pending_count > 0,
        "benchmark_ready": False,
        "llm_review_ready": False,
        "provider_ready": False,
    }


def _blocked_reasons(
    *,
    object_count: int,
    query_count: int,
    reviewed_eligible_count: int,
    pending_count: int,
) -> list[str]:
    reasons: list[str] = []
    if object_count == 0:
        reasons.append("no_retrieval_objects_for_case")
    if query_count == 0:
        reasons.append("no_reviewed_query_rows_for_case")
    if pending_count > 0:
        reasons.append("reviewed_queries_pending")
    if reviewed_eligible_count == 0:
        reasons.append("no_benchmark_eligible_query_rows")
    reasons.extend(
        [
            "benchmark_threshold_not_met",
            "provider_execution_disabled",
            "llm_review_disabled",
            "evaluated_retrieval_quality_false",
        ]
    )
    return sorted(set(reasons))


def _build_bundle_from_rows(
    *,
    case_id: str,
    object_rows: list[dict[str, Any]],
    query_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    canonical_case_id = normalize_case_id(case_id)
    case_objects = sorted(
        [row for row in object_rows if row.get("case_id") == canonical_case_id],
        key=lambda row: (int(row.get("retrieval_priority", 999)), str(row.get("object_id", ""))),
    )
    case_queries = sorted(
        [row for row in query_rows if row.get("case_id") == canonical_case_id],
        key=lambda row: str(row.get("query_id", "")),
    )
    if not case_objects:
        raise ValueError(f"unknown case_id {case_id!r}: no retrieval objects found")

    object_refs = [_object_ref(row) for row in case_objects]
    query_refs = [_query_ref(row) for row in case_queries]
    object_ids = {row["object_id"] for row in object_refs}
    for query_ref in query_refs:
        for object_id in query_ref["expected_object_ids"] + query_ref["evidence_object_id_refs"]:
            if object_id not in object_ids:
                raise ValueError(f"query {query_ref['query_id']} references object outside case bundle: {object_id}")
    reviewed_eligible_count = sum(1 for row in case_queries if row.get("benchmark_eligible") is True)
    pending_count = sum(1 for row in case_queries if row.get("review_status") == "review_pending")
    provenance_refs = sorted(
        {
            *[str(row["provenance_ref"]) for row in object_refs],
            *[str(ref) for row in query_refs for ref in row["provenance_refs"]],
        }
    )
    metadata = _case_metadata(case_objects)
    bundle = {
        "bundle_id": f"case_review_bundle:{canonical_case_id}",
        "generated_at": STABLE_GENERATED_AT,
        "status_label": CASE_BUNDLE_STATUS_LABEL,
        "case_id": canonical_case_id,
        "ticker": metadata["ticker"],
        "company": metadata["company"],
        "fiscal_period": metadata["fiscal_period"],
        "object_count": len(object_refs),
        "reviewed_query_count": len(query_refs),
        "reviewed_eligible_query_count": reviewed_eligible_count,
        "retrieval_object_refs": object_refs,
        "reviewed_query_refs": query_refs,
        "provenance_refs": provenance_refs,
        "safe_report_refs": _safe_report_refs(),
        "readiness_flags": _readiness_flags(
            object_count=len(object_refs),
            query_count=len(query_refs),
            reviewed_eligible_count=reviewed_eligible_count,
            pending_count=pending_count,
        ),
        "blocked_reasons": _blocked_reasons(
            object_count=len(object_refs),
            query_count=len(query_refs),
            reviewed_eligible_count=reviewed_eligible_count,
            pending_count=pending_count,
        ),
        "no_raw_text": True,
        "provider_execution": False,
        "embeddings_generated": False,
        "vector_db_generated": False,
        "evaluated_retrieval_quality": False,
        "production_claims": False,
    }
    errors = validate_case_review_bundle_payload(bundle)
    if errors:
        raise ValueError("; ".join(errors))
    return bundle


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _write_bundle_markdown(path: Path, bundle: dict[str, Any]) -> None:
    _validate_output_path(path, suffixes={".md"}, role="case bundle Markdown")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Case Review Bundle: {bundle['case_id']}",
        "",
        "## Status",
        f"- status: `{bundle['status_label']}`",
        f"- no raw text: `{str(bundle['no_raw_text']).lower()}`",
        f"- provider execution: `{str(bundle['provider_execution']).lower()}`",
        f"- embeddings generated: `{str(bundle['embeddings_generated']).lower()}`",
        f"- vector DB generated: `{str(bundle['vector_db_generated']).lower()}`",
        f"- evaluated retrieval quality: `{str(bundle['evaluated_retrieval_quality']).lower()}`",
        f"- production claims: `{str(bundle['production_claims']).lower()}`",
        "",
        "## Case",
        f"- case ID: `{bundle['case_id']}`",
        f"- ticker: `{bundle['ticker']}`",
        f"- company: `{bundle['company']}`",
        f"- fiscal period: `{bundle['fiscal_period']}`",
        "",
        "## Inventory",
        f"- retrieval objects: `{bundle['object_count']}`",
        f"- reviewed query rows: `{bundle['reviewed_query_count']}`",
        f"- benchmark-eligible query rows: `{bundle['reviewed_eligible_query_count']}`",
        f"- provenance refs: `{len(bundle['provenance_refs'])}`",
        "",
        "## Blocked Reasons",
    ]
    lines.extend(f"- `{reason}`" for reason in bundle["blocked_reasons"])
    lines.extend(
        [
            "",
            "## Safe Report Refs",
        ]
    )
    lines.extend(
        f"- `{ref['report_type']}`: `{ref['path']}` exists=`{str(ref['exists']).lower()}`"
        for ref in bundle["safe_report_refs"]
    )
    lines.extend(
        [
            "",
            "## Reviewer Note",
            "This bundle is metadata-only. It is a routing and readiness artifact for future bounded case review, not an LLM output or retrieval benchmark result.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_case_review_bundle(
    *,
    case_id: str,
    objects_path: Path,
    query_set_path: Path,
    out_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    _validate_output_path(out_path, suffixes={".json"}, role="case bundle JSON")
    object_rows, query_rows = _load_validated_inputs(objects_path=objects_path, query_set_path=query_set_path)
    bundle = _build_bundle_from_rows(case_id=case_id, object_rows=object_rows, query_rows=query_rows)
    _write_json(out_path, bundle)
    _write_bundle_markdown(report_path, bundle)
    return bundle


def _case_summary(bundle: dict[str, Any], *, bundle_path: Path, report_path: Path) -> dict[str, Any]:
    if bundle["reviewed_eligible_query_count"] > 0:
        readiness_status = "case_review_has_eligible_rows_but_provider_blocked"
    elif bundle["reviewed_query_count"] > 0:
        readiness_status = "case_review_pending_only"
    else:
        readiness_status = "case_review_no_query_rows"
    return {
        "case_id": bundle["case_id"],
        "ticker": bundle["ticker"],
        "company": bundle["company"],
        "fiscal_period": bundle["fiscal_period"],
        "object_count": bundle["object_count"],
        "reviewed_query_count": bundle["reviewed_query_count"],
        "reviewed_eligible_query_count": bundle["reviewed_eligible_query_count"],
        "readiness_status": readiness_status,
        "blocked_reasons": bundle["blocked_reasons"],
        "bundle_path": _display_path(bundle_path),
        "report_path": _display_path(report_path),
    }


def _write_index_markdown(path: Path, index: dict[str, Any]) -> None:
    _validate_output_path(path, suffixes={".md"}, role="case bundle index Markdown")
    lines = [
        "# Case Review Bundle Index",
        "",
        "## Status",
        f"- status: `{index['status_label']}`",
        f"- case count: `{index['case_count']}`",
        f"- bundle count: `{index['bundle_count']}`",
        f"- provider execution: `{str(index['provider_execution']).lower()}`",
        f"- embeddings generated: `{str(index['embeddings_generated']).lower()}`",
        f"- vector DB generated: `{str(index['vector_db_generated']).lower()}`",
        f"- evaluated retrieval quality: `{str(index['evaluated_retrieval_quality']).lower()}`",
        f"- production claims: `{str(index['production_claims']).lower()}`",
        "",
        "## Cases",
    ]
    for case in index["cases"]:
        lines.append(
            f"- `{case['case_id']}` objects=`{case['object_count']}` queries=`{case['reviewed_query_count']}` "
            f"eligible=`{case['reviewed_eligible_query_count']}` readiness=`{case['readiness_status']}`"
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
            "The index summarizes metadata-only case bundles. It does not execute providers or LLM reviewers and does not report retrieval quality.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_all_case_review_bundles(
    *,
    objects_path: Path,
    query_set_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    object_rows, query_rows = _load_validated_inputs(objects_path=objects_path, query_set_path=query_set_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    case_ids = sorted({str(row["case_id"]) for row in object_rows})
    case_summaries: list[dict[str, Any]] = []
    blocked_reasons: set[str] = set()
    totals = Counter()
    for case_id in case_ids:
        bundle_path = out_dir / f"{case_id}.case_review_bundle.json"
        report_path = out_dir / f"{case_id}.case_review_bundle.md"
        bundle = _build_bundle_from_rows(case_id=case_id, object_rows=object_rows, query_rows=query_rows)
        _write_json(bundle_path, bundle)
        _write_bundle_markdown(report_path, bundle)
        summary = _case_summary(bundle, bundle_path=bundle_path, report_path=report_path)
        case_summaries.append(summary)
        blocked_reasons.update(bundle["blocked_reasons"])
        totals["object_count"] += bundle["object_count"]
        totals["reviewed_query_count"] += bundle["reviewed_query_count"]
        totals["reviewed_eligible_query_count"] += bundle["reviewed_eligible_query_count"]

    index = {
        "generated_at": STABLE_GENERATED_AT,
        "status_label": CASE_BUNDLE_INDEX_STATUS_LABEL,
        "case_count": len(case_summaries),
        "bundle_count": len(case_summaries),
        "object_count": totals["object_count"],
        "reviewed_query_count": totals["reviewed_query_count"],
        "reviewed_eligible_query_count": totals["reviewed_eligible_query_count"],
        "cases": case_summaries,
        "blocked_reasons": sorted(blocked_reasons),
        "no_raw_text": True,
        "provider_execution": False,
        "embeddings_generated": False,
        "vector_db_generated": False,
        "evaluated_retrieval_quality": False,
        "production_claims": False,
    }
    errors = validate_case_review_bundle_index_payload(index)
    if errors:
        raise ValueError("; ".join(errors))
    _write_json(out_dir / "case_review_bundle_index.json", index)
    _write_index_markdown(out_dir / "case_review_bundle_index.md", index)
    return index


def _payload_safety_errors(payload: dict[str, Any], *, context: str) -> list[str]:
    errors = validate_provider_output_payload(payload, context=context)
    errors.extend(validate_no_forbidden_payload_keys(payload, context=context))
    errors.extend(validate_no_raw_text_like_values(payload, context=context))

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


def validate_case_review_bundle_payload(payload: dict[str, Any]) -> list[str]:
    errors = _payload_safety_errors(payload, context="case review bundle")
    keys = set(payload)
    for field in sorted(BUNDLE_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - BUNDLE_REQUIRED_FIELDS):
        errors.append(f"unexpected field {field}")
    if errors:
        return errors

    if payload.get("status_label") != CASE_BUNDLE_STATUS_LABEL:
        errors.append(f"status_label must be {CASE_BUNDLE_STATUS_LABEL}")
    for field in (
        "no_raw_text",
        "provider_execution",
        "embeddings_generated",
        "vector_db_generated",
        "evaluated_retrieval_quality",
        "production_claims",
    ):
        expected = True if field == "no_raw_text" else False
        if payload.get(field) is not expected:
            errors.append(f"{field} must be {str(expected).lower()}")
    if not isinstance(payload.get("provenance_refs"), list) or not payload["provenance_refs"]:
        errors.append("provenance_refs must not be empty")
    retrieval_object_refs = payload.get("retrieval_object_refs")
    if not isinstance(retrieval_object_refs, list) or not retrieval_object_refs:
        errors.append("retrieval_object_refs must not be empty")
        retrieval_object_refs = []
    if payload.get("object_count") != len(retrieval_object_refs):
        errors.append("object_count must equal retrieval_object_refs length")
    object_ids = set()
    for index, ref in enumerate(retrieval_object_refs, start=1):
        if not isinstance(ref, dict):
            errors.append(f"retrieval_object_refs[{index}] must be an object")
            continue
        object_id = str(ref.get("object_id", ""))
        object_ids.add(object_id)
        if ref.get("case_id") != payload.get("case_id"):
            errors.append(f"retrieval_object_refs[{index}].case_id must match bundle case_id")
        for field in ("source_hash", "text_hash", "normalized_transcript_hash", "provenance_hash", "provenance_ref"):
            if not str(ref.get(field, "")).strip():
                errors.append(f"retrieval_object_refs[{index}].{field} must be present")
        for field in ("content_included", "embeddings_included", "vector_db_included"):
            if ref.get(field) is not False:
                errors.append(f"retrieval_object_refs[{index}].{field} must be false")
    reviewed_query_refs = payload.get("reviewed_query_refs")
    if not isinstance(reviewed_query_refs, list):
        errors.append("reviewed_query_refs must be an array")
        reviewed_query_refs = []
    if payload.get("reviewed_query_count") != len(reviewed_query_refs):
        errors.append("reviewed_query_count must equal reviewed_query_refs length")
    for index, ref in enumerate(reviewed_query_refs, start=1):
        if not isinstance(ref, dict):
            errors.append(f"reviewed_query_refs[{index}] must be an object")
            continue
        if ref.get("case_id") != payload.get("case_id"):
            errors.append(f"reviewed_query_refs[{index}].case_id must match bundle case_id")
        for object_id in ref.get("expected_object_ids", []) + ref.get("evidence_object_id_refs", []):
            if object_id not in object_ids:
                errors.append(f"reviewed_query_refs[{index}] references object outside bundle: {object_id}")
        if not ref.get("provenance_refs"):
            errors.append(f"reviewed_query_refs[{index}].provenance_refs must not be empty")
    readiness_flags = payload.get("readiness_flags")
    if not isinstance(readiness_flags, dict):
        errors.append("readiness_flags must be an object")
    elif any(not isinstance(value, bool) for value in readiness_flags.values()):
        errors.append("readiness_flags values must be booleans")
    if payload.get("readiness_flags", {}).get("benchmark_ready") is not False:
        errors.append("readiness_flags.benchmark_ready must be false")
    if payload.get("readiness_flags", {}).get("llm_review_ready") is not False:
        errors.append("readiness_flags.llm_review_ready must be false")
    return errors


def validate_case_review_bundle_index_payload(payload: dict[str, Any]) -> list[str]:
    errors = _payload_safety_errors(payload, context="case review bundle index")
    keys = set(payload)
    for field in sorted(INDEX_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - INDEX_REQUIRED_FIELDS):
        errors.append(f"unexpected field {field}")
    if errors:
        return errors

    if payload.get("status_label") != CASE_BUNDLE_INDEX_STATUS_LABEL:
        errors.append(f"status_label must be {CASE_BUNDLE_INDEX_STATUS_LABEL}")
    for field in (
        "no_raw_text",
        "provider_execution",
        "embeddings_generated",
        "vector_db_generated",
        "evaluated_retrieval_quality",
        "production_claims",
    ):
        expected = True if field == "no_raw_text" else False
        if payload.get(field) is not expected:
            errors.append(f"{field} must be {str(expected).lower()}")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be an array")
        cases = []
    if payload.get("case_count") != len(cases):
        errors.append("case_count must equal cases length")
    if payload.get("bundle_count") != len(cases):
        errors.append("bundle_count must equal cases length")
    if payload.get("object_count") != sum(int(case.get("object_count", 0)) for case in cases if isinstance(case, dict)):
        errors.append("object_count must equal case object_count sum")
    if payload.get("reviewed_query_count") != sum(
        int(case.get("reviewed_query_count", 0)) for case in cases if isinstance(case, dict)
    ):
        errors.append("reviewed_query_count must equal case reviewed_query_count sum")
    if payload.get("reviewed_eligible_query_count") != sum(
        int(case.get("reviewed_eligible_query_count", 0)) for case in cases if isinstance(case, dict)
    ):
        errors.append("reviewed_eligible_query_count must equal case reviewed_eligible_query_count sum")
    return errors


def validate_case_review_bundle_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("case bundle file must contain a JSON object")
    status = payload.get("status_label")
    if status == CASE_BUNDLE_STATUS_LABEL:
        errors = validate_case_review_bundle_payload(payload)
        if errors:
            raise ValueError("; ".join(errors))
        return {
            "status_label": CASE_BUNDLE_STATUS_LABEL,
            "case_id": payload["case_id"],
            "object_count": payload["object_count"],
            "reviewed_query_count": payload["reviewed_query_count"],
            "reviewed_eligible_query_count": payload["reviewed_eligible_query_count"],
            "provider_execution": False,
            "embeddings_generated": False,
            "vector_db_generated": False,
            "evaluated_retrieval_quality": False,
        }
    if status == CASE_BUNDLE_INDEX_STATUS_LABEL:
        errors = validate_case_review_bundle_index_payload(payload)
        if errors:
            raise ValueError("; ".join(errors))
        return {
            "status_label": CASE_BUNDLE_INDEX_STATUS_LABEL,
            "case_count": payload["case_count"],
            "bundle_count": payload["bundle_count"],
            "object_count": payload["object_count"],
            "reviewed_query_count": payload["reviewed_query_count"],
            "reviewed_eligible_query_count": payload["reviewed_eligible_query_count"],
            "provider_execution": False,
            "embeddings_generated": False,
            "vector_db_generated": False,
            "evaluated_retrieval_quality": False,
        }
    raise ValueError(f"unsupported case bundle status_label {status!r}")
