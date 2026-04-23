from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import pandas as pd

from earnings_call_sentiment.corpus import ensure_corpus_layout, repo_root, to_repo_relative
from earnings_call_sentiment.pipeline.run import load_transcript_segments
from earnings_call_sentiment.review_workflow import build_segments_from_text, chunk_text_for_review
from earnings_call_sentiment.signals.behavior import _classify_context

_GUIDANCE_KEYWORDS = (
    "guidance",
    "outlook",
    "expect",
    "forecast",
    "revenue",
    "margin",
    "eps",
    "free cash flow",
    "capex",
)
_PRESSURE_KEYWORDS = (
    "pressure",
    "headwind",
    "risk",
    "slowdown",
    "uncertain",
    "challenging",
    "pushback",
    "cadence",
)
_QA_SWITCH_PATTERNS = (
    r"\bquestion and answer\b",
    r"\bq&a\b",
    r"\bquestion[- ]and[- ]answer session\b",
)


def _normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return path


def _looks_like_qa_switch(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in _QA_SWITCH_PATTERNS)


def _extract_speaker_prefix(text: str) -> tuple[str | None, str]:
    match = re.match(r"^\s*([A-Z][A-Za-z .&'’/-]{1,80}?):\s*(.+)$", text)
    if match is None:
        return None, _normalize_space(text)
    speaker = _normalize_space(match.group(1))
    spoken = _normalize_space(match.group(2))
    return speaker or None, spoken


def _section_label(raw_section: str) -> str:
    return "question_and_answer" if raw_section == "q_and_a" else "prepared_remarks"


def _guidance_flag(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _GUIDANCE_KEYWORDS)


def _pressure_flag(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _PRESSURE_KEYWORDS)


