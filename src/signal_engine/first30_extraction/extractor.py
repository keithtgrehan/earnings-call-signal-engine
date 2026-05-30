from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LABELS = {
    "guidance_revision",
    "guidance_statement",
    "analyst_pressure",
    "management_hedging",
    "uncertainty",
    "reassurance",
    "answer_shift",
    "neutral/no_signal",
}

CANDIDATE_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "fiscal_period",
    "label",
    "rule_id",
    "confidence",
    "review_status",
    "gold_status",
    "source_ref",
    "source_sha256",
    "normalized_transcript_sha256",
    "chunk_id",
    "retrieval_object_id",
    "evidence_id",
    "object_type",
    "chunk_type",
    "section",
    "speaker",
    "span_start_char",
    "span_end_char",
    "text_hash",
    "provenance_hash",
    "raw_text_committed",
    "commit_allowed",
    "training_allowed",
]

SUPPRESSION_MARKERS = {
    "safe harbor": "safe_harbor",
    "forward-looking statements": "safe_harbor",
    "non-gaap": "non_gaap",
    "non gaap": "non_gaap",
    "operator": "operator_instructions",
    "refinitiv": "vendor_disclaimer",
    "streetevents": "vendor_disclaimer",
    "factset": "vendor_disclaimer",
    "lseg": "vendor_disclaimer",
    "seeking alpha": "vendor_disclaimer",
    "motley fool": "vendor_disclaimer",
    "marketscreener": "vendor_disclaimer",
}

RULES: list[tuple[str, str, tuple[str, ...], float]] = [
    ("guidance_revision", "guidance_revision_terms", ("raise guidance", "raised guidance", "lower guidance", "lowered guidance", "narrow", "narrowed", "revis", "update guidance", "updated guidance"), 0.82),
    ("guidance_statement", "guidance_statement_terms", ("guidance", "outlook", "forecast", "expect", "expects", "expected", "we see", "we anticipate"), 0.70),
    ("analyst_pressure", "analyst_pressure_terms", ("pressure", "margin pressure", "why", "concern", "concerns", "challeng", "push", "pressed"), 0.66),
    ("management_hedging", "management_hedging_terms", ("may", "might", "could", "roughly", "approximately", "depends", "not prepared to", "too early"), 0.62),
    ("uncertainty", "uncertainty_terms", ("uncertain", "uncertainty", "visibility", "volatile", "macro", "headwind", "risk"), 0.64),
    ("reassurance", "reassurance_terms", ("confident", "comfortable", "on track", "reassur", "resilient", "strong demand"), 0.60),
    ("answer_shift", "answer_shift_terms", ("that said", "however", "to be clear", "let me frame", "different way", "not how we think"), 0.58),
]


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_chunk_text(path: str) -> str:
    if not path:
        return ""
    chunk_path = Path(path)
    if not chunk_path.exists():
        return ""
    return chunk_path.read_text(encoding="utf-8", errors="replace")


def suppressed_reason(text: str, row: dict[str, str]) -> str:
    lowered = text.lower()
    section = str(row.get("section", "")).lower()
    topic = str(row.get("topic", "")).lower()
    if section in {"safe_harbor", "operator"}:
        return section
    if topic in {"safe_harbor", "operator"}:
        return topic
    for marker, reason in SUPPRESSION_MARKERS.items():
        if marker in lowered:
            return reason
    if "great quarter" in lowered and not any(term in lowered for term in ("guidance", "outlook", "expect", "pressure", "uncertain")):
        return "generic_optimism"
    if "last year" in lowered and not any(term in lowered for term in ("guidance", "outlook", "expect", "revis")):
        return "historical_only_results"
    return ""


def classify_candidate(text: str, row: dict[str, str]) -> tuple[str, str, float]:
    lowered = text.lower()
    topic = str(row.get("topic", "")).lower()
    section = str(row.get("section", "")).lower()
    object_type = str(row.get("object_type", "")).lower()
    for label, rule_id, terms, confidence in RULES:
        if any(term in lowered for term in terms) or any(term in topic for term in terms):
            if label == "analyst_pressure" and "qa" not in section and object_type != "evidence_object":
                continue
            return label, rule_id, confidence
    if topic == "guidance_revision_candidate":
        return "guidance_revision", "chunk_type_guidance_revision_candidate", 0.78
    if topic == "guidance_statement":
        return "guidance_statement", "chunk_type_guidance_statement", 0.74
    return "neutral/no_signal", "no_signal_metadata_fallback", 0.20


