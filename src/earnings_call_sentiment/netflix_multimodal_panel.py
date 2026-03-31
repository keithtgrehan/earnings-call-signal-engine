from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd

from earnings_call_sentiment.nlp_sidecars import (
    DEFAULT_ZERO_SHOT_LABEL_CONFIG,
    run_sidecar_models,
    write_case_evaluation_summary,
)
from earnings_call_sentiment.visual.summary import write_visual_behavior_outputs

CASE_ID = "netflix_q1_2022"
CASE_DIR = Path("data/demo_cases") / CASE_ID
MULTIMODAL_DIR = CASE_DIR / "demo" / "multimodal"
CURATED_OUTPUT_DIR = Path("outputs") / CASE_ID / "model_sidecars_curated"
REQUESTED_VIDEO_PATH = Path(
    "/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix Q1 2022 Earnings Interview.mp4"
)
FALLBACK_VIDEO_PATH = Path(
    "/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix/Netflix Q1 2022 Earnings Interview.mp4"
)
UPLOADED_TRANSCRIPT_FALLBACK_PATH = Path(
    "/mnt/data/Netflix-Inc.-Q1-2022-Pre-Recorded-Earnings-Call-Apr-19-2022.pdf"
)
UPLOADED_SHAREHOLDER_FALLBACK_PATH = Path(
    "/mnt/data/netflix-Q1-22-Shareholder-Letter (1).pdf"
)

EXPECTED_POLARITY_BY_CATEGORY = {
    "growth_pressure": "negative",
    "guidance_pressure": "negative",
    "analyst_skepticism": "negative",
    "headwind_disclosure": "negative",
    "long_term_reassurance": "positive",
}

COMPARISON_NOTE_BY_CODE = {
    "no_expected_polarity": "no directional comparison note was applied",
    "aligned_with_expected_category": "sidecars broadly moved with the deterministic read",
    "mixed_vs_expected_category": "sidecars split around the deterministic read",
    "diverged_from_expected_category": "sidecars pointed away from the deterministic read",
    "supporting_only_non_polar_category": "non-polar framing moment; sidecars add color only",
}

SUPPORTING_CAVEATS = {
    "deterministic": [
        "Transcript-backed deterministic artifacts remain the canonical review path for this case.",
        "This bundle does not change or overwrite the fixed Netflix demo outputs.",
    ],
    "nlp_sidecars": [
        "Optional NLP sidecars are supporting inspection aids only.",
        "Model outputs can disagree with each other and with deterministic categories without implying lift.",
        "Embedding similarity is not sentiment truth.",
    ],
    "audio": [
        "Audio behavior remains supporting-only and is limited to curated Q&A windows already aligned in the repo.",
        "Audio timing cues are observational review support, not mental-state inference.",
    ],
    "visual": [
        "Visual behavior is observational only and is not emotion or deception inference.",
        "If face visibility or pose quality is weak, visual support should be suppressed rather than forced.",
    ],
}

MOMENT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "moment_id": "qa_growth_headwinds",
        "rank": 1,
        "top_8_showcase": True,
        "unit_type": "qa_answers",
        "source_kind": "joined_review",
        "selector": {"row_id": "transcript_growth_headwinds"},
        "deterministic_signal_category": "growth_pressure",
        "plain_english_label": "management acknowledged growth pressure",
        "why_selected": "Direct management answer to the lead skeptical question, with the clearest transcript-backed admission of pressure.",
    },
    {
        "moment_id": "qa_q1_miss_explanation",
        "rank": 2,
        "top_8_showcase": True,
        "unit_type": "qa_answers",
        "source_kind": "joined_review",
        "selector": {"row_id": "transcript_q2_paid_net_adds_guide"},
        "deterministic_signal_category": "guidance_pressure",
        "plain_english_label": "management explained the miss directly",
        "why_selected": "Best bounded explanation of the miss versus prior expectations and the near-term pressure path.",
    },
    {
        "moment_id": "guidance_negative_q2_net_adds",
        "rank": 3,
        "top_8_showcase": True,
        "unit_type": "guidance_spans",
        "source_kind": "guidance",
        "selector": {"text_contains": "negative 2 million paid net adds in Q2"},
        "deterministic_signal_category": "guidance_pressure",
        "plain_english_label": "negative Q2 paid net adds guidance",
        "why_selected": "The most presentation-useful explicit guide reset language in the deterministic artifacts.",
    },
    {
        "moment_id": "qa_ad_supported_option",
        "rank": 4,
        "top_8_showcase": True,
        "unit_type": "qa_answers",
        "source_kind": "joined_review",
        "selector": {"row_id": "transcript_ad_supported_option"},
        "deterministic_signal_category": "strategic_option",
        "plain_english_label": "qualified answer on the ad-supported option",
        "why_selected": "High-interest answer with strategic value for demo review, but still clearly framed as exploratory.",
    },
    {
        "moment_id": "chunk_monetize_sharing_competition",
        "rank": 5,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "chunk",
        "selector": {"start": 115.0, "end": 183.077},
        "deterministic_signal_category": "headwind_disclosure",
        "plain_english_label": "monetizing sharing while acknowledging competition",
        "why_selected": "Shows the tension between acknowledging competition and trying to reframe execution response.",
    },
    {
        "moment_id": "chunk_long_term_market_unchanged",
        "rank": 6,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "chunk",
        "selector": {"start": 183.077, "end": 228.462},
        "deterministic_signal_category": "long_term_reassurance",
        "plain_english_label": "long-term market remains intact",
        "why_selected": "Useful contrast moment where management tries to stabilize the long-term market narrative.",
    },
    {
        "moment_id": "letter_growth_slowdown",
        "rank": 7,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "letter_growth_slowdown"},
        "deterministic_signal_category": "growth_pressure",
        "plain_english_label": "growth slowdown",
        "why_selected": "Concise management-authored disclosure anchor from the shareholder letter for the same slowdown story.",
    },
    {
        "moment_id": "chunk_opening_analyst_skepticism",
        "rank": 8,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "chunk",
        "selector": {"start": 33.846, "end": 52.308},
        "deterministic_signal_category": "analyst_skepticism",
        "plain_english_label": "opening analyst skepticism",
        "why_selected": "Useful showcase opener because the analyst question itself frames the tone shift problem clearly.",
    },
    {
        "moment_id": "letter_headwinds",
        "rank": 9,
        "top_8_showcase": False,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "letter_headwinds"},
        "deterministic_signal_category": "headwind_disclosure",
        "plain_english_label": "competitive and macro headwinds",
        "why_selected": "Complements the Q&A by stating the headwinds in management-authored letter form.",
    },
    {
        "moment_id": "letter_margin_framing",
        "rank": 10,
        "top_8_showcase": False,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "letter_margin_framing"},
        "deterministic_signal_category": "margin_framing",
        "plain_english_label": "forward margin framing",
        "why_selected": "Adds a bounded management framing moment around margins without pretending it is a new deterministic label.",
    },
    {
        "moment_id": "financial_anchor_q1",
        "rank": 11,
        "top_8_showcase": False,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "financial_context_q1_2022"},
        "deterministic_signal_category": "financial_anchor",
        "plain_english_label": "quarter anchored by reported financials",
        "why_selected": "Keeps the support pack tied to reported quarter facts rather than only narrative excerpts.",
    },
)


@dataclass(frozen=True)
class BundlePaths:
    asset_audit_doc: Path
    moment_manifest: Path
    model_comparison: Path
    disagreement_hotspots: Path
    audio_support: Path
    visual_support: Path | None
    visual_support_skipped: Path | None
    clip_manifest: Path
    caveats: Path
    pressure_panel: Path
    disagreement_panel: Path
    panel_json: Path
    panel_md: Path
    evidence_panel_doc: Path
    panel_summary_doc: Path


def _repo_root(root: Path | None = None) -> Path:
    return Path.cwd().resolve() if root is None else Path(root).expanduser().resolve()


def case_root(root: Path | None = None) -> Path:
    return _repo_root(root) / CASE_DIR


def multimodal_dir(root: Path | None = None) -> Path:
    return _repo_root(root) / MULTIMODAL_DIR


def curated_output_dir(root: Path | None = None) -> Path:
    return _repo_root(root) / CURATED_OUTPUT_DIR


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _truncate(text: str, *, limit: int = 240) -> str:
    compact = " ".join(str(text).split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3]}..."


