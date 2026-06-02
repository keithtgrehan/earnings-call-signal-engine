from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any

METADATA_SUMMARY_STATUS_LABEL = "retrieval_object_scaffold_only"
RETRIEVAL_OBJECT_METADATA_TYPES = (
    "semantic_chunk_metadata",
    "event_aligned_chunk_metadata",
    "evidence_object_metadata",
)
REQUIRED_METADATA_FIELDS = {
    "case_id",
    "object_id",
    "object_type",
    "company",
    "ticker",
    "fiscal_period",
    "source_type",
    "provenance_ref",
    "source_hash",
    "text_hash",
    "normalized_transcript_hash",
    "provenance_hash",
    "section_label",
    "speaker_role",
    "topic",
    "span_start_char",
    "span_end_char",
    "rights_tier",
    "retrieval_priority",
    "content_included",
    "embeddings_included",
    "vector_db_included",
}
FORBIDDEN_METADATA_PAYLOAD_KEYS = {
    "raw_text",
    "raw_transcript_text",
    "raw_chunk_text",
    "transcript_text",
    "asr_text",
    "audio_text",
    "chunk_text",
    "chunk_body_text",
    "evidence_text",
    "redacted_evidence_preview",
    "embedding",
    "embeddings",
    "vector",
    "vectors",
    "vector_db",
    "payload_text",
    "retrieval_payload_text",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
OBJECT_ID_RE = re.compile(r"^rom_(semantic|event|evidence)_[0-9a-f]{16}$")

_TYPE_PRIORITY = {
    "evidence_object_metadata": 1,
    "event_aligned_chunk_metadata": 2,
    "semantic_chunk_metadata": 3,
}
_TYPE_ID_PREFIX = {
    "evidence_object_metadata": "rom_evidence",
    "event_aligned_chunk_metadata": "rom_event",
    "semantic_chunk_metadata": "rom_semantic",
}
_STABLE_ID_FIELDS = (
    "object_type",
    "case_id",
    "source_type",
    "source_hash",
    "text_hash",
    "normalized_transcript_hash",
    "provenance_ref",
    "provenance_hash",
    "span_start_char",
    "span_end_char",
)


def retrieval_object_metadata_priority(object_type: str) -> int:
    if object_type not in _TYPE_PRIORITY:
        raise ValueError(f"Unsupported retrieval object metadata type: {object_type!r}")
    return _TYPE_PRIORITY[object_type]


def _compact_key(value: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return re.sub(r"[^a-z0-9]", "", snake)


def validate_no_forbidden_metadata_payload_keys(payload: Any, *, context: str = "metadata") -> list[str]:
    errors: list[str] = []
    forbidden = {_compact_key(key) for key in FORBIDDEN_METADATA_PAYLOAD_KEYS}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                if _compact_key(str(key)) in forbidden:
                    errors.append(f"{context}: forbidden raw/vector payload key {key_path}")
                visit(nested, key_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")
    return errors


def stable_metadata_object_id(row: dict[str, Any]) -> str:
    object_type = str(row.get("object_type", ""))
    prefix = _TYPE_ID_PREFIX.get(object_type, "rom_unknown")
    payload = {field: row.get(field) for field in _STABLE_ID_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:16]}"


def build_retrieval_object_metadata(
    *,
    object_type: str,
    case_id: str,
    company: str = "",
    ticker: str = "",
    fiscal_period: str = "",
    source_type: str,
    provenance_ref: str,
    source_hash: str,
    text_hash: str,
    normalized_transcript_hash: str,
    provenance_hash: str,
    section_label: str = "",
    speaker_role: str = "",
    topic: str = "",
    span_start_char: int | None = None,
    span_end_char: int | None = None,
    rights_tier: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "case_id": case_id,
        "object_id": "",
        "object_type": object_type,
        "company": company,
        "ticker": ticker,
        "fiscal_period": fiscal_period,
        "source_type": source_type,
        "provenance_ref": provenance_ref,
        "source_hash": source_hash,
        "text_hash": text_hash,
        "normalized_transcript_hash": normalized_transcript_hash,
        "provenance_hash": provenance_hash,
        "section_label": section_label,
        "speaker_role": speaker_role,
        "topic": topic,
        "span_start_char": span_start_char,
        "span_end_char": span_end_char,
        "rights_tier": rights_tier,
        "retrieval_priority": retrieval_object_metadata_priority(object_type),
        "content_included": False,
        "embeddings_included": False,
        "vector_db_included": False,
    }
    row["object_id"] = stable_metadata_object_id(row)
    errors = validate_retrieval_object_metadata_record(row)
    if errors:
        raise ValueError("; ".join(errors))
    return row


def validate_retrieval_object_metadata_record(row: dict[str, Any]) -> list[str]:
    errors = validate_no_forbidden_metadata_payload_keys(row)
    keys = set(row)
    for field in sorted(REQUIRED_METADATA_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - REQUIRED_METADATA_FIELDS):
        errors.append(f"unexpected field {field}")

    object_type = row.get("object_type")
    object_id = row.get("object_id")
    if not isinstance(object_id, str) or not OBJECT_ID_RE.fullmatch(object_id):
        errors.append("object_id must match rom_(semantic|event|evidence)_<16 lowercase hex>")
    if object_type not in RETRIEVAL_OBJECT_METADATA_TYPES:
        errors.append(f"invalid object_type {object_type!r}")
    elif row.get("retrieval_priority") != retrieval_object_metadata_priority(str(object_type)):
        errors.append(f"{object_type} must use retrieval_priority {retrieval_object_metadata_priority(str(object_type))}")

    for field in ("case_id", "source_type", "provenance_ref", "rights_tier"):
        if field in row and not str(row.get(field) or "").strip():
            errors.append(f"{field} must be present")
    for field in ("source_hash", "text_hash", "normalized_transcript_hash", "provenance_hash"):
        value = row.get(field)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            errors.append(f"{field} must be a sha256:<64 lowercase hex> value")
    for field in ("company", "ticker", "fiscal_period", "section_label", "speaker_role", "topic"):
        if field in row and not isinstance(row.get(field), str):
            errors.append(f"{field} must be a string")
    for field in ("span_start_char", "span_end_char"):
        if row.get(field) is not None and not isinstance(row.get(field), int):
            errors.append(f"{field} must be an integer or null")
    if isinstance(row.get("span_start_char"), int) and isinstance(row.get("span_end_char"), int):
        if row["span_start_char"] > row["span_end_char"]:
            errors.append("span_start_char must be <= span_end_char")
    for field in ("content_included", "embeddings_included", "vector_db_included"):
        if row.get(field) is not False:
            errors.append(f"{field} must be false")
    if object_type in RETRIEVAL_OBJECT_METADATA_TYPES and row.get("object_id") != stable_metadata_object_id(row):
        errors.append("object_id must match stable object_id derived from metadata")
    return errors


def validate_retrieval_object_metadata_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    object_ids: Counter[str] = Counter(str(row.get("object_id", "")) for row in rows)
    duplicates = sorted(object_id for object_id, count in object_ids.items() if object_id and count > 1)
    for duplicate in duplicates:
        errors.append(f"duplicate object_id {duplicate}")
    for index, row in enumerate(rows, start=1):
        errors.extend(f"row {index}: {error}" for error in validate_retrieval_object_metadata_record(row))
    return errors


def summarize_retrieval_object_metadata_rows(
    rows: list[dict[str, Any]],
    *,
    source_manifest: str = "",
    out_path: str = "",
) -> dict[str, Any]:
    return {
        "status_label": METADATA_SUMMARY_STATUS_LABEL,
        "source_manifest": source_manifest,
        "out_path": out_path,
        "object_count": len(rows),
        "counts_by_object_type": dict(sorted(Counter(str(row.get("object_type", "")) for row in rows).items())),
        "counts_by_case_id": dict(sorted(Counter(str(row.get("case_id", "")) for row in rows).items())),
        "content_included": False,
        "embeddings_included": False,
        "vector_db_included": False,
        "evaluated_retrieval_quality": False,
        "production_rag_claim": False,
    }


def validate_retrieval_object_metadata_summary(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    expected = summarize_retrieval_object_metadata_rows(
        rows,
        source_manifest=str(summary.get("source_manifest", "")),
        out_path=str(summary.get("out_path", "")),
    )
    if summary.get("status_label") != METADATA_SUMMARY_STATUS_LABEL:
        errors.append(f"status_label must be {METADATA_SUMMARY_STATUS_LABEL!r}")
    if summary.get("object_count") != expected["object_count"]:
        errors.append(f"object_count must equal JSONL row count {expected['object_count']}")
    for key in ("counts_by_object_type", "counts_by_case_id"):
        counts = summary.get(key)
        if counts != expected[key]:
            errors.append(f"{key} must match JSONL counts")
        if isinstance(counts, dict):
            total = 0
            for count_key, value in counts.items():
                if not isinstance(value, int) or isinstance(value, bool):
                    errors.append(f"{key}.{count_key} must be an integer count")
                    continue
                total += value
            if total != expected["object_count"]:
                errors.append(f"{key} must sum to object_count {expected['object_count']}")
    for key in (
        "content_included",
        "embeddings_included",
        "vector_db_included",
        "evaluated_retrieval_quality",
        "production_rag_claim",
    ):
        if summary.get(key) is not False:
            errors.append(f"{key} must be false")
    return errors
