from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

REQUIRED_EXTRACTED_FIELDS = (
    "case_id",
    "candidate_id",
    "suggested_label",
    "suggested_confidence",
    "reason",
    "source_file",
    "evidence_span",
    "packet_file",
)

HUMAN_ADJUDICATION_FIELDS = (
    "human_decision",
    "final_label",
    "final_evidence_span",
    "reviewer_notes",
    "time_spent_seconds",
    "adjudicator",
    "adjudication_timestamp",
)

REVIEW_QUEUE_FIELDS = (
    "case_id",
    "candidate_id",
    "suggested_label",
    "suggested_confidence",
    "reason",
    "source_file",
    "evidence_span",
    "context_before",
    "context_after",
    "surrounding_context",
    "packet_file",
    "transcript_file_if_matched",
    "evidence_match_status",
    "parser_warning",
    "human_decision",
    "final_label",
    "final_evidence_span",
    "reviewer_notes",
    "time_spent_seconds",
    "adjudicator",
    "adjudication_timestamp",
    "normalized_label",
    "source_type",
    "rule_family",
    "likely_review_priority",
    "priority_reason",
    "is_likely_boilerplate",
    "needs_context_lookup",
    "duplicate_key",
    "duplicate_count",
)

ALLOWED_NORMALIZED_LABELS = {
    "risk_friction",
    "opportunity_commitment",
    "uncertainty_hedging",
    "neutral",
    "other",
    "analyst_pressure",
    "guidance_revision",
    "uncertainty",
    "commitment",
}

LABEL_ALIASES = {
    "risk": "risk_friction",
    "friction": "risk_friction",
    "analyst_pressure": "risk_friction",
    "opportunity": "opportunity_commitment",
    "commitment": "opportunity_commitment",
    "uncertainty": "uncertainty_hedging",
    "hedging": "uncertainty_hedging",
    "guidance_revision": "risk_friction",
    "none": "neutral",
}


@dataclass(frozen=True)
class ValidationIssue:
    candidate_id: str
    field: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class ReviewQueueRow:
    case_id: str = ""
    candidate_id: str = ""
    suggested_label: str = ""
    suggested_confidence: str = ""
    reason: str = ""
    source_file: str = ""
    evidence_span: str = ""
    context_before: str = ""
    context_after: str = ""
    surrounding_context: str = ""
    packet_file: str = ""
    transcript_file_if_matched: str = ""
    evidence_match_status: str = ""
    parser_warning: str = ""
    human_decision: str = ""
    final_label: str = ""
    final_evidence_span: str = ""
    reviewer_notes: str = ""
    time_spent_seconds: str = ""
    adjudicator: str = ""
    adjudication_timestamp: str = ""
    normalized_label: str = ""
    source_type: str = ""
    rule_family: str = ""
    likely_review_priority: str = ""
    priority_reason: str = ""
    is_likely_boilerplate: str = ""
    needs_context_lookup: str = ""
    duplicate_key: str = ""
    duplicate_count: str = "1"

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "ReviewQueueRow":
        payload = {field: str(row.get(field, "") if row.get(field, "") is not None else "") for field in REVIEW_QUEUE_FIELDS}
        return cls(**payload)

    def to_dict(self) -> dict[str, str]:
        return {field: str(getattr(self, field)) for field in REVIEW_QUEUE_FIELDS}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return LABEL_ALIASES.get(label, label)


def blank_human_fields() -> dict[str, str]:
    return {field: "" for field in HUMAN_ADJUDICATION_FIELDS}


def validate_row(row: dict[str, Any] | ReviewQueueRow) -> list[ValidationIssue]:
    payload = row.to_dict() if isinstance(row, ReviewQueueRow) else {field: str(row.get(field, "") or "") for field in REVIEW_QUEUE_FIELDS}
    candidate_id = payload.get("candidate_id", "")
    issues: list[ValidationIssue] = []
    for field in REQUIRED_EXTRACTED_FIELDS:
        if not payload.get(field, "").strip():
            issues.append(ValidationIssue(candidate_id, field, "required field is blank"))
    for field in HUMAN_ADJUDICATION_FIELDS:
        if field not in payload:
            issues.append(ValidationIssue(candidate_id, field, "blank adjudication field is missing"))
    normalized_label = payload.get("normalized_label", "").strip()
    if normalized_label and normalized_label not in ALLOWED_NORMALIZED_LABELS:
        issues.append(ValidationIssue(candidate_id, "normalized_label", f"unexpected normalized label: {normalized_label}"))
    return issues


def json_schema() -> dict[str, Any]:
    properties = {field: {"type": "string"} for field in REVIEW_QUEUE_FIELDS}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Signal Engine Gold Review Queue Row",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(REVIEW_QUEUE_FIELDS),
    }
