#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import is_high_business_context, load_candidates, write_csv  # noqa: E402

REVIEW_FIELDS = [
    "candidate_id",
    "case_id",
    "text",
    "weak_label",
    "confidence",
    "noise_flag",
    "priority_score",
    "priority_reason",
    "review_decision",
    "final_label",
]


def priority(row: dict[str, object], label_counts: Counter[str]) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []
    text = str(row.get("text") or "")
    label = str(row.get("weak_label") or "")
    try:
        confidence = float(row.get("confidence") or 0.0)
    except ValueError:
        confidence = 0.0
    if is_high_business_context(text):
        score += 3
        reasons.append("high_business_context")
    if label_counts[label] <= 3:
        score += 2
        reasons.append("rare_label")
    if confidence < 0.55:
        score += 2
        reasons.append("low_confidence")
    if row.get("duplicate_of"):
        score -= 1
        reasons.append("duplicate_flagged")
    return max(score, 0), ";".join(reasons) or "coverage"


def build_review_queue(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    label_counts = Counter(str(row.get("weak_label") or "") for row in candidates)
    queue: list[dict[str, object]] = []
    for row in candidates:
        score, reason = priority(row, label_counts)
        queue.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "text": row.get("text", ""),
                "weak_label": row.get("weak_label", ""),
                "confidence": row.get("confidence", ""),
                "noise_flag": row.get("noise_flag", ""),
                "priority_score": score,
                "priority_reason": reason,
                "review_decision": "",
                "final_label": "",
            }
        )
    queue.sort(key=lambda item: (-int(item["priority_score"]), str(item["candidate_id"])))
    return queue


def write_summary(queue: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = Counter(str(row.get("weak_label") or "missing") for row in queue)
    noise = Counter(str(row.get("noise_flag") or "clean") for row in queue)
    lines = [
        "# Review Queue Summary",
        "",
        f"- total_candidates: `{len(queue)}`",
        f"- next_review_target: `{min(50, len(queue))}`",
        "",
        "## Weak Labels",
        "",
    ]
    for label, count in sorted(labels.items()):
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Noise Flags", ""])
    for flag, count in sorted(noise.items()):
        lines.append(f"- `{flag}`: {count}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an unfiltered human review queue from candidates.")
    parser.add_argument("--candidates", default=str(ROOT / "data" / "labeling" / "candidates.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "data" / "labeling" / "review_queue.csv"))
    parser.add_argument("--summary-out", default=str(ROOT / "docs" / "labeling" / "review_queue_summary.md"))
    args = parser.parse_args(argv)
    candidates = load_candidates(Path(args.candidates))
    queue = build_review_queue(candidates)
    write_csv(Path(args.out), queue, REVIEW_FIELDS)
    write_summary(queue, Path(args.summary_out))
    print(f"review queue rows: {len(queue)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
