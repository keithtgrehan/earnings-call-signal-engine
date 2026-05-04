from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from data_layer.io import write_json, write_jsonl


def _votes(text_row: dict[str, Any], fusion_row: dict[str, Any] | None) -> dict[str, str | None]:
    return {
        "rule": text_row.get("rule_signal"),
        "snorkel": text_row.get("snorkel_label"),
        "baseline_classifier": text_row.get("baseline_signal"),
        "transformer_classifier": text_row.get("transformer_signal"),
        "finbert": text_row.get("finbert_signal"),
        "fusion": fusion_row.get("fused_signal") if fusion_row else None,
        "audio_model": None,
        "video_model": None,
        "llm_triage": None,
    }


def _majority(votes: dict[str, str | None], fallback: str) -> str:
    counts = Counter(value for value in votes.values() if value)
    if not counts:
        return fallback
    return counts.most_common(1)[0][0]


def build_ensemble_outputs(
    *,
    text_rows: list[dict[str, Any]],
    fusion_rows: list[dict[str, Any]],
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    fusion_by_id = {str(row["segment_id"]): row for row in fusion_rows}
    rows: list[dict[str, Any]] = []
    for text_row in text_rows:
        segment_id = str(text_row["segment_id"])
        fusion_row = fusion_by_id.get(segment_id)
        model_votes = _votes(text_row, fusion_row)
        final_signal = _majority(model_votes, str(text_row.get("rule_signal") or "neutral"))
        confidence = float((fusion_row or {}).get("confidence") or text_row.get("signal_confidence") or 0.0)
        vote_values = {value for value in model_votes.values() if value}
        disagreement_flags = []
        if len(vote_values) > 1:
            disagreement_flags.append("model_vote_disagreement")
        if confidence < 0.55:
            disagreement_flags.append("low_confidence")
        rows.append(
            {
                "segment_id": segment_id,
                "final_signal": final_signal,
                "final_emotion": text_row.get("emotion"),
                "final_sentiment": text_row.get("sentiment"),
                "confidence": round(confidence, 4),
                "uncertainty": round(1.0 - confidence, 4),
                "model_votes": model_votes,
                "disagreement_flags": disagreement_flags,
                "human_review_recommended": bool(disagreement_flags),
                "evidence": text_row.get("evidence", {}),
                "probabilities": (fusion_row or {}).get("fused_probabilities") or text_row.get("signal_probabilities"),
            }
        )
    status = {
        "stage": "ensemble",
        "status": "completed",
        "dry_run": dry_run,
        "rows": len(rows),
        "review_recommended": sum(1 for row in rows if row["human_review_recommended"]),
    }
    if not dry_run:
        write_jsonl(output_dir / "ensemble_outputs.jsonl", rows)
        write_json(output_dir / "ensemble_status.json", status)
    return {"rows": rows, "status": status}
