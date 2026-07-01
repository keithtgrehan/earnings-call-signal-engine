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
from signal_engine.retrieval.object_metadata import (
    RETRIEVAL_OBJECT_METADATA_TYPES,
    validate_retrieval_object_metadata_rows,
)
from signal_engine.retrieval.providers.safety import validate_provider_output_payload

MIN_REVIEWED_ELIGIBLE_QUERIES = 20
REVIEWED_QUERY_SET_STATUSES = {"template_only", "smoke_only", "review_pending", "reviewed", "rejected"}
REVIEWED_QUERY_SET_QUERY_TYPES = {
    "positive_evidence_lookup",
    "metadata_category_lookup",
    "abstention_guardrail",
    "qna_abstention",
    "negative_control",
    "guidance_revision_lookup",
    "uncertainty_language_lookup",
    "analyst_pressure_lookup",
    "topic_lookup",
    "evidence_object_lookup",
    "case_comparison_lookup",
}
REVIEWED_QUERY_SET_REQUIRED_FIELDS = {
    "query_id",
    "case_id",
    "query_type",
    "query_text_or_safe_query_label",
    "expected_object_ids",
    "expected_object_types",
    "expected_topics",
    "evidence_object_id_refs",
    "provenance_refs",
    "reviewer",
    "reviewed_at",
    "review_status",
    "benchmark_eligible",
    "notes",
}
REVIEWED_QUERY_SET_STATUS_TEMPLATE_ONLY = "template_only"
REVIEWED_QUERY_SET_STATUS_SMOKE_ONLY_BLOCKED = "smoke_only_blocked"
REVIEWED_QUERY_SET_STATUS_REVIEW_PENDING_BLOCKED = "review_pending_blocked"
REVIEWED_QUERY_SET_STATUS_REVIEWED_NOT_ELIGIBLE = "reviewed_not_eligible"
REVIEWED_QUERY_SET_STATUS_REVIEWED_ELIGIBLE_BELOW_MINIMUM = "reviewed_eligible_below_minimum"
REVIEWED_QUERY_SET_STATUS_BENCHMARK_READY_INPUTS_ONLY = "benchmark_ready_inputs_only"
FORBIDDEN_REVIEWED_QUERY_KEYS = {
    "answer",
    "answer_text",
    "expected_answer",
    "gold_label",
    "gold_labels",
    "adjudication",
    "adjudication_row",
    "training_label",
    "promotion_row",
}
ANSWER_LEAKAGE_RE = re.compile(r"\b(expected\s+answer|answer\s+text|gold\s+label|adjudication|training\s+label|promotion\s+row)\b", re.IGNORECASE)
OVERCLAIM_TEXT_RE = re.compile(
    r"\b(evaluated\s+rag|production\s+rag|production\s+retrieval|provider\s+ranking|benchmark\s+result)\b",
    re.IGNORECASE,
)
ISO_LIKE_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PLACEHOLDER_RE = re.compile(r"(PLACEHOLDER|REVIEW_REQUIRED|\{[^}]+\}|reviewed_evidence_id)", re.IGNORECASE)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(row)
    return rows


