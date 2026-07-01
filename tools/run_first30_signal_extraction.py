#!/usr/bin/env python3
"""Run deterministic first30 signal-candidate extraction over retrieval metadata."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.first30_extraction import CANDIDATE_FIELDS, extract_candidates_from_retrieval_objects

DEFAULT_RETRIEVAL_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_OUT = ROOT / "data" / "review" / "staging" / "first30_signal_candidates.jsonl"
SUMMARY_REPORT = ROOT / "reports" / "extraction" / "first30_signal_extraction_summary.md"
COUNTS_BY_LABEL = ROOT / "reports" / "extraction" / "first30_signal_counts_by_label.csv"
COUNTS_BY_CASE = ROOT / "reports" / "extraction" / "first30_signal_counts_by_case.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary: dict[str, Any], out_path: Path = SUMMARY_REPORT) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Signal Extraction Summary",
        "",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Cases with candidates: {summary['cases']}",
        f"- Label counts: `{json.dumps(summary['labels'], sort_keys=True)}`",
        f"- Suppressed rows: `{json.dumps(summary['suppressed'], sort_keys=True)}`",
        "- Deterministic candidates only: true",
        "- Gold labels created: 0",
        "- Review status: pending_human_review",
        "- Raw evidence text committed: false",
        "- Training performed: false",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_extraction(
    retrieval_objects: Path = DEFAULT_RETRIEVAL_OBJECTS,
    out_path: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    rows = read_csv(retrieval_objects)
    candidates, summary = extract_candidates_from_retrieval_objects(rows)
    write_jsonl(out_path, candidates)
    label_counts = Counter(row["label"] for row in candidates)
    case_counts = Counter(row["case_id"] for row in candidates)
    write_csv(COUNTS_BY_LABEL, [{"label": label, "count": count} for label, count in sorted(label_counts.items())], ["label", "count"])
    write_csv(COUNTS_BY_CASE, [{"case_id": case_id, "count": count} for case_id, count in sorted(case_counts.items())], ["case_id", "count"])
    write_summary({**summary, "out": str(out_path)})
    return {**summary, "out": str(out_path), "fields": CANDIDATE_FIELDS}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run first30 deterministic signal-candidate extraction.")
    parser.add_argument("--retrieval-objects", type=Path, default=DEFAULT_RETRIEVAL_OBJECTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(run_extraction(args.retrieval_objects, args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
