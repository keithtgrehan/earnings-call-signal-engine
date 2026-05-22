#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _priority(row: dict[str, object]) -> int:
    score = 0
    if row.get("signal_type") == "guidance_revision":
        score += 5
    if row.get("signal_type") == "answer_shift":
        score += 4
    if row.get("signal_type") == "management_hedging" and row.get("transcript_section") == "qa":
        score += 3
    if row.get("signal_type") == "uncertainty":
        score += 3
    if row.get("false_positive_bucket") == "prior_missing":
        score += 2
    if row.get("signal_type") == "neutral/no_signal":
        score -= 3
    if row.get("false_positive_bucket"):
        score -= 1
    return score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Agent 1 human review queue from candidate records.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/agent1_candidates_deduped.jsonl")
    parser.add_argument("--out", default="data/review/staging/agent1_review_queue.jsonl")
    parser.add_argument("--summary", default="reports/agent1/review_queue_summary.md")
    args = parser.parse_args(argv)
    rows = _load_jsonl(Path(args.in_path))
    queue = sorted(rows, key=_priority, reverse=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in queue:
            handle.write(json.dumps({**row, "review_priority": _priority(row)}, sort_keys=True) + "\n")
    summary = Path(args.summary)
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        "\n".join(
            [
                "# Agent 1 Review Queue Summary",
                "",
                "Rows are deterministic candidates only and remain `not_gold` until human adjudication.",
                "",
                f"- Queue rows: `{len(queue)}`",
                "- No canonical gold labels were written.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Agent 1 review queue built: {len(queue)} candidate row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
