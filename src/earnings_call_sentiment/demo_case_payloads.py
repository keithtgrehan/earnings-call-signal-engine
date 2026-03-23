from __future__ import annotations

from copy import deepcopy
from typing import Any

NETFLIX_EVIDENCE_ROW_ORDER = [
    "transcript_growth_headwinds",
    "transcript_q2_paid_net_adds_guide",
    "transcript_ad_supported_option",
    "letter_growth_slowdown",
    "letter_headwinds",
    "letter_margin_framing",
    "financial_context_q1_2022",
]


def normalize_demo_evidence_rows(case_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_rows = _select_evidence_rows(case_id, rows)
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected_rows, start=1):
        audio_support = row.get("optional_audio_support") if isinstance(row.get("optional_audio_support"), dict) else {}
        source_type = str(row.get("source_type") or row.get("source") or "").strip()
        source_section_or_speaker = _normalize_source_section_or_speaker(row, source_type)
        source_excerpt = str(row.get("source_excerpt") or row.get("raw_excerpt") or row.get("quote") or "").strip()

        normalized_rows.append(
            {
                "row_id": row.get("row_id"),
                "case_id": case_id,
                "source_type": source_type,
                "source_excerpt": source_excerpt,
                "source_section_or_speaker": source_section_or_speaker,
                "extracted_signal": row.get("extracted_signal"),
                "plain_english_label": row.get("plain_english_label"),
                "why_it_matters": row.get("why_it_matters"),
                "ambiguity_note": row.get("ambiguity_note") or row.get("remaining_ambiguity"),
                "review_priority": row.get("review_priority"),
                "has_audio_support": bool(audio_support),
                "audio_row_id": audio_support.get("row_id") if audio_support else None,
                "audio_summary": audio_support.get("plain_english_audio_summary") if audio_support else None,
                "optional_timestamp": row.get("optional_timestamp"),
                "display_order": index,
            }
        )
    return normalized_rows


def normalize_demo_joined_audio_rows(case_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": row.get("row_id"),
            "case_id": case_id,
            "plain_english_label": row.get("plain_english_label"),
            "analyst_question_excerpt": row.get("analyst_question_excerpt"),
            "management_answer_excerpt": row.get("management_answer_excerpt"),
            "plain_english_interpretation": row.get("plain_english_interpretation"),
            "plain_english_audio_summary": row.get("plain_english_audio_summary"),
            "transcript_hedge_markers": row.get("transcript_hedge_markers") or [],
            "question_time_range": row.get("question_time_range"),
            "answer_time_range": row.get("answer_time_range"),
            "review_priority": row.get("review_priority"),
        }
        for row in rows
    ]


def normalize_demo_market_context(market_context: dict[str, Any]) -> dict[str, Any]:
    source = market_context.get("source") or {}
    primary_url = source.get("primary_url") or source.get("pricing_url") or source.get("url")
    secondary_url = source.get("secondary_url") or source.get("coverage_url")
    quarter = market_context.get("quarter")

    return {
        "case_id": market_context.get("case_id"),
        "company": market_context.get("company"),
        "quarter": quarter,
        "event_date": market_context.get("event_date"),
        "panel_title": f"Market context around the {quarter} release window" if quarter else "Market context",
        "key_extracted_signals": list(market_context.get("key_extracted_signals") or []),
        "market_reaction_window": deepcopy(market_context.get("market_reaction_window") or {}),
        "market_reaction_note": market_context.get("market_reaction_note"),
        "source": {
            "primary_url": primary_url,
            "secondary_url": secondary_url,
        },
        "caveat": market_context.get("caveat"),
    }


def build_demo_fixture_index(
    *,
    case_id: str,
    company: str,
    quarter: str,
    case_status: str,
    artifact_paths: dict[str, Any],
    preview_row_ids: list[str],
    notes: list[str],
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "company": company,
        "quarter": quarter,
        "case_status": case_status,
        "artifact_paths": deepcopy(artifact_paths),
        "preview_row_ids": preview_row_ids,
        "notes": list(notes),
    }


def inject_market_context(summary: dict[str, Any], market_context: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(summary)
    updated["market_context"] = deepcopy(market_context)
    return updated


def _select_evidence_rows(case_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if case_id != "netflix_q1_2022":
        return list(rows)

    row_by_id = {row.get("row_id"): row for row in rows}
    return [row_by_id[row_id] for row_id in NETFLIX_EVIDENCE_ROW_ORDER if row_id in row_by_id]


def _normalize_source_section_or_speaker(row: dict[str, Any], source_type: str) -> str:
    if row.get("source_section_or_speaker"):
        value = str(row["source_section_or_speaker"]).strip()
    else:
        speaker = str(row.get("speaker") or "").strip()
        section = str(row.get("section") or "").strip()
        if source_type == "transcript":
            if speaker and section == "question_and_answer":
                value = f"{speaker} / Q&A"
            elif speaker:
                value = speaker
            elif section == "question_and_answer":
                value = "Management / Q&A"
            else:
                value = "Transcript"
        elif source_type == "shareholder_letter":
            value = "Shareholder letter"
        elif source_type == "financials":
            value = "Income statement"
        else:
            value = speaker or section or source_type

    if source_type == "follow_up_transcript" and "secondary context" not in value.lower():
        value = f"{value} (secondary context)"
    return value
