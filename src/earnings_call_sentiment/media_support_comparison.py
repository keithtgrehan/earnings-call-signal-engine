from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from earnings_call_sentiment.media_quality import build_media_quality_summary
from earnings_call_sentiment.media_support_eval import repo_root
from earnings_call_sentiment.multimodal_support import build_multimodal_support_summary


def aggregate_support_target(
    labels: pd.DataFrame,
    *,
    direction_column: str = "multimodal_support_direction",
    direction_threshold: float = 0.2,
) -> dict[str, Any]:
    counts = {
        str(key): int(value)
        for key, value in labels[direction_column].astype(str).value_counts().to_dict().items()
    }
    supportive = counts.get("supportive", 0)
    cautionary = counts.get("cautionary", 0)
    neutral = counts.get("neutral", 0)
    denominator = supportive + cautionary + neutral
    signed_mean = 0.0 if denominator == 0 else float(cautionary - supportive) / float(denominator)
    if signed_mean >= direction_threshold:
        direction = "cautionary"
    elif signed_mean <= -direction_threshold:
        direction = "supportive"
    else:
        direction = "neutral"
    return {
        "counts": counts,
        "target_support_signed_mean": round(signed_mean, 4),
        "target_support_direction": direction,
    }


def classify_support_score(score: float, *, neutral_band: float = 0.03) -> str:
    if score >= neutral_band:
        return "cautionary"
    if score <= -neutral_band:
        return "supportive"
    return "neutral"


def _resolve_path(path_value: str | Path | float | None) -> Path | None:
    if path_value is None:
        return None
    text = str(path_value).strip()
    if not text:
        return None
    path = Path(text)
    return path if path.is_absolute() else repo_root() / path


def _load_json(path_value: str | Path | float | None) -> dict[str, Any] | None:
    path = _resolve_path(path_value)
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _coerce_optional_float(value: Any) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def recompute_multimodal_case(case_row: dict[str, Any]) -> dict[str, Any]:
    metrics_path = _resolve_path(case_row.get("metrics_path"))
    qa_shift_path = _resolve_path(case_row.get("qa_shift_path"))
    audio_path = _resolve_path(case_row.get("audio_summary_path"))
    visual_path = _resolve_path(case_row.get("visual_summary_path"))

    metrics_available = metrics_path is not None and metrics_path.exists()
    qa_shift_available = qa_shift_path is not None and qa_shift_path.exists()
    audio_summary_available = audio_path is not None and audio_path.exists()
    visual_summary_available = visual_path is not None and visual_path.exists()

    metrics_payload = _load_json(metrics_path) or {}
    qa_shift_summary = _load_json(qa_shift_path) or {}
    audio_summary = _load_json(audio_path)
    visual_summary = _load_json(visual_path)
    media_quality = build_media_quality_summary(
        audio_summary=audio_summary,
        visual_summary=visual_summary,
    )
    summary = None
    if metrics_available:
        summary = build_multimodal_support_summary(
            metrics_payload=metrics_payload,
            qa_shift_summary=qa_shift_summary,
            audio_summary=audio_summary,
            visual_summary=visual_summary,
            media_quality=media_quality,
        )
    return {
        "summary": summary,
        "media_quality": media_quality,
        "artifact_presence": {
            "metrics_available": metrics_available,
            "qa_shift_available": qa_shift_available,
            "audio_summary_available": audio_summary_available,
            "visual_summary_available": visual_summary_available,
        },
    }


