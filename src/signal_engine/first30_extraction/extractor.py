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

FIRST100_CANDIDATE_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "fiscal_period",
    "suggested_label",
    "suggested_confidence",
    "evidence_object_id",
    "chunk_id",
    "retrieval_object_id",
    "object_type",
    "source_path",
    "source_sha256",
    "normalized_transcript_hash",
    "text_hash",
    "provenance_hash",
    "speaker_role",
    "transcript_section",
    "rule_id",
    "rule_version",
    "contamination_flags",
    "gold_status",
    "review_status",
    "raw_text_committed",
    "commit_allowed",
    "training_allowed",
]

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

FIRST100_RULE_VERSION = "first100_deterministic_v1"
FIRST100_TARGET_LABELS = [
    "guidance_revision",
    "guidance_statement",
    "analyst_pressure",
    "management_hedging",
    "uncertainty",
    "reassurance",
    "answer_shift",
    "neutral/no_signal",
]
FIRST100_RAW_TEXT_FIELDS = {
    "evidence_text",
    "raw_text",
    "text",
    "snippet",
    "quote",
    "final_evidence_text",
}
CLAIM_GUARDRAIL_TERMS = (
    "alpha",
    "buy",
    "sell",
    "trading advice",
    "causal",
    "causality",
    "statistical significance",
    "significant at",
)


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


def _chunk_id(row: dict[str, str]) -> str:
    if row.get("chunk_id"):
        return row["chunk_id"]
    source_ref = row.get("source_ref", "")
    if source_ref:
        return Path(source_ref).stem
    return ""


def _retrieval_sort_key(row: dict[str, str]) -> tuple[int, str, str]:
    priority = {
        "evidence_object": 0,
        "event_aligned_chunk": 1,
        "semantic_chunk": 2,
    }.get(row.get("object_type", ""), 9)
    return priority, row.get("case_id", ""), row.get("object_id", "")


