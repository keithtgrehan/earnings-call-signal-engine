from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import Any

REVIEW_SCHEMA_VERSION = "review_schema_v1"
EXPORT_TOOL_VERSION = "argilla_export_v1"
IMPORT_TOOL_VERSION = "argilla_import_v1"
EVALUATOR_SCHEMA_VERSION = "review_evaluator_v1"
PROVENANCE_EVENT_SCHEMA_VERSION = "provenance_event_v1"

CANONICAL_REVIEW_FIELDS = (
    "schema_version",
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
    "assigned_reviewer_id",
    "reviewer_action_audit",
    "disagreement_status",
    "adjudication_notes",
    "evidence_mismatch_class",
)

ALLOWED_REVIEW_ACTIONS = {"accept", "reject", "edit", "relabel", "uncertain"}
GOLD_REVIEW_ACTIONS = {"accept", "edit", "relabel"}
REVIEW_STATUSES = {
    "pending",
    "in_review",
    "accepted",
    "rejected",
    "edited",
    "relabeled",
    "uncertain",
    "adjudication_required",
}
PROMOTABLE_STATUSES = {"accepted", "edited", "relabeled"}
DISAGREEMENT_STATUSES = {"", "none", "reviewer_disagreement", "adjudication_required", "resolved"}
EVIDENCE_MISMATCH_CLASSES = {"none", "exact_mismatch", "partial_mismatch", "transcript_missing", "section_mismatch"}

ALLOWED_TRANSITIONS = {
    "pending": {"pending", "in_review", "accepted", "rejected", "edited", "relabeled", "uncertain"},
    "in_review": {"in_review", "accepted", "rejected", "edited", "relabeled", "uncertain", "adjudication_required"},
    "accepted": {"accepted", "adjudication_required"},
    "rejected": {"rejected", "adjudication_required"},
    "edited": {"edited", "adjudication_required"},
    "relabeled": {"relabeled", "adjudication_required"},
    "uncertain": {"uncertain", "in_review", "adjudication_required"},
    "adjudication_required": {"adjudication_required", "accepted", "rejected", "edited", "relabeled", "uncertain"},
}


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


def status_for_action(action: str) -> str:
    return {
        "accept": "accepted",
        "reject": "rejected",
        "edit": "edited",
        "relabel": "relabeled",
        "uncertain": "uncertain",
    }.get(normalize_action(action), "pending")


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
    action = normalize_action(first_present(row, ("reviewer_action", "review_action", "review_decision")))
    status = first_present(row, ("review_status", "status"), status_for_action(action) if action else "pending")
    return {
        "schema_version": first_present(row, ("schema_version",), REVIEW_SCHEMA_VERSION),
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
        "reviewer_action": action,
        "reviewer_notes": first_present(row, ("reviewer_notes", "review_notes", "notes")),
        "confidence": normalize_confidence(first_present(row, ("confidence", "deterministic_confidence", "score"))),
        "source_url": first_present(row, ("source_url", "url")),
        "transcript_path": first_present(row, ("transcript_path", "source_path", "source_file")),
        "created_at": first_present(row, ("created_at", "generated_at"), created_at or utc_now()),
        "reviewer_id": first_present(row, ("reviewer_id", "reviewer")),
        "review_status": status,
        "assigned_reviewer_id": first_present(row, ("assigned_reviewer_id", "reviewer_assigned_to")),
        "reviewer_action_audit": first_present(row, ("reviewer_action_audit",), ""),
        "disagreement_status": first_present(row, ("disagreement_status",), "none"),
        "adjudication_notes": first_present(row, ("adjudication_notes",), ""),
        "evidence_mismatch_class": first_present(row, ("evidence_mismatch_class",), "none"),
    }


def validate_transition(previous: str, new: str) -> bool:
    previous_status = clean_text(previous) or "pending"
    new_status = clean_text(new) or "pending"
    return new_status in ALLOWED_TRANSITIONS.get(previous_status, set())


def classify_evidence_match(evidence_text: str, transcript_text: str | None, *, section_mismatch: bool = False) -> str:
    evidence = clean_text(evidence_text)
    if section_mismatch:
        return "section_mismatch"
    if transcript_text is None:
        return "transcript_missing"
    transcript = clean_text(transcript_text)
    if not evidence:
        return "exact_mismatch"
    if evidence in transcript:
        return "none"
    evidence_terms = {term.lower() for term in evidence.split() if len(term) > 3}
    transcript_terms = {term.lower() for term in transcript.split()}
    if evidence_terms and len(evidence_terms & transcript_terms) / len(evidence_terms) >= 0.5:
        return "partial_mismatch"
    return "exact_mismatch"


def validate_transcript_evidence(row: dict[str, Any], *, repo_root: Path | None = None, row_number: int = 0) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    transcript_path_text = clean_text(row.get("transcript_path"))
    if not transcript_path_text:
        row["evidence_mismatch_class"] = "transcript_missing"
        return issues
    path = Path(transcript_path_text)
    if not path.is_absolute() and repo_root is not None:
        path = repo_root / path
    if not path.exists():
        issues.append(ValidationIssue(row_number, "transcript_path", f"transcript path does not exist: {transcript_path_text}"))
        row["evidence_mismatch_class"] = "transcript_missing"
        return issues
    transcript_text = path.read_text(encoding="utf-8", errors="replace")
    mismatch = classify_evidence_match(clean_text(row.get("evidence_text")), transcript_text)
    row["evidence_mismatch_class"] = mismatch
    if mismatch not in {"none", "partial_mismatch"}:
        issues.append(ValidationIssue(row_number, "evidence_text", f"evidence mismatch class `{mismatch}`"))
    return issues


