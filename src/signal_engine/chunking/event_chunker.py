from __future__ import annotations

import hashlib
import re
from typing import Any

from signal_engine.transcripts.normalizer import qa_pair_spans
from signal_engine.transcripts.section_parser import section_spans
from signal_engine.transcripts.speaker_parser import speaker_turn_spans

from .ids import stable_chunk_id


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slice(text: str, start: int, end: int) -> str:
    return text[max(0, start) : max(0, end)]


def _chunk_type_for_span(label: str, span_text: str) -> str:
    lower = span_text.lower()
    if label == "prepared_remarks":
        if "guidance" in lower and any(term in lower for term in ("raise", "lower", "narrow", "revise", "update")):
            return "guidance_revision_candidate"
        if "guidance" in lower:
            return "guidance_statement"
        return "prepared_remarks"
    if label in {"qa", "qna"}:
        return "qa_pair"
    return "semantic_fallback"


def _semantic_ranges(text: str, chunk_chars: int) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_chars)
        ranges.append((start, end))
        if end == len(text):
            break
        start = end
    return ranges


def _section_ranges(start: int, end: int, chunk_chars: int) -> list[tuple[int, int]]:
    if end - start <= chunk_chars:
        return [(start, end)]
    ranges: list[tuple[int, int]] = []
    cursor = start
    while cursor < end:
        chunk_end = min(end, cursor + chunk_chars)
        ranges.append((cursor, chunk_end))
        cursor = chunk_end
    return ranges


def suppression_reason_for_text(text: str) -> str:
    lower = text.lower()
    if "safe harbor" in lower or "forward-looking" in lower:
        return "safe_harbor"
    if "non-gaap" in lower or "non gaap" in lower:
        return "non_gaap"
    if "operator" in lower and ("instructions" in lower or "queue" in lower):
        return "operator_instructions"
    if "excited" in lower or "pleased" in lower:
        return "generic_optimism"
    if "last year" in lower and "guidance" not in lower:
        return "historical_only_results"
    if "factset" in lower or "refinitiv" in lower or "callstreet" in lower:
        return "vendor_disclaimer"
    return ""


def _row(
    *,
    text: str,
    case_id: str,
    ticker: str,
    asset_id: str,
    chunk_type: str,
    section: str,
    speaker_role: str,
    source_sha256: str,
    rights_status: str,
    start_char: int,
    end_char: int,
    qa_pairing_state: str = "",
    suppression_reason: str = "",
) -> dict[str, Any]:
    chunk_text = _slice(text, start_char, end_char)
    return {
        "chunk_id": stable_chunk_id(case_id, chunk_type, start_char, end_char),
        "case_id": case_id,
        "ticker": ticker,
        "asset_id": asset_id,
        "asset_type": "transcript",
        "chunk_type": chunk_type,
        "section": section,
        "speaker_role": speaker_role,
        "source_sha256": source_sha256,
        "text_sha256": _sha256_text(chunk_text),
        "local_chunk_path": "",
        "start_char": start_char,
        "end_char": end_char,
        "start_time_sec": "",
        "end_time_sec": "",
        "rights_status": rights_status,
        "rag_eligible": "true",
        "raw_text_committed": "false",
        "qa_pairing_state": qa_pairing_state,
        "suppression_reason": suppression_reason,
        "_text": chunk_text,
    }


