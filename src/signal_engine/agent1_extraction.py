from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import hashlib
import re
from pathlib import Path
from typing import Any

TARGET_LABELS = {
    "guidance_revision",
    "analyst_pressure",
    "management_hedging",
    "uncertainty",
    "reassurance",
    "answer_shift",
    "neutral/no_signal",
}

MANDATORY_CONTAMINATION_FLAGS = ["raw_text_not_committed", "manual_local_source_only", "not_gold", "not_training_ready"]
SAFE_HARBOR_PATTERNS = ("safe harbor", "forward-looking statement", "non-gaap", "operator", "transcript disclaimer")
BUSINESS_TOPICS = (
    "revenue",
    "sales",
    "margin",
    "eps",
    "earnings",
    "profit",
    "demand",
    "pricing",
    "volume",
    "inventory",
    "guidance",
    "outlook",
    "cost",
    "cash flow",
    "pipeline",
)
GUIDANCE_CUES = ("guidance", "outlook", "forecast", "expect", "target", "project")
COMPARATORS = {
    "raised": ("raise", "raised", "increase", "increased", "higher"),
    "lowered": ("lower", "lowered", "reduce", "reduced", "below"),
    "narrowed": ("narrow", "narrowed"),
    "widened": ("widen", "widened"),
    "maintained": ("maintain", "maintained", "reiterate", "reiterated", "unchanged"),
    "withdrawn": ("withdraw", "withdrawn", "suspend", "suspended"),
}


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def section_transcript_text(text: str) -> dict[str, Any]:
    lower = text.lower()
    qa_start = _first_index(lower, ["question-and-answer", "question and answer", "q&a"])
    sections: list[dict[str, Any]] = []
    if qa_start >= 0:
        sections.append({"section": "prepared_remarks", "char_start": 0, "char_end": qa_start})
        sections.append({"section": "qa", "char_start": qa_start, "char_end": len(text)})
    else:
        sections.append({"section": "unknown", "char_start": 0, "char_end": len(text)})
    turns = _speaker_turns(text, qa_start=qa_start)
    return {"sections": sections, "speaker_turns": turns, "sectioning_confidence": "medium" if qa_start >= 0 else "low"}


def _first_index(text: str, needles: list[str]) -> int:
    positions = [text.find(needle) for needle in needles if text.find(needle) >= 0]
    return min(positions) if positions else -1


def _speaker_turns(text: str, *, qa_start: int) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    cursor = 0
    for line in text.splitlines():
        start = cursor
        end = cursor + len(line)
        cursor = end + 1
        stripped = line.strip()
        if not stripped:
            continue
        speaker_name = "unknown"
        body = stripped
        if ":" in stripped:
            speaker_name, body = stripped.split(":", 1)
            speaker_name = speaker_name.strip() or "unknown"
            body = body.strip()
        role = infer_speaker_role(speaker_name)
        section = "qa" if qa_start >= 0 and start >= qa_start else "prepared_remarks" if qa_start >= 0 else "unknown"
        turns.append(
            {
                "turn_index": len(turns),
                "speaker_name": speaker_name,
                "speaker_role": role,
                "transcript_section": section,
                "char_start": start,
                "char_end": end,
                "text": body,
            }
        )
    return turns


def infer_speaker_role(speaker_name: str) -> str:
    lowered = speaker_name.lower()
    if "operator" in lowered:
        return "operator"
    if "analyst" in lowered or "question" in lowered:
        return "analyst"
    if lowered and lowered != "unknown":
        return "management"
    return "unknown"


def generate_candidates_for_transcript(
    *,
    case_id: str,
    source_file: str,
    source_sha256: str,
    text: str,
    extractor_version: str = "agent1_rules_v1",
) -> list[dict[str, Any]]:
    sectioned = section_transcript_text(text)
    turns = sectioned["speaker_turns"]
    candidates: list[dict[str, Any]] = []
    for index, turn in enumerate(turns):
        body = str(turn["text"])
        if _is_boilerplate(body, turn["speaker_role"]):
            candidates.append(_candidate(case_id, source_file, source_sha256, turn, "neutral/no_signal", "neutral", "high", "boilerplate_safe_harbor", "neutral_boilerplate_v1"))
            continue
        candidates.extend(_guidance_candidates(case_id, source_file, source_sha256, turn))
        candidates.extend(_analyst_pressure_candidates(case_id, source_file, source_sha256, turn, turns, index))
        candidates.extend(_management_hedging_candidates(case_id, source_file, source_sha256, turn))
        candidates.extend(_uncertainty_candidates(case_id, source_file, source_sha256, turn))
        candidates.extend(_reassurance_candidates(case_id, source_file, source_sha256, turn))
        if turn["speaker_role"] == "analyst" and turn["transcript_section"] == "qa":
            answer = _next_management_turn(turns, index)
            if answer:
                candidates.append(_answer_shift_candidate(case_id, source_file, source_sha256, turn, answer))
    return deduplicate_candidates(candidates)


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def _is_boilerplate(text: str, speaker_role: str) -> bool:
    lowered = text.lower()
    return speaker_role == "operator" or any(pattern in lowered for pattern in SAFE_HARBOR_PATTERNS)