def validate_export_lineage(row: dict[str, Any], manifest: dict[str, Any], *, row_number: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    review_ids = set(manifest.get("review_ids") or [])
    provenance_ids = set(manifest.get("provenance_ids") or [])
    if clean_text(row.get("review_id")) not in review_ids:
        issues.append(ValidationIssue(row_number, "review_id", "review_id is not present in export manifest"))
    if clean_text(row.get("provenance_id")) not in provenance_ids:
        issues.append(ValidationIssue(row_number, "provenance_id", "provenance_id is not present in export manifest"))
    return issues


def build_export_manifest(rows: list[dict[str, Any]], *, source_path: str, output_path: str) -> dict[str, Any]:
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "tool_version": EXPORT_TOOL_VERSION,
        "generated_at": utc_now(),
        "source_path": source_path,
        "output_path": output_path,
        "row_count": len(rows),
        "review_ids": [clean_text(row.get("review_id")) for row in rows],
        "provenance_ids": [clean_text(row.get("provenance_id")) for row in rows],
    }


def validate_canonical_review(
    row: dict[str, Any],
    *,
    row_number: int,
    require_reviewed: bool = False,
    previous_status: str | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in CANONICAL_REVIEW_FIELDS:
        if field not in row:
            issues.append(ValidationIssue(row_number, field, "field is required"))
    for field in ("schema_version", "review_id", "provenance_id", "case_id", "signal_type", "evidence_text", "created_at"):
        if not clean_text(row.get(field)):
            issues.append(ValidationIssue(row_number, field, "value must not be empty"))
    if clean_text(row.get("schema_version")) != REVIEW_SCHEMA_VERSION:
        issues.append(ValidationIssue(row_number, "schema_version", f"expected `{REVIEW_SCHEMA_VERSION}`"))
    try:
        number = float(row.get("confidence"))
    except (TypeError, ValueError):
        issues.append(ValidationIssue(row_number, "confidence", "must be a number from 0.0 to 1.0"))
    else:
        if number < 0.0 or number > 1.0:
            issues.append(ValidationIssue(row_number, "confidence", "must be from 0.0 to 1.0"))
    action = normalize_action(row.get("reviewer_action"))
    if action and action not in ALLOWED_REVIEW_ACTIONS:
        issues.append(ValidationIssue(row_number, "reviewer_action", f"invalid action `{action}`"))
    status = clean_text(row.get("review_status"))
    if status not in REVIEW_STATUSES:
        issues.append(ValidationIssue(row_number, "review_status", f"invalid review_status `{status}`"))
    if previous_status is not None and not validate_transition(previous_status, status):
        issues.append(ValidationIssue(row_number, "review_status", f"invalid transition `{previous_status}` -> `{status}`"))
    disagreement = clean_text(row.get("disagreement_status"))
    if disagreement not in DISAGREEMENT_STATUSES:
        issues.append(ValidationIssue(row_number, "disagreement_status", f"invalid disagreement_status `{disagreement}`"))
    mismatch = clean_text(row.get("evidence_mismatch_class"))
    if mismatch not in EVIDENCE_MISMATCH_CLASSES:
        issues.append(ValidationIssue(row_number, "evidence_mismatch_class", f"invalid evidence_mismatch_class `{mismatch}`"))
    if require_reviewed:
        if action not in ALLOWED_REVIEW_ACTIONS:
            issues.append(ValidationIssue(row_number, "reviewer_action", "reviewed import requires a valid action"))
        if not clean_text(row.get("reviewer_id")):
            issues.append(ValidationIssue(row_number, "reviewer_id", "reviewed import requires reviewer_id"))
        expected_status = status_for_action(action)
        if status != expected_status:
            issues.append(ValidationIssue(row_number, "review_status", f"expected `{expected_status}` for action `{action}`"))
    return issues


def gold_label_from_review(row: dict[str, Any]) -> dict[str, Any] | None:
    action = normalize_action(row.get("reviewer_action"))
    status = clean_text(row.get("review_status"))
    if action not in GOLD_REVIEW_ACTIONS or status not in PROMOTABLE_STATUSES:
        return None
    signal_type = first_present(row, ("reviewer_signal_type", "final_signal_type", "final_label", "gold_signal_type"), clean_text(row.get("signal_type")))
    direction = first_present(row, ("reviewer_direction", "final_direction", "gold_direction"), clean_text(row.get("predicted_direction")))
    evidence_text = first_present(row, ("reviewer_evidence_text", "final_evidence_text"), clean_text(row.get("evidence_text")))
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
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
        "evidence_mismatch_class": clean_text(row.get("evidence_mismatch_class")),
        "created_at": clean_text(row.get("created_at")),
    }
