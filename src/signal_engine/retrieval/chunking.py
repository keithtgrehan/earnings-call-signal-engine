from __future__ import annotations

from typing import Any


def redact_text(text: str, *, allowed: bool, max_chars: int = 160) -> str:
    if not allowed:
        return "[redacted: raw text commit not allowed]"
    return text[:max_chars]


def build_semantic_chunks(
    *,
    case_id: str,
    ticker: str,
    company: str,
    fiscal_period: str,
    source_ref: str,
    rights_tier: str,
    commit_allowed: bool,
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for index, section in enumerate(sections, start=1):
        chunks.append(
            {
                "object_id": f"{case_id}:semantic:{index}",
                "object_type": "semantic_chunk",
                "case_id": case_id,
                "ticker": ticker,
                "company": company,
                "fiscal_period": fiscal_period,
                "source_type": "manual_local",
                "source_ref": source_ref,
                "rights_tier": rights_tier,
                "commit_allowed": commit_allowed,
                "raw_text_commit_allowed": commit_allowed,
                "section": section.get("section", "unknown"),
                "speaker_role": "unknown",
                "topic": "",
                "span_hints": {
                    "char_start": section.get("char_start"),
                    "char_end": section.get("char_end"),
                },
                "provenance": {
                    "source_path": source_ref,
                    "span_ids": [f"{case_id}:section:{index}"],
                    "provenance_hash": section.get("provenance_hash", "synthetic_or_local_span"),
                },
                "deterministic_signal_refs": [],
                "evidence_text": "" if not commit_allowed else section.get("text", ""),
                "redacted_evidence_preview": redact_text(str(section.get("text", "")), allowed=commit_allowed),
                "retrieval_priority": 3,
                "deterministic_output_override_allowed": False,
            }
        )
    return chunks