def _has_business_topic(text: str) -> bool:
    return _contains_any(text, BUSINESS_TOPICS)


def _period_present(text: str) -> bool:
    return bool(re.search(r"\b(20\d{2}|fy\s?\d{2,4}|q[1-4]|quarter|year|annual|full year)\b", text.lower()))


def _guidance_direction(text: str) -> str:
    lowered = text.lower()
    for direction, needles in COMPARATORS.items():
        if any(needle in lowered for needle in needles):
            return direction
    return "prior_missing"


def _guidance_candidates(case_id: str, source_file: str, source_sha256: str, turn: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(turn["text"])
    if turn["speaker_role"] != "management" or not _contains_any(text, GUIDANCE_CUES) or not _has_business_topic(text) or not _period_present(text):
        return []
    direction = _guidance_direction(text)
    bucket = "prior_missing" if direction == "prior_missing" else ""
    confidence = "low" if direction == "prior_missing" else "medium"
    return [_candidate(case_id, source_file, source_sha256, turn, "guidance_revision", direction, confidence, bucket, "guidance_revision_v1")]


def _analyst_pressure_candidates(
    case_id: str, source_file: str, source_sha256: str, turn: dict[str, Any], turns: list[dict[str, Any]], index: int
) -> list[dict[str, Any]]:
    text = str(turn["text"])
    pressure = ("why", "concern", "pressure", "what gives you confidence", "how can you", "why did")
    if turn["speaker_role"] != "analyst" or turn["transcript_section"] != "qa" or not _contains_any(text, pressure) or not _has_business_topic(text):
        return []
    has_answer = _next_management_turn(turns, index) is not None
    bucket = "" if has_answer else "analyst_only_unpaired"
    confidence = "medium" if has_answer else "low"
    return [_candidate(case_id, source_file, source_sha256, turn, "analyst_pressure", "pressure", confidence, bucket, "analyst_pressure_v1")]


def _management_hedging_candidates(case_id: str, source_file: str, source_sha256: str, turn: dict[str, Any]) -> list[dict[str, Any]]:
    hedges = ("uncertain", "hard to predict", "limited visibility", "not prepared to quantify", "too early to call", "depends on")
    text = str(turn["text"])
    if turn["speaker_role"] == "management" and _contains_any(text, hedges) and _has_business_topic(text):
        return [_candidate(case_id, source_file, source_sha256, turn, "management_hedging", "hedged", "medium", "", "management_hedging_v1")]
    return []


def _uncertainty_candidates(case_id: str, source_file: str, source_sha256: str, turn: dict[str, Any]) -> list[dict[str, Any]]:
    terms = ("uncertain", "volatility", "risk", "headwind", "unpredictable", "limited visibility", "hard to predict")
    text = str(turn["text"])
    if _contains_any(text, terms) and _has_business_topic(text):
        return [_candidate(case_id, source_file, source_sha256, turn, "uncertainty", "uncertain", "medium", "", "uncertainty_v1")]
    return []


def _reassurance_candidates(case_id: str, source_file: str, source_sha256: str, turn: dict[str, Any]) -> list[dict[str, Any]]:
    terms = ("confident", "comfortable", "on track", "well positioned", "reassure", "excited")
    text = str(turn["text"])
    if turn["speaker_role"] == "management" and _contains_any(text, terms):
        if _has_business_topic(text):
            return [_candidate(case_id, source_file, source_sha256, turn, "reassurance", "reassuring", "medium", "", "reassurance_v1")]
        return [_candidate(case_id, source_file, source_sha256, turn, "neutral/no_signal", "neutral", "medium", "generic_optimism", "neutral_generic_optimism_v1")]
    return []


def _next_management_turn(turns: list[dict[str, Any]], index: int) -> dict[str, Any] | None:
    for turn in turns[index + 1 : index + 4]:
        if turn.get("speaker_role") == "management":
            return turn
        if turn.get("speaker_role") == "analyst":
            return None
    return None


def _answer_shift_candidate(case_id: str, source_file: str, source_sha256: str, question: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    answer_text = str(answer.get("text", ""))
    lowered = answer_text.lower()
    if "not prepared to quantify" in lowered or "won't quantify" in lowered:
        shift_type = "refusal_to_quantify"
    elif "let me frame" in lowered or "reframe" in lowered:
        shift_type = "reframing"
    elif "as we said in prepared remarks" in lowered:
        shift_type = "prepared_remarks_repeat"
    elif _contains_any(answer_text, ("different topic", "instead", "focus on")):
        shift_type = "topic_shift"
    elif _contains_any(answer_text, ("partially", "some of that", "one part")):
        shift_type = "partial_answer"
    elif _contains_any(answer_text, ("uncertain", "limited visibility", "depends on")):
        shift_type = "hedged_answer"
    elif _contains_any(answer_text, ("confident", "comfortable", "on track")):
        shift_type = "reassuring_answer"
    else:
        shift_type = "direct_answer"
    combined_turn = dict(question)
    combined_turn["char_end"] = answer.get("char_end", question["char_end"])
    combined_turn["text"] = f"{question.get('text', '')} / {answer_text}"
    return _candidate(case_id, source_file, source_sha256, combined_turn, "answer_shift", shift_type, "medium", "", "answer_shift_v1")


def _candidate(
    case_id: str,
    source_file: str,
    source_sha256: str,
    turn: dict[str, Any],
    signal_type: str,
    suggested_direction: str,
    suggested_confidence: str,
    false_positive_bucket: str,
    rule_id: str,
) -> dict[str, Any]:
    evidence_span_ref = f"chars:{turn['char_start']}-{turn['char_end']}"
    seed = case_id + signal_type + evidence_span_ref + rule_id
    evidence_preview = _redact_preview(str(turn.get("text", "")))
    record = {
        "candidate_id": "sha256:" + hashlib.sha256(seed.encode("utf-8")).hexdigest(),
        "case_id": case_id,
        "signal_type": signal_type,
        "suggested_label": signal_type,
        "suggested_direction": suggested_direction,
        "suggested_confidence": suggested_confidence,
        "redacted_preview": evidence_preview,
        "evidence_span_ref": evidence_span_ref,
        "source_file": source_file,
        "source_sha256": source_sha256,
        "transcript_section": turn.get("transcript_section", "unknown"),
        "speaker_role": turn.get("speaker_role", "unknown"),
        "speaker_name": turn.get("speaker_name", "unknown"),
        "rule_id": rule_id,
        "rule_version": "1",
        "provenance_hash": sha256_text("|".join([case_id, source_file, evidence_span_ref, rule_id, source_sha256])),
        "text_hash": sha256_text(str(turn.get("text", ""))),
        "contamination_flags": MANDATORY_CONTAMINATION_FLAGS.copy(),
        "false_positive_bucket": false_positive_bucket,
        "gold_status": "not_gold",
        "review_status": "pending_human_review",
        "created_at": datetime.now(UTC).isoformat(),
        "extractor_version": "agent1_rules_v1",
    }
    if false_positive_bucket:
        record["contamination_flags"].append(false_positive_bucket)
    return record


def _redact_preview(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return ""
    return normalized[:96] + ("..." if len(normalized) > 96 else "")


def validate_candidate(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "candidate_id",
        "case_id",
        "signal_type",
        "suggested_label",
        "suggested_direction",
        "suggested_confidence",
        "evidence_span_ref",
        "source_file",
        "source_sha256",
        "transcript_section",
        "speaker_role",
        "rule_id",
        "rule_version",
        "provenance_hash",
        "text_hash",
        "contamination_flags",
        "false_positive_bucket",
        "gold_status",
        "review_status",
        "created_at",
        "extractor_version",
    }
    for field in sorted(required):
        if field not in row:
            errors.append(f"missing required field {field}")
    if row.get("signal_type") not in TARGET_LABELS:
        errors.append(f"invalid signal_type {row.get('signal_type')!r}")
    if not str(row.get("provenance_hash", "")).startswith("sha256:"):
        errors.append("missing provenance_hash")
    if not str(row.get("source_sha256", "")).startswith("sha256:"):
        errors.append("source_sha256 must be sha256-prefixed")
    flags = set(row.get("contamination_flags") or [])
    for flag in MANDATORY_CONTAMINATION_FLAGS:
        if flag not in flags:
            errors.append(f"missing contamination flag {flag}")
    if "evidence_text" in row:
        errors.append("candidate records must not commit raw evidence_text")
    if row.get("gold_status") != "not_gold":
        errors.append("candidate gold_status must remain not_gold")
    return errors


def validate_candidates(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for error in validate_candidate(row):
            errors.append(f"row {index}: {error}")
    return errors


def deduplicate_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (str(row.get("case_id", "")), str(row.get("evidence_span_ref", "")), str(row.get("rule_id", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def candidate_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("signal_type", "unknown")) for row in rows).items()))


def forbid_raw_transcript_output(path: Path) -> list[str]:
    normalized = str(path).replace("\\", "/").lower()
    if re.search(r"raw|transcript.*\.txt|\.vtt|\.srt|\.html?$", normalized):
        return ["raw transcript-like output paths are forbidden for Agent 1 candidate automation"]
    return []