def load_reviewed_query_set(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def is_reviewed_query_set_rows(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and any("review_status" in row or "expected_object_ids" in row for row in rows)


def _compact_key(value: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return re.sub(r"[^a-z0-9]", "", snake)


def _string_list(row: dict[str, Any], field: str, errors: list[str]) -> list[str]:
    value = row.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{field} must be an array of strings")
        return []
    return value


def _walk_strings(payload: Any) -> list[str]:
    values: list[str] = []
    if isinstance(payload, dict):
        for value in payload.values():
            values.extend(_walk_strings(value))
    elif isinstance(payload, list):
        for value in payload:
            values.extend(_walk_strings(value))
    elif isinstance(payload, str):
        values.append(payload)
    return values


def _placeholder_count(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        for value in _walk_strings(row):
            if PLACEHOLDER_RE.search(value):
                count += 1
    return count


def _object_index(object_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("object_id", "")): row for row in object_rows if str(row.get("object_id", "")).strip()}


def _unknown_ref_count(rows: list[dict[str, Any]], object_rows: list[dict[str, Any]]) -> int:
    objects = _object_index(object_rows)
    count = 0
    for row in rows:
        for field in ("expected_object_ids", "evidence_object_id_refs"):
            for object_id in row.get(field, []) if isinstance(row.get(field), list) else []:
                if isinstance(object_id, str) and object_id not in objects:
                    count += 1
    return count


def _reviewed_query_row_errors(
    row: dict[str, Any],
    *,
    object_rows_by_id: dict[str, dict[str, Any]],
    allow_template: bool,
) -> list[str]:
    errors = validate_provider_output_payload(row, context="reviewed query row")
    errors.extend(validate_no_forbidden_payload_keys(row, context="reviewed query row"))
    errors.extend(validate_no_raw_text_like_values(row, context="reviewed query row"))

    keys = set(row)
    for field in sorted(REVIEWED_QUERY_SET_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - REVIEWED_QUERY_SET_REQUIRED_FIELDS):
        errors.append(f"unexpected field {field}")
    forbidden_compact = {_compact_key(key) for key in FORBIDDEN_REVIEWED_QUERY_KEYS}
    for key in sorted(keys):
        if _compact_key(str(key)) in forbidden_compact:
            errors.append(f"forbidden reviewed query key {key}")
    if errors:
        return errors

    for field in ("query_id", "case_id", "query_type", "query_text_or_safe_query_label", "reviewer", "reviewed_at", "review_status", "notes"):
        if not isinstance(row.get(field), str):
            errors.append(f"{field} must be a string")
        elif field in {"query_id", "case_id", "query_type", "query_text_or_safe_query_label", "review_status"} and not row[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(row.get("benchmark_eligible"), bool):
        errors.append("benchmark_eligible must be a boolean")

    expected_object_ids = _string_list(row, "expected_object_ids", errors)
    expected_object_types = _string_list(row, "expected_object_types", errors)
    _string_list(row, "expected_topics", errors)
    evidence_refs = _string_list(row, "evidence_object_id_refs", errors)
    provenance_refs = _string_list(row, "provenance_refs", errors)

    for value in _walk_strings(row):
        errors.extend(validate_claim_safety_text(value))
        if ANSWER_LEAKAGE_RE.search(value):
            errors.append("answer leakage wording is not allowed in reviewed query rows")
        if OVERCLAIM_TEXT_RE.search(value):
            errors.append("production or benchmark overclaim wording is not allowed in reviewed query rows")

    review_status = row.get("review_status")
    if review_status not in REVIEWED_QUERY_SET_STATUSES:
        errors.append(f"invalid review_status {review_status!r}")
    query_type = row.get("query_type")
    if query_type not in REVIEWED_QUERY_SET_QUERY_TYPES:
        errors.append(f"invalid query_type {query_type!r}")
    if review_status == "template_only" and not allow_template:
        errors.append("template_only rows require --allow-template")
    if review_status in {"template_only", "smoke_only", "review_pending", "rejected"} and row.get("benchmark_eligible") is True:
        errors.append("benchmark_eligible=true requires review_status=reviewed")
    if review_status == "reviewed":
        if not str(row.get("reviewer", "")).strip():
            errors.append("reviewer must be present for reviewed rows")
        reviewed_at = str(row.get("reviewed_at", ""))
        if not reviewed_at.strip():
            errors.append("reviewed_at must be present for reviewed rows")
        elif not ISO_LIKE_UTC_RE.fullmatch(reviewed_at):
            errors.append("reviewed_at must use YYYY-MM-DDTHH:MM:SSZ format")
    elif str(row.get("reviewer", "")).strip() or str(row.get("reviewed_at", "")).strip():
        errors.append("reviewer and reviewed_at must stay empty until review_status=reviewed")

    if not expected_object_ids:
        errors.append("expected_object_ids must not be empty")
    if not provenance_refs:
        errors.append("provenance_refs must not be empty")
    for object_type in expected_object_types:
        if object_type not in RETRIEVAL_OBJECT_METADATA_TYPES:
            errors.append(f"expected_object_types contains unsupported value {object_type!r}")

    case_id = str(row.get("case_id", ""))
    expected_provenance_refs: set[str] = set()
    for object_id in expected_object_ids:
        object_row = object_rows_by_id.get(object_id)
        if object_row is None:
            errors.append(f"unknown expected_object_id {object_id}")
            continue
        if object_row.get("case_id") != case_id:
            errors.append(f"expected_object_id {object_id} does not match case_id {case_id}")
        if expected_object_types and object_row.get("object_type") not in expected_object_types:
            errors.append(f"expected_object_id {object_id} object_type is not listed in expected_object_types")
        expected_provenance_refs.add(str(object_row.get("provenance_ref", "")))
    if set(provenance_refs) != expected_provenance_refs:
        errors.append("provenance_refs must exactly match referenced expected object provenance refs")
    for object_id in evidence_refs:
        object_row = object_rows_by_id.get(object_id)
        if object_row is None:
            errors.append(f"unknown evidence_object_id_ref {object_id}")
        elif object_row.get("object_type") != "evidence_object_metadata":
            errors.append(f"evidence_object_id_ref {object_id} must reference evidence_object_metadata")
        else:
            if object_row.get("case_id") != case_id:
                errors.append(f"evidence_object_id_ref {object_id} does not match case_id {case_id}")
            if object_row.get("provenance_ref") not in provenance_refs:
                errors.append(f"evidence_object_id_ref {object_id} provenance_ref must be present")
    if _placeholder_count([row]):
        errors.append("reviewed query row contains placeholder text")
    return errors


def validate_reviewed_query_set_rows(
    rows: list[dict[str, Any]],
    object_rows: list[dict[str, Any]],
    *,
    allow_template: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not rows:
        return ["reviewed query set is empty"]
    object_errors = validate_retrieval_object_metadata_rows(object_rows)
    errors.extend(f"retrieval object metadata: {error}" for error in object_errors)
    object_rows_by_id = _object_index(object_rows)

    query_ids = Counter(str(row.get("query_id", "")) for row in rows)
    for query_id, count in sorted(query_ids.items()):
        if query_id and count > 1:
            errors.append(f"duplicate query_id {query_id}")
    for index, row in enumerate(rows, start=1):
        row_errors = _reviewed_query_row_errors(row, object_rows_by_id=object_rows_by_id, allow_template=allow_template)
        errors.extend(f"query row {index}: {error}" for error in row_errors)
    return errors


def summarize_reviewed_query_set(rows: list[dict[str, Any]], *, object_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = dict(sorted(Counter(str(row.get("review_status", "")) for row in rows).items()))
    reviewed_eligible_count = sum(
        1 for row in rows if row.get("review_status") == "reviewed" and row.get("benchmark_eligible") is True
    )
    placeholder_count = _placeholder_count(rows)
    unknown_object_ref_count = _unknown_ref_count(rows, object_rows)
    benchmark_threshold_met = (
        reviewed_eligible_count >= MIN_REVIEWED_ELIGIBLE_QUERIES
        and placeholder_count == 0
        and unknown_object_ref_count == 0
    )

    if rows and all(row.get("review_status") == "template_only" for row in rows):
        readiness_status = REVIEWED_QUERY_SET_STATUS_TEMPLATE_ONLY
    elif benchmark_threshold_met:
        readiness_status = REVIEWED_QUERY_SET_STATUS_BENCHMARK_READY_INPUTS_ONLY
    elif reviewed_eligible_count > 0:
        readiness_status = REVIEWED_QUERY_SET_STATUS_REVIEWED_ELIGIBLE_BELOW_MINIMUM
    elif any(row.get("review_status") == "smoke_only" for row in rows):
        readiness_status = REVIEWED_QUERY_SET_STATUS_SMOKE_ONLY_BLOCKED
    elif any(row.get("review_status") == "review_pending" for row in rows):
        readiness_status = REVIEWED_QUERY_SET_STATUS_REVIEW_PENDING_BLOCKED
    else:
        readiness_status = REVIEWED_QUERY_SET_STATUS_REVIEWED_NOT_ELIGIBLE

    return {
        "query_set_readiness_status": readiness_status,
        "query_count": len(rows),
        "query_status_counts": status_counts,
        "reviewed_eligible_query_count": reviewed_eligible_count,
        "minimum_reviewed_eligible_queries": MIN_REVIEWED_ELIGIBLE_QUERIES,
        "benchmark_threshold_met": benchmark_threshold_met,
        "placeholder_count": placeholder_count,
        "unknown_object_ref_count": unknown_object_ref_count,
        "has_reviewed_eligible_queries": reviewed_eligible_count > 0,
        "benchmark_ready_query_set": readiness_status == REVIEWED_QUERY_SET_STATUS_BENCHMARK_READY_INPUTS_ONLY,
        "benchmark_complete": False,
        "evaluated_retrieval_quality": False,
        "production_rag_claim": False,
    }


def validate_and_summarize_reviewed_query_set(
    *,
    query_set_path: Path,
    objects_path: Path,
    allow_template: bool = False,
) -> dict[str, Any]:
    rows = load_reviewed_query_set(query_set_path)
    object_rows = read_jsonl(objects_path)
    errors = validate_reviewed_query_set_rows(rows, object_rows, allow_template=allow_template)
    if errors:
        raise ValueError("; ".join(errors))
    summary = summarize_reviewed_query_set(rows, object_rows=object_rows)
    report_errors = validate_provider_output_payload(summary, context="reviewed query set summary")
    if report_errors:
        raise ValueError("; ".join(report_errors))
    return summary
