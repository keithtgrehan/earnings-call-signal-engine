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
    args = parser.parse_args(argv)
    packet_paths: list[Path] = []
    for pattern in args.packet_glob:
        packet_paths.extend(Path(path) for path in glob.glob(pattern))
    pool, queue = build_first_100_queue(packet_paths)
    staging = Path(args.staging_dir)
    _write_jsonl(staging / "first_100_candidate_pool.jsonl", pool)
    _write_jsonl(staging / "first_100_review_queue.jsonl", queue)
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
    print(f"First-100 review queue built: {len(queue)} row(s), all not_gold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