def _first100_candidate_row(
    row: dict[str, str],
    *,
    label: str,
    rule_id: str,
    confidence: float,
    text_hash: str,
    contamination_flags: list[str],
) -> dict[str, str]:
    object_id = row.get("object_id", "")
    object_type = row.get("object_type", "")
    evidence_object_id = object_id if object_type == "evidence_object" else ""
    chunk_id = _chunk_id(row)
    candidate_id = stable_hash(
        {
            "first100": True,
            "object_id": object_id,
            "chunk_id": chunk_id,
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
        "suggested_label": label,
        "suggested_confidence": f"{confidence:.2f}",
        "evidence_object_id": evidence_object_id,
        "chunk_id": chunk_id,
        "retrieval_object_id": object_id,
        "object_type": object_type,
        "source_path": row.get("source_ref", ""),
        "source_sha256": row.get("source_sha256", ""),
        "normalized_transcript_hash": row.get("normalized_transcript_sha256", ""),
        "text_hash": text_hash or row.get("text_sha256", ""),
        "provenance_hash": row.get("provenance_hash", ""),
        "speaker_role": row.get("speaker") or row.get("speaker_role", ""),
        "transcript_section": row.get("section", ""),
        "rule_id": rule_id,
        "rule_version": FIRST100_RULE_VERSION,
        "contamination_flags": ";".join(sorted(set(contamination_flags))),
        "gold_status": "not_gold",
        "review_status": "pending_human_review",
        "raw_text_committed": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
    }


def expand_first100_candidates_from_retrieval_objects(
    retrieval_rows: list[dict[str, str]],
    *,
    target_count: int = 100,
    max_candidates_per_case_label: int = 8,
    max_semantic_neutral_per_case: int = 3,
) -> tuple[list[dict[str, str]], dict[str, Any], list[dict[str, str]]]:
    """Build metadata-only first100 review candidates from retrieval objects.

    The function reads local chunk text only to classify or suppress candidate rows.
    No source text is included in returned candidate or suppression records.
    """
    candidates: list[dict[str, str]] = []
    suppression_rows: list[dict[str, str]] = []
    suppressed = Counter()
    per_case_label = defaultdict(int)
    used_ids: set[str] = set()
    by_label_seen = Counter()
    object_counts = Counter(row.get("object_type", "") for row in retrieval_rows)
    case_ids = {row.get("case_id", "") for row in retrieval_rows if row.get("case_id")}

    non_semantic_rows = [row for row in retrieval_rows if row.get("object_type") != "semantic_chunk"]
    semantic_rows = sorted([row for row in retrieval_rows if row.get("object_type") == "semantic_chunk"], key=_retrieval_sort_key)
    semantic_first_by_case: list[dict[str, str]] = []
    semantic_rest: list[dict[str, str]] = []
    semantic_cases_seen: set[str] = set()
    for row in semantic_rows:
        case_id = row.get("case_id", "")
        if case_id and case_id not in semantic_cases_seen:
            semantic_first_by_case.append(row)
            semantic_cases_seen.add(case_id)
        else:
            semantic_rest.append(row)
    ordered_rows = sorted(non_semantic_rows, key=_retrieval_sort_key) + semantic_first_by_case + semantic_rest

    for row in ordered_rows:
        if len(candidates) >= target_count:
            break
        object_id = row.get("object_id", "")
        object_type = row.get("object_type", "")
        if object_id in used_ids:
            continue
        if row.get("raw_text_committed") != "false":
            suppressed["raw_text_committed"] += 1
            suppression_rows.append(
                {
                    "object_id": object_id,
                    "case_id": row.get("case_id", ""),
                    "ticker": row.get("ticker", ""),
                    "reason": "raw_text_committed",
                    "object_type": object_type,
                }
            )
            continue
        if object_type not in {"evidence_object", "event_aligned_chunk", "semantic_chunk"}:
            continue
        text = read_chunk_text(row.get("source_ref", ""))
        reason = suppressed_reason(text, row)
        if reason:
            suppressed[reason] += 1
            suppression_rows.append(
                {
                    "object_id": object_id,
                    "case_id": row.get("case_id", ""),
                    "ticker": row.get("ticker", ""),
                    "reason": reason,
                    "object_type": object_type,
                }
            )
            continue
        contamination_flags = ["machine_candidate_only", "not_gold"]
        if object_type == "semantic_chunk":
            label = "neutral/no_signal"
            rule_id = "semantic_fallback_neutral_diagnostic"
            confidence = 0.18
            contamination_flags.append("semantic_fallback_diagnostic")
            case_neutral_key = (row.get("case_id", ""), "semantic_neutral")
            if per_case_label[case_neutral_key] >= max_semantic_neutral_per_case:
                continue
        else:
            label, rule_id, confidence = classify_candidate(text, row)
        by_label_seen[label] += 1
        key = (row.get("case_id", ""), label)
        if per_case_label[key] >= max_candidates_per_case_label:
            continue
        text_hash = stable_hash({"source_ref": row.get("source_ref", ""), "text": text}) if text else row.get("text_sha256", "")
        candidates.append(
            _first100_candidate_row(
                row,
                label=label,
                rule_id=rule_id,
                confidence=confidence,
                text_hash=text_hash,
                contamination_flags=contamination_flags,
            )
        )
        per_case_label[key] += 1
        if object_type == "semantic_chunk":
            per_case_label[(row.get("case_id", ""), "semantic_neutral")] += 1
        used_ids.add(object_id)

    label_counts = Counter(row["suggested_label"] for row in candidates)
    case_counts = Counter(row["case_id"] for row in candidates)
    underrepresented = {
        label: 5 - label_counts.get(label, 0)
        for label in FIRST100_TARGET_LABELS
        if label_counts.get(label, 0) < 5
    }
    no_candidate_cases = sorted(case_id for case_id in case_ids if case_id not in case_counts)
    summary = {
        "candidate_count": len(candidates),
        "target_count": target_count,
        "target_met": len(candidates) >= target_count,
        "cases": len(case_counts),
        "candidate_cases": sorted(case_counts),
        "cases_without_candidates": no_candidate_cases,
        "labels": dict(sorted(label_counts.items())),
        "labels_seen_before_caps": dict(sorted(by_label_seen.items())),
        "underrepresented_labels": underrepresented,
        "object_counts": dict(sorted(object_counts.items())),
        "suppressed": dict(sorted(suppressed.items())),
        "suppressed_count": sum(suppressed.values()),
        "blockers": _first100_blockers(len(candidates), target_count, underrepresented, no_candidate_cases),
        "gold_labels_created": 0,
        "raw_text_committed": False,
    }
    return candidates, summary, suppression_rows


def _first100_blockers(
    candidate_count: int,
    target_count: int,
    underrepresented: dict[str, int],
    no_candidate_cases: list[str],
) -> list[str]:
    blockers: list[str] = []
    if candidate_count < target_count:
        blockers.append(f"target_not_met: {candidate_count}/{target_count} reviewable metadata-only candidates")
    if underrepresented:
        blockers.append("underrepresented_labels: " + ", ".join(f"{label} needs {count}" for label, count in sorted(underrepresented.items())))
    if no_candidate_cases:
        blockers.append("cases_without_candidates: " + ", ".join(no_candidate_cases[:20]))
    return blockers


def validate_first100_candidate_rows(
    rows: list[dict[str, str]],
    *,
    retrieval_object_ids: set[str] | None = None,
    evidence_ids: set[str] | None = None,
    chunk_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    required = set(FIRST100_CANDIDATE_FIELDS)
    seen_candidate_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = required - set(row)
        for field in sorted(missing):
            errors.append(f"row {index}: missing {field}")
        candidate_id = row.get("candidate_id", "")
        if not candidate_id:
            errors.append(f"row {index}: candidate_id is required")
        elif candidate_id in seen_candidate_ids:
            errors.append(f"row {index}: duplicate candidate_id {candidate_id}")
        seen_candidate_ids.add(candidate_id)
        label = row.get("suggested_label", "")
        if label not in LABELS:
            errors.append(f"row {index}: invalid suggested_label {label!r}")
        if row.get("gold_status") != "not_gold":
            errors.append(f"row {index}: gold_status must be not_gold")
        if row.get("review_status") != "pending_human_review":
            errors.append(f"row {index}: review_status must be pending_human_review")
        if row.get("raw_text_committed") != "false":
            errors.append(f"row {index}: raw_text_committed must be false")
        if row.get("commit_allowed") != "false":
            errors.append(f"row {index}: commit_allowed must be false")
        if row.get("training_allowed") != "false":
            errors.append(f"row {index}: training_allowed must be false for candidate rows")
        for field in ("source_sha256", "normalized_transcript_hash", "text_hash", "provenance_hash"):
            if not str(row.get(field, "")).startswith("sha256:"):
                errors.append(f"row {index}: {field} must be a sha256 hash")
        if not row.get("source_path"):
            errors.append(f"row {index}: source_path is required")
        if not row.get("evidence_object_id") and not row.get("chunk_id"):
            errors.append(f"row {index}: evidence_object_id or chunk_id is required")
        object_id = row.get("retrieval_object_id", "")
        if retrieval_object_ids is not None and object_id and object_id not in retrieval_object_ids:
            errors.append(f"row {index}: retrieval_object_id {object_id} does not exist")
        evidence_id = row.get("evidence_object_id", "")
        if evidence_ids is not None and evidence_id and evidence_id not in evidence_ids:
            errors.append(f"row {index}: evidence_object_id {evidence_id} does not exist")
        chunk_id = row.get("chunk_id", "")
        if chunk_ids is not None and chunk_id and chunk_id not in chunk_ids:
            errors.append(f"row {index}: chunk_id {chunk_id} does not exist")
        for forbidden_field in FIRST100_RAW_TEXT_FIELDS:
            if forbidden_field in row:
                errors.append(f"row {index}: raw text field {forbidden_field} is not allowed")
        joined = json.dumps({key: row.get(key, "") for key in ("rule_id", "suggested_label", "contamination_flags", "review_status", "gold_status")}, sort_keys=True).lower()
        source_type_blob = json.dumps({key: row.get(key, "") for key in ("source_type", "object_type")}, sort_keys=True).lower()
        if "external_dataset" in source_type_blob:
            errors.append(f"row {index}: external_dataset sources are not allowed")
        for term in CLAIM_GUARDRAIL_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", joined):
                errors.append(f"row {index}: forbidden claim/trading term {term!r}")
    return errors


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