def _candidate_row(row: dict[str, str], label: str, rule_id: str, confidence: float, text_hash: str) -> dict[str, str]:
    object_id = row.get("object_id", "")
    candidate_id = stable_hash(
        {
            "object_id": object_id,
            "label": label,
            "rule_id": rule_id,
            "text_hash": text_hash,
            "span_start_char": row.get("span_start_char", ""),
            "span_end_char": row.get("span_end_char", ""),
        }
    )[:32]
    return {
        "candidate_id": candidate_id,
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "fiscal_period": row.get("fiscal_period", ""),
        "label": label,
        "rule_id": rule_id,
        "confidence": f"{confidence:.2f}",
        "review_status": "pending_human_review",
        "gold_status": "not_gold",
        "source_ref": row.get("source_ref", ""),
        "source_sha256": row.get("source_sha256", ""),
        "normalized_transcript_sha256": row.get("normalized_transcript_sha256", ""),
        "chunk_id": Path(row.get("source_ref", "")).stem if row.get("source_ref") else "",
        "retrieval_object_id": object_id,
        "evidence_id": object_id if row.get("object_type") == "evidence_object" else "",
        "object_type": row.get("object_type", ""),
        "chunk_type": row.get("topic", ""),
        "section": row.get("section", ""),
        "speaker": row.get("speaker", ""),
        "span_start_char": row.get("span_start_char", ""),
        "span_end_char": row.get("span_end_char", ""),
        "text_hash": text_hash or row.get("text_sha256", ""),
        "provenance_hash": row.get("provenance_hash", ""),
        "raw_text_committed": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
    }


def extract_candidates_from_retrieval_objects(
    retrieval_rows: list[dict[str, str]],
    *,
    max_candidates_per_case_label: int = 3,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    candidates: list[dict[str, str]] = []
    suppressed = Counter()
    per_case_label = defaultdict(int)
    for row in retrieval_rows:
        if row.get("raw_text_committed") != "false":
            suppressed["raw_text_committed"] += 1
            continue
        if row.get("object_type") not in {"evidence_object", "event_aligned_chunk"}:
            continue
        text = read_chunk_text(row.get("source_ref", ""))
        reason = suppressed_reason(text, row)
        if reason:
            suppressed[reason] += 1
            continue
        label, rule_id, confidence = classify_candidate(text, row)
        key = (row.get("case_id", ""), label)
        if per_case_label[key] >= max_candidates_per_case_label:
            continue
        text_hash = stable_hash({"source_ref": row.get("source_ref", ""), "text": text}) if text else row.get("text_sha256", "")
        candidates.append(_candidate_row(row, label, rule_id, confidence, text_hash))
        per_case_label[key] += 1
    summary = {
        "candidate_count": len(candidates),
        "cases": len({row["case_id"] for row in candidates}),
        "labels": dict(sorted(Counter(row["label"] for row in candidates).items())),
        "suppressed": dict(sorted(suppressed.items())),
        "gold_labels_created": 0,
        "raw_text_committed": False,
    }
    return candidates, summary


def validate_candidate_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    required = set(CANDIDATE_FIELDS)
    raw_text_like = re.compile(r"\b(guidance|outlook|revenue|margin|question|answer|operator)\b", re.IGNORECASE)
    for index, row in enumerate(rows, start=1):
        missing = required - set(row)
        for field in sorted(missing):
            errors.append(f"row {index}: missing {field}")
        if row.get("label") not in LABELS:
            errors.append(f"row {index}: invalid label {row.get('label')!r}")
        if row.get("gold_status") != "not_gold":
            errors.append(f"row {index}: gold_status must be not_gold")
        if row.get("review_status") != "pending_human_review":
            errors.append(f"row {index}: review_status must be pending_human_review")
        if row.get("raw_text_committed") != "false" or row.get("commit_allowed") != "false":
            errors.append(f"row {index}: raw text and commits must remain disabled")
        for field in ("source_sha256", "normalized_transcript_sha256", "text_hash", "provenance_hash"):
            if not str(row.get(field, "")).startswith("sha256:"):
                errors.append(f"row {index}: {field} must be a sha256 hash")
        for forbidden_field in ("evidence_text", "raw_text", "text", "snippet", "quote"):
            if forbidden_field in row and raw_text_like.search(str(row[forbidden_field])):
                errors.append(f"row {index}: raw evidence-like text field {forbidden_field} is not allowed")
    return errors
