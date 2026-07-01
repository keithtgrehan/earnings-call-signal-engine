from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


def normalize_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def token_overlap_score(left: str, right: str) -> float:
    left_tokens = set(normalize_tokens(left))
    right_tokens = set(normalize_tokens(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def fuzzy_window_score(asr_text: str, transcript_text: str, *, window_chars: int = 6000, stride_chars: int = 1500) -> dict[str, Any]:
    if not asr_text.strip() or not transcript_text.strip():
        return {"score": 0.0, "start_char": 0, "end_char": 0, "method": "missing_text"}
    asr_prefix = asr_text[:window_chars]
    best = {"score": 0.0, "start_char": 0, "end_char": min(len(transcript_text), window_chars), "method": "fuzzy_window_scoring"}
    limit = max(1, len(transcript_text) - window_chars + 1)
    for start in range(0, limit, stride_chars):
        end = min(len(transcript_text), start + window_chars)
        window = transcript_text[start:end]
        overlap = token_overlap_score(asr_prefix, window)
        fuzzy = SequenceMatcher(None, " ".join(normalize_tokens(asr_prefix)[:400]), " ".join(normalize_tokens(window)[:400])).ratio()
        score = (0.7 * overlap) + (0.3 * fuzzy)
        if score > best["score"]:
            best = {"score": score, "start_char": start, "end_char": end, "method": "fuzzy_window_scoring"}
    return best


def prepared_section(text: str) -> tuple[str, int, int]:
    lowered = text.lower()
    qna_markers = ["question-and-answer", "question and answer", "q&a", "questions and answers"]
    qna_positions = [lowered.find(marker) for marker in qna_markers if lowered.find(marker) >= 0]
    end = min(qna_positions) if qna_positions else min(len(text), 25000)
    return text[:end], 0, end


def alignment_row(
    *,
    case_id: str,
    audio_sha256: str,
    transcript_sha256: str,
    alignment_status: str = "not_run",
    alignment_method: str = "",
    alignment_score: float = 0.0,
    matched_span_count: int = 0,
    matched_start_char: int = 0,
    matched_end_char: int = 0,
    partial_alignment: bool = False,
    review_required: bool = False,
    source_relation: str = "",
    notes: str = "Alignment requires local ASR segments and registered transcript spans.",
) -> dict[str, Any]:
    return {
        "alignment_id": f"{case_id}_audio_transcript_alignment",
        "case_id": case_id,
        "audio_asset_id": f"{case_id}_audio",
        "transcript_asset_id": f"{case_id}_transcript",
        "audio_sha256": audio_sha256,
        "transcript_sha256": transcript_sha256,
        "alignment_status": alignment_status,
        "alignment_method": alignment_method,
        "alignment_score": f"{alignment_score:.3f}",
        "matched_span_count": matched_span_count,
        "matched_transcript_start_char": matched_start_char,
        "matched_transcript_end_char": matched_end_char,
        "partial_alignment": partial_alignment,
        "review_required": review_required,
        "source_relation": source_relation,
        "raw_text_committed": False,
        "notes": notes,
    }
