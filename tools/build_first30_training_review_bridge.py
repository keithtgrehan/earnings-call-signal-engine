#!/usr/bin/env python3
"""Summarize review candidates without promoting them to training labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first30_signal_candidates.jsonl"
REPORT_PATH = ROOT / "reports" / "review" / "first30_training_review_bridge.md"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_bridge(candidates_path: Path = DEFAULT_CANDIDATES, out_path: Path = REPORT_PATH) -> dict[str, Any]:
    rows = read_jsonl(candidates_path)
    adjudicated = [row for row in rows if row.get("review_status") == "human_reviewed" and row.get("gold_status") == "gold"]
    summary = {
        "candidate_rows": len(rows),
        "pending_human_review": sum(1 for row in rows if row.get("review_status") == "pending_human_review"),
        "valid_adjudicated_labels": len(adjudicated),
        "training_ready": False,
        "weak_candidate_labels_promoted_to_gold": False,
        "training_performed": False,
    }
    write_report(summary, out_path)
    return summary


def write_report(summary: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Training Review Bridge",
        "",
        f"- Candidate rows: {summary['candidate_rows']}",
        f"- Pending human review: {summary['pending_human_review']}",
        f"- Valid adjudicated labels: {summary['valid_adjudicated_labels']}",
        "- Training ready: false",
        "- Weak/candidate labels promoted to gold: false",
        "- Training performed: false",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first30 training/review bridge report.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    print(json.dumps(build_bridge(args.candidates, args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
