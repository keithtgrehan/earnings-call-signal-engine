#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation_backbone import load_jsonl, write_csv


def _load_holdout_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {row["source_label_id"] for row in load_jsonl(path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prioritize the next high-value rows for second review.")
    parser.add_argument(
        "--error-analysis-path",
        default=str(ROOT / "data" / "nlp_research" / "signal_error_analysis.json"),
    )
    parser.add_argument(
        "--holdout-path",
        default=str(ROOT / "data" / "nlp_research" / "gold_holdout_candidates.jsonl"),
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "nlp_research" / "second_review_priority_queue.csv"),
    )
    args = parser.parse_args(argv)

    error_payload = json.loads(Path(args.error_analysis_path).read_text(encoding="utf-8"))
    holdout_ids = _load_holdout_ids(Path(args.holdout_path))
    queue_rows = []
    for case in error_payload["cases"]:
        priority = int(case["priority_score"])
        reasons = list(case["recommended_actions"])
        if case["id"] in holdout_ids:
            priority += 2
            reasons.append("gold_holdout_candidate")
        if case["gold_label"] == "neutral":
            priority += 1
            reasons.append("neutral_class_support")
        queue_rows.append(
            {
                "id": case["id"],
                "text": case["text"],
                "current_label": case["gold_label"],
                "priority_reason": "; ".join(dict.fromkeys(reasons)),
                "reviewer_label": "",
                "reviewer_confidence": "",
                "reviewer_notes": "",
                "priority_score": priority,
            }
        )
    queue_rows = sorted(queue_rows, key=lambda row: (-int(row["priority_score"]), row["id"]))[:18]
    write_csv(
        Path(args.out),
        fieldnames=[
            "id",
            "text",
            "current_label",
            "priority_reason",
            "reviewer_label",
            "reviewer_confidence",
            "reviewer_notes",
        ],
        rows=[
            {
                "id": row["id"],
                "text": row["text"],
                "current_label": row["current_label"],
                "priority_reason": row["priority_reason"],
                "reviewer_label": "",
                "reviewer_confidence": "",
                "reviewer_notes": "",
            }
            for row in queue_rows
        ],
    )
    print(json.dumps({"status": "ok", "queue_size": len(queue_rows), "out": args.out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
