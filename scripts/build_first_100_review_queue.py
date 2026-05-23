#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.gold_review import build_first_100_queue


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first-100 human review queue from candidate packets; all rows remain not_gold.")
    parser.add_argument("--packet-glob", action="append", default=["data/corpus/high_signal_cases/*/labels/human_labeling_packet.md", "data/labeling/*packet*.md"])
    parser.add_argument("--staging-dir", default="data/review/staging")
    parser.add_argument("--report", default="reports/review/first_100_queue_summary.md")
    parser.add_argument("--ranked-out", default="data/review/staging/first_100_ranked_review_queue.jsonl")
    parser.add_argument("--ranked-report", default="reports/review/first_100_ranked_queue_summary.md")
    args = parser.parse_args(argv)
    packet_paths: list[Path] = []
    for pattern in args.packet_glob:
        packet_paths.extend(Path(path) for path in glob.glob(pattern))
    pool, queue = build_first_100_queue(packet_paths)
    staging = Path(args.staging_dir)
    _write_jsonl(staging / "first_100_candidate_pool.jsonl", pool)
    _write_jsonl(staging / "first_100_review_queue.jsonl", queue)
    ranked = sorted(queue, key=lambda row: _rank_score(row), reverse=True)
    _write_jsonl(Path(args.ranked_out), ranked)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# First-100 Review Queue Summary",
                "",
                "All rows are candidate metadata only: `gold_status=not_gold` and `review_status=pending_human_review`.",
                "",
                f"- Packet files read: `{len(packet_paths)}`",
                f"- Candidate pool size: `{len(pool)}`",
                f"- First-100 queue size: `{len(queue)}`",
                "- Machine suggestions are preserved as review metadata only.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ranked_report = Path(args.ranked_report)
    ranked_report.parent.mkdir(parents=True, exist_ok=True)
    ranked_report.write_text(
        "\n".join(
            [
                "# First-100 Ranked Queue Summary",
                "",
                "Ranking favors transcript-backed, evidence-complete, business-signal candidates and keeps all rows `not_gold`.",
                "",
                f"- Ranked queue size: `{len(ranked)}`",
                "- Canonical gold labels written: `0`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"First-100 review queue built: {len(queue)} row(s), all not_gold.")
    return 0


def _rank_score(row: dict[str, object]) -> int:
    score = 0
    source_file = str(row.get("source_file", ""))
    evidence = str(row.get("evidence_text", ""))
    label = str(row.get("suggested_label", ""))
    flags = set(row.get("contamination_flags") or [])
    if "raw transcript" in source_file.lower() or source_file.endswith((".txt", ".md")):
        score += 4
    if len(evidence) >= 80:
        score += 3
    if label in {"guidance_revision", "analyst_pressure", "management_hedging", "uncertainty", "reassurance", "answer_shift"}:
        score += 3
    if row.get("speaker_role") and row.get("speaker_role") != "unknown":
        score += 1
    if row.get("transcript_section") and row.get("transcript_section") != "unknown":
        score += 1
    if flags:
        score -= len(flags)
    return score


if __name__ == "__main__":
    raise SystemExit(main())