def _timestamp_label(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    value = max(0, int(round(float(seconds))))
    minutes, sec = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def resolve_video_source(video_path: str | Path | None = None) -> dict[str, Any]:
    requested = Path(video_path).expanduser().resolve() if video_path else REQUESTED_VIDEO_PATH
    fallback = FALLBACK_VIDEO_PATH
    candidates = [requested]
    if fallback not in candidates:
        candidates.append(fallback)

    existing = [candidate for candidate in candidates if candidate.exists() and candidate.is_file()]
    preferred = existing[0] if existing else None
    return {
        "requested_path": str(requested),
        "requested_exists": requested.exists(),
        "fallback_candidates": [str(path) for path in candidates[1:]],
        "resolved_video_path": str(preferred) if preferred else None,
        "resolved_from_fallback": bool(preferred and preferred != requested),
    }


def _uploaded_source_checks() -> dict[str, dict[str, Any]]:
    checks = {
        "uploaded_transcript_pdf": UPLOADED_TRANSCRIPT_FALLBACK_PATH,
        "uploaded_shareholder_letter_pdf": UPLOADED_SHAREHOLDER_FALLBACK_PATH,
    }
    return {
        key: {"path": str(path), "exists": path.exists()}
        for key, path in checks.items()
    }


def _sanitize_visual_quality_note(note: str | None) -> str:
    cleaned = str(note or "").strip()
    replacements = {
        "low face visibility reduces confidence": "low face visibility limits visual usability",
        "unstable face tracking reduces confidence": "unstable face tracking limits visual usability",
        "low landmark confidence reduces confidence": "low landmark coverage limits visual usability",
        "small on-screen face reduces confidence": "small on-screen face limits visual usability",
        "usable visual segment": "usable visual segment for bounded observation",
        "usable face visibility and landmark support": "face visibility and landmark coverage were usable for a bounded visual pass",
        "quality gate suppressed confidence uplift": "quality gate suppressed visual carry-through",
        "No usable visual segments were available for model-backed scoring.": "no usable segments were available for model-backed visual scoring",
    }
    return replacements.get(cleaned, cleaned)


def _sanitize_audio_timing_note(note: str | None) -> str:
    cleaned = str(note or "").strip()
    replacements = {
        "Audio timings are attached only to a few curated Q&A moments matched against an ASR transcript. They are supporting review cues, not full transcript-to-media alignment.": (
            "Audio timings are attached only to a few curated Q&A moments matched against an ASR transcript. "
            "They are supporting review cues, not a full transcript-to-media map."
        ),
    }
    return replacements.get(cleaned, cleaned)


def _comparison_note(code: str) -> str:
    return COMPARISON_NOTE_BY_CODE.get(code, COMPARISON_NOTE_BY_CODE["no_expected_polarity"])


def _visual_observation_tag(direction: str | None) -> str:
    mapping = {
        "supportive": "steady_visible_delivery",
        "cautionary": "raised_visible_change",
        "neutral": "mixed_visible_change",
        "unavailable": "unavailable",
    }
    return mapping.get(str(direction or "").strip().lower(), "unavailable")


def _sanitize_visual_summary_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for item in items:
        sanitized.append(
            {
                "segment_id": int(item.get("segment_id", 0)),
                "section": str(item.get("section", "")),
                "speaker_role": str(item.get("speaker_role", "")),
                "start_time_s": float(item.get("start_time_s", 0.0)),
                "end_time_s": float(item.get("end_time_s", 0.0)),
                "visual_change_score": float(item.get("visual_change_score", 0.0)),
                "head_motion_energy": float(item.get("head_motion_energy", 0.0)),
                "head_pose_drift_mean": float(item.get("head_pose_drift_mean", 0.0)),
                "blink_rate_per_10s": float(item.get("blink_rate_per_10s", 0.0)),
                "face_visible_pct": float(item.get("face_visible_pct", 0.0)),
                "quality_note": _sanitize_visual_quality_note(item.get("confidence_note")),
                "observation_tag": _visual_observation_tag(item.get("support_direction")),
                "text": str(item.get("text", "")),
            }
        )
    return sanitized


def _sanitize_visual_quality_gate(quality_gate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(quality_gate, dict):
        return {}
    sanitized = dict(quality_gate)
    if "mean_landmark_confidence" in sanitized:
        sanitized["mean_landmark_coverage"] = sanitized.pop("mean_landmark_confidence")
    if "landmark_confidence_ok" in sanitized:
        sanitized["landmark_coverage_ok"] = sanitized.pop("landmark_confidence_ok")
    return sanitized


def _sanitize_visual_summary(summary: dict[str, Any]) -> dict[str, Any]:
    quality_assessment = dict(summary.get("visual_confidence_support", {}))
    model_backed = dict(summary.get("model_support", {}))
    return {
        "schema_version": summary.get("schema_version"),
        "video_available": summary.get("video_available"),
        "visual_features_available": summary.get("visual_features_available"),
        "video_quality_ok": summary.get("video_quality_ok"),
        "quality_gate": _sanitize_visual_quality_gate(summary.get("quality_gate", {})),
        "video_metadata": summary.get("video_metadata"),
        "face_visibility_overall": summary.get("face_visibility_overall"),
        "prepared_baseline_visual_stability": summary.get("prepared_baseline_visual_stability"),
        "qa_visual_shift_score": summary.get("qa_visual_shift_score"),
        "facial_tension_level": summary.get("facial_tension_level"),
        "head_motion_pressure": summary.get("head_motion_pressure"),
        "visual_stability": summary.get("visual_stability"),
        "observation_mode": summary.get("support_mode"),
        "quality_assessment": {
            "level": quality_assessment.get("level"),
            "suppressed": quality_assessment.get("suppressed"),
            "reason": _sanitize_visual_quality_note(quality_assessment.get("reason")),
        },
        "model_backed_scoring": {
            "available": model_backed.get("available"),
            "mode": model_backed.get("mode"),
            "reason": _sanitize_visual_quality_note(model_backed.get("reason")),
        },
        "most_usable_visual_windows": _sanitize_visual_summary_items(
            list(summary.get("strongest_visual_evidence", []))
        ),
        "most_visually_changed_segments": _sanitize_visual_summary_items(
            list(summary.get("most_visually_changed_segments", []))
        ),
        "notable_limited_quality_segments": [
            {
                **item,
                "quality_note": _sanitize_visual_quality_note(item.get("confidence_note")),
            }
            for item in list(summary.get("notable_low_confidence_segments", []))
        ],
        "limitations": list(summary.get("limitations", [])),
        "notes": [
            "Visual rows are bounded observational notes only and should not be read as corroboration of transcript or sidecar reads.",
            "Pose coverage is limited in this recording, so visible-delivery notes stay narrow even when face visibility is usable.",
        ],
    }


def build_asset_audit(root: Path | None = None, *, video_path: str | Path | None = None) -> dict[str, Any]:
    case_dir = case_root(root)
    video_source = resolve_video_source(video_path)
    transcript_pdf = case_dir / "raw" / "transcript" / "netflix_q1_2022_transcript.pdf"
    shareholder_pdf = case_dir / "raw" / "shareholder_letter" / "netflix_q1_2022_shareholder_letter.pdf"
    financial_xlsx = case_dir / "raw" / "financials" / "netflix_q1_2022_financials.xlsx"
    financial_csv = case_dir / "raw" / "financials" / "netflix_q1_2022_income_statement.csv"
    video_verification = _read_json(case_dir / "raw" / "video" / "video_verification.json")
    audio_status = _read_json(case_dir / "processed" / "audio_behavior" / "audio_status.json")
    audio_summary = _read_json(case_dir / "processed" / "audio_behavior" / "audio_behavior_summary.json")

    video_usable = bool(video_source["resolved_video_path"])
    if video_usable and video_source["resolved_from_fallback"]:
        video_usability_reason = (
            "The exact requested file path did not match, but a local Netflix MP4 fallback was found and used for a bounded supporting-only visual pass."
        )
    elif video_usable:
        video_usability_reason = "The exact requested file path matched directly and was used for a bounded supporting-only visual pass."
    else:
        video_usability_reason = "No local MP4 was found, so visual support should be skipped."

    return {
        "case_id": CASE_ID,
        "review_generated_at": datetime.now(UTC).isoformat(),
        "preferred_video_check": video_source,
        "repo_case_sources": {
            "transcript_pdf": {"path": str(transcript_pdf), "exists": transcript_pdf.exists()},
            "shareholder_letter_pdf": {"path": str(shareholder_pdf), "exists": shareholder_pdf.exists()},
            "financial_workbook": {"path": str(financial_xlsx), "exists": financial_xlsx.exists()},
            "income_statement_csv": {"path": str(financial_csv), "exists": financial_csv.exists()},
            "video_verification_json": {
                "path": str(case_dir / "raw" / "video" / "video_verification.json"),
                "exists": True,
                "payload": video_verification,
            },
            "processed_audio_status": {
                "path": str(case_dir / "processed" / "audio_behavior" / "audio_status.json"),
                "exists": True,
                "payload": audio_status,
            },
            "processed_audio_summary": {
                "path": str(case_dir / "processed" / "audio_behavior" / "audio_behavior_summary.json"),
                "exists": True,
                "payload": {
                    "audio_available": audio_summary.get("audio_available"),
                    "audio_quality_ok": audio_summary.get("audio_quality_ok"),
                    "usable_review_moments": audio_status.get("usable_review_moments"),
                },
            },
        },
        "requested_external_fallback_sources": _uploaded_source_checks(),
        "missing_or_untracked_items": [
            "The repo does not track the raw Netflix MP4 in data/demo_cases/netflix_q1_2022/raw/video/.",
            "The repo does not track the extracted WAV in data/demo_cases/netflix_q1_2022/raw/audio/.",
        ],
        "video_usable_for_bounded_visual_analysis": video_usable,
        "video_usability_reason": video_usability_reason,
    }


def _load_joined_review_rows(root: Path | None = None) -> dict[str, dict[str, Any]]:
    payload = _read_json(case_root(root) / "processed" / "joined_review" / "joined_review_moments.json")
    return {
        str(row["row_id"]): row
        for row in payload.get("joined_review_moments", [])
        if isinstance(row, dict) and row.get("row_id")
    }


def _load_evidence_rows(root: Path | None = None) -> dict[str, dict[str, Any]]:
    payload = _read_json(case_root(root) / "demo" / "evidence_rows" / "netflix_q1_2022_evidence_rows.json")
    return {
        str(row["row_id"]): row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("row_id")
    }


def _load_chunks(root: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(case_root(root) / "processed" / "chunks" / "chunks_scored.csv", keep_default_na=False)


def _load_guidance(root: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(case_root(root) / "processed" / "signals" / "guidance.csv", keep_default_na=False)


def _load_qa_pairs(root: Path | None = None) -> list[dict[str, Any]]:
    payload = _read_json(case_root(root) / "processed" / "qa_pairs" / "qa_pairs.json")
    rows = payload.get("qa_pairs", payload if isinstance(payload, list) else [])
    return [row for row in rows if isinstance(row, dict)]


def _load_audio_rows(root: Path | None = None) -> dict[str, dict[str, Any]]:
    payload = _read_json(case_root(root) / "processed" / "audio_behavior" / "audio_review_rows.json")
    return {
        str(row["row_id"]): row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("row_id")
    }


def _select_chunk(frame: pd.DataFrame, *, start: float, end: float) -> dict[str, Any]:
    match = frame[(frame["start"].astype(float) == float(start)) & (frame["end"].astype(float) == float(end))]
    if match.empty:
        raise RuntimeError(f"Unable to locate Netflix chunk {start}-{end}.")
    return dict(match.iloc[0].to_dict())


def _select_guidance(frame: pd.DataFrame, *, text_contains: str) -> dict[str, Any]:
    match = frame[frame["text"].astype(str).str.contains(text_contains, case=False, regex=False, na=False)]
    if match.empty:
        raise RuntimeError(f"Unable to locate Netflix guidance span containing '{text_contains}'.")
    return dict(match.iloc[0].to_dict())


def _find_qa_pair(qa_pairs: list[dict[str, Any]], *, answer_excerpt: str) -> dict[str, Any]:
    needle = " ".join(answer_excerpt.split()[:12]).strip()
    for row in qa_pairs:
        answer_text = str(row.get("answer_text", ""))
        if needle and needle in answer_text:
            return row
    raise RuntimeError(f"Unable to locate Netflix QA pair for excerpt '{needle}'.")


def _find_qa_pair_by_id(qa_pairs: list[dict[str, Any]], *, qa_pair_id: int | None) -> dict[str, Any] | None:
    if qa_pair_id is None:
        return None
    for row in qa_pairs:
        if int(row.get("qa_pair_id", -1)) == int(qa_pair_id):
            return row
    return None


def build_curated_moment_manifest(root: Path | None = None) -> dict[str, Any]:
    joined_rows = _load_joined_review_rows(root)
    evidence_rows = _load_evidence_rows(root)
    chunks = _load_chunks(root)
    guidance = _load_guidance(root)
    qa_pairs = _load_qa_pairs(root)
    audio_rows = _load_audio_rows(root)

    moments: list[dict[str, Any]] = []
    for spec in MOMENT_SPECS:
        source_kind = str(spec["source_kind"])
        selector = dict(spec["selector"])
        if source_kind == "joined_review":
            row = joined_rows[str(selector["row_id"])]
            audio_row = audio_rows.get(str(row.get("audio_support", {}).get("row_id") or row.get("optional_audio_support", {}).get("row_id") or ""))
            qa_pair = _find_qa_pair_by_id(qa_pairs, qa_pair_id=int(audio_row["qa_pair_id"]) if audio_row and audio_row.get("qa_pair_id") else None)
            if qa_pair is None:
                qa_pair = _find_qa_pair(qa_pairs, answer_excerpt=str(row.get("quote", row.get("source_excerpt", ""))))
            start_s = audio_row.get("question_start_s") if audio_row else None
            end_s = audio_row.get("answer_end_s") if audio_row else None
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_deterministic_artifact": str(row.get("source_artifact_path", "")),
                "source_locator": str(row.get("source_locator", "")),
                "text": str(qa_pair.get("answer_text", row.get("quote", ""))),
                "quote_or_span": str(row.get("quote", row.get("source_excerpt", ""))),
                "question_text": str(qa_pair.get("question_text", "")),
                "question_speaker": str(qa_pair.get("question_speaker", "")),
                "answer_speakers": qa_pair.get("answer_speakers", []),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label") or row.get("plain_english_label", "")),
                "deterministic_signal_summary": str(row.get("extracted_signal", row.get("clear_signal", ""))),
                "why_selected": spec["why_selected"],
                "source_row_id": str(row.get("row_id", "")),
                "start_time_s": start_s,
                "end_time_s": end_s,
                "timestamp_range": str(row.get("optional_timestamp", "")) or None,
                "audio_row_id": str(audio_row["row_id"]) if audio_row else None,
                "deterministic_polarity_hint": None,
            }
        elif source_kind == "chunk":
            row = _select_chunk(chunks, start=float(selector["start"]), end=float(selector["end"]))
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_deterministic_artifact": "processed/chunks/chunks_scored.csv",
                "source_locator": f"start:{row['start']}-end:{row['end']}",
                "text": str(row["text"]),
                "quote_or_span": str(row["text"]),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label", spec["moment_id"].replace("_", " "))),
                "deterministic_signal_summary": str(row["text"]),
                "why_selected": spec["why_selected"],
                "source_row_id": spec["moment_id"],
                "start_time_s": float(row["start"]),
                "end_time_s": float(row["end"]),
                "timestamp_range": f"{_timestamp_label(float(row['start']))}-{_timestamp_label(float(row['end']))}",
                "audio_row_id": None,
                "deterministic_polarity_hint": str(row.get("sentiment", "")).strip().lower() or None,
                "source_sentiment": str(row.get("sentiment", "")),
                "source_score": float(row.get("score")) if str(row.get("score", "")).strip() else None,
                "source_signed_score": float(row.get("signed_score")) if str(row.get("signed_score", "")).strip() else None,
                "positive_prob": float(row.get("positive_prob")) if str(row.get("positive_prob", "")).strip() else None,
                "negative_prob": float(row.get("negative_prob")) if str(row.get("negative_prob", "")).strip() else None,
            }
        elif source_kind == "guidance":
            row = _select_guidance(guidance, text_contains=str(selector["text_contains"]))
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_deterministic_artifact": "processed/signals/guidance.csv",
                "source_locator": f"start:{row['start']}-end:{row['end']}",
                "text": str(row["text"]),
                "quote_or_span": str(row["text"]),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label", "negative Q2 paid net adds guidance")),
                "deterministic_signal_summary": str(row["text"]),
                "why_selected": spec["why_selected"],
                "source_row_id": spec["moment_id"],
                "start_time_s": float(row["start"]),
                "end_time_s": float(row["end"]),
                "timestamp_range": f"{_timestamp_label(float(row['start']))}-{_timestamp_label(float(row['end']))}",
                "audio_row_id": None,
                "deterministic_polarity_hint": str(row.get("sentiment", "")).strip().lower() or None,
                "source_sentiment": str(row.get("sentiment", "")),
                "source_score": float(row.get("score")) if str(row.get("score", "")).strip() else None,
                "guidance_strength": float(row.get("guidance_strength")) if str(row.get("guidance_strength", "")).strip() else None,
                "topic": str(row.get("topic", "")),
                "period": str(row.get("period", "")),
                "matched_cues": str(row.get("matched_cues", "")),
            }
        elif source_kind == "evidence_row":
            row = evidence_rows[str(selector["row_id"])]
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_deterministic_artifact": f"demo/evidence_rows/netflix_q1_2022_evidence_rows.json#{row['row_id']}",
                "source_locator": str(row["row_id"]),
                "text": str(row["source_excerpt"]),
                "quote_or_span": str(row["source_excerpt"]),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label") or row["plain_english_label"]),
                "deterministic_signal_summary": str(row["extracted_signal"]),
                "why_selected": spec["why_selected"],
                "source_row_id": str(row["row_id"]),
                "start_time_s": None,
                "end_time_s": None,
                "timestamp_range": None,
                "audio_row_id": None,
                "deterministic_polarity_hint": None,
                "source_type": str(row.get("source_type", "")),
            }
        else:  # pragma: no cover - guarded by static specs
            raise RuntimeError(f"Unsupported Netflix moment source kind: {source_kind}")

        moment["expected_sidecar_polarity"] = EXPECTED_POLARITY_BY_CATEGORY.get(moment["deterministic_signal_category"])
        moments.append(moment)

    ordered = sorted(moments, key=lambda item: int(item["rank"]))
    return {
        "case_id": CASE_ID,
        "primary_moment_count": len(ordered),
        "showcase_moment_count": sum(1 for moment in ordered if moment["top_8_showcase"]),
        "moments": ordered,
        "notes": [
            "These moments are transcript-first selections built from committed deterministic Netflix artifacts.",
            "Audio and visual layers remain optional support only.",
        ],
    }


