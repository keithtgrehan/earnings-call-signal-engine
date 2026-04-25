#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation_backbone import write_json
from signal_engine.signal_baseline import HUMAN_REVIEWED_LABELS_RELATIVE_PATH, SIGNAL_FAMILY_LABELS, load_supervised_examples, training_readiness


def _count_candidates(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    total = 0
    accepted = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            if str(row.get("accepted", "")).strip().lower() in {"true", "yes", "y", "1"}:
                accepted += 1
    return total, accepted


def _gap(total: int, target: int) -> int:
    return max(target - total, 0)


def _next_batch_recommendation(class_counts: dict[str, int]) -> str:
    lowest = sorted(class_counts.items(), key=lambda item: (item[1], item[0]))
    focus = ", ".join(f"{label} ({count})" for label, count in lowest[:2])
    return (
        "Prioritize the next 20-30 reviewed rows toward the thinnest classes, starting with "
        f"{focus}, while keeping at least 20 percent of the batch neutral."
    )


def _render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Label Dataset Growth Report",
        "",
        "This report tracks reviewed-label growth without turning mined candidates into truth automatically.",
        "",
        f"- current_reviewed_label_count: `{payload['current_reviewed_label_count']}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- accepted_candidate_count: `{payload['accepted_candidate_count']}`",
        f"- benchmark_training_ready: `{payload['benchmark_training_ready']}`",
        f"- gold_holdout_viable: `{payload['gold_holdout_viable']}`",
        "",
        "## Current Class Balance",
        "",
    ]
    for label, count in payload["class_balance"].items():
        lines.append(f"- `{label}`: `{count}`")
    lines.extend(
        [
            "",
            "## Gap To Milestones",
            "",
        ]
    )
    for target, gap in payload["target_gaps"].items():
        lines.append(f"- `{target}`: `{gap}` more reviewed labels needed")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            f"- {payload['recommended_next_labeling_batch']}",
            "",
            "## Boundaries",
            "",
            "- Local fixtures remain the primary training source.",
            "- Candidate mining creates review queues only.",
            "- Manual review is still required before promotion into the canonical label set.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report growth status for the reviewed signal label dataset.")
    parser.add_argument("--labels-path", default=str(ROOT / HUMAN_REVIEWED_LABELS_RELATIVE_PATH))
    parser.add_argument(
        "--candidate-review-path",
        default=str(ROOT / "data" / "nlp_research" / "signal_label_candidates_review.csv"),
    )
    parser.add_argument(
        "--gold-holdout-path",
        default=str(ROOT / "data" / "nlp_research" / "gold_holdout_candidates.jsonl"),
    )
    parser.add_argument(
        "--json-out",
        default=str(ROOT / "data" / "nlp_research" / "label_dataset_growth.json"),
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "label-dataset-growth-report.md"),
    )
    args = parser.parse_args(argv)

    labels = load_supervised_examples(Path(args.labels_path))
    class_balance = {label: 0 for label in SIGNAL_FAMILY_LABELS}
    for row in labels:
        class_balance[row["signal_family"]] += 1
    candidate_count, accepted_candidate_count = _count_candidates(Path(args.candidate_review_path))
    readiness = training_readiness(labels)
    holdout_exists = Path(args.gold_holdout_path).exists()

    payload = {
        "current_reviewed_label_count": len(labels),
        "class_balance": class_balance,
        "candidate_count": candidate_count,
        "accepted_candidate_count": accepted_candidate_count,
        "target_gaps": {
            "100_labels": _gap(len(labels), 100),
            "300_labels": _gap(len(labels), 300),
            "1000_labels": _gap(len(labels), 1000),
        },
        "recommended_next_labeling_batch": _next_batch_recommendation(class_balance),
        "benchmark_training_ready": bool(readiness["ready"]),
        "benchmark_training_reason": readiness["reason"],
        "gold_holdout_viable": holdout_exists or min(class_balance.values()) >= 4,
    }
    write_json(Path(args.json_out), payload)
    report_out = Path(args.report_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(_render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