def _load_optional_frame(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, keep_default_na=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _signal_overlap_flags(
    *,
    start_time: float | None,
    end_time: float | None,
    guidance_df: pd.DataFrame,
    uncertainty_df: pd.DataFrame,
    skepticism_df: pd.DataFrame,
) -> dict[str, bool]:
    flags = {
        "guidance_related": False,
        "uncertainty_flag": False,
        "pushback_flag": False,
    }
    if start_time is None or end_time is None:
        return flags

    for frame, key in (
        (guidance_df, "guidance_related"),
        (uncertainty_df, "uncertainty_flag"),
    ):
        if frame.empty or not {"start", "end"}.issubset(frame.columns):
            continue
        for _, row in frame.iterrows():
            try:
                overlap = max(
                    0.0,
                    min(end_time, float(row["end"])) - max(start_time, float(row["start"])),
                )
            except Exception:
                overlap = 0.0
            if overlap > 0.0:
                flags[key] = True
                break

    if not skepticism_df.empty and {"text"}.issubset(skepticism_df.columns):
        flags["pushback_flag"] = bool(
            any(_normalize_space(text) for text in skepticism_df["text"].tolist())
        )
    return flags


def _build_segment_rows(
    segments: list[dict[str, Any]],
    *,
    source_doc: str,
    guidance_df: pd.DataFrame,
    uncertainty_df: pd.DataFrame,
    skepticism_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    qa_started = False
    for segment_id, segment in enumerate(segments):
        raw_text = _normalize_space(segment.get("text"))
        if not raw_text:
            continue
        speaker, clean_text = _extract_speaker_prefix(raw_text)
        if _looks_like_qa_switch(clean_text):
            qa_started = True
        section_hint, speaker_role, _ = _classify_context(clean_text)
        if qa_started or section_hint == "q_and_a":
            section = "question_and_answer"
        else:
            section = "prepared_remarks"
        flags = _signal_overlap_flags(
            start_time=float(segment.get("start")) if "start" in segment else None,
            end_time=float(segment.get("end")) if "end" in segment else None,
            guidance_df=guidance_df,
            uncertainty_df=uncertainty_df,
            skepticism_df=skepticism_df,
        )
        flags["guidance_related"] = flags["guidance_related"] or _guidance_flag(clean_text)
        flags["pushback_flag"] = flags["pushback_flag"] or _pressure_flag(clean_text)
        flags["question_like"] = speaker_role == "analyst"
        rows.append(
            {
                "segment_id": segment_id,
                "source_doc": source_doc,
                "speaker": speaker or "",
                "speaker_role": speaker_role,
                "section": section,
                "start": float(segment.get("start", 0.0)),
                "end": float(segment.get("end", 0.0)),
                "text": clean_text,
                "word_count": len(re.findall(r"\b\w+\b", clean_text)),
                "guidance_related": bool(flags["guidance_related"]),
                "uncertainty_flag": bool(flags["uncertainty_flag"]),
                "pushback_flag": bool(flags["pushback_flag"]),
                "question_like": bool(flags["question_like"]),
            }
        )
    return rows


def _build_transcript_blocks(segment_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    block_id = 0

    def flush() -> None:
        nonlocal current, block_id
        if current is None:
            return
        current["block_id"] = block_id
        current["text"] = _normalize_space(" ".join(current.pop("text_parts")))
        current["segment_ids"] = list(current["segment_ids"])
        blocks.append(current)
        block_id += 1
        current = None

    for row in segment_rows:
        if current is None:
            current = {
                "source_doc": row["source_doc"],
                "section": row["section"],
                "speaker": row["speaker"],
                "speaker_role": row["speaker_role"],
                "speaker_title": "",
                "start": row["start"],
                "end": row["end"],
                "segment_ids": [int(row["segment_id"])],
                "guidance_related": bool(row["guidance_related"]),
                "uncertainty_flag": bool(row["uncertainty_flag"]),
                "pushback_flag": bool(row["pushback_flag"]),
                "text_parts": [row["text"]],
            }
            continue

        same_block = (
            current["section"] == row["section"]
            and current["speaker_role"] == row["speaker_role"]
            and current["speaker"] == row["speaker"]
        )
        if same_block:
            current["end"] = row["end"]
            current["segment_ids"].append(int(row["segment_id"]))
            current["guidance_related"] = bool(current["guidance_related"] or row["guidance_related"])
            current["uncertainty_flag"] = bool(current["uncertainty_flag"] or row["uncertainty_flag"])
            current["pushback_flag"] = bool(current["pushback_flag"] or row["pushback_flag"])
            current["text_parts"].append(row["text"])
            continue
        flush()
        current = {
            "source_doc": row["source_doc"],
            "section": row["section"],
            "speaker": row["speaker"],
            "speaker_role": row["speaker_role"],
            "speaker_title": "",
            "start": row["start"],
            "end": row["end"],
            "segment_ids": [int(row["segment_id"])],
            "guidance_related": bool(row["guidance_related"]),
            "uncertainty_flag": bool(row["uncertainty_flag"]),
            "pushback_flag": bool(row["pushback_flag"]),
            "text_parts": [row["text"]],
        }

    flush()
    return blocks


def _build_qa_pairs(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qa_pairs: list[dict[str, Any]] = []
    current_question: dict[str, Any] | None = None
    current_answers: list[dict[str, Any]] = []
    pair_id = 0
    for block in blocks:
        if block["section"] != "question_and_answer":
            continue
        if block["speaker_role"] == "analyst":
            if current_question is not None:
                qa_pairs.append(
                    {
                        "qa_pair_id": pair_id,
                        "question_speaker": current_question.get("speaker", ""),
                        "question_text": current_question.get("text", ""),
                        "question_segment_ids": current_question.get("segment_ids", []),
                        "question_start": current_question.get("start"),
                        "question_end": current_question.get("end"),
                        "answer_speakers": [item.get("speaker", "") for item in current_answers if item.get("speaker", "")],
                        "answer_text": _normalize_space(" ".join(item.get("text", "") for item in current_answers)),
                        "answer_segment_ids": [
                            segment_id
                            for item in current_answers
                            for segment_id in item.get("segment_ids", [])
                        ],
                        "answer_start": current_answers[0].get("start") if current_answers else None,
                        "answer_end": current_answers[-1].get("end") if current_answers else None,
                    }
                )
            pair_id += 1
            current_question = block
            current_answers = []
            continue
        if current_question is not None and block["speaker_role"] == "management":
            current_answers.append(block)

    if current_question is not None:
        qa_pairs.append(
            {
                "qa_pair_id": pair_id,
                "question_speaker": current_question.get("speaker", ""),
                "question_text": current_question.get("text", ""),
                "question_segment_ids": current_question.get("segment_ids", []),
                "question_start": current_question.get("start"),
                "question_end": current_question.get("end"),
                "answer_speakers": [item.get("speaker", "") for item in current_answers if item.get("speaker", "")],
                "answer_text": _normalize_space(" ".join(item.get("text", "") for item in current_answers)),
                "answer_segment_ids": [
                    segment_id for item in current_answers for segment_id in item.get("segment_ids", [])
                ],
                "answer_start": current_answers[0].get("start") if current_answers else None,
                "answer_end": current_answers[-1].get("end") if current_answers else None,
            }
        )
    return [row for row in qa_pairs if row["question_text"]]


def _build_event_chunks(
    *,
    case_id: str,
    segment_rows: list[dict[str, Any]],
    chunks_scored_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    if chunks_scored_df.empty:
        chunks_scored_df = pd.DataFrame(segment_rows)
        if "signed_score" not in chunks_scored_df.columns:
            chunks_scored_df["signed_score"] = 0.0
        if "sentiment" not in chunks_scored_df.columns:
            chunks_scored_df["sentiment"] = ""
        chunks_scored_df["chunk_source"] = "synthetic_from_segments"
    else:
        chunks_scored_df = chunks_scored_df.copy()
        chunks_scored_df["chunk_source"] = "chunks_scored_csv"

    chunks: list[dict[str, Any]] = []
    for index, (_, row) in enumerate(chunks_scored_df.iterrows(), start=1):
        start_time = float(row.get("start", 0.0)) if str(row.get("start", "")).strip() else None
        end_time = float(row.get("end", 0.0)) if str(row.get("end", "")).strip() else None
        overlap_rows = []
        if start_time is not None and end_time is not None:
            for segment_row in segment_rows:
                overlap = max(
                    0.0,
                    min(end_time, float(segment_row["end"])) - max(start_time, float(segment_row["start"])),
                )
                if overlap > 0.0:
                    overlap_rows.append(segment_row)
        text = _normalize_space(row.get("text"))
        dominant = overlap_rows[0] if overlap_rows else {}
        guidance_related = bool(
            any(bool(item["guidance_related"]) for item in overlap_rows) or _guidance_flag(text)
        )
        uncertainty_flag = bool(any(bool(item["uncertainty_flag"]) for item in overlap_rows))
        pushback_flag = bool(any(bool(item["pushback_flag"]) for item in overlap_rows) or _pressure_flag(text))
        section = str(dominant.get("section", "prepared_remarks") or "prepared_remarks")
        speaker_role = str(dominant.get("speaker_role", "management") or "management")
        chunk_type = "prepared_remarks"
        if section == "question_and_answer" and speaker_role == "analyst":
            chunk_type = "qa_question"
        elif section == "question_and_answer":
            chunk_type = "qa_answer"
        chunks.append(
            {
                "case_id": case_id,
                "object_id": f"{case_id}_event_chunk_{index:04d}",
                "object_type": "event_chunk",
                "event_type": chunk_type,
                "section": section,
                "speaker": str(dominant.get("speaker", "") or ""),
                "speaker_role": speaker_role,
                "start": start_time,
                "end": end_time,
                "text": text,
                "sentiment": _normalize_space(row.get("sentiment")),
                "score": float(row.get("score", 0.0)) if str(row.get("score", "")).strip() else 0.0,
                "signed_score": float(row.get("signed_score", 0.0))
                if str(row.get("signed_score", "")).strip()
                else 0.0,
                "guidance_related": guidance_related,
                "uncertainty_flag": uncertainty_flag,
                "pushback_flag": pushback_flag,
                "segment_ids": [int(item["segment_id"]) for item in overlap_rows],
                "source_artifact": str(row.get("chunk_source", "")),
            }
        )
    return chunks


def _build_evidence_objects(
    *,
    case_id: str,
    company: str,
    ticker: str,
    fiscal_period: str,
    event_date: str,
    transcript_source_type: str,
    blocks: list[dict[str, Any]],
    qa_pairs: list[dict[str, Any]],
    event_chunks: list[dict[str, Any]],
    guidance_df: pd.DataFrame,
    uncertainty_df: pd.DataFrame,
    reassurance_df: pd.DataFrame,
    skepticism_df: pd.DataFrame,
    source_paths: dict[str, str],
) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []

    def base_payload(object_id: str, object_type: str, text: str) -> dict[str, Any]:
        return {
            "case_id": case_id,
            "object_id": object_id,
            "object_type": object_type,
            "company": company,
            "ticker": ticker,
            "fiscal_period": fiscal_period,
            "event_date": event_date,
            "source_type": transcript_source_type,
            "text": _normalize_space(text),
        }

    for block in blocks:
        payload = base_payload(
            f"{case_id}_speaker_turn_{int(block['block_id']):04d}",
            "speaker_turn",
            block["text"],
        )
        payload.update(
            {
                "section": block["section"],
                "speaker": block["speaker"],
                "speaker_role": block["speaker_role"],
                "start": block["start"],
                "end": block["end"],
                "flags": {
                    "guidance_related": bool(block["guidance_related"]),
                    "uncertainty_flag": bool(block["uncertainty_flag"]),
                    "pushback_flag": bool(block["pushback_flag"]),
                },
                "provenance": {
                    "segment_ids": block.get("segment_ids", []),
                    "local_path_refs": [source_paths["segment_metadata"], source_paths["transcript_sectioned"]],
                },
            }
        )
        objects.append(payload)

    for pair in qa_pairs:
        question = base_payload(
            f"{case_id}_qa_question_{int(pair['qa_pair_id']):04d}",
            "qa_question",
            pair["question_text"],
        )
        question.update(
            {
                "section": "question_and_answer",
                "speaker": pair.get("question_speaker", ""),
                "speaker_role": "analyst",
                "start": pair.get("question_start"),
                "end": pair.get("question_end"),
                "provenance": {
                    "segment_ids": pair.get("question_segment_ids", []),
                    "local_path_refs": [source_paths["qa_pairs"]],
                },
            }
        )
        objects.append(question)
        if pair.get("answer_text"):
            answer = base_payload(
                f"{case_id}_qa_answer_{int(pair['qa_pair_id']):04d}",
                "qa_answer",
                pair["answer_text"],
            )
            answer.update(
                {
                    "section": "question_and_answer",
                    "speaker": "; ".join(pair.get("answer_speakers", [])),
                    "speaker_role": "management",
                    "start": pair.get("answer_start"),
                    "end": pair.get("answer_end"),
                    "provenance": {
                        "segment_ids": pair.get("answer_segment_ids", []),
                        "local_path_refs": [source_paths["qa_pairs"]],
                    },
                }
            )
            objects.append(answer)

    for index, (_, row) in enumerate(guidance_df.iterrows(), start=1):
        payload = base_payload(
            f"{case_id}_guidance_span_{index:04d}",
            "guidance_span",
            row.get("text", ""),
        )
        payload.update(
            {
                "section": "",
                "speaker": "",
                "speaker_role": "",
                "start": float(row.get("start", 0.0)) if str(row.get("start", "")).strip() else None,
                "end": float(row.get("end", 0.0)) if str(row.get("end", "")).strip() else None,
                "topic": _normalize_space(row.get("topic")),
                "period": _normalize_space(row.get("period")),
                "flags": {"guidance_related": True},
                "provenance": {"local_path_refs": [source_paths["guidance"]]},
            }
        )
        objects.append(payload)

    def append_signal_rows(frame: pd.DataFrame, object_type: str, path_key: str) -> None:
        for index, (_, row) in enumerate(frame.iterrows(), start=1):
            payload = base_payload(
                f"{case_id}_{object_type}_{index:04d}",
                object_type,
                row.get("text", ""),
            )
            payload.update(
                {
                    "section": _normalize_space(row.get("section")),
                    "speaker": _normalize_space(row.get("analyst_name") or row.get("speaker")),
                    "speaker_role": _normalize_space(row.get("speaker_role") or "management"),
                    "start": float(row.get("segment_start", 0.0))
                    if str(row.get("segment_start", "")).strip()
                    else None,
                    "end": float(row.get("segment_end", 0.0))
                    if str(row.get("segment_end", "")).strip()
                    else None,
                    "matched_phrase": _normalize_space(row.get("matched_phrase")),
                    "strength": int(float(row.get("strength", 0) or 0)),
                    "provenance": {"local_path_refs": [source_paths[path_key]]},
                }
            )
            objects.append(payload)

    append_signal_rows(uncertainty_df, "uncertainty_span", "uncertainty")
    append_signal_rows(reassurance_df, "reassurance_span", "reassurance")
    append_signal_rows(skepticism_df, "skepticism_span", "skepticism")

    for chunk in event_chunks:
        payload = base_payload(chunk["object_id"], "event_chunk", chunk["text"])
        payload.update(
            {
                "section": chunk["section"],
                "speaker": chunk["speaker"],
                "speaker_role": chunk["speaker_role"],
                "start": chunk["start"],
                "end": chunk["end"],
                "event_type": chunk["event_type"],
                "score": chunk["signed_score"],
                "flags": {
                    "guidance_related": bool(chunk["guidance_related"]),
                    "uncertainty_flag": bool(chunk["uncertainty_flag"]),
                    "pushback_flag": bool(chunk["pushback_flag"]),
                },
                "provenance": {
                    "segment_ids": chunk.get("segment_ids", []),
                    "local_path_refs": [source_paths["event_chunks"]],
                },
            }
        )
        objects.append(payload)
    return objects


def _build_alignment_payload(
    *,
    case_id: str,
    event_chunks: list[dict[str, Any]],
    audio_summary_path: Path | None,
    multimodal_summary_path: Path | None,
    audio_verified: bool,
    video_verified: bool,
) -> dict[str, Any]:
    windows: list[dict[str, Any]] = []
    for chunk in event_chunks:
        if chunk["start"] is None or chunk["end"] is None:
            continue
        if not (chunk["guidance_related"] or chunk["uncertainty_flag"] or chunk["pushback_flag"]):
            continue
        windows.append(
            {
                "window_id": f"{chunk['object_id']}_window",
                "event_object_id": chunk["object_id"],
                "window_start_s": round(max(0.0, float(chunk["start"]) - 15.0), 3),
                "window_end_s": round(float(chunk["end"]) + 15.0, 3),
                "reason": {
                    "guidance_related": bool(chunk["guidance_related"]),
                    "uncertainty_flag": bool(chunk["uncertainty_flag"]),
                    "pushback_flag": bool(chunk["pushback_flag"]),
                },
                "audio_alignment_status": "ready" if audio_verified else "not_available",
                "video_alignment_status": "ready" if video_verified else "not_available",
                "sparse_keyframe_plan": "package_sparse_keyframes_if_local_video_exists"
                if video_verified
                else "skip_until_video_verified",
            }
        )
    return {
        "case_id": case_id,
        "audio_verified": bool(audio_verified),
        "video_verified": bool(video_verified),
        "audio_behavior_summary_path": to_repo_relative(audio_summary_path) if audio_summary_path else "",
        "multimodal_support_summary_path": to_repo_relative(multimodal_summary_path)
        if multimodal_summary_path
        else "",
        "flagged_windows": windows,
    }


def export_case_artifacts(
    *,
    case_id: str,
    company: str,
    ticker: str,
    fiscal_period: str,
    event_date: str,
    transcript_source_type: str,
    transcript_local_path: str,
    transcript_parse_status: str,
    audio_verified: bool,
    video_verified: bool,
    processed_case_dir: str = "",
) -> dict[str, str]:
    layout = ensure_corpus_layout()
    repo = repo_root()
    transcript_path = repo / transcript_local_path
    processed_dir = repo / processed_case_dir if processed_case_dir else None

    if processed_dir is not None and (processed_dir / "transcript.json").exists():
        segments = load_transcript_segments(processed_dir / "transcript.json")
        source_doc = "transcript_json"
    else:
        text = transcript_path.read_text(encoding="utf-8", errors="ignore")
        segments = build_segments_from_text(text)
        source_doc = "transcript_txt"

    guidance_df = _load_optional_frame((processed_dir / "guidance.csv") if processed_dir else None)
    uncertainty_df = _load_optional_frame((processed_dir / "uncertainty_signals.csv") if processed_dir else None)
    reassurance_df = _load_optional_frame((processed_dir / "reassurance_signals.csv") if processed_dir else None)
    skepticism_df = _load_optional_frame((processed_dir / "analyst_skepticism.csv") if processed_dir else None)
    chunks_scored_df = _load_optional_frame((processed_dir / "chunks_scored.csv") if processed_dir else None)
    audio_summary_path = (processed_dir / "audio_behavior_summary.json") if processed_dir and (processed_dir / "audio_behavior_summary.json").exists() else None
    multimodal_summary_path = (processed_dir / "multimodal_support_summary.json") if processed_dir and (processed_dir / "multimodal_support_summary.json").exists() else None

    segment_rows = _build_segment_rows(
        segments,
        source_doc=source_doc,
        guidance_df=guidance_df,
        uncertainty_df=uncertainty_df,
        skepticism_df=skepticism_df,
    )
    blocks = _build_transcript_blocks(segment_rows)
    qa_pairs = _build_qa_pairs(blocks)
    event_chunks = _build_event_chunks(case_id=case_id, segment_rows=segment_rows, chunks_scored_df=chunks_scored_df)

    segment_metadata_path = layout["processed_chunks"] / f"{case_id}.segment_metadata.json"
    transcript_sectioned_path = layout["processed_chunks"] / f"{case_id}.transcript_sectioned.json"
    qa_pairs_path = layout["processed_chunks"] / f"{case_id}.qa_pairs.json"
    event_chunks_path = layout["processed_chunks"] / f"{case_id}.event_chunks.jsonl"
    evidence_path = layout["processed_evidence_objects"] / f"{case_id}.evidence_objects.jsonl"
    alignment_path = layout["processed_alignments"] / f"{case_id}.alignment_windows.json"

    _write_json(segment_metadata_path, {"segments": segment_rows, "transcript_parse_status": transcript_parse_status})
    _write_json(transcript_sectioned_path, {"blocks": blocks})
    _write_json(qa_pairs_path, {"qa_pairs": qa_pairs})
    _write_jsonl(event_chunks_path, event_chunks)

    source_paths = {
        "segment_metadata": to_repo_relative(segment_metadata_path),
        "transcript_sectioned": to_repo_relative(transcript_sectioned_path),
        "qa_pairs": to_repo_relative(qa_pairs_path),
        "event_chunks": to_repo_relative(event_chunks_path),
        "guidance": to_repo_relative(processed_dir / "guidance.csv") if processed_dir and (processed_dir / "guidance.csv").exists() else "",
        "uncertainty": to_repo_relative(processed_dir / "uncertainty_signals.csv") if processed_dir and (processed_dir / "uncertainty_signals.csv").exists() else "",
        "reassurance": to_repo_relative(processed_dir / "reassurance_signals.csv") if processed_dir and (processed_dir / "reassurance_signals.csv").exists() else "",
        "skepticism": to_repo_relative(processed_dir / "analyst_skepticism.csv") if processed_dir and (processed_dir / "analyst_skepticism.csv").exists() else "",
    }

    evidence_objects = _build_evidence_objects(
        case_id=case_id,
        company=company,
        ticker=ticker,
        fiscal_period=fiscal_period,
        event_date=event_date,
        transcript_source_type=transcript_source_type,
        blocks=blocks,
        qa_pairs=qa_pairs,
        event_chunks=event_chunks,
        guidance_df=guidance_df,
        uncertainty_df=uncertainty_df,
        reassurance_df=reassurance_df,
        skepticism_df=skepticism_df,
        source_paths=source_paths,
    )
    _write_jsonl(evidence_path, evidence_objects)

    alignment_payload = _build_alignment_payload(
        case_id=case_id,
        event_chunks=event_chunks,
        audio_summary_path=audio_summary_path,
        multimodal_summary_path=multimodal_summary_path,
        audio_verified=audio_verified,
        video_verified=video_verified,
    )
    _write_json(alignment_path, alignment_payload)

    return {
        "segment_metadata_path": to_repo_relative(segment_metadata_path),
        "transcript_sectioned_path": to_repo_relative(transcript_sectioned_path),
        "qa_pairs_path": to_repo_relative(qa_pairs_path),
        "event_chunks_path": to_repo_relative(event_chunks_path),
        "evidence_objects_path": to_repo_relative(evidence_path),
        "alignment_path": to_repo_relative(alignment_path),
    }


def load_evidence_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def build_text_only_chunks(text: str) -> list[str]:
    return chunk_text_for_review(text, max_chars=900)
