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
from earnings_call_sentiment.reference_case_standard import default_supporting_only_caveats
from earnings_call_sentiment.visual.summary import write_visual_behavior_outputs


CASE_ID = "meta_q3_2022"
CASE_SCOPE = "Meta Q3 2022"
CASE_DIR = Path("data/demo_cases") / CASE_ID
MULTIMODAL_DIR = CASE_DIR / "demo" / "multimodal"
CURATED_OUTPUT_DIR = Path("outputs") / CASE_ID / "model_sidecars_curated"
REQUESTED_VIDEO_PATH = Path(
    "/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Meta/Facebook (META) Q3 2022 Earnings Call.mp4"
)
FALLBACK_VIDEO_PATH = CASE_DIR / "raw" / "video" / "meta_q3_2022_video.mp4"

EXPECTED_POLARITY_BY_CATEGORY = {
    "macro_ads_pressure": "negative",
    "efficiency_restraint": "negative",
    "monetization_headwind": "negative",
    "profitability_pressure": "negative",
    "capex_pressure": "negative",
    "reality_labs_losses": "negative",
    "analyst_pressure": "negative",
    "recovery_caution": "negative",
    "revenue_outlook": "negative",
    "expense_outlook": "negative",
    "qa_capex_pressure": "negative",
    "qa_reels_pressure": "negative",
}

MAIN_TRANSCRIPT_TIMINGS = {
    "transcript_macro_ads_pressure": (77.308, 127.693),
    "transcript_conservative_budget": (127.693, 245.386),
    "transcript_reels_headwind": (409.617, 463.848),
}

SOURCE_ARTIFACT_BY_TYPE = {
    "transcript": "processed/transcript_text/transcript_cleaned.txt",
    "results_release": "processed/signals/results_release_text.txt",
    "presentation": "processed/signals/presentation_text.txt",
    "follow_up_transcript": "processed/follow_up_text/transcript.txt",
}

