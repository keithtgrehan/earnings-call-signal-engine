from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from typing import Any

CANONICAL_REVIEW_FIELDS = (
    "review_id",
    "provenance_id",
    "case_id",
    "signal_type",
    "topic",
    "transcript_section",
    "speaker_role",
    "evidence_text",
    "evidence_start_hint",
    "evidence_end_hint",
    "predicted_direction",
    "reviewer_action",
    "reviewer_notes",
    "confidence",
    "source_url",
    "transcript_path",
    "created_at",
    "reviewer_id",
    "review_status",
)

ALLOWED_REVIEW_ACTIONS = {"accept", "reject", "edit", "relabel", "uncertain"}
GOLD_REVIEW_ACTIONS = {"accept", "edit", "relabel"}
REVIEW_STATUSES = {"pending", "reviewed", "imported", "rejected", "invalid"}


@dataclass(frozen=True)
class ValidationIssue:
    row_number: int
    field: str
    message: str


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_action(value: Any) -> str:
    action = clean_text(value).lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "accepted": "accept",
        "reject_signal": "reject",
        "rejected": "reject",
        "edited": "edit",
        "edit_label": "edit",
        "relabeled": "relabel",
        "unclear": "uncertain",
        "unsure": "uncertain",
    }
    return aliases.get(action, action)


def normalize_confidence(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    text = clean_text(value).lower()
    mapping = {"high": 0.9, "medium": 0.6, "low": 0.35}
    if text in mapping:
        return mapping[text]
    try:
        number = float(text)
    except ValueError:
        return 0.0
    if number > 1.0:
        number /= 100.0
    return round(min(1.0, max(0.0, number)), 4)


def stable_review_id(*parts: Any) -> str:
    payload = "||".join(clean_text(part) for part in parts)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    return f"review_{digest}"


def first_present(row: dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = clean_text(row.get(key))
        if value:
            return value
    return default


def canonical_review_from_signal(row: dict[str, Any], *, row_number: int, created_at: str | None = None) -> dict[str, Any]:
    evidence_text = first_present(row, ("evidence_text", "text", "matched_text", "segment_text", "utterance", "content"))
    case_id = first_present(row, ("case_id", "call_id", "conversation_id", "source_call_id", "ticker"))
    signal_type = first_present(row, ("signal_type", "signal_family", "label", "weak_label", "suggested_label"))
    provenance_id = first_present(row, ("provenance_id", "source_id", "candidate_id", "id"))
    if not provenance_id:
        provenance_id = stable_review_id(case_id, signal_type, evidence_text)
    review_id = first_present(row, ("review_id",))
    if not review_id:
        review_id = stable_review_id(provenance_id, case_id, signal_type, evidence_text, row_number)
    return {
        "review_id": review_id,
        "provenance_id": provenance_id,
        "case_id": case_id,
        "signal_type": signal_type,
        "topic": first_present(row, ("topic", "signal_topic", "reason")),
        "transcript_section": first_present(row, ("transcript_section", "section", "section_name"), "unknown"),
        "speaker_role": first_present(row, ("speaker_role", "role", "speaker_type"), "unknown"),
        "evidence_text": evidence_text,
        "evidence_start_hint": first_present(row, ("evidence_start_hint", "start_hint", "start_char", "message_index")),
        "evidence_end_hint": first_present(row, ("evidence_end_hint", "end_hint", "end_char")),
        "predicted_direction": first_present(row, ("predicted_direction", "direction", "guidance_direction")),
        "reviewer_action": normalize_action(first_present(row, ("reviewer_action", "review_action", "review_decision"))),
        "reviewer_notes": first_present(row, ("reviewer_notes", "review_notes", "notes")),
        "confidence": normalize_confidence(first_present(row, ("confidence", "deterministic_confidence", "score"))),
        "source_url": first_present(row, ("source_url", "url")),
        "transcript_path": first_present(row, ("transcript_path", "source_path", "source_file")),
        "created_at": first_present(row, ("created_at", "generated_at"), created_at or utc_now()),
        "reviewer_id": first_present(row, ("reviewer_id", "reviewer")),
        "review_status": first_present(row, ("review_status", "status"), "pending"),
    }


def validate_canonical_review(row: dict[str, Any], *, row_number: int, require_reviewed: bool = False) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in CANONICAL_REVIEW_FIELDS:
        if field not in row:
            issues.append(ValidationIssue(row_number, field, "field is required"))
    for field in ("review_id", "provenance_id", "case_id", "signal_type", "evidence_text", "created_at"):
        if not clean_text(row.get(field)):
            issues.append(ValidationIssue(row_number, field, "value must not be empty"))
    confidence = row.get("confidence")
    try:
        number = float(confidence)
    except (TypeError, ValueError):
        issues.append(ValidationIssue(row_number, "confidence", "must be a number from 0.0 to 1.0"))
    else:
        if number < 0.0 or number > 1.0:
            issues.append(ValidationIssue(row_number, "confidence", "must be from 0.0 to 1.0"))
    action = normalize_action(row.get("reviewer_action"))
    if action and action not in ALLOWED_REVIEW_ACTIONS:
        issues.append(ValidationIssue(row_number, "reviewer_action", f"invalid action `{action}`"))
    if require_reviewed:
        if action not in ALLOWED_REVIEW_ACTIONS:
            issues.append(ValidationIssue(row_number, "reviewer_action", "reviewed import requires a valid action"))
        if not clean_text(row.get("reviewer_id")):
            issues.append(ValidationIssue(row_number, "reviewer_id", "reviewed import requires reviewer_id"))
    status = clean_text(row.get("review_status"))
    if status and status not in REVIEW_STATUSES:
        issues.append(ValidationIssue(row_number, "review_status", f"invalid review_status `{status}`"))
    return issues


def gold_label_from_review(row: dict[str, Any]) -> dict[str, Any] | None:
    action = normalize_action(row.get("reviewer_action"))
    if action not in GOLD_REVIEW_ACTIONS:
        return None
    signal_type = first_present(row, ("reviewer_signal_type", "final_signal_type", "final_label", "gold_signal_type"), clean_text(row.get("signal_type")))
    direction = first_present(row, ("reviewer_direction", "final_direction", "gold_direction"), clean_text(row.get("predicted_direction")))
    evidence_text = first_present(row, ("reviewer_evidence_text", "final_evidence_text"), clean_text(row.get("evidence_text")))
    return {
        "id": clean_text(row.get("review_id")),
        "review_id": clean_text(row.get("review_id")),
        "provenance_id": clean_text(row.get("provenance_id")),
        "case_id": clean_text(row.get("case_id")),
        "signal_family": signal_type,
        "signal_type": signal_type,
        "direction": direction,
        "topic": clean_text(row.get("topic")),
        "transcript_section": clean_text(row.get("transcript_section")),
        "speaker_role": clean_text(row.get("speaker_role")),
        "text": evidence_text,
        "evidence_text": evidence_text,
        "evidence_start_hint": clean_text(row.get("evidence_start_hint")),
        "evidence_end_hint": clean_text(row.get("evidence_end_hint")),
        "source_url": clean_text(row.get("source_url")),
        "transcript_path": clean_text(row.get("transcript_path")),
        "label_source": "argilla_human_review",
        "reviewer_id": clean_text(row.get("reviewer_id")),
        "reviewer_action": action,
        "reviewer_notes": clean_text(row.get("reviewer_notes")),
        "created_at": clean_text(row.get("created_at")),
    }
