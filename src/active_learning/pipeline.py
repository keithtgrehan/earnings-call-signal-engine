from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from data_layer.io import write_csv, write_json


def _priority(row: dict[str, Any], label_counts: Counter[str]) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []
    if float(row.get("confidence") or 0.0) < 0.55:
        score += 3
        reasons.append("low_confidence")
    if row.get("disagreement_flags"):
        score += 3
        reasons.append("model_disagreement")
    if label_counts[str(row.get("final_signal"))] <= 2:
        score += 2
        reasons.append("rare_label")
    if row.get("final_signal") in {"risk_friction", "uncertainty_hedging"}:
        score += 1
        reasons.append("high_value_signal")
    return score, ";".join(reasons) or "coverage_sample"


def select_review_batch(
    ensemble_rows: list[dict[str, Any]],
    *,
    output_dir: Path,
    limit: int = 50,
    dry_run: bool = False,
) -> dict[str, Any]:
    label_counts = Counter(str(row.get("final_signal")) for row in ensemble_rows)
    ranked: list[dict[str, Any]] = []
    for row in ensemble_rows:
        score, reason = _priority(row, label_counts)
        if score <= 0:
            continue
        ranked.append(
            {
                "segment_id": row.get("segment_id"),
                "final_signal": row.get("final_signal"),
                "final_emotion": row.get("final_emotion"),
                "final_sentiment": row.get("final_sentiment"),
                "confidence": row.get("confidence"),
                "uncertainty": row.get("uncertainty"),
                "review_priority": score,
                "review_reason": reason,
                "human_label_signal": "",
                "human_label_emotion": "",
                "review_notes": "",
            }
        )
    ranked.sort(key=lambda item: (-int(item["review_priority"]), str(item["segment_id"])))
    batch = ranked[:limit]
    status = {
        "stage": "active-learning",
        "status": "completed",
        "dry_run": dry_run,
        "candidate_rows": len(ranked),
        "review_batch_rows": len(batch),
        "selection_rules": ["low confidence", "model disagreement", "rare labels", "high-value segments"],
    }
    if not dry_run:
        write_csv(
            output_dir / "next_review_batch.csv",
            batch,
            fieldnames=[
                "segment_id",
                "final_signal",
                "final_emotion",
                "final_sentiment",
                "confidence",
                "uncertainty",
                "review_priority",
                "review_reason",
                "human_label_signal",
                "human_label_emotion",
                "review_notes",
            ],
        )
        write_json(output_dir / "active_learning_status.json", status)
    return {"rows": batch, "status": status}
