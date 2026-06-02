from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from signal_engine.retrieval.evaluate import (
    validate_claim_safety_text,
    validate_no_forbidden_payload_keys,
    validate_no_raw_text_like_values,
)
from signal_engine.retrieval.providers.safety import validate_provider_output_payload
from signal_engine.retrieval.reviewed_query_set import (
    ANSWER_LEAKAGE_RE,
    ISO_LIKE_UTC_RE,
    MIN_REVIEWED_ELIGIBLE_QUERIES,
    OVERCLAIM_TEXT_RE,
    REVIEWED_QUERY_SET_STATUSES,
    load_reviewed_query_set,
    read_jsonl,
    summarize_reviewed_query_set,
    validate_reviewed_query_set_rows,
)

REVIEW_IMPORT_STATUS_LABEL = "retrieval_review_import_only"
REVIEW_WORKSHEET_COLUMNS = [
    "query_id",
    "case_id",
    "query_type",
    "expected_object_ids",
    "expected_object_types",
    "evidence_object_id_refs",
    "provenance_refs",
    "review_status",
    "benchmark_eligible",
    "reviewer",
    "reviewed_at",
    "reviewer_decision",
    "reviewer_notes",
    "rejection_reason",
]
IMMUTABLE_WORKSHEET_FIELDS = {
    "query_id",
    "case_id",
    "query_type",
    "expected_object_ids",
    "expected_object_types",
    "evidence_object_id_refs",
    "provenance_refs",
}
LIST_WORKSHEET_FIELDS = {
    "expected_object_ids",
    "expected_object_types",
    "evidence_object_id_refs",
    "provenance_refs",
}
ALLOWED_REVIEWER_DECISIONS = {"", "pending", "approved", "rejected"}
FORBIDDEN_REVIEW_UPDATE_VALUE_RE = re.compile(
    r"\b(answer\s+leakage|expected\s+answer|answer\s+text|gold\s+label|adjudication|training\s+label|promotion\s+row)\b",
    re.IGNORECASE,
)
FORBIDDEN_REVIEW_OUTPUT_NAME_RE = re.compile(
    r"(embedding|embeddings|vector|vectors|index|indexes|indices|faiss|chroma|lancedb|provider_artifact)",
    re.IGNORECASE,
)


def _validate_output_path(path: Path, *, expected_suffixes: set[str], role: str) -> None:
    if path.suffix.lower() not in expected_suffixes:
        allowed = ", ".join(sorted(expected_suffixes))
        raise ValueError(f"{role} output must use one of: {allowed}")
    if FORBIDDEN_REVIEW_OUTPUT_NAME_RE.search(path.name):
        raise ValueError(f"{role} output filename suggests generated provider/vector artifacts: {path.name}")