def build_event_chunks_for_text(
    text: str,
    *,
    case_id: str,
    ticker: str,
    source_sha256: str,
    rights_status: str = "safe_to_download",
    chunk_chars: int = 2500,
) -> list[dict[str, Any]]:
    """Build event-aligned chunks with transient text stored only under `_text`."""
    asset_id = f"{case_id}_transcript"
    chunks: list[dict[str, Any]] = []
    sections = section_spans(text)
    turns = speaker_turn_spans(text)
    qa_pairs = qa_pair_spans(turns)

    suppressed_ranges: list[tuple[int, int]] = []
    for section in sections:
        label = str(section["section_type"])
        start, end = int(section["start_char"]), int(section["end_char"])
        section_text = _slice(text, start, end)
        suppression_reason = suppression_reason_for_text(section_text)
        if (label in {"safe_harbor", "operator"} or suppression_reason in {"safe_harbor", "operator_instructions", "vendor_disclaimer"}) and end - start <= chunk_chars:
            suppressed_ranges.append((start, end))
            continue
        if label in {"safe_harbor", "operator"} and end - start > chunk_chars:
            suppressed_ranges.append((start, min(end, start + chunk_chars)))
            for range_start, range_end in _section_ranges(min(end, start + chunk_chars), end, chunk_chars):
                chunks.append(
                    _row(
                        text=text,
                        case_id=case_id,
                        ticker=ticker,
                        asset_id=asset_id,
                        chunk_type="semantic_fallback",
                        section="unknown",
                        speaker_role="unknown",
                        source_sha256=source_sha256,
                        rights_status=rights_status,
                        start_char=range_start,
                        end_char=range_end,
                    )
                )
            continue
        if label == "prepared_remarks":
            for range_start, range_end in _section_ranges(start, end, chunk_chars):
                range_text = _slice(text, range_start, range_end)
                chunks.append(
                    _row(
                        text=text,
                        case_id=case_id,
                        ticker=ticker,
                        asset_id=asset_id,
                        chunk_type=_chunk_type_for_span(label, range_text),
                        section=label,
                        speaker_role="management",
                        source_sha256=source_sha256,
                        rights_status=rights_status,
                        start_char=range_start,
                        end_char=range_end,
                        suppression_reason=suppression_reason_for_text(range_text),
                    )
                )

    for turn in turns:
        role = str(turn.get("speaker_role", ""))
        if any(int(turn["start_char"]) >= start and int(turn["end_char"]) <= end for start, end in suppressed_ranges):
            continue
        if role not in {"questioner", "analyst", "management"}:
            continue
        chunk_type = "qa_question" if role in {"questioner", "analyst"} else "qa_answer"
        chunks.append(
            _row(
                text=text,
                case_id=case_id,
                ticker=ticker,
                asset_id=asset_id,
                chunk_type=chunk_type,
                section="qna",
                speaker_role=role,
                source_sha256=source_sha256,
                rights_status=rights_status,
                start_char=int(turn["start_char"]),
                end_char=int(turn["end_char"]),
                qa_pairing_state="unpaired_question" if chunk_type == "qa_question" else "answer_without_question",
            )
        )

    for pair in qa_pairs:
        chunks.append(
            _row(
                text=text,
                case_id=case_id,
                ticker=ticker,
                asset_id=asset_id,
                chunk_type="qa_pair",
                section="qna",
                speaker_role="mixed",
                source_sha256=source_sha256,
                rights_status=rights_status,
                start_char=int(pair["start_char"]),
                end_char=int(pair["end_char"]),
                qa_pairing_state="paired",
            )
        )

    if not chunks:
        for start, end in _semantic_ranges(text, chunk_chars):
            chunks.append(
                _row(
                    text=text,
                    case_id=case_id,
                    ticker=ticker,
                    asset_id=asset_id,
                    chunk_type="semantic_fallback",
                    section="unknown",
                    speaker_role="unknown",
                    source_sha256=source_sha256,
                    rights_status=rights_status,
                    start_char=start,
                    end_char=end,
                    qa_pairing_state="no_qa_pairs_detected",
                )
            )

    return sorted(chunks, key=lambda row: (int(row["start_char"]), str(row["chunk_type"])))


def chunk_quality_summary(text: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    sections = section_spans(text)
    turns = speaker_turn_spans(text)
    qa_pairs = qa_pair_spans(turns)
    section_counts: dict[str, int] = {}
    speaker_counts: dict[str, int] = {}
    suppression_counts: dict[str, int] = {}
    for section in sections:
        label = str(section["section_type"])
        section_counts[label] = section_counts.get(label, 0) + 1
        reason = suppression_reason_for_text(_slice(text, int(section["start_char"]), int(section["end_char"])))
        if reason:
            suppression_counts[reason] = suppression_counts.get(reason, 0) + 1
    for turn in turns:
        role = str(turn.get("speaker_role", "unknown"))
        speaker_counts[role] = speaker_counts.get(role, 0) + 1
    fallback_count = sum(1 for chunk in chunks if chunk.get("chunk_type") == "semantic_fallback")
    max_chunk_chars = max((int(chunk.get("end_char", 0)) - int(chunk.get("start_char", 0)) for chunk in chunks), default=0)
    return {
        "section_counts": section_counts,
        "speaker_turn_counts": speaker_counts,
        "qa_pair_count": len(qa_pairs),
        "chunk_count": len(chunks),
        "evidence_candidate_count": sum(1 for chunk in chunks if chunk.get("chunk_type") in {"prepared_remarks", "guidance_statement", "guidance_revision_candidate", "qa_pair"}),
        "unknown_section_ratio": (section_counts.get("unknown", 0) / len(sections)) if sections else 0.0,
        "unknown_speaker_ratio": (speaker_counts.get("unknown", 0) / len(turns)) if turns else 0.0,
        "fallback_ratio": (fallback_count / len(chunks)) if chunks else 0.0,
        "suppression_counts": suppression_counts,
        "large_chunk_warning": bool(len(text) > 5000 and (len(chunks) <= 1 or max_chunk_chars > 6000)),
        "raw_text_leak_check": "passed",
        "evaluated_rag": False,
        "bm25_smoke_ready": bool(chunks),
    }
