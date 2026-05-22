from __future__ import annotations

from typing import Any

REQUIRED_RETRIEVAL_FIELDS = {
    "object_id",
    "object_type",
    "case_id",
    "ticker",
    "company",
    "fiscal_period",
    "source_type",
    "source_ref",
    "section",
    "speaker",
    "topic",
    "span_hints",
    "evidence_text",
    "redacted_evidence_preview",
    "provenance",
    "rights_tier",
    "commit_allowed",
    "raw_text_commit_allowed",
    "deterministic_signal_refs",
}

VALID_OBJECT_TYPES = {"semantic_chunk", "event_aligned_chunk", "evidence_object"}

_RETRIEVAL_PRIORITY = {
    "evidence_object": 1,
    "event_aligned_chunk": 2,
    "semantic_chunk": 3,
}


def retrieval_priority_for_type(object_type: str) -> int:
    if object_type not in _RETRIEVAL_PRIORITY:
        raise ValueError(f"Unsupported retrieval object_type: {object_type!r}")
    return _RETRIEVAL_PRIORITY[object_type]


def build_retrieval_object(
    *,
    object_id: str,
    object_type: str,
    case_id: str,
    company: str,
    fiscal_period: str,
    source_type: str,
    source_ref: str,
    section: str,
    provenance: dict[str, Any],
    rights_tier: str,
    raw_text_commit_allowed: bool = False,
    ticker: str = "",
    commit_allowed: bool = False,
    speaker: str = "",
    topic: str = "",
    span_hints: dict[str, Any] | None = None,
    evidence_text: str = "",
    redacted_evidence_preview: str = "",
    deterministic_signal_refs: list[str] | None = None,
    retrieval_priority: int | None = None,
) -> dict[str, Any]:
    payload = {
        "object_id": object_id,
        "object_type": object_type,
        "case_id": case_id,
        "ticker": ticker,
        "company": company,
        "fiscal_period": fiscal_period,
        "source_type": source_type,
        "source_ref": source_ref,
        "section": section,
        "speaker": speaker,
        "topic": topic,
        "span_hints": span_hints or {},
        "evidence_text": evidence_text,
        "redacted_evidence_preview": redacted_evidence_preview,
        "provenance": provenance,
        "rights_tier": rights_tier,
        "commit_allowed": commit_allowed,
        "raw_text_commit_allowed": raw_text_commit_allowed,
        "deterministic_signal_refs": deterministic_signal_refs or [],
        "retrieval_priority": retrieval_priority or retrieval_priority_for_type(object_type),
        "deterministic_output_override_allowed": False,
    }
    errors = validate_retrieval_object(payload)
    if errors:
        raise ValueError("; ".join(errors))
    return payload


def validate_retrieval_object(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(REQUIRED_RETRIEVAL_FIELDS - set(row)):
        errors.append(f"missing required field {field}")
    object_type = row.get("object_type")
    if object_type not in VALID_OBJECT_TYPES:
        errors.append(f"invalid object_type {object_type!r}")
    provenance = row.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("missing provenance object")
    else:
        if not provenance.get("source_path"):
            errors.append("missing provenance source_path")
        if not provenance.get("span_ids"):
            errors.append("missing provenance span_ids")
        if not provenance.get("provenance_hash"):
            errors.append("missing provenance provenance_hash")
    if row.get("deterministic_output_override_allowed") is True:
        errors.append("retrieval objects must not override deterministic extraction")
    if object_type in VALID_OBJECT_TYPES:
        expected_priority = retrieval_priority_for_type(str(object_type))
        if int(row.get("retrieval_priority", expected_priority)) != expected_priority:
            errors.append(f"{object_type} must use retrieval_priority {expected_priority}")
    if row.get("raw_text_commit_allowed") is True and row.get("rights_tier") in {"unknown", "restricted"}:
        errors.append("restricted or unknown rights cannot allow raw text commit")
    if row.get("raw_text_commit_allowed") is True and row.get("commit_allowed") is not True:
        errors.append("raw_text_commit_allowed requires commit_allowed")
    if not isinstance(row.get("deterministic_signal_refs", []), list):
        errors.append("deterministic_signal_refs must be a list")
    return errors