MOMENT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "moment_id": "transcript_macro_ads_pressure",
        "rank": 1,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "transcript_macro_ads_pressure"},
        "deterministic_signal_category": "macro_ads_pressure",
        "plain_english_label": "management flagged macro and ads pressure",
        "why_selected": "Most direct transcript-first statement of macro weakness, ads signal loss, competition, and long-term investment pressure.",
    },
    {
        "moment_id": "transcript_conservative_budget",
        "rank": 2,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "transcript_conservative_budget"},
        "deterministic_signal_category": "efficiency_restraint",
        "plain_english_label": "management turned more cautious on 2023 spending",
        "why_selected": "Best transcript bridge from macro caution into flatter headcount and tighter 2023 budgeting.",
    },
    {
        "moment_id": "transcript_reels_headwind",
        "rank": 3,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "transcript_reels_headwind"},
        "deterministic_signal_category": "monetization_headwind",
        "plain_english_label": "Reels monetization remained a clear headwind",
        "why_selected": "Cleanest prepared-remarks statement tying product momentum to an explicit revenue headwind and delayed neutrality.",
    },
    {
        "moment_id": "release_profitability_deterioration",
        "rank": 4,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "release_profitability_deterioration"},
        "deterministic_signal_category": "profitability_pressure",
        "plain_english_label": "profitability deteriorated sharply",
        "why_selected": "Official disclosed anchor for why the quarter felt defensive before any reviewer interpretation of tone.",
    },
    {
        "moment_id": "release_expense_capex_guidance",
        "rank": 5,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "release_expense_capex_guidance"},
        "deterministic_signal_category": "capex_pressure",
        "plain_english_label": "efficiency language still came with heavy spending",
        "why_selected": "Strongest official disclosure row for the tension between cost discipline language and continued capex intensity.",
    },
    {
        "moment_id": "presentation_reality_labs_drag",
        "rank": 6,
        "top_8_showcase": True,
        "unit_type": "chunks",
        "source_kind": "evidence_row",
        "selector": {"row_id": "presentation_reality_labs_drag"},
        "deterministic_signal_category": "reality_labs_losses",
        "plain_english_label": "Reality Labs remained a major drag on profits",
        "why_selected": "Makes the Reality Labs loss burden concrete without forcing a broader thesis about whether the strategy is right.",
    },
    {
        "moment_id": "follow_up_reels_headwind_pressure",
        "rank": 7,
        "top_8_showcase": True,
        "unit_type": "qa_answers",
        "source_kind": "follow_up_evidence_qa",
        "selector": {"row_id": "follow_up_reels_headwind_pressure"},
        "deterministic_signal_category": "analyst_pressure",
        "plain_english_label": "analyst kept pressure on the weak spots",
        "why_selected": "Adds secondary same-day pressure-testing on the Reels headwind and how long management expects the drag to persist.",
    },
    {
        "moment_id": "follow_up_macro_caution",
        "rank": 8,
        "top_8_showcase": True,
        "unit_type": "qa_answers",
        "source_kind": "follow_up_evidence_qa",
        "selector": {"row_id": "follow_up_macro_caution"},
        "deterministic_signal_category": "recovery_caution",
        "plain_english_label": "management stayed cautious on the recovery story",
        "why_selected": "Best bounded follow-up answer where management refuses to sound fully confident on recovery timing.",
    },
    {
        "moment_id": "guidance_q4_revenue_outlook",
        "rank": 9,
        "top_8_showcase": False,
        "unit_type": "guidance_spans",
        "source_kind": "guidance",
        "selector": {"text_contains": "fourth quarter 2022 total revenue to be in the range of $30-32.5 billion"},
        "deterministic_signal_category": "revenue_outlook",
        "plain_english_label": "Q4 revenue outlook stayed under pressure",
        "why_selected": "Direct timed outlook span for reviewers who want the spoken revenue guide rather than the release excerpt only.",
    },
    {
        "moment_id": "guidance_2023_expense_range",
        "rank": 10,
        "top_8_showcase": False,
        "unit_type": "guidance_spans",
        "source_kind": "guidance",
        "selector": {"text_contains": "full-year 2023 total expenses will be in the range of $96-101 billion"},
        "deterministic_signal_category": "expense_outlook",
        "plain_english_label": "2023 expenses remained elevated",
        "why_selected": "Most direct spoken expense range span for the still-heavy 2023 spending plan.",
    },
    {
        "moment_id": "qa_capex_ai_pressure",
        "rank": 11,
        "top_8_showcase": False,
        "unit_type": "qa_answers",
        "source_kind": "audio_review",
        "selector": {"row_id": "qa_capex_ai_pressure_audio"},
        "deterministic_signal_category": "qa_capex_pressure",
        "plain_english_label": "AI capex and ROI pushback",
        "why_selected": "Direct analyst pushback on capex and AI ROI, with a bounded answer-level audio window already aligned in the repo.",
        "deterministic_signal_summary": "Management defended elevated AI capex with ROI language, but kept the near-term spend burden explicit.",
    },
    {
        "moment_id": "qa_reels_transition_pressure",
        "rank": 12,
        "top_8_showcase": False,
        "unit_type": "qa_answers",
        "source_kind": "audio_review",
        "selector": {"row_id": "qa_reels_headwind_audio"},
        "deterministic_signal_category": "qa_reels_pressure",
        "plain_english_label": "Reels transition pressure under direct questioning",
        "why_selected": "Highest-value main-call pressure answer on the Reels drag, with both bounded audio and local video available.",
        "deterministic_signal_summary": "Management kept the eventual-tailwind story but still described Reels as a meaningful near-term headwind.",
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


def resolve_video_source(video_path: str | Path | None = None, *, root: Path | None = None) -> dict[str, Any]:
    requested = Path(video_path).expanduser().resolve() if video_path else REQUESTED_VIDEO_PATH
    fallback = _repo_root(root) / FALLBACK_VIDEO_PATH
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


def build_asset_audit(root: Path | None = None, *, video_path: str | Path | None = None) -> dict[str, Any]:
    case_dir = case_root(root)
    video_source = resolve_video_source(video_path, root=root)
    transcript_pdf = case_dir / "raw" / "transcript" / "meta_q3_2022_earnings_call_transcript.pdf"
    follow_up_pdf = case_dir / "raw" / "follow_up_transcript" / "meta_q3_2022_follow_up_call_transcript.pdf"
    release_pdf = case_dir / "raw" / "results_release" / "meta_q3_2022_results_release.pdf"
    deck_pdf = case_dir / "raw" / "presentation" / "meta_q3_2022_earnings_presentation.pdf"
    video_verification = _read_json(case_dir / "raw" / "video" / "video_verification.json")
    audio_status = _read_json(case_dir / "processed" / "audio_behavior" / "audio_status.json")
    audio_summary = _read_json(case_dir / "processed" / "audio_behavior" / "audio_behavior_summary.json")

    video_usable = bool(video_source["resolved_video_path"])
    if video_usable and video_source["resolved_from_fallback"]:
        video_usability_reason = (
            "The exact requested Meta MP4 path did not match, but a local fallback video was found and was available for a bounded supporting-only visual pass."
        )
    elif video_usable:
        video_usability_reason = "The exact requested Meta MP4 path matched directly and was available for a bounded supporting-only visual pass."
    else:
        video_usability_reason = "No usable local Meta MP4 was found, so visual behavior should be skipped honestly."

    return {
        "case_id": CASE_ID,
        "case_scope": CASE_SCOPE,
        "review_generated_at": datetime.now(UTC).isoformat(),
        "preferred_video_check": video_source,
        "repo_case_sources": {
            "transcript_pdf": {"path": str(transcript_pdf), "exists": transcript_pdf.exists()},
            "follow_up_transcript_pdf": {"path": str(follow_up_pdf), "exists": follow_up_pdf.exists()},
            "results_release_pdf": {"path": str(release_pdf), "exists": release_pdf.exists()},
            "earnings_presentation_pdf": {"path": str(deck_pdf), "exists": deck_pdf.exists()},
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
        "missing_or_untracked_items": [
            "The requested local MP4 lives outside the repo and is not persisted under the case package.",
            "Only two main-call Q&A windows currently have curated audio timing attached in the repo.",
            "Follow-up, presentation, and release moments do not carry transcript-aligned main-call video timestamps.",
        ],
        "video_usable_for_bounded_visual_analysis": video_usable,
        "video_usability_reason": video_usability_reason,
    }


def _load_evidence_rows(root: Path | None = None) -> dict[str, dict[str, Any]]:
    payload = _read_json(case_root(root) / "demo" / "evidence_rows" / "meta_q3_2022_evidence_rows.json")
    return {
        str(row["row_id"]): row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("row_id")
    }


def _load_guidance(root: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(case_root(root) / "processed" / "signals" / "guidance.csv", keep_default_na=False)


def _load_audio_rows(root: Path | None = None) -> dict[str, dict[str, Any]]:
    payload = _read_json(case_root(root) / "processed" / "audio_behavior" / "audio_review_rows.json")
    return {
        str(row["row_id"]): row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("row_id")
    }


def _load_qa_pairs(root: Path | None = None) -> list[dict[str, Any]]:
    payload = _read_json(case_root(root) / "processed" / "qa_pairs" / "qa_pairs.json")
    rows = payload.get("qa_pairs", payload if isinstance(payload, list) else [])
    return [row for row in rows if isinstance(row, dict)]


def _load_follow_up_qa_pairs(root: Path | None = None) -> list[dict[str, Any]]:
    payload = _read_json(case_root(root) / "processed" / "qa_pairs" / "follow_up_qa_pairs.json")
    rows = payload.get("qa_pairs", payload if isinstance(payload, list) else [])
    return [row for row in rows if isinstance(row, dict)]


def _select_guidance(frame: pd.DataFrame, *, text_contains: str) -> dict[str, Any]:
    match = frame[frame["text"].astype(str).str.contains(text_contains, case=False, regex=False, na=False)]
    if match.empty:
        raise RuntimeError(f"Unable to locate Meta guidance span containing '{text_contains}'.")
    return dict(match.iloc[0].to_dict())


def _find_qa_pair(qa_pairs: list[dict[str, Any]], *, answer_excerpt: str) -> dict[str, Any]:
    needle = " ".join(str(answer_excerpt).split()[:12]).strip()
    for row in qa_pairs:
        answer_text = str(row.get("answer_text", ""))
        if needle and needle in answer_text:
            return row
    raise RuntimeError(f"Unable to locate Meta QA pair for excerpt '{needle}'.")


def _source_artifact_for_row(row: dict[str, Any]) -> str:
    source_type = str(row.get("source_type", "")).strip()
    return SOURCE_ARTIFACT_BY_TYPE.get(source_type, "processed/transcript_text/transcript_cleaned.txt")


def _moment_timestamp_range(start_time_s: float | None, end_time_s: float | None) -> str | None:
    start_label = _timestamp_label(start_time_s)
    end_label = _timestamp_label(end_time_s)
    if start_label and end_label:
        return f"{start_label}-{end_label}"
    return None


def _evidence_row_timing(row_id: str) -> tuple[float | None, float | None]:
    return MAIN_TRANSCRIPT_TIMINGS.get(row_id, (None, None))


def build_curated_moment_manifest(root: Path | None = None) -> dict[str, Any]:
    evidence_rows = _load_evidence_rows(root)
    guidance = _load_guidance(root)
    audio_rows = _load_audio_rows(root)
    qa_pairs = _load_qa_pairs(root)
    follow_up_qa_pairs = _load_follow_up_qa_pairs(root)

    moments: list[dict[str, Any]] = []
    for spec in MOMENT_SPECS:
        source_kind = str(spec["source_kind"])
        selector = dict(spec["selector"])
        if source_kind == "evidence_row":
            row = evidence_rows[str(selector["row_id"])]
            start_s, end_s = _evidence_row_timing(str(row["row_id"]))
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_doc": str(row.get("source_type", "")),
                "source_deterministic_artifact": _source_artifact_for_row(row),
                "source_locator": str(row.get("row_id", "")),
                "text": str(row["source_excerpt"]),
                "quote_or_span": str(row["source_excerpt"]),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label") or row["plain_english_label"]),
                "deterministic_signal_summary": str(row["extracted_signal"]),
                "why_selected": spec["why_selected"],
                "source_row_id": str(row["row_id"]),
                "source_section_or_speaker": str(row.get("source_section_or_speaker", "")),
                "start_time_s": start_s,
                "end_time_s": end_s,
                "timestamp_range": _moment_timestamp_range(start_s, end_s),
                "audio_row_id": None,
            }
        elif source_kind == "follow_up_evidence_qa":
            row = evidence_rows[str(selector["row_id"])]
            qa_pair = _find_qa_pair(follow_up_qa_pairs, answer_excerpt=str(row["source_excerpt"]))
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_doc": "follow_up_transcript",
                "source_deterministic_artifact": "processed/qa_pairs/follow_up_qa_pairs.json",
                "source_locator": f"qa_pair_id:{qa_pair.get('qa_pair_id')}",
                "text": str(qa_pair.get("answer_text", row["source_excerpt"])),
                "quote_or_span": str(row["source_excerpt"]),
                "question_text": str(qa_pair.get("question_text", "")),
                "question_speaker": str(qa_pair.get("question_speaker", "")),
                "answer_speakers": qa_pair.get("answer_speakers", []),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label") or row["plain_english_label"]),
                "deterministic_signal_summary": str(row["extracted_signal"]),
                "why_selected": spec["why_selected"],
                "source_row_id": str(row["row_id"]),
                "source_section_or_speaker": str(row.get("source_section_or_speaker", "")),
                "start_time_s": None,
                "end_time_s": None,
                "timestamp_range": None,
                "audio_row_id": None,
            }
        elif source_kind == "guidance":
            row = _select_guidance(guidance, text_contains=str(selector["text_contains"]))
            start_s = float(row["start"])
            end_s = float(row["end"])
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_doc": "transcript",
                "source_deterministic_artifact": "processed/signals/guidance.csv",
                "source_locator": f"start:{row['start']}-end:{row['end']}",
                "text": str(row["text"]),
                "quote_or_span": str(row["text"]),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label") or spec["moment_id"].replace("_", " ")),
                "deterministic_signal_summary": str(row["text"]),
                "why_selected": spec["why_selected"],
                "source_row_id": spec["moment_id"],
                "source_section_or_speaker": "main transcript / guidance span",
                "start_time_s": start_s,
                "end_time_s": end_s,
                "timestamp_range": _moment_timestamp_range(start_s, end_s),
                "audio_row_id": None,
                "source_sentiment": str(row.get("sentiment", "")),
                "source_score": float(row.get("score")) if str(row.get("score", "")).strip() else None,
                "guidance_strength": float(row.get("guidance_strength")) if str(row.get("guidance_strength", "")).strip() else None,
                "topic": str(row.get("topic", "")),
                "period": str(row.get("period", "")),
                "matched_cues": str(row.get("matched_cues", "")),
            }
        elif source_kind == "audio_review":
            row = audio_rows[str(selector["row_id"])]
            qa_pair = next(
                qa_row for qa_row in qa_pairs if int(qa_row.get("qa_pair_id", -1)) == int(row.get("qa_pair_id", -2))
            )
            start_s = float(row["answer_start_s"])
            end_s = float(row["answer_end_s"])
            moment = {
                "moment_id": spec["moment_id"],
                "rank": spec["rank"],
                "top_8_showcase": spec["top_8_showcase"],
                "unit_type": spec["unit_type"],
                "source_doc": "main_transcript_q_and_a",
                "source_deterministic_artifact": "processed/qa_pairs/qa_pairs.json",
                "source_locator": f"qa_pair_id:{qa_pair.get('qa_pair_id')}",
                "text": str(qa_pair.get("answer_text", "")),
                "quote_or_span": str(row.get("management_answer_excerpt", qa_pair.get("answer_text", ""))),
                "question_text": str(qa_pair.get("question_text", "")),
                "question_speaker": str(qa_pair.get("question_speaker", "")),
                "answer_speakers": qa_pair.get("answer_speakers", []),
                "deterministic_signal_category": spec["deterministic_signal_category"],
                "plain_english_label": str(spec.get("plain_english_label") or row.get("plain_english_label", "")),
                "deterministic_signal_summary": str(spec.get("deterministic_signal_summary") or row.get("plain_english_label", "")),
                "why_selected": spec["why_selected"],
                "source_row_id": str(row["row_id"]),
                "source_section_or_speaker": f"{qa_pair.get('question_speaker', '')} / main call Q&A",
                "start_time_s": start_s,
                "end_time_s": end_s,
                "timestamp_range": _moment_timestamp_range(start_s, end_s),
                "audio_row_id": str(row["row_id"]),
            }
        else:  # pragma: no cover - guarded by static specs
            raise RuntimeError(f"Unsupported Meta moment source kind: {source_kind}")

        moment["expected_direction_from_deterministic"] = EXPECTED_POLARITY_BY_CATEGORY.get(moment["deterministic_signal_category"])
        moment["main_call_media_eligible"] = bool(moment.get("start_time_s") is not None)
        moments.append(moment)

    ordered = sorted(moments, key=lambda item: int(item["rank"]))
    return {
        "case_id": CASE_ID,
        "case_scope": CASE_SCOPE,
        "primary_moment_count": len(ordered),
        "showcase_moment_count": sum(1 for moment in ordered if moment["top_8_showcase"]),
        "moments": ordered,
        "notes": [
            "These moments are transcript-first selections built from committed Meta Q3 2022 deterministic artifacts.",
            "Audio, NLP, and visual layers remain supporting-only reviewer context.",
            "Secondary follow-up call moments are included as clearly labeled pressure-testing context only.",
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
                    "sentiment": str(moment.get("expected_direction_from_deterministic", "")),
                    "score": moment.get("source_score", ""),
                    "signed_score": moment.get("source_score", ""),
                    "positive_prob": "",
                    "negative_prob": "",
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


def _label_counts(labels: list[str]) -> dict[str, int]:
    return {str(label): int(count) for label, count in pd.Series(labels).value_counts().to_dict().items()} if labels else {}


def _sidecar_label_summary(labels: list[str]) -> dict[str, Any]:
    label_counts = _label_counts(labels)
    if not label_counts:
        return {
            "sidecar_label_counts": {},
            "leading_sidecar_label": None,
            "leading_sidecar_label_is_tied": False,
            "tied_leading_sidecar_labels": [],
        }
    highest_count = max(label_counts.values())
    leaders = sorted(label for label, count in label_counts.items() if count == highest_count)
    return {
        "sidecar_label_counts": label_counts,
        "leading_sidecar_label": leaders[0] if len(leaders) == 1 else None,
        "leading_sidecar_label_is_tied": len(leaders) > 1,
        "tied_leading_sidecar_labels": leaders if len(leaders) > 1 else [],
    }


def _expected_direction_check(expected_direction: str, comparable_labels: list[str]) -> str:
    if expected_direction and comparable_labels:
        if all(label == expected_direction for label in comparable_labels):
            return "all_comparable_labels_match_expected_direction"
        if any(label == expected_direction for label in comparable_labels):
            return "some_comparable_labels_match_expected_direction"
        return "no_comparable_labels_match_expected_direction"
    if comparable_labels:
        return "non_polar_context_only"
    return "no_expected_direction"


def _support_signal_metadata(*, expected_direction: str, comparable_labels: list[str]) -> dict[str, Any]:
    label_counts = _label_counts(comparable_labels)
    label_set = set(label_counts)
    positive_present = "positive" in label_set
    negative_present = "negative" in label_set
    neutral_present = "neutral" in label_set

    if not comparable_labels:
        return {
            "review_bucket": "no_comparable_signal",
            "review_priority": "low",
            "review_priority_reason": "No comparable sidecar polarity was available for this moment.",
        }
    if not expected_direction:
        return {
            "review_bucket": "non_polar_context_only",
            "review_priority": "low",
            "review_priority_reason": "This deterministic category is non-polar, so sidecar spread is descriptive context only.",
        }
    if len(label_set) == 1 and expected_direction in label_set:
        return {
            "review_bucket": "consistent_directional_read",
            "review_priority": "low",
            "review_priority_reason": "Comparable sidecar labels point in the same direction as the expected deterministic read.",
        }
    if positive_present and negative_present:
        return {
            "review_bucket": "directional_conflict",
            "review_priority": "high",
            "review_priority_reason": "Comparable sidecar labels split across positive and negative directions on a moment with an expected deterministic polarity.",
        }
    if expected_direction in label_set and neutral_present:
        return {
            "review_bucket": "softened_directional_read",
            "review_priority": "medium",
            "review_priority_reason": "Comparable sidecar labels keep the expected direction in view, but at least one model softens it toward neutral.",
        }
    return {
        "review_bucket": "directional_conflict",
        "review_priority": "high",
        "review_priority_reason": "Comparable sidecar labels do not preserve the expected deterministic direction and should be treated as a review hotspot.",
    }


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

        label_summary = _sidecar_label_summary(comparable_labels)
        expected_direction = str(moment.get("expected_direction_from_deterministic") or "")
        direction_check = _expected_direction_check(expected_direction, comparable_labels)
        support_signal = _support_signal_metadata(
            expected_direction=expected_direction,
            comparable_labels=comparable_labels,
        )
        panel_row = {
            "moment_id": moment["moment_id"],
            "rank": moment["rank"],
            "top_8_showcase": moment["top_8_showcase"],
            "unit_type": moment["unit_type"],
            "deterministic_signal_category": moment["deterministic_signal_category"],
            "expected_direction_from_deterministic": expected_direction or None,
            "leading_sidecar_label": label_summary["leading_sidecar_label"],
            "leading_sidecar_label_is_tied": label_summary["leading_sidecar_label_is_tied"],
            "tied_leading_sidecar_labels": label_summary["tied_leading_sidecar_labels"],
            "sidecar_label_counts": label_summary["sidecar_label_counts"],
            "model_outputs": per_model,
            "pairwise_disagreement": len(set(comparable_labels)) > 1 if comparable_labels else False,
            "expected_direction_check": direction_check,
            "review_bucket": support_signal["review_bucket"],
            "review_priority": support_signal["review_priority"],
            "review_priority_reason": support_signal["review_priority_reason"],
            "quote_or_span": _truncate(str(moment["quote_or_span"])),
        }
        panel_rows.append(panel_row)
        if panel_row["pairwise_disagreement"] or direction_check == "no_comparable_labels_match_expected_direction":
            disagreements.append(
                {
                    "moment_id": moment["moment_id"],
                    "rank": moment["rank"],
                    "deterministic_signal_category": moment["deterministic_signal_category"],
                    "expected_direction_from_deterministic": expected_direction or None,
                    "observed_labels": comparable_labels,
                    "sidecar_label_counts": label_summary["sidecar_label_counts"],
                    "leading_sidecar_label": label_summary["leading_sidecar_label"],
                    "leading_sidecar_label_is_tied": label_summary["leading_sidecar_label_is_tied"],
                    "tied_leading_sidecar_labels": label_summary["tied_leading_sidecar_labels"],
                    "expected_direction_check": direction_check,
                    "review_bucket": support_signal["review_bucket"],
                    "review_priority": support_signal["review_priority"],
                    "review_priority_reason": support_signal["review_priority_reason"],
                    "distinct_label_count": len(set(comparable_labels)),
                    "quote_or_span": _truncate(str(moment["quote_or_span"])),
                }
            )

    similarity_hotspots: list[dict[str, Any]] = []
    for model_name, output in sidecar_outputs.items():
        disagreement_report = output["disagreement_report"]
        if disagreement_report.get("similarity_hotspots"):
            for item in disagreement_report["similarity_hotspots"]:
                similarity_hotspots.append({"model_name": model_name, **item})
    priority_order = {"high": 0, "medium": 1, "low": 2}
    disagreements = sorted(
        disagreements,
        key=lambda item: (
            priority_order.get(str(item.get("review_priority")), 9),
            -int(item.get("distinct_label_count", 0)),
            int(item["rank"]),
        ),
    )

    comparison_payload = {
        "case_id": CASE_ID,
        "case_scope": CASE_SCOPE,
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
        "pairwise_summary": evaluation_summary.get("pairwise_classification", []),
        "moment_rows": panel_rows,
        "notes": [
            "Deterministic transcript-backed outputs remain canonical; these comparisons are supporting-only review aids.",
            "Expected direction from the deterministic layer is only used as bounded same-direction context, not proof.",
            "Tied leading labels stay explicit so mixed rows do not pretend to have sidecar consensus.",
            "Secondary follow-up-call rows remain useful review context, but they do not override the canonical main-call transcript.",
        ],
    }
    disagreement_payload = {
        "case_id": CASE_ID,
        "case_scope": CASE_SCOPE,
        "status": "ok" if sidecar_outputs else "no_sidecar_outputs",
        "pairwise_model_disagreements": disagreements,
        "embedding_similarity_hotspots": similarity_hotspots[:8],
        "noisy_or_unhelpful_sidecars": [
            item
            for item in disagreements
            if item["review_bucket"] in {"softened_directional_read", "directional_conflict"}
        ],
        "notes": [
            "Disagreement hotspots are review priorities, not proof that any sidecar is more correct than the deterministic read.",
            "Embedding hotspots flag semantic similarity for inspection only.",
            "Rows without comparable sidecar polarity stay explicit rather than being normalized away.",
        ],
    }
    return comparison_payload, disagreement_payload


def _audio_interpretation(row: dict[str, Any]) -> str:
    cues: list[str] = []
    pause_ms = float(row.get("pause_before_answer_ms") or 0.0)
    filler_density = float(row.get("filler_density") or 0.0)
    summary_text = str(row.get("plain_english_audio_summary", "")).lower()

    if pause_ms >= 750:
        cues.append("a noticeable pre-answer pause")
    elif pause_ms >= 150:
        cues.append("a shorter pre-answer pause")
    if filler_density >= 0.5:
        cues.append("heavier filler or qualification language")
    elif filler_density >= 0.15:
        cues.append("some filler or qualification language")
    elif "qualification" in summary_text or "hedging" in summary_text:
        cues.append("qualifying opening language")
    if not cues:
        cues.append("no strong pause or filler escalation")
    return (
        f"Measured cues show {', '.join(cues)}. Use this as measured pacing/context only; "
        "it does not change the transcript-first deterministic read."
    )


def build_audio_support(
    manifest: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    audio_rows = _load_audio_rows(root)
    audio_summary = _read_json(case_root(root) / "processed" / "audio_behavior" / "audio_behavior_summary.json")
    moments: list[dict[str, Any]] = []
    for moment in manifest["moments"]:
        audio_row_id = str(moment.get("audio_row_id") or "")
        if audio_row_id and audio_row_id in audio_rows:
            row = audio_rows[audio_row_id]
            moments.append(
                {
                    "moment_id": moment["moment_id"],
                    "status": "aligned",
                    "question_time_range": row.get("question_time_range"),
                    "answer_time_range": row.get("answer_time_range"),
                    "pause_before_answer_ms": row.get("pause_before_answer_ms"),
                    "answer_start_delay_seconds": row.get("answer_start_delay_seconds"),
                    "filler_density": row.get("filler_density"),
                    "hesitation_label": row.get("hesitation_label"),
                    "qa_shift_label": row.get("qa_shift_label"),
                    "plain_english_audio_summary": row.get("plain_english_audio_summary"),
                    "plain_english_interpretation": _audio_interpretation(row),
                    "timing_note": (
                        "Audio timings are attached only to a few curated main-call Q&A moments matched against an ASR transcript. "
                        "They are supporting review cues, not full transcript-to-media coverage."
                    ),
                }
            )
        else:
            moments.append(
                {
                    "moment_id": moment["moment_id"],
                    "status": "unavailable",
                    "reason": "No curated audio timing is attached to this deterministic moment.",
                }
            )
    return {
        "case_id": CASE_ID,
        "case_scope": CASE_SCOPE,
        "status": "ok",
        "audio_available": audio_summary.get("audio_available"),
        "audio_quality_ok": audio_summary.get("audio_quality_ok"),
        "summary": {
            "hesitation_overall": audio_summary.get("hesitation_overall"),
            "qa_hesitation_shift": audio_summary.get("qa_hesitation_shift"),
            "pause_pressure_delta": audio_summary.get("pause_pressure_delta"),
            "audio_signal_usability": audio_summary.get("audio_confidence_support"),
        },
        "moments": moments,
        "notes": [
            "Audio rows were reused from the committed curated Meta Q3 2022 Q&A audio artifacts.",
            "Audio support remains bounded to the two aligned main-call Q&A windows already present in the repo.",
            "Pause, filler, and qualification cues are observational only and should not be treated as intent or certainty inference.",
        ],
    }


def _normalize_visual_segment_fields(row: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(row))
    if "support_direction" in normalized:
        normalized["context_role"] = normalized.pop("support_direction")
    if "support_note" in normalized:
        normalized["context_note"] = normalized.pop("support_note")
    if "confidence_note" in normalized:
        normalized["quality_note"] = normalized.pop("confidence_note")
    return normalized


def _normalize_visual_summary(summary: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(summary))
    if "visual_support_direction" in normalized:
        normalized["visual_layer_role"] = normalized.pop("visual_support_direction")
    if "visual_confidence_support" in normalized:
        normalized["visual_signal_usability"] = normalized.pop("visual_confidence_support")
    if "strongest_visual_evidence" in normalized:
        normalized["most_reviewable_visual_segments"] = normalized.pop("strongest_visual_evidence")
    if "most_confident_visual_segments" in normalized:
        normalized["most_usable_visual_segments"] = normalized.pop("most_confident_visual_segments")
    if "notable_low_confidence_segments" in normalized:
        normalized["notable_low_usability_segments"] = normalized.pop("notable_low_confidence_segments")
    model_support = normalized.get("model_support")
    if isinstance(model_support, dict) and "support_direction" in model_support:
        model_support["context_role"] = model_support.pop("support_direction")
    for key in (
        "most_reviewable_visual_segments",
        "most_visually_changed_segments",
        "most_usable_visual_segments",
        "notable_low_usability_segments",
    ):
        normalized[key] = [
            _normalize_visual_segment_fields(item) if isinstance(item, dict) else item
            for item in normalized.get(key, [])
        ]
    return normalized


def _soften_heuristic_visual_summary(summary: dict[str, Any]) -> dict[str, Any]:
    softened = json.loads(json.dumps(summary))
    if softened.get("support_mode") != "heuristic_fallback" or softened.get("model_support", {}).get("available"):
        return _normalize_visual_summary(softened)

    softened["visual_support_direction"] = "context_only"
    softened.setdefault("limitations", []).append(
        "This run is heuristic fallback only, so visually steady delivery should be treated as bounded context and does not change the transcript-first read."
    )
    softened.setdefault("notes", []).append(
        "Heuristic fallback can describe visible steadiness or change, but it does not establish certainty or corroboration and does not change the transcript-first read."
    )
    for key in (
        "strongest_visual_evidence",
        "most_visually_changed_segments",
        "most_confident_visual_segments",
        "notable_low_confidence_segments",
    ):
        for item in softened.get(key, []):
            if isinstance(item, dict):
                item["support_direction"] = "context_only"
    return _normalize_visual_summary(softened)


def _visual_moment_row(row: dict[str, Any], *, support_mode: str | None) -> dict[str, Any]:
    quality_note = str(row["confidence_note"])
    if quality_note != "usable visual segment":
        return {
            "status": "suppressed",
            "start_time_s": float(row["start_time_s"]),
            "end_time_s": float(row["end_time_s"]),
            "reason": quality_note,
        }

    context_role = str(row["support_direction"])
    context_note = str(row["support_note"])
    if support_mode == "heuristic_fallback":
        context_role = "context_only"
        lowered = context_note.lower()
        if "steady" in lowered or "stable" in lowered:
            context_note = (
                "heuristic fallback only; visible delivery stayed broadly steady and did not add a strong visual reason to revisit the transcript-first read"
            )
        elif "tension" in lowered or "motion" in lowered:
            context_note = (
                "heuristic fallback only; visible motion changed in this window, but this remains observational context only and does not corroborate the transcript read"
            )
        else:
            context_note = (
                "heuristic fallback only; visible cues were mixed and remained observational context only"
            )
        quality_note = f"{quality_note}; heuristic fallback only"
    return {
        "status": "aligned",
        "start_time_s": float(row["start_time_s"]),
        "end_time_s": float(row["end_time_s"]),
        "visual_stability_label": str(row["visual_stability_label"]),
        "context_role": context_role,
        "context_note": context_note,
        "quality_note": quality_note,
        "face_visible_pct": float(row["face_visible_pct"]),
        "visual_change_score": float(row["visual_change_score"]),
        "head_motion_energy": float(row["head_motion_energy"]),
    }


def build_visual_support(
    manifest: dict[str, Any],
    *,
    root: Path | None = None,
    video_path: str | Path | None = None,
    sample_fps: float = 0.25,
) -> tuple[dict[str, Any], bool]:
    resolved_video = resolve_video_source(video_path, root=root)
    video_file = Path(resolved_video["resolved_video_path"]).expanduser().resolve() if resolved_video["resolved_video_path"] else None
    if video_file is None:
        return (
            {
                "case_id": CASE_ID,
                "case_scope": CASE_SCOPE,
                "status": "skipped",
                "reason": "No usable local Meta MP4 was available for the bounded visual pass.",
                "video_source_check": resolved_video,
            },
            True,
        )
    if sample_fps <= 0:
        return (
            {
                "case_id": CASE_ID,
                "case_scope": CASE_SCOPE,
                "status": "skipped",
                "reason": (
                    "A bounded visual pass was intentionally skipped after earlier full-video heuristic attempts exceeded "
                    "the reviewer-safe runtime cap in this session."
                ),
                "video_source_check": resolved_video,
            },
            True,
        )

    segments: list[dict[str, Any]] = []
    segment_to_moment: dict[int, str] = {}
    for index, moment in enumerate(
        [item for item in manifest["moments"] if item.get("main_call_media_eligible")],
        start=1,
    ):
        segment_to_moment[index] = moment["moment_id"]
        segments.append(
            {
                "segment_id": index,
                "start": float(moment["start_time_s"]),
                "end": float(moment["end_time_s"]),
                "phase": "q_and_a" if moment["unit_type"] == "qa_answers" else "prepared_remarks",
                "speaker_role": "management",
                "text": str(moment["text"]),
            }
        )
    qa_segments_df = pd.DataFrame(segments)
    if qa_segments_df.empty:
        return (
            {
                "case_id": CASE_ID,
                "case_scope": CASE_SCOPE,
                "status": "skipped",
                "reason": "No timestamped main-call moments were available for the bounded visual pass.",
                "video_source_check": resolved_video,
            },
            True,
        )

    try:
        visual_dir = curated_output_dir(root) / "visual_support"
        outputs = write_visual_behavior_outputs(video_file, qa_segments_df, visual_dir, sample_fps=sample_fps)
    except Exception as exc:
        return (
            {
                "case_id": CASE_ID,
                "case_scope": CASE_SCOPE,
                "status": "skipped",
                "reason": f"Visual analysis could not run cleanly in this environment: {exc}",
                "video_source_check": resolved_video,
            },
            True,
        )

    summary = _soften_heuristic_visual_summary(outputs["summary"])
    support_mode = str(summary.get("support_mode") or "")
    moment_rows: list[dict[str, Any]] = []
    for row in outputs["segments_df"].to_dict(orient="records"):
        moment_id = segment_to_moment.get(int(row["segment_id"]))
        if not moment_id:
            continue
        moment_rows.append({"moment_id": moment_id, **_visual_moment_row(row, support_mode=support_mode)})

    return (
        {
            "case_id": CASE_ID,
            "case_scope": CASE_SCOPE,
            "status": "ok",
            "video_source_path": str(video_file),
            "sample_fps": sample_fps,
            "summary": summary,
            "moments": moment_rows,
            "intermediate_paths": {
                "frames_csv": str(outputs["frames_path"]),
                "segments_csv": str(outputs["segments_path"]),
                "summary_json": str(outputs["summary_path"]),
            },
            "notes": [
                "Visual behavior remains supporting-only and was run only on bounded timestamped main-call moments.",
                "The current visual layer is heuristic fallback only unless model-backed support is explicitly present.",
                "Suppressed moment rows stay explicit rather than being normalized into neutral support.",
            ],
        },
        False,
    )


def _moment_lookup(rows: list[dict[str, Any]], *, key: str = "moment_id") -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if row.get(key)}


def _audio_reviewer_brief(audio_row: dict[str, Any] | None) -> str:
    if not audio_row or audio_row.get("status") != "aligned":
        return "No curated audio timing is attached to this moment."
    pause_ms = float(audio_row.get("pause_before_answer_ms") or 0.0)
    filler_density = float(audio_row.get("filler_density") or 0.0)
    if pause_ms >= 750:
        return "Measured audio cues show a noticeable pre-answer pause plus qualification/filler context."
    if filler_density >= 0.15:
        return "Measured audio cues mainly add qualification or filler context rather than a large pause signal."
    return "A curated audio window is available, but it adds only limited pacing context."


def _visual_reviewer_brief(visual_row: dict[str, Any] | None) -> str:
    if not visual_row or visual_row.get("status") != "aligned":
        return "No aligned visual window is attached to this moment."
    return "The visual layer remains heuristic context only and does not change the transcript-first read."


def _reviewer_note(moment: dict[str, Any], comparison_row: dict[str, Any], audio_row: dict[str, Any] | None, visual_row: dict[str, Any] | None) -> str:
    bucket = str(comparison_row.get("review_bucket", ""))
    priority_reason = str(comparison_row.get("review_priority_reason", "")).strip()
    if bucket == "consistent_directional_read":
        return "Deterministic read stays primary, and the optional sidecars mostly stay in the same direction on this moment."
    if bucket == "softened_directional_read":
        return f"Deterministic read stays primary. {priority_reason} {_audio_reviewer_brief(audio_row)}"
    if bucket == "directional_conflict":
        return f"Deterministic read stays primary. {priority_reason} {_visual_reviewer_brief(visual_row)}"
    if bucket == "no_comparable_signal":
        return "Optional sidecars were unavailable or non-comparable here, so review this moment transcript-first."
    return "This moment is best read transcript-first because any sidecar spread is descriptive context only."


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
        caveat = "Deterministic transcript-backed output stays canonical; sidecars, audio, and visual cues are supporting-only reviewer context."
        row = {
            "moment_id": moment_id,
            "rank": moment["rank"],
            "top_8_showcase": moment["top_8_showcase"],
            "why_selected": moment["why_selected"],
            "timestamp_range": moment.get("timestamp_range"),
            "raw_quote_or_span": moment["quote_or_span"],
            "deterministic_signal": {
                "category": moment["deterministic_signal_category"],
                "label": moment["plain_english_label"],
                "summary": moment["deterministic_signal_summary"],
                "source_artifact": moment["source_deterministic_artifact"],
                "source_locator": moment["source_locator"],
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
        "case_scope": CASE_SCOPE,
        "status": "ok",
        "selected_moment_count": len(rows),
        "showcase_moment_count": sum(1 for row in rows if row["top_8_showcase"]),
        "panel_rows": rows,
        "top_disagreement_hotspots": disagreement_rows[:8],
        "strong_supporting_context_moments": [
            {
                "moment_id": row["moment_id"],
                "rank": row["rank"],
                "leading_sidecar_label": row["sidecar_outputs"].get("leading_sidecar_label"),
                "reviewer_note": row["reviewer_note"],
                "review_priority_reason": row["sidecar_outputs"].get("review_priority_reason"),
            }
            for row in rows
            if row["sidecar_outputs"].get("review_bucket") in {"consistent_directional_read", "softened_directional_read"}
        ][:8],
        "what_sidecars_added": [
            "A bounded cross-model comparison on a fixed Meta Q3 2022 moment set.",
            "A ranked shortlist of disagreement hotspots that distinguishes directional conflict from lighter softening toward neutral.",
            "Optional embedding-similarity clustering for inspection only when available.",
        ],
        "what_sidecars_did_not_add": [
            "No sidecar output replaces or adjudicates the deterministic transcript-backed read.",
            "No sidecar output here establishes predictive edge, validation, or statistical lift.",
            "No visual heuristic output should be read as corroboration.",
        ],
        "future_ui_surface_notes": [
            "The top-8 showcase moments can be surfaced as a fixed reviewer panel without redesigning the current UI shell.",
            "Pressure and disagreement subpanels already carry reviewer notes, bounded caveats, and clip-ready metadata for later UI follow-up.",
        ],
    }
    pressure_panel = {
        "case_id": CASE_ID,
        "case_scope": CASE_SCOPE,
        "status": "ok",
        "rows": pressure_rows,
    }
    disagreement_panel = {
        "case_id": CASE_ID,
        "case_scope": CASE_SCOPE,
        "status": "ok",
        "rows": disagreement_rows,
    }
    return panel_payload, pressure_panel, disagreement_panel


def _render_asset_audit_markdown(audit: dict[str, Any], visual_payload: dict[str, Any] | None = None) -> str:
    preferred_video = audit["preferred_video_check"]
    resolved_video = preferred_video["resolved_video_path"] or "not found"
    requested_matched_directly = bool(resolved_video != "not found" and not preferred_video["resolved_from_fallback"])
    fallback_video = resolved_video if preferred_video["resolved_from_fallback"] else "not needed"
    lines = [
        "# Meta Multimodal Asset Audit",
        "",
        f"- Case: `{audit['case_id']}`",
        f"- Requested exact MP4 path: `{preferred_video['requested_path']}`",
        f"- Requested exact MP4 path matched directly: `{requested_matched_directly}`",
        f"- Resolved local MP4 fallback used: `{fallback_video}`",
        f"- Bounded visual analysis usable: `{audit['video_usable_for_bounded_visual_analysis']}`",
        "",
        "## What Exists",
        "",
    ]
    for key, item in audit["repo_case_sources"].items():
        lines.append(f"- `{key}`: `{item['exists']}`")
        lines.append(f"  path: `{item['path']}`")
    lines.extend(["", "## Missing Or Weak Coverage", ""])
    for item in audit["missing_or_untracked_items"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Conclusion", "", f"- {audit['video_usability_reason']}"])
    if visual_payload and visual_payload.get("status") == "skipped":
        lines.append(f"- Final persisted visual output was skipped: {visual_payload.get('reason')}")
    elif visual_payload and visual_payload.get("status") == "ok":
        visual_mode = visual_payload.get("summary", {}).get("support_mode")
        if visual_mode == "heuristic_fallback":
            lines.append("- Visual support is heuristic fallback only; it remains observational context rather than corroboration.")
    return "\n".join(lines) + "\n"


def _render_panel_markdown(panel_payload: dict[str, Any], pressure_panel: dict[str, Any], disagreement_panel: dict[str, Any]) -> str:
    lines = [
        "# Meta Multimodal Evidence Panel",
        "",
        "- Deterministic transcript-backed outputs remain canonical.",
        "- NLP, audio, and visual layers are supporting-only reviewer context.",
        "",
        "## How To Read This Pack",
        "",
        "- Start with the transcript-backed deterministic read for each moment.",
        "- Treat same-direction sidecar output as bounded comparison context, not proof that the deterministic read is correct.",
        "- Treat disagreement hotspots as review priorities, not winners or losers.",
        "- Treat audio as measured pause, filler, and qualification context only.",
        "- Treat heuristic visual output as observational context only, never corroboration.",
        "",
        "## Top 8 Showcase",
        "",
    ]
    for row in panel_payload["panel_rows"]:
        if not row["top_8_showcase"]:
            continue
        lines.extend(
            [
                f"### {row['rank']}. {row['moment_id']}",
                "",
                f"- Deterministic label: `{row['deterministic_signal']['label']}`",
                f"- Category: `{row['deterministic_signal']['category']}`",
                f"- Why selected: {row['why_selected']}",
                f"- Timestamp: `{row.get('timestamp_range') or 'not available'}`",
                f"- Quote: {row['raw_quote_or_span']}",
                f"- Reviewer note: {row['reviewer_note']}",
                f"- Caveat: {row['caveat']}",
                "",
            ]
        )
    lines.extend(["## Pressure Moments Panel", ""])
    for row in pressure_panel["rows"]:
        lines.extend(
            [
                f"### {row['moment_id']}",
                "",
                f"- Analyst question: {_truncate(str(row.get('analyst_question', '')), limit=180)}",
                f"- Executive answer: {_truncate(str(row.get('executive_answer', '')), limit=180)}",
                f"- Reviewer note: {row['reviewer_note']}",
                "",
            ]
        )
    lines.extend(["## Disagreement Hotspots", ""])
    if disagreement_panel["rows"]:
        for row in disagreement_panel["rows"]:
            lines.extend(
                [
                    f"- `{row['moment_id']}` [{row.get('review_priority', 'low')}]: {_truncate(str(row['quote_or_span']), limit=160)}",
                    f"  Reason: {row.get('review_priority_reason', 'Review transcript-first before leaning on sidecars.')}",
                ]
            )
    else:
        lines.append("- No material pairwise sidecar disagreement hotspots were written for this run.")
    return "\n".join(lines) + "\n"


def _render_summary_markdown(
    *,
    audit: dict[str, Any],
    visual_payload: dict[str, Any],
    bundle_paths: BundlePaths,
    models: list[str],
    sample_fps: float,
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
        visual_support_mode = visual_summary.get("support_mode")
        if visual_support_mode == "heuristic_fallback" and not visual_summary.get("model_support", {}).get("available", False):
            visual_support_note = "observational fallback only; no model-backed visual scoring"

    lines = [
        "# Meta Multimodal Panel Summary",
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
        f"- `PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps {sample_fps:g} --models {' '.join(models)}`",
        "",
        "## How To Read This Pack",
        "",
        "- Start with the transcript-backed deterministic rows and use this bundle as reviewer support only.",
        "- A same-direction sidecar read is bounded same-direction context, not proof of correctness.",
        "- A disagreement hotspot is a review priority, not a winner or loser among models.",
        "- Audio stays on measured pause, filler, and qualification cues; visual stays observational only.",
        "",
        "## Supporting-Layer Comparison Snapshot",
        "",
    ]
    if visual_support_mode:
        visual_mode_line = f"- Visual support mode: `{visual_support_mode}`"
        if visual_support_note:
            visual_mode_line += f" ({visual_support_note})"
        lines.append(visual_mode_line)
    if pairwise_summary:
        for row in pairwise_summary[:3]:
            lines.append(
                f"- `{row.get('left_model')}` vs `{row.get('right_model')}`: "
                f"comparable-label same-label rate `{row.get('comparable_label_agreement_rate')}` across "
                f"`{row.get('rows_compared')}` curated moments."
            )
    else:
        lines.append("- No pairwise sidecar summary was available.")
    lines.extend(
        [
            "",
            "## What Was Skipped",
            "",
        ]
    )
    if visual_payload.get("status") == "skipped":
        lines.append(f"- Visual support was skipped in the final persisted bundle: {visual_payload.get('reason')}")
    else:
        lines.append("- Visual support was written into the final persisted bundle.")
    lines.extend(
        [
            "",
            "## Outputs To Inspect First",
            "",
            f"- `{bundle_paths.asset_audit_doc}`",
            f"- `{bundle_paths.panel_json}`",
            f"- `{bundle_paths.panel_md}`",
            f"- `{bundle_paths.model_comparison}`",
            f"- `{bundle_paths.disagreement_hotspots}`",
            f"- `{bundle_paths.caveats}`",
            "",
            "## Known Limitations",
            "",
            "- Audio remains limited to the two aligned main-call Q&A windows already present in the repo.",
            "- Follow-up, presentation, and release moments do not have main-call video timestamps.",
        ]
    )
    if visual_support_mode == "heuristic_fallback":
        lines.append("- Visual support is currently heuristic fallback only and does not include model-backed visual scoring.")
    lines.extend(
        [
            "- Sidecars are supporting-only and do not replace the deterministic Meta Q3 2022 artifacts.",
            "",
            "## Recommended Next Step",
            "",
            "- Read the asset audit first, then review the top-8 showcase moments, then scan the ranked disagreement hotspots before any UI follow-up.",
        ]
    )
    return "\n".join(lines) + "\n"


def bundle_paths(root: Path | None = None) -> BundlePaths:
    multi_dir = multimodal_dir(root)
    docs_dir = _repo_root(root) / "docs"
    return BundlePaths(
        asset_audit_doc=docs_dir / "meta_multimodal_asset_audit.md",
        moment_manifest=multi_dir / "meta_multimodal_moment_manifest.json",
        model_comparison=multi_dir / "meta_model_comparison.json",
        disagreement_hotspots=multi_dir / "meta_disagreement_hotspots.json",
        audio_support=multi_dir / "meta_audio_support.json",
        visual_support=multi_dir / "meta_visual_support.json",
        visual_support_skipped=multi_dir / "meta_visual_support_skipped.json",
        clip_manifest=multi_dir / "meta_clip_manifest.json",
        caveats=multi_dir / "meta_supporting_only_caveats.json",
        pressure_panel=multi_dir / "meta_pressure_moments_panel.json",
        disagreement_panel=multi_dir / "meta_disagreement_hotspots_panel.json",
        panel_json=multi_dir / "meta_multimodal_panel.json",
        panel_md=multi_dir / "meta_multimodal_panel.md",
        evidence_panel_doc=docs_dir / "meta_multimodal_evidence_panel.md",
        panel_summary_doc=docs_dir / "meta_multimodal_panel_summary.md",
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
    _write_json(paths.caveats, default_supporting_only_caveats(CASE_SCOPE))
    _write_json(
        paths.clip_manifest,
        {
            "case_id": CASE_ID,
            "case_scope": CASE_SCOPE,
            "source_video_path": audit["preferred_video_check"]["resolved_video_path"],
            "clips": [
                {
                    "moment_id": moment["moment_id"],
                    "rank": moment["rank"],
                    "top_8_showcase": moment["top_8_showcase"],
                    "deterministic_signal_category": moment["deterministic_signal_category"],
                    "plain_english_label": moment["plain_english_label"],
                    "start_time_s": moment.get("start_time_s"),
                    "end_time_s": moment.get("end_time_s"),
                    "timestamp_range": moment.get("timestamp_range"),
                    "clip_ready": bool(moment.get("start_time_s") is not None and audit["preferred_video_check"]["resolved_video_path"]),
                    "clip_note": (
                        "A timed main-call media window is available for bounded reviewer playback."
                        if bool(moment.get("start_time_s") is not None and audit["preferred_video_check"]["resolved_video_path"])
                        else "No timed main-call media window is available for this moment."
                    ),
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
        if paths.visual_support and paths.visual_support.exists():
            paths.visual_support.unlink()
        if paths.visual_support_skipped:
            _write_json(paths.visual_support_skipped, visual_payload)
    else:
        if paths.visual_support_skipped and paths.visual_support_skipped.exists():
            paths.visual_support_skipped.unlink()
        if paths.visual_support:
            _write_json(paths.visual_support, visual_payload)

    paths.asset_audit_doc.write_text(
        _render_asset_audit_markdown(audit, visual_payload),
        encoding="utf-8",
    )
    paths.evidence_panel_doc.write_text(
        _render_panel_markdown(panel_payload, pressure_panel, disagreement_panel),
        encoding="utf-8",
    )
    paths.panel_summary_doc.write_text(
        _render_summary_markdown(
            audit=audit,
            visual_payload=visual_payload,
            bundle_paths=paths,
            models=list(models or ["finbert_tone", "financial_roberta", "deberta_zero_shot", "mpnet_embeddings"]),
            sample_fps=sample_fps,
            pairwise_summary=comparison_payload.get("pairwise_summary"),
        ),
        encoding="utf-8",
    )

    return {
        "case_id": CASE_ID,
        "bundle_paths": {field: str(getattr(paths, field)) for field in paths.__dataclass_fields__},
        "visual_skipped": visual_skipped,
        "sidecar_runtime": sidecar_runtime,
    }