def evaluate_downstream_decision_cases(cases: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, case in cases.iterrows():
        case_dict = case.to_dict()
        recomputed = recompute_multimodal_case(case_dict)
        current_metrics_available = bool(recomputed["artifact_presence"].get("metrics_available", False))
        current_summary = recomputed["summary"] if current_metrics_available else None
        current_summary_dict = current_summary if isinstance(current_summary, dict) else {}
        current_score = (
            float(current_summary.get("calibrated_support_score", 0.0))
            if isinstance(current_summary, dict)
            else None
        )
        current_direction = classify_support_score(current_score) if current_score is not None else ""

        baseline_score = 0.0
        baseline_direction = "neutral"

        saved_score = None
        saved_direction = None
        saved_path = _resolve_path(case_dict.get("saved_multimodal_summary_path"))
        saved_summary_available = saved_path is not None and saved_path.exists()
        if saved_summary_available:
            saved_summary = _load_json(saved_path) or {}
            saved_score = float(saved_summary.get("calibrated_support_score", 0.0))
            saved_direction = classify_support_score(saved_score)

        target_score = _coerce_optional_float(case_dict.get("target_support_signed_mean"))
        target_direction = str(case_dict.get("target_support_direction", "")).strip()
        has_support_target = bool(target_direction) and target_score is not None

        rows.append(
            {
                **case_dict,
                "has_support_target": has_support_target,
                "baseline_direction": baseline_direction,
                "baseline_score": baseline_score,
                "baseline_match": "" if not has_support_target else baseline_direction == target_direction,
                "baseline_abs_error": "" if not has_support_target else round(abs(target_score - baseline_score), 4),
                "current_metrics_available": current_metrics_available,
                "current_direction": current_direction,
                "current_score": "" if current_score is None else round(current_score, 4),
                "current_match": ""
                if (not has_support_target or current_score is None)
                else current_direction == target_direction,
                "current_abs_error": ""
                if (not has_support_target or current_score is None)
                else round(abs(target_score - current_score), 4),
                "current_availability_note": (
                    ""
                    if current_metrics_available
                    else "Current metrics.json is not present locally; excluded from current multimodal comparison summaries."
                ),
                "saved_summary_available": saved_summary_available,
                "saved_direction": saved_direction or "",
                "saved_score": "" if saved_score is None else round(saved_score, 4),
                "saved_match": ""
                if (saved_direction is None or not has_support_target)
                else str(saved_direction == target_direction).lower(),
                "saved_abs_error": ""
                if (saved_score is None or not has_support_target)
                else round(abs(target_score - saved_score), 4),
                "audio_support_direction": current_summary_dict.get("audio_support_direction", "unavailable"),
                "video_support_direction": current_summary_dict.get("video_support_direction", "unavailable"),
                "fusion_mode": current_summary_dict.get("fusion_mode", "unavailable"),
                "multimodal_alignment": current_summary_dict.get("multimodal_alignment", "unavailable"),
                "multimodal_confidence_adjustment": int(current_summary_dict.get("multimodal_confidence_adjustment", 0)),
                "audio_quality_ok": bool(recomputed["media_quality"].get("audio_quality_ok", False)),
                "video_quality_ok": bool(recomputed["media_quality"].get("video_quality_ok", False)),
            }
        )

    result_frame = pd.DataFrame(rows)
    comparable = result_frame[result_frame["has_support_target"]].copy()
    comparable_current = comparable[comparable["current_metrics_available"]].copy()
    excluded_current = int(len(comparable) - len(comparable_current))

    summary: dict[str, Any] = {
        "case_count": int(len(result_frame)),
        "case_count_with_support_targets": int(len(comparable)),
        "case_count_without_support_targets": int(len(result_frame) - len(comparable)),
        "artifact_coverage": {
            "rows_with_current_metrics": int(result_frame["current_metrics_available"].astype(bool).sum()),
            "rows_without_current_metrics": int(len(result_frame) - result_frame["current_metrics_available"].astype(bool).sum()),
            "support_target_rows_with_current_metrics": int(len(comparable_current)),
            "support_target_rows_without_current_metrics": excluded_current,
        },
        "transcript_only_baseline": {
            "case_count": int(len(comparable)),
            "label_accuracy": round(float(comparable["baseline_match"].mean()), 4) if not comparable.empty else 0.0,
            "mean_abs_error_vs_target": round(float(comparable["baseline_abs_error"].mean()), 4)
            if not comparable.empty
            else 0.0,
        },
        "current_conservative_multimodal": {
            "case_count": int(len(comparable_current)),
            "excluded_support_target_rows_missing_current_metrics": excluded_current,
            "label_accuracy": round(float(comparable_current["current_match"].mean()), 4)
            if not comparable_current.empty
            else 0.0,
            "mean_abs_error_vs_target": round(float(comparable_current["current_abs_error"].mean()), 4)
            if not comparable_current.empty
            else 0.0,
        },
        "notes": [],
    }

    if "gold_guidance_label" in result_frame.columns:
        summary["gold_guidance_label_distribution"] = {
            str(key): int(value)
            for key, value in result_frame["gold_guidance_label"].astype(str).value_counts().to_dict().items()
        }

    if excluded_current:
        summary["notes"].append(
            f"{excluded_current} support-target row(s) were excluded from current multimodal accuracy/error summaries because metrics.json is not present locally."
        )
    if summary["case_count_without_support_targets"]:
        summary["notes"].append(
            "Rows without source-level support targets remain transcript-first packaged cases and are not included in target-matching summaries."
        )

    comparable_saved = comparable[comparable["saved_direction"].astype(str).str.strip() != ""].copy()
    if not comparable_saved.empty:
        comparable_saved["saved_match_bool"] = comparable_saved["saved_match"].astype(str).str.lower() == "true"
        comparable_saved["saved_abs_error_float"] = comparable_saved["saved_abs_error"].astype(float)
        summary["legacy_saved_multimodal"] = {
            "case_count": int(len(comparable_saved)),
            "label_accuracy": round(float(comparable_saved["saved_match_bool"].mean()), 4),
            "mean_abs_error_vs_target": round(float(comparable_saved["saved_abs_error_float"].mean()), 4),
        }

    return result_frame, summary


def summarize_task_impact_results(cases: pd.DataFrame, results: pd.DataFrame) -> dict[str, Any]:
    if results.empty:
        return {
            "submission_count": 0,
            "conditions": {},
            "notes": ["No participant submissions were recorded yet."],
        }

    merged = results.merge(
        cases[["case_id", "gold_guidance_label"]],
        on="case_id",
        how="left",
    )
    merged["label_match"] = merged["predicted_guidance_label"].astype(str) == merged["gold_guidance_label"].astype(str)

    conditions: dict[str, Any] = {}
    for condition, group in merged.groupby("condition"):
        conditions[str(condition)] = {
            "submission_count": int(len(group)),
            "mean_completion_seconds": round(float(pd.to_numeric(group["completion_seconds"], errors="coerce").mean()), 2),
            "label_accuracy": round(float(group["label_match"].mean()), 4),
            "mean_clarity_rating": round(float(pd.to_numeric(group["clarity_rating"], errors="coerce").mean()), 2),
            "mean_evidence_quality_score": round(
                float(pd.to_numeric(group["evidence_quality_score"], errors="coerce").mean()), 2
            ),
        }

    return {
        "submission_count": int(len(merged)),
        "conditions": conditions,
        "notes": [
            "This summary is descriptive only until enough counterbalanced participant observations exist for paired testing."
        ],
    }