def _json_cell(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _parse_bool(value: Any, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"{field} must be true or false")


def _parse_json_list(value: str, *, field: str, query_id: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{query_id}: {field} must be a JSON array") from exc
    if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
        raise ValueError(f"{query_id}: {field} must be a JSON array of strings")
    return parsed


def _worksheet_payload_for_safety(row: dict[str, str]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if value not in {"", None}}


def _validate_text_safety(row: dict[str, str], *, context: str) -> list[str]:
    errors = validate_provider_output_payload(row, context=context)
    errors.extend(validate_no_forbidden_payload_keys(row, context=context))
    errors.extend(validate_no_raw_text_like_values(row, context=context))
    for key, value in row.items():
        if not isinstance(value, str) or not value.strip():
            continue
        errors.extend(f"{key}: {error}" for error in validate_claim_safety_text(value))
        if ANSWER_LEAKAGE_RE.search(value) or FORBIDDEN_REVIEW_UPDATE_VALUE_RE.search(value):
            errors.append(f"{key}: answer leakage wording is not allowed")
        if OVERCLAIM_TEXT_RE.search(value):
            errors.append(f"{key}: production or benchmark overclaim wording is not allowed")
    return errors


def _read_review_updates_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("review update worksheet is missing a header")
        for column in reader.fieldnames:
            if column not in REVIEW_WORKSHEET_COLUMNS:
                raise ValueError(f"unexpected worksheet column {column}")
        missing = [column for column in REVIEW_WORKSHEET_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"missing worksheet column(s): {', '.join(missing)}")
        rows = [dict(row) for row in reader]
    return rows


def _validated_inputs(
    *,
    query_set_path: Path,
    objects_path: Path,
    allow_template: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = load_reviewed_query_set(query_set_path)
    object_rows = read_jsonl(objects_path)
    errors = validate_reviewed_query_set_rows(rows, object_rows, allow_template=allow_template)
    if errors:
        raise ValueError("; ".join(errors))
    summary = summarize_reviewed_query_set(rows, object_rows=object_rows)
    return rows, object_rows, summary


def export_review_worksheet(
    *,
    query_set_path: Path,
    objects_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    _validate_output_path(out_path, expected_suffixes={".csv"}, role="review worksheet")
    query_rows, object_rows, query_summary = _validated_inputs(
        query_set_path=query_set_path,
        objects_path=objects_path,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_WORKSHEET_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in query_rows:
            worksheet_row = {
                "query_id": row["query_id"],
                "case_id": row["case_id"],
                "query_type": row["query_type"],
                "expected_object_ids": _json_cell(row["expected_object_ids"]),
                "expected_object_types": _json_cell(row["expected_object_types"]),
                "evidence_object_id_refs": _json_cell(row["evidence_object_id_refs"]),
                "provenance_refs": _json_cell(row["provenance_refs"]),
                "review_status": row["review_status"],
                "benchmark_eligible": str(row["benchmark_eligible"]).lower(),
                "reviewer": row["reviewer"],
                "reviewed_at": row["reviewed_at"],
                "reviewer_decision": "",
                "reviewer_notes": "",
                "rejection_reason": "",
            }
            safety_errors = _validate_text_safety(worksheet_row, context="review worksheet row")
            if safety_errors:
                raise ValueError("; ".join(safety_errors))
            writer.writerow(worksheet_row)
    summary = {
        "status_label": REVIEW_IMPORT_STATUS_LABEL,
        "worksheet_path": _display_path(out_path),
        "query_set_path": _display_path(query_set_path),
        "objects_path": _display_path(objects_path),
        "row_count": len(query_rows),
        "query_set_readiness_status": query_summary["query_set_readiness_status"],
        "benchmark_eligible_rows": query_summary["reviewed_eligible_query_count"],
        "benchmark_threshold_met": query_summary["benchmark_threshold_met"],
        "benchmark_complete": False,
        "provider_execution": False,
        "embeddings_generated": False,
        "vector_db_generated": False,
        "evaluated_retrieval_quality": False,
    }
    report_errors = validate_provider_output_payload(summary, context="review worksheet export summary")
    if report_errors:
        raise ValueError("; ".join(report_errors))
    return summary


def _normalize_update_row(row: dict[str, str], *, query_id: str) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for field in REVIEW_WORKSHEET_COLUMNS:
        value = row.get(field, "")
        if field in LIST_WORKSHEET_FIELDS:
            normalized[field] = _parse_json_list(value, field=field, query_id=query_id)
        elif field == "benchmark_eligible":
            normalized[field] = _parse_bool(value, field=f"{query_id}: benchmark_eligible")
        else:
            normalized[field] = value.strip() if isinstance(value, str) else value
    return normalized


def _validate_update_row(
    *,
    base_row: dict[str, Any],
    update_row: dict[str, str],
) -> dict[str, Any]:
    query_id = str(base_row["query_id"])
    safety_payload = _worksheet_payload_for_safety(update_row)
    safety_errors = _validate_text_safety(safety_payload, context=f"review update row {query_id}")
    if safety_errors:
        raise ValueError("; ".join(safety_errors))
    normalized = _normalize_update_row(update_row, query_id=query_id)

    if normalized["query_id"] != query_id:
        raise ValueError(f"{query_id}: worksheet query_id mismatch")
    for field in sorted(IMMUTABLE_WORKSHEET_FIELDS):
        if normalized[field] != base_row[field]:
            raise ValueError(f"{query_id}: immutable field {field} changed")

    review_status = normalized["review_status"]
    benchmark_eligible = normalized["benchmark_eligible"]
    reviewer = normalized["reviewer"]
    reviewed_at = normalized["reviewed_at"]
    reviewer_decision = normalized["reviewer_decision"].lower()

    if review_status not in REVIEWED_QUERY_SET_STATUSES:
        raise ValueError(f"{query_id}: invalid review_status {review_status!r}")
    if reviewer_decision not in ALLOWED_REVIEWER_DECISIONS:
        raise ValueError(f"{query_id}: invalid reviewer_decision {reviewer_decision!r}")
    if benchmark_eligible and review_status != "reviewed":
        raise ValueError(f"{query_id}: benchmark_eligible=true requires review_status=reviewed")
    if review_status == "reviewed":
        if not reviewer:
            raise ValueError(f"{query_id}: reviewer must be present for reviewed rows")
        if not reviewed_at:
            raise ValueError(f"{query_id}: reviewed_at must be present for reviewed rows")
        if not ISO_LIKE_UTC_RE.fullmatch(reviewed_at):
            raise ValueError(f"{query_id}: reviewed_at must use YYYY-MM-DDTHH:MM:SSZ format")
        if reviewer_decision != "approved":
            raise ValueError(f"{query_id}: review_status=reviewed requires reviewer_decision=approved")
    elif reviewer or reviewed_at:
        raise ValueError(f"{query_id}: reviewer and reviewed_at must stay empty until review_status=reviewed")
    if benchmark_eligible and reviewer_decision != "approved":
        raise ValueError(f"{query_id}: benchmark_eligible=true requires reviewer_decision=approved")
    if review_status == "rejected" and benchmark_eligible:
        raise ValueError(f"{query_id}: rejected rows cannot be benchmark eligible")

    candidate = dict(base_row)
    candidate["review_status"] = review_status
    candidate["benchmark_eligible"] = benchmark_eligible
    candidate["reviewer"] = reviewer
    candidate["reviewed_at"] = reviewed_at
    return candidate


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def build_review_import_summary(
    *,
    candidate_rows: list[dict[str, Any]],
    update_rows: list[dict[str, str]],
    object_rows: list[dict[str, Any]],
    query_set_path: Path,
    review_updates_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    query_summary = summarize_reviewed_query_set(candidate_rows, object_rows=object_rows)
    decisions = [str(row.get("reviewer_decision", "")).strip().lower() for row in update_rows]
    summary = {
        "status_label": REVIEW_IMPORT_STATUS_LABEL,
        "query_set_path": _display_path(query_set_path),
        "review_updates_path": _display_path(review_updates_path),
        "candidate_output_path": _display_path(out_path),
        "total_rows": len(candidate_rows),
        "reviewed_rows": sum(1 for row in candidate_rows if row.get("review_status") == "reviewed"),
        "approved_rows": sum(1 for decision in decisions if decision == "approved"),
        "rejected_rows": sum(1 for row in candidate_rows if row.get("review_status") == "rejected"),
        "benchmark_eligible_rows": query_summary["reviewed_eligible_query_count"],
        "minimum_benchmark_eligible_rows": MIN_REVIEWED_ELIGIBLE_QUERIES,
        "threshold_met": query_summary["benchmark_threshold_met"],
        "benchmark_threshold_met": query_summary["benchmark_threshold_met"],
        "query_set_readiness_status": query_summary["query_set_readiness_status"],
        "benchmark_ready_query_set": query_summary["benchmark_ready_query_set"],
        "benchmark_complete": False,
        "provider_execution": False,
        "embeddings_generated": False,
        "vector_db_generated": False,
        "evaluated_retrieval_quality": False,
        "production_rag_claim": False,
    }
    report_errors = validate_provider_output_payload(summary, context="review import summary")
    if report_errors:
        raise ValueError("; ".join(report_errors))
    return summary


def write_review_import_summary_json(path: Path, payload: dict[str, Any]) -> None:
    _validate_output_path(path, expected_suffixes={".json"}, role="review import summary JSON")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_review_import_summary_markdown(path: Path, payload: dict[str, Any]) -> None:
    _validate_output_path(path, expected_suffixes={".md"}, role="review import summary Markdown")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Review Import Summary",
        "",
        "## Run status",
        f"- status: `{payload['status_label']}`",
        f"- query-set readiness: `{payload['query_set_readiness_status']}`",
        f"- benchmark threshold met: `{str(payload['benchmark_threshold_met']).lower()}`",
        f"- benchmark complete: `{str(payload['benchmark_complete']).lower()}`",
        f"- provider execution: `{str(payload['provider_execution']).lower()}`",
        f"- embeddings generated: `{str(payload['embeddings_generated']).lower()}`",
        f"- vector DB generated: `{str(payload['vector_db_generated']).lower()}`",
        f"- evaluated retrieval quality: `{str(payload['evaluated_retrieval_quality']).lower()}`",
        f"- production RAG claim: `{str(payload['production_rag_claim']).lower()}`",
        "",
        "## Inputs",
        f"- query set: `{payload['query_set_path']}`",
        f"- review updates: `{payload['review_updates_path']}`",
        f"- candidate output: `{payload['candidate_output_path']}`",
        "",
        "## Row counts",
        f"- total rows: `{payload['total_rows']}`",
        f"- reviewed rows: `{payload['reviewed_rows']}`",
        f"- approved rows: `{payload['approved_rows']}`",
        f"- rejected rows: `{payload['rejected_rows']}`",
        f"- benchmark-eligible rows: `{payload['benchmark_eligible_rows']}`",
        f"- minimum benchmark-eligible rows: `{payload['minimum_benchmark_eligible_rows']}`",
        "",
        "## Safety statement",
        "- This import path updates metadata-only reviewer/status fields only.",
        "- It does not run providers, create embeddings, create vector stores, or report benchmark scores.",
        "- Threshold status is only an input-readiness gate; it is not a benchmark result.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def import_review_updates(
    *,
    query_set_path: Path,
    review_updates_path: Path,
    objects_path: Path,
    out_path: Path,
    summary_json_path: Path | None = None,
    summary_md_path: Path | None = None,
) -> dict[str, Any]:
    _validate_output_path(out_path, expected_suffixes={".jsonl"}, role="reviewed query-set candidate")
    if out_path.resolve() == query_set_path.resolve():
        raise ValueError("import output must not overwrite the source query-set")
    base_rows, object_rows, _ = _validated_inputs(query_set_path=query_set_path, objects_path=objects_path)
    update_rows = _read_review_updates_csv(review_updates_path)
    if len(update_rows) != len(base_rows):
        raise ValueError(f"review update row count {len(update_rows)} does not match query set row count {len(base_rows)}")

    base_by_id = {str(row["query_id"]): row for row in base_rows}
    update_ids = [str(row.get("query_id", "")).strip() for row in update_rows]
    if len(set(update_ids)) != len(update_ids):
        raise ValueError("review update worksheet contains duplicate query_id values")
    if set(update_ids) != set(base_by_id):
        raise ValueError("review update worksheet query_id set must match source query set")

    update_by_id = {str(row["query_id"]).strip(): row for row in update_rows}
    candidate_rows = [_validate_update_row(base_row=row, update_row=update_by_id[str(row["query_id"])]) for row in base_rows]
    errors = validate_reviewed_query_set_rows(candidate_rows, object_rows)
    if errors:
        raise ValueError("; ".join(errors))
    _write_jsonl(out_path, candidate_rows)
    summary = build_review_import_summary(
        candidate_rows=candidate_rows,
        update_rows=update_rows,
        object_rows=object_rows,
        query_set_path=query_set_path,
        review_updates_path=review_updates_path,
        out_path=out_path,
    )
    if summary_json_path is not None:
        write_review_import_summary_json(summary_json_path, summary)
    if summary_md_path is not None:
        write_review_import_summary_markdown(summary_md_path, summary)
    return summary
