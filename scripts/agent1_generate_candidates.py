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

from signal_engine.agent1_extraction import candidate_counts, forbid_raw_transcript_output, generate_candidates_for_transcript, validate_candidates
from agent1_validate_manual_local_sources import load_registry


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_counts(path: Path, counts: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["signal_type", "count"], lineterminator="\n")
        writer.writeheader()
        for signal_type, count in counts.items():
            writer.writerow({"signal_type": signal_type, "count": count})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic Agent 1 candidates from registered manual-local transcripts.")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--out", default="data/review/staging/agent1_candidates.jsonl")
    parser.add_argument("--counts-out", default="reports/agent1/candidate_counts_by_label.csv")
    args = parser.parse_args(argv)
    path_errors = forbid_raw_transcript_output(Path(args.out))
    if path_errors:
        for error in path_errors:
            print(f"- {error}")
        return 1
    rows = [row for row in load_registry(Path(args.registry)) if row.get("media_type") == "transcript"]
    candidates: list[dict[str, object]] = []
    for row in rows:
        source_path = Path(str(row.get("source_path_ref", "")))
        if not source_path.exists() or not str(row.get("source_sha256", "")).startswith("sha256:"):
            continue
        candidates.extend(
            generate_candidates_for_transcript(
                case_id=str(row["case_id"]),
                source_file=str(row["source_path_ref"]),
                source_sha256=str(row["source_sha256"]),
                text=source_path.read_text(encoding="utf-8"),
            )
        )
    errors = validate_candidates(candidates)
    if errors:
        print(f"Agent 1 candidate generation failed: {len(errors)} validation error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    _write_jsonl(Path(args.out), candidates)
    _write_counts(Path(args.counts_out), candidate_counts(candidates))
    print(f"Agent 1 candidate generation complete: {len(candidates)} candidate(s), all not_gold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
