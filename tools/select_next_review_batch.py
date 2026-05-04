#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import load_candidates, write_csv  # noqa: E402

FIELDS = [
    "candidate_id",
    "case_id",
    "text",
    "weak_label",
    "confidence",
    "noise_flag",
    "selection_reason",
    "review_decision",
    "final_label",
]


def load_model_predictions(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row.get("candidate_id")): str(row.get("model_label")) for row in csv.DictReader(handle)}


def select(rows: list[dict[str, Any]], *, model_predictions: dict[str, str], limit: int) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("weak_label") or "") for row in rows)
    selected: list[dict[str, Any]] = []
    for row in rows:
        reasons: list[str] = []
        try:
            confidence = float(row.get("confidence") or 0.0)
        except ValueError:
            confidence = 0.0
        if confidence < 0.55:
            reasons.append("low_confidence")
        label = str(row.get("weak_label") or "")
        if counts[label] <= 3:
            reasons.append("rare_label")
        model_label = model_predictions.get(str(row.get("candidate_id")))
        if model_label and model_label != label:
            reasons.append("model_disagreement")
        if reasons:
            selected.append(
                {
                    "candidate_id": row.get("candidate_id", ""),
                    "case_id": row.get("case_id", ""),
                    "text": row.get("text", ""),
                    "weak_label": label,
                    "confidence": row.get("confidence", ""),
                    "noise_flag": row.get("noise_flag", ""),
                    "selection_reason": ";".join(reasons),
                    "review_decision": "",
                    "final_label": "",
                }
            )
    selected.sort(key=lambda item: (0 if "model_disagreement" in str(item["selection_reason"]) else 1, str(item["candidate_id"])))
    return selected[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select the next minimal active-learning review batch.")
    parser.add_argument("--candidates", default=str(ROOT / "data" / "labeling" / "candidates.jsonl"))
    parser.add_argument("--model-predictions", default=str(ROOT / "data" / "labeling" / "model_predictions.csv"))
    parser.add_argument("--out", default=str(ROOT / "data" / "labeling" / "next_review_batch.csv"))
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)
    candidates = load_candidates(Path(args.candidates))
    predictions = load_model_predictions(Path(args.model_predictions))
    batch = select(candidates, model_predictions=predictions, limit=args.limit)
    write_csv(Path(args.out), batch, FIELDS)
    print(f"next review batch rows: {len(batch)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