def write_curated_sidecar_inputs(
    manifest: dict[str, Any],
    *,
    root: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    target_dir = curated_output_dir(root) / "inputs" if output_dir is None else Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    chunk_rows: list[dict[str, Any]] = []
    guidance_rows: list[dict[str, Any]] = []
    qa_rows: list[dict[str, Any]] = []
    qa_pair_id = 0
    for moment in manifest["moments"]:
        if moment["unit_type"] == "chunks":
            chunk_rows.append(
                {
                    "unit_id": moment["moment_id"],
                    "moment_id": moment["moment_id"],
                    "start": moment.get("start_time_s", ""),
                    "end": moment.get("end_time_s", ""),
                    "text": moment["text"],
                    "sentiment": str(moment.get("source_sentiment", "")),
                    "score": moment.get("source_score", ""),
                    "signed_score": moment.get("source_signed_score", ""),
                    "positive_prob": moment.get("positive_prob", ""),
                    "negative_prob": moment.get("negative_prob", ""),
                }
            )
        elif moment["unit_type"] == "guidance_spans":
            guidance_rows.append(
                {
                    "unit_id": moment["moment_id"],
                    "moment_id": moment["moment_id"],
                    "start": moment.get("start_time_s", ""),
                    "end": moment.get("end_time_s", ""),
                    "text": moment["text"],
                    "sentiment": str(moment.get("source_sentiment", "")),
                    "score": moment.get("source_score", ""),
                    "topic": str(moment.get("topic", "")),
                    "period": str(moment.get("period", "")),
                    "guidance_strength": moment.get("guidance_strength", ""),
                    "matched_cues": str(moment.get("matched_cues", "")),
                }
            )
        elif moment["unit_type"] == "qa_answers":
            qa_pair_id += 1
            qa_rows.append(
                {
                    "unit_id": moment["moment_id"],
                    "moment_id": moment["moment_id"],
                    "qa_pair_id": qa_pair_id,
                    "source_doc": "curated_multimodal_manifest",
                    "question_speaker": moment.get("question_speaker", ""),
                    "question_text": moment.get("question_text", ""),
                    "answer_speakers": moment.get("answer_speakers", []),
                    "answer_text": moment["text"],
                }
            )

    chunks_path = target_dir / "curated_chunks.csv"
    guidance_path = target_dir / "curated_guidance.csv"
    qa_path = target_dir / "curated_qa_pairs.json"

    pd.DataFrame(chunk_rows).to_csv(chunks_path, index=False)
    pd.DataFrame(guidance_rows).to_csv(guidance_path, index=False)
    qa_path.write_text(json.dumps({"qa_pairs": qa_rows}, indent=2), encoding="utf-8")
    return {
        "chunks": chunks_path,
        "guidance_spans": guidance_path,
        "qa_answers": qa_path,
    }


def run_sidecars_for_manifest(
    manifest: dict[str, Any],
    *,
    root: Path | None = None,
    models: list[str] | None = None,
    device: str = "auto",
    zero_shot_config: str = DEFAULT_ZERO_SHOT_LABEL_CONFIG,
) -> dict[str, Any]:
    artifacts = write_curated_sidecar_inputs(manifest, root=root)
    model_names = list(models or ["finbert_tone", "financial_roberta", "deberta_zero_shot", "mpnet_embeddings"])
    output_root = curated_output_dir(root)
    payload = run_sidecar_models(
        case_id=CASE_ID,
        artifact_inputs=artifacts,
        unit_types=["chunks", "guidance_spans", "qa_answers"],
        model_names=model_names,
        output_root=output_root,
        device=device,
        smoke_limit=None,
        prewarm=False,
        resume=True,
        force=False,
        zero_shot_config=zero_shot_config,
    )
    evaluation_paths = write_case_evaluation_summary(case_id=CASE_ID, output_root=output_root)
    return {
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "run_payload": payload,
        "evaluation_paths": {key: str(value) for key, value in evaluation_paths.items()},
        "output_root": str(output_root),
    }


def _load_sidecar_outputs(root: Path | None = None) -> dict[str, dict[str, Any]]:
    base = curated_output_dir(root) / CASE_ID / "model_sidecars"
    outputs: dict[str, dict[str, Any]] = {}
    if not base.exists():
        return outputs
    for model_dir in sorted(path for path in base.iterdir() if path.is_dir() and path.name != "evaluation"):
        rows_path = model_dir / "scored_rows.csv"
        summary_path = model_dir / "run_summary.json"
        disagreement_path = model_dir / "disagreement_report.json"
        if not rows_path.exists() or not summary_path.exists():
            continue
        outputs[model_dir.name] = {
            "rows": pd.read_csv(rows_path, keep_default_na=False),
            "run_summary": _read_json(summary_path),
            "disagreement_report": _read_json(disagreement_path) if disagreement_path.exists() else {},
        }
    return outputs


def build_model_comparison(
    manifest: dict[str, Any],
    *,
    root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    sidecar_outputs = _load_sidecar_outputs(root)
    evaluation_summary_path = curated_output_dir(root) / CASE_ID / "model_sidecars" / "evaluation" / "comparison_summary.json"
    evaluation_summary = _read_json(evaluation_summary_path) if evaluation_summary_path.exists() else {}

    panel_rows: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    noisy_moment_ids: set[str] = set()
    for moment in manifest["moments"]:
        per_model: dict[str, Any] = {}
        comparable_labels: list[str] = []
        for model_name, output in sidecar_outputs.items():
            rows = output["rows"]
            match = rows[rows["unit_id"].astype(str) == str(moment["moment_id"])]
            if match.empty:
                continue
            row = match.iloc[0].to_dict()
            group_top_labels = {}
            raw_groups = str(row.get("group_top_labels_json", "")).strip()
            if raw_groups:
                try:
                    group_top_labels = json.loads(raw_groups)
                except json.JSONDecodeError:
                    group_top_labels = {}
            model_row = {
                "top_label": str(row.get("top_label", "")),
                "top_score": float(row.get("top_score", 0.0) or 0.0),
                "comparable_label": str(row.get("comparable_label", "")),
                "group_top_labels": group_top_labels,
                "output_kind": str(row.get("output_kind", "")),
            }
            if model_row["comparable_label"]:
                comparable_labels.append(model_row["comparable_label"])
            per_model[model_name] = model_row

        label_counts = pd.Series(comparable_labels).value_counts().to_dict() if comparable_labels else {}
        consensus_label = max(label_counts, key=label_counts.get) if label_counts else ""
        expected_polarity = str(moment.get("expected_sidecar_polarity") or "")
        comparison_code = "no_expected_polarity"
        if expected_polarity and comparable_labels:
            if all(label == expected_polarity for label in comparable_labels):
                comparison_code = "aligned_with_expected_category"
            elif any(label == expected_polarity for label in comparable_labels):
                comparison_code = "mixed_vs_expected_category"
            else:
                comparison_code = "diverged_from_expected_category"
        elif comparable_labels:
            comparison_code = "supporting_only_non_polar_category"

        sidecars_split = len(set(comparable_labels)) > 1 if comparable_labels else False

        panel_row = {
            "moment_id": moment["moment_id"],
            "rank": moment["rank"],
            "top_8_showcase": moment["top_8_showcase"],
            "unit_type": moment["unit_type"],
            "deterministic_signal_category": moment["deterministic_signal_category"],
            "expected_sidecar_polarity": expected_polarity or None,
            "consensus_label": consensus_label or None,
            "model_outputs": per_model,
            "sidecars_split": sidecars_split,
            "comparison_note": _comparison_note(comparison_code),
            "quote_or_span": moment["quote_or_span"],
        }
        panel_rows.append(panel_row)

        if sidecars_split or comparison_code == "diverged_from_expected_category":
            if comparison_code in {"mixed_vs_expected_category", "diverged_from_expected_category"}:
                noisy_moment_ids.add(str(moment["moment_id"]))
            disagreements.append(
                {
                    "moment_id": moment["moment_id"],
                    "rank": moment["rank"],
                    "deterministic_signal_category": moment["deterministic_signal_category"],
                    "expected_sidecar_polarity": expected_polarity or None,
                    "observed_labels": comparable_labels,
                    "comparison_note": _comparison_note(comparison_code),
                    "quote_or_span": _truncate(moment["quote_or_span"]),
                }
            )

    similarity_hotspots: list[dict[str, Any]] = []
    for model_name, output in sidecar_outputs.items():
        disagreement_report = output["disagreement_report"]
        if disagreement_report.get("similarity_hotspots"):
            for item in disagreement_report["similarity_hotspots"]:
                similarity_hotspots.append({"model_name": model_name, **item})

    pairwise_summary = []
    for row in evaluation_summary.get("pairwise_classification", []):
        if not isinstance(row, dict):
            continue
        pairwise_summary.append(
            {
                "left_model": row.get("left_model"),
                "right_model": row.get("right_model"),
                "moments_compared": row.get("rows_compared"),
                "same_top_label_rate": row.get("top_label_agreement_rate"),
                "same_broad_label_rate": row.get("comparable_label_agreement_rate"),
                "hotspots": row.get("hotspots", []),
                "review_note": "These rates only describe how often the sidecars landed on the same broad label within the curated Netflix moment set.",
            }
        )

    comparison_payload = {
        "case_id": CASE_ID,
        "status": "ok" if sidecar_outputs else "no_sidecar_outputs",
        "models_run": [
            {
                "model_name": model_name,
                "status": output["run_summary"].get("status"),
                "model_kind": output["run_summary"].get("model_kind"),
                "runtime_s": output["run_summary"].get("runtime_s"),
                "units_processed": output["run_summary"].get("units_processed"),
                "unit_type_counts": output["run_summary"].get("unit_type_counts", {}),
            }
            for model_name, output in sidecar_outputs.items()
        ],
        "pairwise_summary": pairwise_summary,
        "moment_rows": panel_rows,
        "notes": [
            "Deterministic categories remain canonical; these comparisons are supporting-only review aids.",
            "Comparison notes are reviewer aids only and do not override the transcript-backed deterministic read.",
        ],
    }
    disagreement_payload = {
        "case_id": CASE_ID,
        "status": "ok" if sidecar_outputs else "no_sidecar_outputs",
        "pairwise_model_disagreements": disagreements,
        "embedding_similarity_hotspots": similarity_hotspots[:8],
        "noisy_or_unhelpful_sidecars": [
            item for item in disagreements if str(item["moment_id"]) in noisy_moment_ids
        ],
        "notes": [
            "Disagreement hotspots are review priorities, not proof that one layer is better than another.",
            "Embedding hotspots flag semantic similarity across differently labeled moments for manual inspection.",
        ],
    }
    return comparison_payload, disagreement_payload


def build_audio_support(
    manifest: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    audio_rows = _load_audio_rows(root)
    audio_summary = _read_json(case_root(root) / "processed" / "audio_behavior" / "audio_behavior_summary.json")
    moments: list[dict[str, Any]] = []
    for moment in manifest["moments"]:
        audio_row_id = moment.get("audio_row_id")
        if audio_row_id and audio_row_id in audio_rows:
            row = audio_rows[str(audio_row_id)]
            moments.append(
                {
                    "moment_id": moment["moment_id"],
                    "status": "aligned",
                    "question_time_range": row.get("question_time_range"),
                    "answer_time_range": row.get("answer_time_range"),
                    "pause_before_answer_ms": row.get("pause_before_answer_ms"),
                    "filler_density": row.get("filler_density"),
                    "hesitation_label": row.get("hesitation_label"),
                    "qa_shift_label": row.get("qa_shift_label"),
                    "plain_english_audio_summary": row.get("plain_english_audio_summary"),
                    "plain_english_interpretation": row.get("plain_english_interpretation"),
                    "timing_note": _sanitize_audio_timing_note(row.get("timing_note")),
                }
            )
        else:
            moments.append(
                {
                    "moment_id": moment["moment_id"],
                    "status": "unavailable",
                    "reason": "No curated repo audio timing is attached to this deterministic moment.",
                }
            )
    return {
        "case_id": CASE_ID,
        "status": "ok",
        "audio_available": audio_summary.get("audio_available"),
        "audio_quality_ok": audio_summary.get("audio_quality_ok"),
        "summary": {
            "hesitation_overall": audio_summary.get("hesitation_overall"),
            "qa_hesitation_shift": audio_summary.get("qa_hesitation_shift"),
            "pause_pressure_delta": audio_summary.get("pause_pressure_delta"),
            "audio_usability_note": audio_summary.get("audio_confidence_support"),
        },
        "moments": moments,
        "notes": [
            "Audio rows were reused from the committed curated Q&A audio artifacts for this case.",
            "Audio support remains bounded to the aligned Q&A windows already present in the repo.",
        ],
    }


def build_visual_support(
    manifest: dict[str, Any],
    *,
    root: Path | None = None,
    video_path: str | Path | None = None,
    sample_fps: float = 0.25,
) -> tuple[dict[str, Any], bool]:
    resolved_video = resolve_video_source(video_path)
    video_file = Path(resolved_video["resolved_video_path"]).expanduser().resolve() if resolved_video["resolved_video_path"] else None
    if video_file is None:
        return (
            {
                "case_id": CASE_ID,
                "status": "skipped",
                "reason": "No usable local Netflix MP4 was available for the bounded visual pass.",
                "video_source": resolved_video,
                "notes": [
                    "Visual review was skipped instead of inventing scene-level observations.",
                ],
            },
            True,
        )

    audio_rows = _load_audio_rows(root)
    segments: list[dict[str, Any]] = []
    segment_to_moment: dict[int, str] = {}
    for index, moment in enumerate(manifest["moments"], start=1):
        audio_row_id = str(moment.get("audio_row_id") or "")
        row = audio_rows.get(audio_row_id)
        if not row:
            continue
        segment_to_moment[index] = moment["moment_id"]
        segments.append(
            {
                "segment_id": index,
                "start": float(row["answer_start_s"]),
                "end": float(row["answer_end_s"]),
                "phase": "q_and_a",
                "speaker_role": "management",
                "text": str(row["management_answer_excerpt"]),
            }
        )
    qa_segments_df = pd.DataFrame(segments)
    if qa_segments_df.empty:
        return (
            {
                "case_id": CASE_ID,
                "status": "skipped",
                "reason": "No curated answer-level timestamps were available for a bounded visual pass.",
                "video_source": resolved_video,
                "notes": [
                    "Visual review was skipped because the curated answer windows could not be aligned safely.",
                ],
            },
            True,
        )

    visual_dir = curated_output_dir(root) / "visual_support"
    frames_path = visual_dir / "visual_behavior_frames.csv"
    segments_path = visual_dir / "visual_behavior_segments.csv"
    summary_path = visual_dir / "visual_behavior_summary.json"
    if frames_path.exists() and segments_path.exists() and summary_path.exists():
        summary = _read_json(summary_path)
        segments_df = pd.read_csv(segments_path, keep_default_na=False)
        outputs = {
            "frames_path": frames_path,
            "segments_path": segments_path,
            "summary_path": summary_path,
            "segments_df": segments_df,
            "summary": summary,
        }
    else:
        outputs = write_visual_behavior_outputs(video_file, qa_segments_df, visual_dir, sample_fps=sample_fps)
    summary = outputs["summary"]
    if not summary.get("video_quality_ok"):
        return (
            {
                "case_id": CASE_ID,
                "status": "skipped",
                "reason": _sanitize_visual_quality_note(
                    str(summary.get("visual_confidence_support", {}).get("reason", "Visual quality gate failed."))
                ),
                "video_source": resolved_video,
                "video_source_path": str(video_file),
                "summary": _sanitize_visual_summary(summary),
                "intermediate_paths": {
                    "frames_csv": str(outputs["frames_path"]),
                    "segments_csv": str(outputs["segments_path"]),
                    "summary_json": str(outputs["summary_path"]),
                },
                "notes": [
                    "Visual review was skipped because the quality gate did not support a bounded observational read.",
                ],
            },
            True,
        )

    sanitized_summary = _sanitize_visual_summary(summary)
    moment_rows: list[dict[str, Any]] = []
    for row in outputs["segments_df"].to_dict(orient="records"):
        moment_id = segment_to_moment.get(int(row["segment_id"]))
        if not moment_id:
            continue
        moment_rows.append(
            {
                "moment_id": moment_id,
                "status": "aligned",
                "start_time_s": float(row["start_time_s"]),
                "end_time_s": float(row["end_time_s"]),
                "visual_stability_label": str(row["visual_stability_label"]),
                "observation_tag": _visual_observation_tag(row.get("support_direction")),
                "observation_note": str(row["support_note"]),
                "quality_note": _sanitize_visual_quality_note(row.get("confidence_note")),
                "face_visible_pct": float(row["face_visible_pct"]),
                "visual_change_score": float(row["visual_change_score"]),
                "head_motion_energy": float(row["head_motion_energy"]),
            }
        )

    return (
        {
            "case_id": CASE_ID,
            "status": "ok",
            "video_source": resolved_video,
            "video_source_path": str(video_file),
            "sample_fps": sample_fps,
            "summary": sanitized_summary,
            "moments": moment_rows,
            "intermediate_paths": {
                "frames_csv": str(outputs["frames_path"]),
                "segments_csv": str(outputs["segments_path"]),
                "summary_json": str(outputs["summary_path"]),
            },
            "notes": [
                "Visual behavior remains supporting-only and was run on the bounded timed Q&A answer windows.",
                "Only the windows with existing curated audio timing were used for the visual pass.",
                "Visible-delivery notes are observational only and do not corroborate transcript or sidecar interpretations.",
            ],
        },
        False,
    )


def _moment_lookup(rows: list[dict[str, Any]], *, key: str = "moment_id") -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if row.get(key)}


def _reviewer_note(moment: dict[str, Any], comparison_row: dict[str, Any], audio_row: dict[str, Any] | None, visual_row: dict[str, Any] | None) -> str:
    comparison_note = str(comparison_row.get("comparison_note", ""))
    if comparison_row.get("sidecars_split"):
        return "Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only."
    if comparison_note == _comparison_note("aligned_with_expected_category") and audio_row and audio_row.get("status") == "aligned":
        return "Transcript-first pressure read stays primary here, and the bounded audio cues move in the same general direction."
    if comparison_note == _comparison_note("aligned_with_expected_category"):
        return "Optional sidecars broadly moved with the deterministic read here, which makes this a cleaner optional-context moment than a hotspot."
    if visual_row and visual_row.get("status") == "aligned":
        return "Visual cues were usable for this timed window, but they remain observational context rather than a determinative read."
    if comparison_note == _comparison_note("supporting_only_non_polar_category"):
        return "This is a non-polar management framing moment, so sidecars add color but should not be treated as a categorical override."
    return "This moment is best reviewed transcript-first because the optional support layers are either mixed or only partially available."


def build_panel_payload(
    manifest: dict[str, Any],
    comparison_payload: dict[str, Any],
    disagreement_payload: dict[str, Any],
    audio_payload: dict[str, Any],
    visual_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest_by_id = _moment_lookup(manifest["moments"])
    comparison_by_id = _moment_lookup(comparison_payload["moment_rows"])
    audio_by_id = _moment_lookup(audio_payload["moments"])
    visual_by_id = _moment_lookup(visual_payload.get("moments", [])) if visual_payload.get("status") == "ok" else {}

    rows: list[dict[str, Any]] = []
    pressure_rows: list[dict[str, Any]] = []
    for moment_id, moment in manifest_by_id.items():
        comparison_row = comparison_by_id.get(moment_id, {})
        audio_row = audio_by_id.get(moment_id)
        visual_row = visual_by_id.get(moment_id)
        caveat = (
            "Deterministic transcript-backed artifacts stay canonical; supporting layers here are optional reviewer context only."
        )
        row = {
            "moment_id": moment_id,
            "rank": moment["rank"],
            "top_8_showcase": moment["top_8_showcase"],
            "raw_quote_or_span": moment["quote_or_span"],
            "deterministic_signal": {
                "category": moment["deterministic_signal_category"],
                "label": moment["plain_english_label"],
                "summary": moment["deterministic_signal_summary"],
                "source_artifact": moment["source_deterministic_artifact"],
            },
            "sidecar_outputs": comparison_row,
            "audio_support": audio_row or {"status": "unavailable"},
            "visual_support": visual_row or {"status": "unavailable"},
            "reviewer_note": _reviewer_note(moment, comparison_row, audio_row, visual_row),
            "caveat": caveat,
        }
        rows.append(row)
        if moment["unit_type"] == "qa_answers":
            pressure_rows.append(
                {
                    "moment_id": moment_id,
                    "rank": moment["rank"],
                    "analyst_question": moment.get("question_text"),
                    "executive_answer": moment["text"],
                    "deterministic_read": moment["deterministic_signal_summary"],
                    "nlp_sidecar_read": comparison_row,
                    "audio_support": audio_row or {"status": "unavailable"},
                    "visual_support": visual_row or {"status": "unavailable"},
                    "reviewer_note": row["reviewer_note"],
                }
            )

    rows = sorted(rows, key=lambda item: int(item["rank"]))
    pressure_rows = sorted(pressure_rows, key=lambda item: int(item["rank"]))
    disagreement_rows = [
        {
            **item,
            "audio_support": audio_by_id.get(str(item["moment_id"]), {"status": "unavailable"}),
            "visual_support": visual_by_id.get(str(item["moment_id"]), {"status": "unavailable"}),
        }
        for item in disagreement_payload.get("pairwise_model_disagreements", [])
    ]
    panel_payload = {
        "case_id": CASE_ID,
        "status": "ok",
        "selected_moment_count": len(rows),
        "showcase_moment_count": sum(1 for row in rows if row["top_8_showcase"]),
        "panel_rows": rows,
        "top_disagreement_hotspots": disagreement_rows[:8],
        "cleaner_optional_context_moments": [
            {
                "moment_id": row["moment_id"],
                "rank": row["rank"],
                "consensus_label": row["sidecar_outputs"].get("consensus_label"),
                "reviewer_note": row["reviewer_note"],
            }
            for row in rows
            if row["sidecar_outputs"].get("comparison_note") == _comparison_note("aligned_with_expected_category")
        ][:8],
        "what_sidecars_added": [
            "Fast cross-model comparison checks on the bounded Netflix moment set.",
            "A shortlist of disagreement hotspots to review before any future UI surfacing.",
            "Optional semantic grouping via embeddings where similarity helps cluster noisy moments.",
        ],
        "what_sidecars_did_not_add": [
            "No sidecar output replaces the deterministic transcript-backed evidence rows.",
            "No model output here establishes ground truth, predictive edge, or statistical lift.",
        ],
        "future_ui_surface_notes": [
            "The top-8 showcase moments can be surfaced as a fixed accordion or table without changing the current demo architecture.",
            "Pressure and disagreement subpanels are already shaped as persistent JSON bundles for later UI plumbing.",
        ],
    }
    pressure_panel = {
        "case_id": CASE_ID,
        "status": "ok",
        "rows": pressure_rows,
    }
    disagreement_panel = {
        "case_id": CASE_ID,
        "status": "ok",
        "rows": disagreement_rows,
    }
    return panel_payload, pressure_panel, disagreement_panel


def _render_asset_audit_markdown(audit: dict[str, Any]) -> str:
    preferred_video = audit["preferred_video_check"]
    resolved_video = preferred_video["resolved_video_path"] or "not found"
    requested_matched_directly = bool(resolved_video != "not found" and not preferred_video["resolved_from_fallback"])
    fallback_video = resolved_video if preferred_video["resolved_from_fallback"] else "not needed"
    lines = [
        "# Netflix Multimodal Asset Audit",
        "",
        f"- Case: `{audit['case_id']}`",
        f"- Requested exact MP4 path: `{preferred_video['requested_path']}`",
        f"- Requested exact MP4 path matched directly: `{requested_matched_directly}`",
        f"- Resolved local MP4 fallback found: `{fallback_video}`",
        f"- Bounded visual analysis usable: `{audit['video_usable_for_bounded_visual_analysis']}`",
        "",
        "## What Exists",
        "",
    ]
    for key, item in audit["repo_case_sources"].items():
        lines.append(f"- `{key}`: `{item['exists']}`")
        lines.append(f"  path: `{item['path']}`")
    lines.extend(
        [
            "",
            "## Requested External Fallbacks",
            "",
        ]
    )
    for key, item in audit.get("requested_external_fallback_sources", {}).items():
        lines.append(f"- `{key}`: `{item['exists']}`")
        lines.append(f"  path: `{item['path']}`")
    lines.extend(
        [
            "",
            "## Missing Or Untracked",
            "",
        ]
    )
    for item in audit["missing_or_untracked_items"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- {audit['video_usability_reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def _audio_support_markdown(audio_row: dict[str, Any]) -> str:
    if not audio_row or audio_row.get("status") != "aligned":
        return "unavailable for this moment"
    summary = str(audio_row.get("plain_english_audio_summary", "")).strip() or "bounded audio cues available"
    return f"{summary}; timing window `{audio_row.get('answer_time_range', 'n/a')}`"


def _visual_support_markdown(visual_row: dict[str, Any]) -> str:
    if not visual_row or visual_row.get("status") != "aligned":
        return "unavailable for this moment"
    return (
        f"{visual_row.get('observation_tag', 'unavailable')}: "
        f"{visual_row.get('observation_note', '')} "
        f"(quality note: {visual_row.get('quality_note', 'n/a')})"
    ).strip()


def _render_panel_markdown(panel_payload: dict[str, Any], pressure_panel: dict[str, Any], disagreement_panel: dict[str, Any]) -> str:
    lines = [
        "# Netflix Multimodal Evidence Panel",
        "",
        "- Deterministic transcript-backed outputs remain canonical.",
        "- NLP, audio, and visual layers are supporting only.",
        "",
        "## Top 8 Showcase",
        "",
    ]
    for row in panel_payload["panel_rows"]:
        if row["top_8_showcase"]:
            lines.append(f"- `{row['moment_id']}`")
    lines.extend(
        [
            "",
            "## Selected Moments",
            "",
        ]
    )
    for row in panel_payload["panel_rows"]:
        sidecars = row["sidecar_outputs"]
        lines.extend(
            [
                f"### {row['rank']}. {row['moment_id']}",
                "",
                f"- Top-8 showcase: `{row['top_8_showcase']}`",
                f"- Quote: {row['raw_quote_or_span']}",
                (
                    f"- Deterministic signal: `{row['deterministic_signal']['category']}` | "
                    f"`{row['deterministic_signal']['label']}`"
                ),
                (
                    f"- Sidecar read: consensus `{sidecars.get('consensus_label') or 'unavailable'}` | "
                    f"comparison note `{sidecars.get('comparison_note') or 'unavailable'}` | "
                    f"sidecars split `{'yes' if sidecars.get('sidecars_split') else 'no'}`"
                ),
                f"- Audio support: {_audio_support_markdown(row['audio_support'])}",
                f"- Visual support: {_visual_support_markdown(row['visual_support'])}",
                f"- Reviewer note: {row['reviewer_note']}",
                f"- Caveat: {row['caveat']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Pressure Moments Panel",
            "",
        ]
    )
    for row in pressure_panel["rows"]:
        lines.extend(
            [
                f"### {row['moment_id']}",
                "",
                f"- Analyst question: {_truncate(str(row.get('analyst_question', '')), limit=180)}",
                f"- Executive answer: {_truncate(str(row.get('executive_answer', '')), limit=180)}",
                f"- Deterministic read: {_truncate(str(row.get('deterministic_read', '')), limit=180)}",
                (
                    f"- NLP sidecar read: consensus "
                    f"`{row.get('nlp_sidecar_read', {}).get('consensus_label') or 'unavailable'}`"
                ),
                f"- Audio support: {_audio_support_markdown(row['audio_support'])}",
                f"- Visual support: {_visual_support_markdown(row['visual_support'])}",
                f"- Reviewer note: {row['reviewer_note']}",
                "",
            ]
        )
    lines.extend(["## Disagreement Hotspots", ""])
    if disagreement_panel["rows"]:
        for row in disagreement_panel["rows"]:
            lines.extend(
                [
                    f"### {row['moment_id']}",
                    "",
                    f"- Observed labels: `{', '.join(row.get('observed_labels', [])) or 'unavailable'}`",
                    f"- Comparison note: `{row.get('comparison_note', 'unavailable')}`",
                    f"- Quote: {_truncate(str(row['quote_or_span']), limit=220)}",
                    f"- Audio support: {_audio_support_markdown(row['audio_support'])}",
                    f"- Visual support: {_visual_support_markdown(row['visual_support'])}",
                    "",
                ]
            )
    else:
        lines.append("- No material pairwise sidecar disagreement hotspots were written for this run.")
    lines.extend(
        [
            "## Cleaner Optional-Context Moments",
            "",
        ]
    )
    for row in panel_payload.get("cleaner_optional_context_moments", []):
        lines.append(
            f"- `{row['moment_id']}`: consensus `{row.get('consensus_label') or 'unavailable'}` | {row.get('reviewer_note', '')}"
        )
    if not panel_payload.get("cleaner_optional_context_moments"):
        lines.append("- No cleaner optional-context moments were recorded for this run.")
    lines.extend(
        [
            "",
            "## What Sidecars Added",
            "",
        ]
    )
    for item in panel_payload.get("what_sidecars_added", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## What Sidecars Did Not Add",
            "",
        ]
    )
    for item in panel_payload.get("what_sidecars_did_not_add", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Later UI Surfacing",
            "",
        ]
    )
    for item in panel_payload.get("future_ui_surface_notes", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _render_summary_markdown(
    *,
    audit: dict[str, Any],
    sidecar_runtime: dict[str, Any],
    visual_payload: dict[str, Any],
    bundle_paths: BundlePaths,
    models: list[str],
    sample_fps: float,
    device: str,
    video_path: str | Path | None = None,
    pairwise_summary: list[dict[str, Any]] | None = None,
) -> str:
    preferred_video = audit["preferred_video_check"]
    resolved_video = preferred_video["resolved_video_path"] or "not found"
    requested_matched_directly = bool(resolved_video != "not found" and not preferred_video["resolved_from_fallback"])
    fallback_video = resolved_video if preferred_video["resolved_from_fallback"] else "not needed"
    visual_support_mode = None
    visual_support_note = None
    if visual_payload.get("status") == "ok":
        visual_summary = visual_payload.get("summary", {})
        visual_support_mode = visual_summary.get("observation_mode")
        if visual_support_mode == "heuristic_fallback" and not visual_summary.get("model_backed_scoring", {}).get("available", False):
            visual_support_note = "observational fallback only; no model-backed visual scoring"

    command_parts = [
        "PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py",
        f"--device {device}",
        f"--visual-sample-fps {sample_fps}",
    ]
    default_models = ["finbert_tone", "financial_roberta", "deberta_zero_shot", "mpnet_embeddings"]
    if models != default_models:
        command_parts.append(f"--models {' '.join(models)}")
    if video_path:
        command_parts.append(f"--video-path \"{Path(video_path).expanduser()}\"")
    sidecar_run_models = sidecar_runtime.get("run_payload", {}).get("models", []) if isinstance(sidecar_runtime, dict) else []
    sidecar_statuses = [str(item.get("status", "")) for item in sidecar_run_models if isinstance(item, dict)]

    lines = [
        "# Netflix Multimodal Panel Summary",
        "",
        "## What Ran",
        "",
        f"- Curated moment manifest generated for `{CASE_ID}` with `{len(MOMENT_SPECS)}` bounded moments and a top-8 showcase subset.",
        f"- Sidecar models requested: `{', '.join(models)}`",
        f"- Visual sample FPS: `{sample_fps}`",
        f"- Requested exact MP4 path: `{preferred_video['requested_path']}`",
        f"- Requested exact MP4 path matched directly: `{requested_matched_directly}`",
        f"- Resolved local MP4 fallback used: `{fallback_video}`",
        "",
        "## Exact Commands",
        "",
        f"- `{' '.join(command_parts)}`",
        "",
        "## Pairwise Sidecar Comparison",
        "",
    ]
    if sidecar_statuses and all(status == "skipped_resume" for status in sidecar_statuses):
        lines.insert(
            10,
            "- Sidecar execution mode: reused existing curated intermediate outputs for all requested models (`skipped_resume`).",
        )
    elif sidecar_statuses:
        lines.insert(
            10,
            f"- Sidecar execution statuses: `{', '.join(sidecar_statuses)}`",
        )
    if visual_support_mode:
        visual_mode_line = f"- Visual review mode: `{visual_support_mode}`"
        if visual_support_note:
            visual_mode_line += f" ({visual_support_note})"
        lines.append(visual_mode_line)
    if pairwise_summary:
        for row in pairwise_summary[:3]:
            lines.append(
                f"- `{row.get('left_model')}` vs `{row.get('right_model')}`: "
                f"same broad label rate `{row.get('same_broad_label_rate')}` across "
                f"`{row.get('moments_compared')}` curated moments."
            )
    else:
        lines.append("- No pairwise sidecar summary was available.")
    lines.extend(
        [
            "",
            "## What Was Skipped",
            "",
            f"- Visual skipped: `{visual_payload.get('status') == 'skipped'}`",
        ]
    )
    if visual_payload.get("status") == "skipped":
        lines.append(f"- Visual skip reason: {visual_payload.get('reason')}")
    uploaded_fallbacks = audit.get("requested_external_fallback_sources", {})
    if uploaded_fallbacks:
        transcript_exists = uploaded_fallbacks.get("uploaded_transcript_pdf", {}).get("exists")
        shareholder_exists = uploaded_fallbacks.get("uploaded_shareholder_letter_pdf", {}).get("exists")
        lines.append(f"- Uploaded transcript fallback present: `{transcript_exists}`")
        lines.append(f"- Uploaded shareholder-letter fallback present: `{shareholder_exists}`")
    lines.extend(
        [
            "",
            "## Outputs To Inspect First",
            "",
            f"- `{bundle_paths.panel_json}`",
            f"- `{bundle_paths.panel_md}`",
            f"- `{bundle_paths.model_comparison}`",
            f"- `{bundle_paths.disagreement_hotspots}`",
            "",
            "## Known Limitations",
            "",
            "- Audio remains limited to the curated Q&A windows already aligned in the repo.",
        ]
    )
    if preferred_video["resolved_from_fallback"]:
        lines.append("- The exact requested local MP4 path did not match; this bundle used a fallback local Netflix MP4 for the bounded visual pass.")
    if any(not item.get("exists") for item in uploaded_fallbacks.values()):
        lines.append("- The provided `/mnt/data` fallback PDFs were not present in this environment, so the repo-local transcript and shareholder-letter sources were used.")
    lines.append("- Visual coverage is bounded to those timed Q&A windows and should be suppressed if the quality gate is weak.")
    if visual_support_mode == "heuristic_fallback":
        lines.append("- Visual support is currently heuristic fallback only and does not include model-backed visual scoring.")
    lines.extend(
        [
            "- Sidecars are supporting-only and do not replace the deterministic Netflix demo artifacts.",
            "",
            "## Recommended Next Step",
            "",
            "- Review the top-8 showcase moments first, then scan the disagreement hotspots before considering any UI surfacing.",
        ]
    )
    return "\n".join(lines) + "\n"


def bundle_paths(root: Path | None = None) -> BundlePaths:
    multi_dir = multimodal_dir(root)
    docs_dir = _repo_root(root) / "docs"
    return BundlePaths(
        asset_audit_doc=docs_dir / "netflix_multimodal_asset_audit.md",
        moment_manifest=multi_dir / "netflix_multimodal_moment_manifest.json",
        model_comparison=multi_dir / "netflix_model_comparison.json",
        disagreement_hotspots=multi_dir / "netflix_disagreement_hotspots.json",
        audio_support=multi_dir / "netflix_audio_support.json",
        visual_support=multi_dir / "netflix_visual_support.json",
        visual_support_skipped=multi_dir / "netflix_visual_support_skipped.json",
        clip_manifest=multi_dir / "netflix_clip_manifest.json",
        caveats=multi_dir / "netflix_supporting_only_caveats.json",
        pressure_panel=multi_dir / "netflix_pressure_moments_panel.json",
        disagreement_panel=multi_dir / "netflix_disagreement_hotspots_panel.json",
        panel_json=multi_dir / "netflix_multimodal_panel.json",
        panel_md=multi_dir / "netflix_multimodal_panel.md",
        evidence_panel_doc=docs_dir / "netflix_multimodal_evidence_panel.md",
        panel_summary_doc=docs_dir / "netflix_multimodal_panel_summary.md",
    )


def write_review_bundle(
    *,
    root: Path | None = None,
    video_path: str | Path | None = None,
    models: list[str] | None = None,
    device: str = "auto",
    sample_fps: float = 0.25,
) -> dict[str, Any]:
    audit = build_asset_audit(root, video_path=video_path)
    manifest = build_curated_moment_manifest(root)
    sidecar_runtime = run_sidecars_for_manifest(manifest, root=root, models=models, device=device)
    comparison_payload, disagreement_payload = build_model_comparison(manifest, root=root)
    audio_payload = build_audio_support(manifest, root=root)
    visual_payload, visual_skipped = build_visual_support(
        manifest,
        root=root,
        video_path=video_path,
        sample_fps=sample_fps,
    )
    panel_payload, pressure_panel, disagreement_panel = build_panel_payload(
        manifest,
        comparison_payload,
        disagreement_payload,
        audio_payload,
        visual_payload,
    )

    paths = bundle_paths(root)
    paths.moment_manifest.parent.mkdir(parents=True, exist_ok=True)
    _write_json(paths.moment_manifest, manifest)
    _write_json(paths.model_comparison, comparison_payload)
    _write_json(paths.disagreement_hotspots, disagreement_payload)
    _write_json(paths.audio_support, audio_payload)
    _write_json(paths.caveats, SUPPORTING_CAVEATS)
    _write_json(
        paths.clip_manifest,
        {
            "case_id": CASE_ID,
            "source_video_path": audit["preferred_video_check"]["resolved_video_path"],
            "clips": [
                {
                    "moment_id": moment["moment_id"],
                    "start_time_s": moment.get("start_time_s"),
                    "end_time_s": moment.get("end_time_s"),
                    "timestamp_range": moment.get("timestamp_range"),
                    "clip_ready": bool(moment.get("start_time_s") is not None and audit["preferred_video_check"]["resolved_video_path"]),
                }
                for moment in manifest["moments"]
            ],
        },
    )
    _write_json(paths.pressure_panel, pressure_panel)
    _write_json(paths.disagreement_panel, disagreement_panel)
    _write_json(paths.panel_json, panel_payload)
    paths.panel_md.write_text(
        _render_panel_markdown(panel_payload, pressure_panel, disagreement_panel),
        encoding="utf-8",
    )

    if visual_skipped:
        if paths.visual_support.exists():
            paths.visual_support.unlink()
        _write_json(paths.visual_support_skipped, visual_payload)
    else:
        if paths.visual_support_skipped.exists():
            paths.visual_support_skipped.unlink()
        _write_json(paths.visual_support, visual_payload)

    paths.asset_audit_doc.write_text(_render_asset_audit_markdown(audit), encoding="utf-8")
    paths.evidence_panel_doc.write_text(paths.panel_md.read_text(encoding="utf-8"), encoding="utf-8")
    resolved_models = list(models or ["finbert_tone", "financial_roberta", "deberta_zero_shot", "mpnet_embeddings"])
    paths.panel_summary_doc.write_text(
        _render_summary_markdown(
            audit=audit,
            sidecar_runtime=sidecar_runtime,
            visual_payload=visual_payload,
            bundle_paths=paths,
            models=resolved_models,
            sample_fps=sample_fps,
            device=device,
            video_path=video_path,
            pairwise_summary=comparison_payload.get("pairwise_summary", []),
        ),
        encoding="utf-8",
    )

    return {
        "audit": audit,
        "manifest": manifest,
        "sidecar_runtime": sidecar_runtime,
        "comparison": comparison_payload,
        "disagreement": disagreement_payload,
        "audio": audio_payload,
        "visual": visual_payload,
        "panel": panel_payload,
        "bundle_paths": {field: str(getattr(paths, field)) for field in paths.__dataclass_fields__},
    }
