from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .quality_checks import transcript_quality_flags
from .section_parser import section_spans
from .speaker_parser import speaker_turn_spans

NORMALIZER_VERSION = "normalized_transcript_v1"


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_case_period(case_id: str) -> tuple[str, str]:
    match = re.search(r"(20\d{2}).*?(q[1-4])", case_id, re.I)
    if not match:
        return "", ""
    return match.group(1), match.group(2).upper()


def qa_pair_spans(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    pending_question: dict[str, Any] | None = None
    for turn in turns:
        role = str(turn.get("speaker_role", ""))
        if role == "questioner":
            pending_question = turn
            continue
        if pending_question and role in {"management", "unknown"}:
            pairs.append(
                {
                    "qa_pair_id": f"qa_pair_{len(pairs) + 1:04d}",
                    "question_turn_id": pending_question["turn_id"],
                    "answer_turn_id": turn["turn_id"],
                    "start_char": pending_question["start_char"],
                    "end_char": turn["end_char"],
                }
            )
            pending_question = None
    return pairs


def normalize_transcript_text(
    text: str,
    *,
    case_id: str,
    ticker: str = "",
    company_name: str = "",
    exchange: str = "NYSE",
    source_url: str = "",
    source_asset_id: str = "",
    source_type: str = "manual_local_transcript",
    rights_status: str = "safe_to_download",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a normalized transcript object with spans/hashes only, never raw body text."""
    sections = section_spans(text)
    turns = speaker_turn_spans(text)
    qa_pairs = qa_pair_spans(turns)
    fiscal_year, fiscal_quarter = _parse_case_period(case_id)
    payload = {
        "case_id": case_id,
        "ticker": ticker,
        "company_name": company_name,
        "exchange": exchange,
        "fiscal_year": fiscal_year,
        "fiscal_quarter": fiscal_quarter,
        "call_date": "",
        "source_url": source_url,
        "source_asset_id": source_asset_id or f"{case_id}_transcript",
        "source_type": source_type,
        "rights_status": rights_status,
        "raw_sha256": _sha256_text(text),
        "source_sha256": _sha256_text(text),
        "normalizer_version": NORMALIZER_VERSION,
        "sections": sections,
        "speaker_turns": turns,
        "qa_pairs": qa_pairs,
        "prepared_remarks": [section["section_id"] for section in sections if section.get("section_type") == "prepared_remarks"],
        "provenance": provenance or {},
        "quality_flags": transcript_quality_flags(
            text,
            section_count=len(sections),
            speaker_turn_count=len(turns),
            qa_pair_count=len(qa_pairs),
        ),
        "raw_text_committed": False,
    }
    payload["normalized_sha256"] = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload
