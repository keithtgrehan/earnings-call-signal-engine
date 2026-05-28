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
    if label == "qa":
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

    for section in sections:
        label = str(section["section_type"])
        start, end = int(section["start_char"]), int(section["end_char"])
        section_text = _slice(text, start, end)
        if label == "prepared_remarks":
            chunks.append(
                _row(
                    text=text,
                    case_id=case_id,
                    ticker=ticker,
                    asset_id=asset_id,
                    chunk_type=_chunk_type_for_span(label, section_text),
                    section=label,
                    speaker_role="management",
                    source_sha256=source_sha256,
                    rights_status=rights_status,
                    start_char=start,
                    end_char=end,
                )
            )

    for turn in turns:
        role = str(turn.get("speaker_role", ""))
        if role not in {"questioner", "management"}:
            continue
        chunk_type = "qa_question" if role == "questioner" else "qa_answer"
        chunks.append(
            _row(
                text=text,
                case_id=case_id,
                ticker=ticker,
                asset_id=asset_id,
                chunk_type=chunk_type,
                section="qa",
                speaker_role=role,
                source_sha256=source_sha256,
                rights_status=rights_status,
                start_char=int(turn["start_char"]),
                end_char=int(turn["end_char"]),
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
                section="qa",
                speaker_role="mixed",
                source_sha256=source_sha256,
                rights_status=rights_status,
                start_char=int(pair["start_char"]),
                end_char=int(pair["end_char"]),
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
                )
            )

    return sorted(chunks, key=lambda row: (int(row["start_char"]), str(row["chunk_type"])))
