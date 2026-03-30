"""Supporting-only retrieval helpers for bounded demo case artifacts.

This module builds a file-based retrieval sidecar from deterministic case-pack
artifacts. The underlying transcript-first artifacts remain canonical.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import csv
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from earnings_call_sentiment.optional_runtime import load_multimodal_config

SCHEMA_VERSION = "1.0.0"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DEVICE = "cpu"
DEFAULT_EMBEDDING_BATCH_SIZE = 16
DEFAULT_EMBEDDING_MAX_LENGTH = 256

SOURCE_TYPE_TRANSCRIPT_CHUNK = "transcript_chunk"
SOURCE_TYPE_ANALYST_QUESTION = "analyst_question_span"
SOURCE_TYPE_QA_ANSWER = "qa_answer_span"
SOURCE_TYPE_GUIDANCE = "guidance_span"
SOURCE_TYPE_SHAREHOLDER_LETTER = "shareholder_letter_paragraph"
SOURCE_TYPE_PRESS_RELEASE = "press_release_paragraph"
SOURCE_TYPE_CURATED_MULTIMODAL = "curated_multimodal_moment"

SOURCE_TYPE_ORDER = {
    SOURCE_TYPE_TRANSCRIPT_CHUNK: 0,
    SOURCE_TYPE_ANALYST_QUESTION: 1,
    SOURCE_TYPE_QA_ANSWER: 2,
    SOURCE_TYPE_GUIDANCE: 3,
    SOURCE_TYPE_SHAREHOLDER_LETTER: 4,
    SOURCE_TYPE_PRESS_RELEASE: 5,
    SOURCE_TYPE_CURATED_MULTIMODAL: 6,
}

PRESSURE_QUERY_TOKENS = {
    "pressure",
    "slowdown",
    "decline",
    "miss",
    "risk",
    "headwind",
    "competition",
    "macro",
    "churn",
}

PRESSURE_TEXT_CUES = (
    "miss",
    "loss",
    "slower",
    "slowdown",
    "soft",
    "pressure",
    "lower",
    "churn",
    "competition",
    "macro",
    "headwind",
    "decline",
    "negative",
    "softer",
)

GUIDANCE_QUERY_TOKENS = {"guidance", "guide", "outlook", "forecast"}
ANALYST_QUERY_TOKENS = {
    "analyst",
    "question",
    "questions",
    "skepticism",
    "skeptical",
    "challenging",
    "challenge",
    "pressure",
}
COMPETITION_QUERY_TOKENS = {
    "competition",
    "competitive",
    "growth",
    "slowdown",
    "slowing",
    "macro",
    "headwind",
    "headwinds",
    "churn",
}
COMPETITION_TEXT_CUES = (
    "competition",
    "competitive",
    "lower growth",
    "slowing growth",
    "slowing revenue growth",
    "slowdown",
    "macro strain",
    "headwind",
    "penetration",
    "lower acquisition",
    "addressable market",
)
SKEPTICISM_STRONG_CUES = (
    "different than",
    "how have your views changed",
    "pressure",
    "competition",
    "macro",
    "miss",
    "loss",
    "churn",
    "read-through",
    "has that view changed",
    "not seeing",
)
SKEPTICISM_MILD_CUES = (
    "why",
    "how",
    "walk us through",
    "parse out",
    "talk us through",
    "help us understand",
    "could you",
)
LOW_INFORMATION_GUIDANCE_PATTERNS = (
    "nonguidance guidance",
    "not providing full year guidance",
)
GENERIC_GUIDANCE_CATEGORIES = {
    "guidance:other:year",
    "guidance:other:unknown",
    "guidance:outlook:unknown",
}


@dataclass(frozen=True)
class RetrievalRow:
    row_id: str
    case_id: str
    source_type: str
    source_artifact: str
    source_locator: str
    moment_id: str | None
    chunk_id: str | None
    span_id: str | None
    text: str
    start_time_s: float | None
    end_time_s: float | None
    deterministic_category: str | None
    plain_english_label: str | None
    top_8_showcase: bool | None
    supporting_only: bool
    section: str | None = None
    speaker: str | None = None
    speaker_role: str | None = None
    review_priority: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifact_paths"] = sorted(set(payload["artifact_paths"]))
        return payload


@dataclass(frozen=True)
class RetrievalBundle:
    rows: list[dict[str, Any]]
    manifest: dict[str, Any]
    embeddings: np.ndarray | None = None


@dataclass(frozen=True)
class RetrievalSearchResult:
    rank: int
    score: float
    lexical_score: float
    semantic_score: float | None
    retrieval_mode: str
    row: dict[str, Any]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_case_root(case_id: str) -> Path:
    return repo_root() / "data" / "demo_cases" / case_id


def default_bundle_dir(case_root: str | Path) -> Path:
    return Path(case_root).expanduser().resolve() / "demo" / "retrieval"


def bundle_prefix_for_case(case_id: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", case_id.strip().lower()).strip("_")
    company = token.split("_", 1)[0]
    return company or token or "case"


def _clean_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", _clean_text(value)).strip()


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _clean_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _slugify_token(value: str, *, fallback: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return token or fallback


def _humanize_token(value: str) -> str:
    return value.replace("_", " ").strip()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_text_key(*, text: str, start_time_s: float | None = None, end_time_s: float | None = None) -> tuple[Any, ...]:
    return (
        round(start_time_s, 3) if start_time_s is not None else None,
        round(end_time_s, 3) if end_time_s is not None else None,
        _normalize_space(text).lower(),
    )


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _query_bigrams(tokens: list[str]) -> list[str]:
    return [" ".join(pair) for pair in zip(tokens, tokens[1:], strict=False)]


def _pressure_adjustment(query_tokens: set[str], search_text: str) -> float:
    if not (query_tokens & PRESSURE_QUERY_TOKENS):
        return 0.0
    if any(cue in search_text for cue in PRESSURE_TEXT_CUES):
        return 0.4
    return -0.2


def _has_pressure_cues(search_text: str) -> bool:
    return any(cue in search_text for cue in PRESSURE_TEXT_CUES)


def _has_competition_cues(search_text: str) -> bool:
    return any(cue in search_text for cue in COMPETITION_TEXT_CUES)


def _skepticism_cue_score(search_text: str) -> float:
    strong_hits = sum(1 for cue in SKEPTICISM_STRONG_CUES if cue in search_text)
    mild_hits = sum(1 for cue in SKEPTICISM_MILD_CUES if cue in search_text)
    return float(strong_hits) + (0.35 * float(mild_hits))


def _structured_duplicate_texts(rows: list[dict[str, Any]]) -> set[str]:
    duplicates: set[str] = set()
    for row in rows:
        if str(row.get("source_type")) == SOURCE_TYPE_TRANSCRIPT_CHUNK:
            continue
        normalized_text = _normalize_space(row.get("text")).lower()
        if normalized_text:
            duplicates.add(normalized_text)
    return duplicates


def _text_source_type_index(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for row in rows:
        normalized_text = _normalize_space(row.get("text")).lower()
        if not normalized_text:
            continue
        index.setdefault(normalized_text, set()).add(str(row.get("source_type") or ""))
    return index


def _row_ranking_adjustment(
    row: dict[str, Any],
    *,
    query_tokens: set[str],
    duplicate_structured_texts: set[str],
    text_source_types: dict[str, set[str]],
) -> float:
    search_text = _row_search_text(row).lower()
    source_type = str(row.get("source_type") or "")
    normalized_text = _normalize_space(row.get("text")).lower()
    word_count = len(_tokenize(str(row.get("text") or "")))
    deterministic_category = str(row.get("deterministic_category") or "")
    plain_label = str(row.get("plain_english_label") or "")
    speaker_role = str(row.get("speaker_role") or "").lower()

    adjustment = 0.0

    if word_count < 6:
        adjustment -= 0.35
    elif word_count < 10:
        adjustment -= 0.18
    elif word_count < 18:
        adjustment -= 0.06

    if any(pattern in search_text for pattern in LOW_INFORMATION_GUIDANCE_PATTERNS):
        adjustment -= 0.45

    if source_type == SOURCE_TYPE_GUIDANCE:
        adjustment += 0.12
        if plain_label.startswith("guidance pressure"):
            adjustment += 0.08
        if deterministic_category in GENERIC_GUIDANCE_CATEGORIES and not _has_pressure_cues(search_text):
            adjustment -= 0.16
    elif source_type == SOURCE_TYPE_QA_ANSWER:
        adjustment += 0.10
    elif source_type == SOURCE_TYPE_ANALYST_QUESTION:
        adjustment += 0.08
    elif source_type in {SOURCE_TYPE_SHAREHOLDER_LETTER, SOURCE_TYPE_PRESS_RELEASE}:
        adjustment += 0.08 if deterministic_category else 0.04
    elif source_type == SOURCE_TYPE_TRANSCRIPT_CHUNK:
        adjustment -= 0.04

    if row.get("top_8_showcase") is True:
        adjustment += 0.05

    if source_type == SOURCE_TYPE_TRANSCRIPT_CHUNK and normalized_text in duplicate_structured_texts:
        adjustment -= 0.22

    analyst_focus = bool(query_tokens & ANALYST_QUERY_TOKENS)
    guidance_focus = bool(query_tokens & GUIDANCE_QUERY_TOKENS)
    pressure_focus = bool(query_tokens & PRESSURE_QUERY_TOKENS)
    competition_focus = bool(query_tokens & COMPETITION_QUERY_TOKENS)
    related_source_types = text_source_types.get(normalized_text, set())

    if analyst_focus:
        skepticism_score = _skepticism_cue_score(search_text)
        if source_type == SOURCE_TYPE_ANALYST_QUESTION:
            adjustment += 0.18
            if skepticism_score >= 1.0:
                adjustment += 0.12
            elif skepticism_score >= 0.35:
                adjustment += 0.06
        elif source_type == SOURCE_TYPE_QA_ANSWER:
            adjustment += 0.05
            if _has_pressure_cues(search_text):
                adjustment += 0.03
        elif source_type == SOURCE_TYPE_TRANSCRIPT_CHUNK and speaker_role == "analyst":
            adjustment -= 0.03
        elif source_type == SOURCE_TYPE_GUIDANCE and not guidance_focus:
            adjustment -= 0.08

    if guidance_focus:
        if source_type == SOURCE_TYPE_GUIDANCE:
            adjustment += 0.12
        elif source_type in {SOURCE_TYPE_SHAREHOLDER_LETTER, SOURCE_TYPE_PRESS_RELEASE} and deterministic_category:
            adjustment += 0.05
        elif source_type == SOURCE_TYPE_TRANSCRIPT_CHUNK and speaker_role == "management":
            adjustment -= 0.02

    if pressure_focus:
        if source_type == SOURCE_TYPE_GUIDANCE and _has_pressure_cues(search_text):
            adjustment += 0.06
        elif source_type in {SOURCE_TYPE_SHAREHOLDER_LETTER, SOURCE_TYPE_PRESS_RELEASE} and deterministic_category:
            adjustment += 0.04

    if competition_focus:
        if source_type == SOURCE_TYPE_QA_ANSWER:
            if _has_competition_cues(search_text):
                adjustment += 0.18
            if any(cue in search_text for cue in ("lower growth", "slowing growth", "slowdown")):
                adjustment += 0.04
        elif source_type in {SOURCE_TYPE_SHAREHOLDER_LETTER, SOURCE_TYPE_PRESS_RELEASE}:
            if deterministic_category == "competitive_and_macro_headwinds":
                adjustment += 0.22
            elif deterministic_category == "account_sharing_and_monetization":
                adjustment += 0.18
            elif deterministic_category == "paid_net_adds_or_outlook":
                adjustment += 0.08
            elif _has_competition_cues(search_text):
                adjustment += 0.10
        elif source_type == SOURCE_TYPE_ANALYST_QUESTION and _has_competition_cues(search_text):
            adjustment += 0.08
        elif source_type == SOURCE_TYPE_GUIDANCE and not guidance_focus:
            adjustment -= 0.08
            if _has_competition_cues(search_text):
                adjustment += 0.03
        elif source_type == SOURCE_TYPE_TRANSCRIPT_CHUNK and _has_competition_cues(search_text):
            adjustment -= 0.02

    if (
        source_type == SOURCE_TYPE_GUIDANCE
        and not guidance_focus
        and {SOURCE_TYPE_QA_ANSWER, SOURCE_TYPE_ANALYST_QUESTION} & related_source_types
    ):
        adjustment -= 0.14

    return round(adjustment, 6)


def _bundle_file_names(case_id: str) -> dict[str, str]:
    prefix = bundle_prefix_for_case(case_id)
    return {
        "rows": f"{prefix}_retrieval_rows.jsonl",
        "manifest": f"{prefix}_retrieval_manifest.json",
        "embeddings": f"{prefix}_retrieval_embeddings.npy",
    }


def _build_block_timing_index(segment_metadata: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    block_index: dict[int, dict[str, Any]] = {}
    for row in segment_metadata:
        block_id = int(row["block_id"])
        entry = block_index.setdefault(
            block_id,
            {
                "block_id": block_id,
                "start_time_s": None,
                "end_time_s": None,
                "segment_ids": [],
                "segment_texts": [],
                "section": _clean_text(row.get("section")),
                "speaker": _clean_text(row.get("speaker")),
                "speaker_role": _clean_text(row.get("speaker_role")),
            },
        )
        start_time_s = _coerce_float(row.get("start"))
        end_time_s = _coerce_float(row.get("end"))
        if start_time_s is not None:
            current = entry["start_time_s"]
            entry["start_time_s"] = start_time_s if current is None else min(current, start_time_s)
        if end_time_s is not None:
            current = entry["end_time_s"]
            entry["end_time_s"] = end_time_s if current is None else max(current, end_time_s)
        if "segment_id" in row:
            entry["segment_ids"].append(int(row["segment_id"]))
        text = _clean_text(row.get("text"))
        if text:
            entry["segment_texts"].append(text)
    return block_index


def _load_transcript_blocks(case_root: Path) -> list[dict[str, Any]]:
    payload = _read_json(case_root / "processed" / "transcript_text" / "transcript_sectioned.json")
    blocks = payload.get("blocks", []) if isinstance(payload, dict) else payload
    if not isinstance(blocks, list):
        raise RuntimeError("transcript_sectioned.json did not contain a list of blocks.")
    return [row for row in blocks if isinstance(row, dict)]


def _load_segment_metadata(case_root: Path) -> list[dict[str, Any]]:
    payload = _read_json(case_root / "processed" / "chunks" / "segment_metadata.json")
    segments = payload.get("segments", []) if isinstance(payload, dict) else payload
    if not isinstance(segments, list):
        raise RuntimeError("segment_metadata.json did not contain a list of segments.")
    return [row for row in segments if isinstance(row, dict)]


def _load_chunks_scored(case_root: Path) -> list[dict[str, Any]]:
    return _read_jsonl(case_root / "processed" / "chunks" / "chunks_scored.jsonl")


def _build_transcript_chunk_rows(
    *,
    case_id: str,
    chunks_scored: list[dict[str, Any]],
    segment_metadata: list[dict[str, Any]],
) -> list[RetrievalRow]:
    if len(chunks_scored) != len(segment_metadata):
        raise RuntimeError(
            "Expected scored chunks and segment metadata to align one-to-one, but found "
            f"{len(chunks_scored)} scored rows and {len(segment_metadata)} metadata rows."
        )

    rows: list[RetrievalRow] = []
    for scored, meta in zip(chunks_scored, segment_metadata, strict=True):
        segment_id = int(meta["segment_id"])
        sentiment = _clean_text(scored.get("sentiment"))
        row = RetrievalRow(
            row_id=f"transcript_chunk_{segment_id:04d}",
            case_id=case_id,
            source_type=SOURCE_TYPE_TRANSCRIPT_CHUNK,
            source_artifact="processed/chunks/chunks_scored.jsonl",
            source_locator=f"segment_id:{segment_id}",
            moment_id=None,
            chunk_id=f"segment_{segment_id:04d}",
            span_id=None,
            text=_normalize_space(scored.get("text")),
            start_time_s=_coerce_float(scored.get("start")),
            end_time_s=_coerce_float(scored.get("end")),
            deterministic_category=f"sentiment:{sentiment.lower()}" if sentiment else None,
            plain_english_label=f"{_humanize_token(_clean_text(meta.get('speaker_role')) or 'transcript')} chunk",
            top_8_showcase=None,
            supporting_only=True,
            section=_clean_text(meta.get("section")) or None,
            speaker=_clean_text(meta.get("speaker")) or None,
            speaker_role=_clean_text(meta.get("speaker_role")) or None,
            artifact_paths=[
                "processed/chunks/chunks_scored.jsonl",
                "processed/chunks/segment_metadata.json",
            ],
            metadata={
                "segment_id": segment_id,
                "block_id": int(meta["block_id"]),
                "sentiment_label": sentiment or None,
                "sentiment_score": _coerce_float(scored.get("score")),
                "sentiment_signed_score": _coerce_float(scored.get("signed_score")),
            },
        )
        rows.append(row)
    return rows


def _build_qa_span_rows(
    *,
    case_id: str,
    transcript_blocks: list[dict[str, Any]],
    block_timings: dict[int, dict[str, Any]],
) -> list[RetrievalRow]:
    rows: list[RetrievalRow] = []
    current_question: dict[str, Any] | None = None
    current_answers: list[dict[str, Any]] = []
    qa_pair_id = 0

    def flush_pair() -> None:
        nonlocal current_question, current_answers
        if current_question is None:
            current_answers = []
            return
        if not current_answers:
            answer_text = ""
            answer_block_ids: list[int] = []
            answer_start = None
            answer_end = None
            answer_speakers: list[str] = []
        else:
            answer_text = " ".join(_normalize_space(item.get("text")) for item in current_answers)
            answer_block_ids = [int(item["block_id"]) for item in current_answers]
            answer_speakers = [
                speaker
                for speaker in [_clean_text(item.get("speaker")) for item in current_answers]
                if speaker
            ]
            starts = [
                block_timings[int(item["block_id"])]["start_time_s"]
                for item in current_answers
                if int(item["block_id"]) in block_timings
                and block_timings[int(item["block_id"])]["start_time_s"] is not None
            ]
            ends = [
                block_timings[int(item["block_id"])]["end_time_s"]
                for item in current_answers
                if int(item["block_id"]) in block_timings
                and block_timings[int(item["block_id"])]["end_time_s"] is not None
            ]
            answer_start = min(starts) if starts else None
            answer_end = max(ends) if ends else None

        question_block_id = int(current_question["block_id"])
        question_timing = block_timings.get(question_block_id, {})
        question_speaker = _clean_text(current_question.get("speaker")) or None
        rows.append(
            RetrievalRow(
                row_id=f"qa_pair_{qa_pair_id:03d}_question",
                case_id=case_id,
                source_type=SOURCE_TYPE_ANALYST_QUESTION,
                source_artifact="processed/transcript_text/transcript_sectioned.json",
                source_locator=f"qa_pair_id:{qa_pair_id}/question/block_id:{question_block_id}",
                moment_id=f"qa_pair_{qa_pair_id:03d}",
                chunk_id=None,
                span_id=f"qa_pair_{qa_pair_id:03d}_question",
                text=_normalize_space(current_question.get("text")),
                start_time_s=question_timing.get("start_time_s"),
                end_time_s=question_timing.get("end_time_s"),
                deterministic_category="analyst_question",
                plain_english_label="analyst question span",
                top_8_showcase=None,
                supporting_only=True,
                section=_clean_text(current_question.get("section")) or None,
                speaker=question_speaker,
                speaker_role=_clean_text(current_question.get("speaker_role")) or None,
                artifact_paths=[
                    "processed/transcript_text/transcript_sectioned.json",
                    "processed/qa_pairs/qa_pairs.json",
                    "processed/chunks/segment_metadata.json",
                ],
                metadata={
                    "qa_pair_id": qa_pair_id,
                    "block_ids": [question_block_id],
                    "segment_ids": question_timing.get("segment_ids", []),
                    "paired_answer_span_id": f"qa_pair_{qa_pair_id:03d}_answer",
                },
            )
        )
        if answer_text:
            rows.append(
                RetrievalRow(
                    row_id=f"qa_pair_{qa_pair_id:03d}_answer",
                    case_id=case_id,
                    source_type=SOURCE_TYPE_QA_ANSWER,
                    source_artifact="processed/transcript_text/transcript_sectioned.json",
                    source_locator=(
                        f"qa_pair_id:{qa_pair_id}/answer/block_ids:{','.join(str(value) for value in answer_block_ids)}"
                    ),
                    moment_id=f"qa_pair_{qa_pair_id:03d}",
                    chunk_id=None,
                    span_id=f"qa_pair_{qa_pair_id:03d}_answer",
                    text=_normalize_space(answer_text),
                    start_time_s=answer_start,
                    end_time_s=answer_end,
                    deterministic_category="management_answer",
                    plain_english_label="management answer span",
                    top_8_showcase=None,
                    supporting_only=True,
                    section=_clean_text(current_question.get("section")) or None,
                    speaker=", ".join(dict.fromkeys(answer_speakers)) or None,
                    speaker_role="management",
                    artifact_paths=[
                        "processed/transcript_text/transcript_sectioned.json",
                        "processed/qa_pairs/qa_pairs.json",
                        "processed/chunks/segment_metadata.json",
                    ],
                    metadata={
                        "qa_pair_id": qa_pair_id,
                        "block_ids": answer_block_ids,
                        "answer_speakers": list(dict.fromkeys(answer_speakers)),
                        "segment_ids": [
                            segment_id
                            for block_id in answer_block_ids
                            for segment_id in block_timings.get(block_id, {}).get("segment_ids", [])
                        ],
                        "paired_question_span_id": f"qa_pair_{qa_pair_id:03d}_question",
                    },
                )
            )
        current_question = None
        current_answers = []

    for block in transcript_blocks:
        section = _clean_text(block.get("section")).lower()
        speaker_role = _clean_text(block.get("speaker_role")).lower()
        if section != "question_and_answer":
            continue
        if speaker_role == "analyst":
            if current_question is not None:
                flush_pair()
            qa_pair_id += 1
            current_question = block
            current_answers = []
            continue
        if current_question is not None and speaker_role == "management":
            current_answers.append(block)
    if current_question is not None:
        flush_pair()
    return rows


def _build_chunk_lookup(rows: Iterable[RetrievalRow]) -> dict[tuple[Any, ...], RetrievalRow]:
    return {
        _normalize_text_key(
            text=row.text,
            start_time_s=row.start_time_s,
            end_time_s=row.end_time_s,
        ): row
        for row in rows
        if row.source_type == SOURCE_TYPE_TRANSCRIPT_CHUNK
    }


def _guidance_label(topic: str | None, period: str | None) -> str:
    parts = ["guidance span"]
    if topic:
        parts.append(_humanize_token(topic))
    if period:
        parts.append(str(period).lower())
    return " / ".join(parts)


def _guidance_descriptor(text: str) -> str:
    lowered = text.lower()
    if any(
        cue in lowered
        for cue in (
            "miss",
            "loss",
            "lose",
            "slower",
            "slowdown",
            "soft",
            "pressure",
            "lower",
            "churn",
            "competition",
            "macro",
            "headwind",
            "decline",
        )
    ):
        return "guidance pressure"
    if any(
        cue in lowered
        for cue in (
            "confident",
            "better",
            "strong",
            "improve",
            "growth",
            "excited",
        )
    ):
        return "guidance support"
    return "guidance span"


def _guidance_plain_label(text: str, topic: str | None, period: str | None) -> str:
    parts = [_guidance_descriptor(text)]
    if topic:
        parts.append(_humanize_token(topic))
    if period:
        parts.append(str(period).lower())
    return " / ".join(parts)


def _build_guidance_rows(
    *,
    case_id: str,
    guidance_rows: list[dict[str, Any]],
    transcript_chunk_lookup: dict[tuple[Any, ...], RetrievalRow],
) -> list[RetrievalRow]:
    built: list[RetrievalRow] = []
    for index, row in enumerate(guidance_rows, start=1):
        text = _normalize_space(row.get("text"))
        start_time_s = _coerce_float(row.get("start"))
        end_time_s = _coerce_float(row.get("end"))
        chunk_row = transcript_chunk_lookup.get(
            _normalize_text_key(text=text, start_time_s=start_time_s, end_time_s=end_time_s)
        )
        topic = _clean_text(row.get("topic")) or None
        period = _clean_text(row.get("period")) or None
        deterministic_category = None
        if topic and period:
            deterministic_category = f"guidance:{topic.lower()}:{period.lower()}"
        elif topic:
            deterministic_category = f"guidance:{topic.lower()}"
        built.append(
            RetrievalRow(
                row_id=f"guidance_span_{index:03d}",
                case_id=case_id,
                source_type=SOURCE_TYPE_GUIDANCE,
                source_artifact="processed/signals/guidance.csv",
                source_locator=f"guidance_row:{index}",
                moment_id=None,
                chunk_id=chunk_row.chunk_id if chunk_row is not None else None,
                span_id=f"guidance_span_{index:03d}",
                text=text,
                start_time_s=start_time_s,
                end_time_s=end_time_s,
                deterministic_category=deterministic_category,
                plain_english_label=_guidance_plain_label(text, topic, period),
                top_8_showcase=None,
                supporting_only=True,
                section=chunk_row.section if chunk_row is not None else None,
                speaker=chunk_row.speaker if chunk_row is not None else None,
                speaker_role=chunk_row.speaker_role if chunk_row is not None else None,
                artifact_paths=[
                    "processed/signals/guidance.csv",
                    "processed/chunks/chunks_scored.jsonl",
                ],
                metadata={
                    "guidance_strength": _coerce_float(row.get("guidance_strength")),
                    "topic": topic,
                    "period": period,
                    "matched_cues": _clean_text(row.get("matched_cues")) or None,
                    "numbers": _clean_text(row.get("numbers")) or None,
                    "source_chunk_row_id": chunk_row.row_id if chunk_row is not None else None,
                },
            )
        )
    return built


def _paragraphs_from_text(text: str) -> list[str]:
    return [
        _normalize_space(part)
        for part in re.split(r"\n\s*\n", _clean_text(text))
        if _normalize_space(part)
    ]


def _resolve_management_document_sources(case_root: Path) -> dict[str, str]:
    shareholder_text = case_root / "processed" / "transcript_text" / "shareholder_letter_text.txt"
    shareholder_evidence = case_root / "processed" / "signals" / "shareholder_letter_evidence.json"
    if shareholder_text.exists() and shareholder_evidence.exists():
        return {
            "text_path": "processed/transcript_text/shareholder_letter_text.txt",
            "evidence_path": "processed/signals/shareholder_letter_evidence.json",
            "source_type": SOURCE_TYPE_SHAREHOLDER_LETTER,
            "speaker": "shareholder letter",
        }

    press_release_text = case_root / "processed" / "transcript_text" / "press_release_text.txt"
    press_release_evidence = case_root / "processed" / "signals" / "press_release_evidence.json"
    if press_release_text.exists() and press_release_evidence.exists():
        return {
            "text_path": "processed/transcript_text/press_release_text.txt",
            "evidence_path": "processed/signals/press_release_evidence.json",
            "source_type": SOURCE_TYPE_PRESS_RELEASE,
            "speaker": "press release",
        }

    raise RuntimeError(
        "Could not find a supported management-document text/evidence pair under the case package. "
        "Expected shareholder_letter_* or press_release_* artifacts."
    )


def _build_management_document_rows(
    *,
    case_id: str,
    document_text: str,
    document_evidence: dict[str, Any],
    source_type: str,
    text_artifact_path: str,
    evidence_artifact_path: str,
    speaker_label: str,
) -> list[RetrievalRow]:
    paragraphs = _paragraphs_from_text(document_text)
    evidence_map: dict[str, list[str]] = {}
    for label, paragraph in (document_evidence.get("evidence", {}) or {}).items():
        normalized = _normalize_space(paragraph)
        if not normalized:
            continue
        evidence_map.setdefault(normalized, []).append(str(label))

    rows: list[RetrievalRow] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        labels = sorted(evidence_map.get(paragraph, []))
        label = labels[0] if labels else None
        label_prefix = (
            "shareholder letter"
            if source_type == SOURCE_TYPE_SHAREHOLDER_LETTER
            else "press release"
        )
        rows.append(
            RetrievalRow(
                row_id=f"{source_type}_{index:03d}",
                case_id=case_id,
                source_type=source_type,
                source_artifact=text_artifact_path,
                source_locator=f"paragraph:{index}",
                moment_id=None,
                chunk_id=None,
                span_id=f"{source_type}_{index:03d}",
                text=paragraph,
                start_time_s=None,
                end_time_s=None,
                deterministic_category=label,
                plain_english_label=(
                    f"{label_prefix} / {_humanize_token(label)}" if label else f"{label_prefix} paragraph"
                ),
                top_8_showcase=None,
                supporting_only=True,
                section=label_prefix.replace(" ", "_"),
                speaker=speaker_label,
                speaker_role="management_document",
                artifact_paths=[
                    text_artifact_path,
                    evidence_artifact_path,
                ],
                metadata={
                    "paragraph_index": index,
                    "matched_evidence_labels": labels,
                },
            )
        )
    return rows


def _build_curated_multimodal_rows(
    *,
    case_id: str,
    audio_review_rows: list[dict[str, Any]],
    qa_answer_rows: dict[int, RetrievalRow],
) -> list[RetrievalRow]:
    built: list[RetrievalRow] = []
    for row in audio_review_rows:
        qa_pair_id = int(row["qa_pair_id"])
        answer_row = qa_answer_rows.get(qa_pair_id)
        if answer_row is None:
            continue
        question_excerpt = _normalize_space(row.get("analyst_question_excerpt"))
        answer_text = answer_row.text
        searchable_text = " ".join(
            part
            for part in [
                question_excerpt,
                answer_text,
                _normalize_space(row.get("plain_english_audio_summary")),
            ]
            if part
        )
        built.append(
            RetrievalRow(
                row_id=f"curated_multimodal_{qa_pair_id:03d}",
                case_id=case_id,
                source_type=SOURCE_TYPE_CURATED_MULTIMODAL,
                source_artifact="processed/audio_behavior/audio_review_rows.json",
                source_locator=f"qa_pair_id:{qa_pair_id}/audio_review",
                moment_id=_clean_text(row.get("row_id")) or f"curated_multimodal_{qa_pair_id:03d}",
                chunk_id=answer_row.chunk_id,
                span_id=f"qa_pair_{qa_pair_id:03d}_audio_review",
                text=searchable_text,
                start_time_s=_coerce_float(row.get("question_start_s")),
                end_time_s=_coerce_float(row.get("answer_end_s")),
                deterministic_category="supporting_only_audio_review",
                plain_english_label=_clean_text(row.get("plain_english_label")) or "curated multimodal moment",
                top_8_showcase=None,
                supporting_only=True,
                section="question_and_answer",
                speaker=", ".join(row.get("answer_speakers", []) or []),
                speaker_role="management",
                review_priority=_clean_text(row.get("review_priority")) or None,
                artifact_paths=[
                    "processed/audio_behavior/audio_review_rows.json",
                    "processed/qa_pairs/qa_pairs.json",
                ],
                metadata={
                    "qa_pair_id": qa_pair_id,
                    "audio_support_mode": _clean_text(row.get("audio_support_mode")) or None,
                    "qa_shift_label": _clean_text(row.get("qa_shift_label")) or None,
                    "hesitation_label": _clean_text(row.get("hesitation_label")) or None,
                    "paired_answer_span_id": answer_row.span_id,
                },
            )
        )
    return built


def build_case_retrieval_rows(
    case_root: str | Path,
    *,
    case_id: str | None = None,
    include_curated_multimodal: bool = False,
) -> list[dict[str, Any]]:
    resolved_case_root = Path(case_root).expanduser().resolve()
    resolved_case_id = case_id or resolved_case_root.name
    transcript_blocks = _load_transcript_blocks(resolved_case_root)
    segment_metadata = _load_segment_metadata(resolved_case_root)
    chunks_scored = _load_chunks_scored(resolved_case_root)
    block_timings = _build_block_timing_index(segment_metadata)
    transcript_rows = _build_transcript_chunk_rows(
        case_id=resolved_case_id,
        chunks_scored=chunks_scored,
        segment_metadata=segment_metadata,
    )
    qa_rows = _build_qa_span_rows(
        case_id=resolved_case_id,
        transcript_blocks=transcript_blocks,
        block_timings=block_timings,
    )
    guidance_rows = _build_guidance_rows(
        case_id=resolved_case_id,
        guidance_rows=_read_csv_rows(resolved_case_root / "processed" / "signals" / "guidance.csv"),
        transcript_chunk_lookup=_build_chunk_lookup(transcript_rows),
    )
    management_document = _resolve_management_document_sources(resolved_case_root)
    shareholder_rows = _build_management_document_rows(
        case_id=resolved_case_id,
        document_text=(resolved_case_root / management_document["text_path"]).read_text(encoding="utf-8"),
        document_evidence=_read_json(resolved_case_root / management_document["evidence_path"]),
        source_type=management_document["source_type"],
        text_artifact_path=management_document["text_path"],
        evidence_artifact_path=management_document["evidence_path"],
        speaker_label=f"{resolved_case_id} {management_document['speaker']}",
    )

    rows: list[RetrievalRow] = [
        *transcript_rows,
        *qa_rows,
        *guidance_rows,
        *shareholder_rows,
    ]
    if include_curated_multimodal:
        audio_payload = _read_json(
            resolved_case_root / "processed" / "audio_behavior" / "audio_review_rows.json"
        )
        audio_rows = audio_payload.get("rows", []) if isinstance(audio_payload, dict) else []
        if not audio_rows and isinstance(audio_payload, list):
            audio_rows = audio_payload
        qa_answer_rows = {
            int(row.metadata["qa_pair_id"]): row
            for row in qa_rows
            if row.source_type == SOURCE_TYPE_QA_ANSWER and "qa_pair_id" in row.metadata
        }
        rows.extend(
            _build_curated_multimodal_rows(
                case_id=resolved_case_id,
                audio_review_rows=[row for row in audio_rows if isinstance(row, dict)],
                qa_answer_rows=qa_answer_rows,
            )
        )

    ordered_rows = sorted(
        rows,
        key=lambda row: (
            SOURCE_TYPE_ORDER.get(row.source_type, 99),
            row.start_time_s if row.start_time_s is not None else float("inf"),
            row.row_id,
        ),
    )
    return [row.to_dict() for row in ordered_rows]


def _cache_dir_from_config() -> str | None:
    config = load_multimodal_config()
    for candidate in (
        config.model_cache_dir,
        config.transformers_cache,
        config.hf_home,
    ):
        if candidate is not None:
            return str(candidate)
    return None


def _resolve_embedding_device(device: str) -> str:
    normalized = _clean_text(device).lower() or DEFAULT_EMBEDDING_DEVICE
    if normalized == "auto":
        try:
            import torch
        except Exception:
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"
    if normalized in {"cpu", "cuda"}:
        return normalized
    raise RuntimeError(f"Unsupported embedding device '{device}'. Use cpu, cuda, or auto.")


def compute_embeddings(
    texts: list[str],
    *,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    device: str = DEFAULT_EMBEDDING_DEVICE,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    max_length: int = DEFAULT_EMBEDDING_MAX_LENGTH,
    local_files_only: bool = False,
) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    import torch
    from transformers import AutoModel, AutoTokenizer

    resolved_device = _resolve_embedding_device(device)
    cache_dir = _cache_dir_from_config()
    model_kwargs: dict[str, Any] = {}
    if cache_dir:
        model_kwargs["cache_dir"] = cache_dir

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        local_files_only=local_files_only,
        **model_kwargs,
    )
    model = AutoModel.from_pretrained(
        model_name,
        local_files_only=local_files_only,
        **model_kwargs,
    )
    device_obj = torch.device("cuda" if resolved_device == "cuda" else "cpu")
    model.to(device_obj)
    model.eval()

    vectors: list[np.ndarray] = []
    with torch.inference_mode():
        for start_index in range(0, len(texts), batch_size):
            batch_texts = texts[start_index : start_index + batch_size]
            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(device_obj) for key, value in encoded.items()}
            outputs = model(**encoded)
            hidden = outputs.last_hidden_state
            attention_mask = encoded["attention_mask"].unsqueeze(-1).expand(hidden.size()).float()
            pooled = (hidden * attention_mask).sum(dim=1) / attention_mask.sum(dim=1).clamp(min=1e-9)
            normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
            vectors.append(normalized.cpu().numpy().astype(np.float32))
    return np.vstack(vectors)


def _source_type_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(row["source_type"])] += 1
    return dict(sorted(counts.items()))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _build_manifest(
    *,
    case_id: str,
    file_names: dict[str, str],
    rows: list[dict[str, Any]],
    model_name: str | None,
    embeddings: np.ndarray | None,
    embedding_error: str | None,
    include_curated_multimodal: bool,
) -> dict[str, Any]:
    if embeddings is None:
        embedding_status = "not_written" if embedding_error is None else "failed"
        embedding_dimensions = None
        embedding_dtype = None
        embedding_row_count = 0
        embedding_file = None
    else:
        embedding_status = "written"
        embedding_dimensions = int(embeddings.shape[1]) if embeddings.ndim == 2 and embeddings.size else 0
        embedding_dtype = str(embeddings.dtype)
        embedding_row_count = int(embeddings.shape[0])
        embedding_file = file_names["embeddings"]

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "bundle_type": "supporting_only_retrieval",
        "case_id": case_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "supporting_only": True,
        "row_count": len(rows),
        "source_type_counts": _source_type_counts(rows),
        "included_curated_multimodal": bool(include_curated_multimodal),
        "files": {
            "rows": file_names["rows"],
            "manifest": file_names["manifest"],
            "embeddings": embedding_file,
        },
        "embedding": {
            "status": embedding_status,
            "model_name": model_name,
            "row_count": embedding_row_count,
            "dimensions": embedding_dimensions,
            "dtype": embedding_dtype,
            "error": embedding_error,
        },
        "notes": [
            "Deterministic transcript-backed artifacts remain canonical.",
            "Chunking remains the bounded evidence unit for review.",
            "This retrieval bundle is supporting-only and preserves source provenance on every row.",
            "Nearest-neighbor similarity is a navigation aid, not adjudication.",
        ],
    }
    return manifest


def write_retrieval_bundle(
    *,
    case_root: str | Path,
    rows: list[dict[str, Any]],
    out_dir: str | Path | None = None,
    include_embeddings: bool = True,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    device: str = DEFAULT_EMBEDDING_DEVICE,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    max_length: int = DEFAULT_EMBEDDING_MAX_LENGTH,
    include_curated_multimodal: bool = False,
) -> dict[str, Path]:
    resolved_case_root = Path(case_root).expanduser().resolve()
    case_id = resolved_case_root.name
    bundle_dir = Path(out_dir).expanduser().resolve() if out_dir is not None else default_bundle_dir(resolved_case_root)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    file_names = _bundle_file_names(case_id)
    rows_path = bundle_dir / file_names["rows"]
    manifest_path = bundle_dir / file_names["manifest"]
    embeddings_path = bundle_dir / file_names["embeddings"]

    embeddings: np.ndarray | None = None
    embedding_error: str | None = None
    if include_embeddings:
        try:
            embeddings = compute_embeddings(
                [str(row["text"]) for row in rows],
                model_name=model_name,
                device=device,
                batch_size=batch_size,
                max_length=max_length,
            )
        except Exception as exc:
            embedding_error = f"{type(exc).__name__}: {exc}"
            embeddings = None
    if embeddings is not None:
        np.save(embeddings_path, embeddings)
    elif embeddings_path.exists():
        embeddings_path.unlink()

    _write_jsonl(rows_path, rows)
    manifest = _build_manifest(
        case_id=case_id,
        file_names=file_names,
        rows=rows,
        model_name=model_name if include_embeddings else None,
        embeddings=embeddings,
        embedding_error=embedding_error,
        include_curated_multimodal=include_curated_multimodal,
    )
    _write_json(manifest_path, manifest)
    return {
        "rows": rows_path,
        "manifest": manifest_path,
        "embeddings": embeddings_path,
    }


def write_retrieval_readme(
    *,
    case_root: str | Path,
    out_dir: str | Path | None = None,
) -> Path:
    resolved_case_root = Path(case_root).expanduser().resolve()
    bundle_dir = Path(out_dir).expanduser().resolve() if out_dir is not None else default_bundle_dir(resolved_case_root)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    file_names = _bundle_file_names(resolved_case_root.name)
    readme_path = bundle_dir / "README.md"
    readme_lines = [
        f"# {resolved_case_root.name} retrieval bundle",
        "",
        "This folder contains a supporting-only retrieval sidecar derived from deterministic case artifacts.",
        "",
        "Contents:",
        f"- `{file_names['rows']}`: normalized retrieval rows with per-row provenance metadata",
        f"- `{file_names['manifest']}`: bundle metadata, source-type counts, and embedding status",
        f"- `{file_names['embeddings']}`: optional row embedding matrix aligned 1:1 with the rows file",
        "",
        "Boundary notes:",
        "- deterministic transcript-backed artifacts remain canonical",
        "- chunking remains the bounded review unit",
        "- lexical and semantic retrieval are navigation aids only",
        "- similarity does not replace transcript-backed review",
    ]
    readme_path.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
    return readme_path


def load_retrieval_bundle(bundle_dir: str | Path) -> RetrievalBundle:
    resolved_bundle_dir = Path(bundle_dir).expanduser().resolve()
    manifest_candidates = sorted(resolved_bundle_dir.glob("*_retrieval_manifest.json"))
    if not manifest_candidates:
        raise RuntimeError(f"No retrieval manifest found under {resolved_bundle_dir}")
    manifest_path = manifest_candidates[0]
    manifest = _read_json(manifest_path)
    rows_name = manifest.get("files", {}).get("rows")
    if not rows_name:
        raise RuntimeError(f"Retrieval manifest did not record a rows file: {manifest_path}")
    rows_path = resolved_bundle_dir / str(rows_name)
    rows = _read_jsonl(rows_path)

    embeddings: np.ndarray | None = None
    embeddings_name = manifest.get("files", {}).get("embeddings")
    if embeddings_name:
        embeddings_path = resolved_bundle_dir / str(embeddings_name)
        if embeddings_path.exists():
            embeddings = np.load(embeddings_path)
    return RetrievalBundle(rows=rows, manifest=manifest, embeddings=embeddings)


def _row_search_text(row: dict[str, Any]) -> str:
    values = [
        row.get("text"),
        row.get("plain_english_label"),
        row.get("deterministic_category"),
        row.get("source_type"),
        row.get("section"),
        row.get("speaker"),
        row.get("speaker_role"),
    ]
    return " ".join(_normalize_space(value) for value in values if _normalize_space(value))


def lexical_scores(query: str, rows: list[dict[str, Any]]) -> list[float]:
    query_text = _normalize_space(query)
    query_tokens = _tokenize(query_text)
    if not query_tokens:
        return [0.0 for _ in rows]

    documents = [_tokenize(_row_search_text(row)) for row in rows]
    document_frequencies: Counter[str] = Counter()
    for tokens in documents:
        for token in set(tokens):
            document_frequencies[token] += 1
    query_phrases = _query_bigrams(query_tokens)
    num_docs = max(1, len(documents))

    scores: list[float] = []
    for row, tokens in zip(rows, documents, strict=True):
        if not tokens:
            scores.append(0.0)
            continue
        token_counts = Counter(tokens)
        doc_length = len(tokens)
        token_score = 0.0
        matched_tokens = 0
        for token in query_tokens:
            if token not in token_counts:
                continue
            matched_tokens += 1
            idf = math.log((1.0 + num_docs) / (1.0 + document_frequencies[token])) + 1.0
            token_score += (token_counts[token] / doc_length) * idf

        search_text = _row_search_text(row).lower()
        phrase_score = 0.0
        if query_text and query_text.lower() in search_text:
            phrase_score += 1.5
        for phrase in query_phrases:
            if phrase and phrase in search_text:
                phrase_score += 0.4

        coverage = matched_tokens / len(query_tokens)
        scores.append(
            round(
                token_score
                + phrase_score
                + coverage
                + _pressure_adjustment(set(query_tokens), search_text),
                6,
            )
        )
    return scores


def semantic_scores_from_embeddings(query_embedding: np.ndarray, row_embeddings: np.ndarray) -> np.ndarray:
    if row_embeddings.ndim != 2:
        raise RuntimeError("Row embeddings must be a 2D matrix.")
    query_vector = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
    if row_embeddings.shape[1] != query_vector.shape[0]:
        raise RuntimeError(
            "Query embedding dimension did not match row embeddings: "
            f"{query_vector.shape[0]} vs {row_embeddings.shape[1]}"
        )
    return np.asarray(row_embeddings @ query_vector, dtype=np.float32)


def _normalize_scores(values: Iterable[float]) -> list[float]:
    series = list(values)
    if not series:
        return []
    minimum = min(series)
    maximum = max(series)
    if math.isclose(minimum, maximum):
        return [0.0 if math.isclose(maximum, 0.0) else 1.0 for _ in series]
    return [(value - minimum) / (maximum - minimum) for value in series]


def search_retrieval_rows(
    *,
    query: str,
    rows: list[dict[str, Any]],
    top_k: int = 8,
    mode: str = "hybrid",
    row_embeddings: np.ndarray | None = None,
    query_embedding: np.ndarray | None = None,
    model_name: str | None = None,
    device: str = DEFAULT_EMBEDDING_DEVICE,
    semantic_weight: float = 0.6,
    exclude_row_ids: set[str] | None = None,
) -> tuple[list[RetrievalSearchResult], list[str]]:
    normalized_mode = _clean_text(mode).lower() or "hybrid"
    if normalized_mode not in {"lexical", "semantic", "hybrid"}:
        raise RuntimeError(f"Unsupported retrieval mode '{mode}'. Use lexical, semantic, or hybrid.")

    notes: list[str] = []
    query_tokens = set(_tokenize(query))
    duplicate_structured_texts = _structured_duplicate_texts(rows)
    text_source_types = _text_source_type_index(rows)
    adjustments = [
        _row_ranking_adjustment(
            row,
            query_tokens=query_tokens,
            duplicate_structured_texts=duplicate_structured_texts,
            text_source_types=text_source_types,
        )
        for row in rows
    ]
    lexical = lexical_scores(query, rows)
    semantic: list[float] | None = None
    effective_mode = normalized_mode

    if normalized_mode in {"semantic", "hybrid"}:
        if row_embeddings is None:
            notes.append("Embedding matrix unavailable; falling back to lexical retrieval.")
        else:
            resolved_query_embedding = query_embedding
            if resolved_query_embedding is None:
                try:
                    resolved_query_embedding = compute_embeddings(
                        [_normalize_space(query)],
                        model_name=model_name or DEFAULT_EMBEDDING_MODEL,
                        device=device,
                        local_files_only=True,
                    )[0]
                except Exception as exc:
                    notes.append(
                        f"Query embedding could not be computed ({type(exc).__name__}: {exc}); "
                        "falling back to lexical retrieval."
                    )
                    resolved_query_embedding = None
            if resolved_query_embedding is not None:
                semantic = semantic_scores_from_embeddings(
                    np.asarray(resolved_query_embedding, dtype=np.float32),
                    np.asarray(row_embeddings, dtype=np.float32),
                ).tolist()

    if normalized_mode == "lexical":
        combined = [
            round(lex + adj, 6)
            for lex, adj in zip(lexical, adjustments, strict=True)
        ]
    elif semantic is None:
        combined = [
            round(lex + adj, 6)
            for lex, adj in zip(lexical, adjustments, strict=True)
        ]
        effective_mode = "lexical"
    elif normalized_mode == "semantic":
        combined = [
            round(sem + adj, 6)
            for sem, adj in zip(semantic, adjustments, strict=True)
        ]
    else:
        semantic_norm = _normalize_scores(semantic)
        lexical_norm = _normalize_scores(lexical)
        combined = [
            round((semantic_weight * sem) + ((1.0 - semantic_weight) * lex) + adj, 6)
            for sem, lex, adj in zip(semantic_norm, lexical_norm, adjustments, strict=True)
        ]

    ranked_indices = sorted(
        range(len(rows)),
        key=lambda idx: (
            combined[idx],
            adjustments[idx],
            lexical[idx],
            semantic[idx] if semantic is not None else -1.0,
        ),
        reverse=True,
    )

    results: list[RetrievalSearchResult] = []
    for index in ranked_indices:
        if len(results) >= max(1, top_k):
            break
        if exclude_row_ids and str(rows[index].get("row_id")) in exclude_row_ids:
            continue
        if combined[index] <= 0 and lexical[index] <= 0 and (semantic is None or semantic[index] <= 0):
            continue
        results.append(
            RetrievalSearchResult(
                rank=len(results) + 1,
                score=float(combined[index]),
                lexical_score=float(lexical[index]),
                semantic_score=(float(semantic[index]) if semantic is not None else None),
                retrieval_mode=effective_mode,
                row=rows[index],
            )
        )
    return results, notes


def build_and_write_case_retrieval_bundle(
    *,
    case_root: str | Path,
    out_dir: str | Path | None = None,
    include_embeddings: bool = True,
    include_curated_multimodal: bool = False,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    device: str = DEFAULT_EMBEDDING_DEVICE,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    max_length: int = DEFAULT_EMBEDDING_MAX_LENGTH,
) -> dict[str, Any]:
    rows = build_case_retrieval_rows(
        case_root,
        include_curated_multimodal=include_curated_multimodal,
    )
    paths = write_retrieval_bundle(
        case_root=case_root,
        rows=rows,
        out_dir=out_dir,
        include_embeddings=include_embeddings,
        include_curated_multimodal=include_curated_multimodal,
        model_name=model_name,
        device=device,
        batch_size=batch_size,
        max_length=max_length,
    )
    readme_path = write_retrieval_readme(case_root=case_root, out_dir=out_dir)
    manifest = _read_json(paths["manifest"])
    return {
        "rows": rows,
        "paths": paths | {"readme": readme_path},
        "manifest": manifest,
    }
