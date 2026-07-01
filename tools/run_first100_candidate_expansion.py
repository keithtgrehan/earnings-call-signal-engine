#!/usr/bin/env python3
"""Expand deterministic metadata-only candidates for first100 human review."""

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

from signal_engine.first30_extraction import (  # noqa: E402
    FIRST100_CANDIDATE_FIELDS,
    expand_first100_candidates_from_retrieval_objects,
)

DEFAULT_RETRIEVAL_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_FIRST30_CANDIDATES = ROOT / "data" / "review" / "staging" / "first30_signal_candidates.jsonl"
DEFAULT_OUT = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
PREFLIGHT_REPORT = ROOT / "reports" / "review" / "first100_candidate_expansion_preflight.md"
SUMMARY_REPORT = ROOT / "reports" / "extraction" / "first100_candidate_expansion_summary.md"
COUNTS_BY_LABEL = ROOT / "reports" / "extraction" / "first100_signal_counts_by_label.csv"
COUNTS_BY_CASE = ROOT / "reports" / "extraction" / "first100_signal_counts_by_case.csv"
SUPPRESSION_REPORT = ROOT / "reports" / "extraction" / "first100_false_positive_suppression.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _first30_label(row: dict[str, Any]) -> str:
    return str(row.get("label") or row.get("suggested_label") or "")


def write_preflight(
    *,
    retrieval_rows: list[dict[str, str]],
    first30_candidates: list[dict[str, Any]],
    out_path: Path = PREFLIGHT_REPORT,
) -> dict[str, Any]:
    retrieval_ids = {row.get("object_id", "") for row in retrieval_rows if row.get("object_id")}
    used_ids = {str(row.get("retrieval_object_id", "")) for row in first30_candidates if row.get("retrieval_object_id")}
    case_ids = {row.get("case_id", "") for row in retrieval_rows if row.get("case_id")}
    first30_cases = {str(row.get("case_id", "")) for row in first30_candidates if row.get("case_id")}
    packet_count = len(list((ROOT / "data" / "review" / "packets").glob("first30_batch_*.md")))
    label_counts = Counter(_first30_label(row) for row in first30_candidates)
    case_counts = Counter(str(row.get("case_id", "")) for row in first30_candidates if row.get("case_id"))
    underrepresented = {label: 5 - count for label, count in label_counts.items() if count < 5}
    no_candidate_cases = sorted(case_ids - first30_cases)
    summary = {
        "current_candidates": len(first30_candidates),
        "current_candidates_by_label": dict(sorted(label_counts.items())),
        "current_candidates_by_case": dict(sorted(case_counts.items())),
        "current_review_packets": packet_count,
        "labels_underrepresented": dict(sorted(underrepresented.items())),
        "cases_with_no_candidates": no_candidate_cases,
        "retrieval_objects_available": len(retrieval_rows),
        "retrieval_objects_not_used_for_first30_candidates": len(retrieval_ids - used_ids),
        "evidence_objects_available": sum(1 for row in retrieval_rows if row.get("object_type") == "evidence_object"),
        "event_chunks_available": sum(1 for row in retrieval_rows if row.get("object_type") == "event_aligned_chunk"),
        "semantic_fallback_available": sum(1 for row in retrieval_rows if row.get("object_type") == "semantic_chunk"),
        "review_readiness": "needs_first100_candidate_expansion",
        "training_blockers": [
            "0 valid adjudicated labels in current workflow",
            "candidate labels are not gold",
            "explicit training rights are not configured",
            "no training performed",
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Candidate Expansion Preflight",
        "",
        f"- Current first30 candidates: {summary['current_candidates']}",
        f"- Current first30 candidates by label: `{json.dumps(summary['current_candidates_by_label'], sort_keys=True)}`",
        f"- Current review packets: {summary['current_review_packets']}",
        f"- Retrieval objects available: {summary['retrieval_objects_available']}",
        f"- Evidence objects available: {summary['evidence_objects_available']}",
        f"- Event-aligned chunks available: {summary['event_chunks_available']}",
        f"- Semantic fallback chunks available: {summary['semantic_fallback_available']}",
        f"- Retrieval objects not yet used for first30 candidates: {summary['retrieval_objects_not_used_for_first30_candidates']}",
        f"- Labels underrepresented: `{json.dumps(summary['labels_underrepresented'], sort_keys=True)}`",
        f"- Cases with no first30 candidates: {len(summary['cases_with_no_candidates'])}",
        "- Review readiness: needs_first100_candidate_expansion",
        "- Training readiness: NOT_READY",
        "",
        "## Training Blockers",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in summary["training_blockers"])
    lines.extend(["", "## Cases With No Current Candidates", ""])
    lines.extend(f"- `{case_id}`" for case_id in no_candidate_cases) if no_candidate_cases else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def write_summary(summary: dict[str, Any], out_path: Path = SUMMARY_REPORT) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Candidate Expansion Summary",
        "",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Target count: {summary['target_count']}",
        f"- Target met: {str(summary['target_met']).lower()}",
        f"- Cases with candidates: {summary['cases']}",
        f"- Label counts: `{json.dumps(summary['labels'], sort_keys=True)}`",
        f"- Object counts: `{json.dumps(summary['object_counts'], sort_keys=True)}`",
        f"- Suppressed rows: `{json.dumps(summary['suppressed'], sort_keys=True)}`",
        f"- Underrepresented labels: `{json.dumps(summary['underrepresented_labels'], sort_keys=True)}`",
        "- Deterministic candidates only: true",
        "- Gold labels created: 0",
        "- Review status: pending_human_review",
        "- Raw evidence text committed: false",
        "- Training performed: false",
        "",
        "## Blockers",
        "",
    ]
    blockers = summary.get("blockers") or []
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_expansion(
    retrieval_objects: Path = DEFAULT_RETRIEVAL_OBJECTS,
    first30_candidates_path: Path = DEFAULT_FIRST30_CANDIDATES,
    out_path: Path = DEFAULT_OUT,
    target_count: int = 100,
) -> dict[str, Any]:
    retrieval_rows = read_csv(retrieval_objects)
    first30_candidates = read_jsonl(first30_candidates_path)
    preflight = write_preflight(retrieval_rows=retrieval_rows, first30_candidates=first30_candidates)
    candidates, summary, suppressions = expand_first100_candidates_from_retrieval_objects(retrieval_rows, target_count=target_count)
    write_jsonl(out_path, candidates)
    label_counts = Counter(row["suggested_label"] for row in candidates)
    case_counts = Counter(row["case_id"] for row in candidates)
    write_csv(COUNTS_BY_LABEL, [{"label": label, "count": count} for label, count in sorted(label_counts.items())], ["label", "count"])
    write_csv(COUNTS_BY_CASE, [{"case_id": case_id, "count": count} for case_id, count in sorted(case_counts.items())], ["case_id", "count"])
    write_csv(SUPPRESSION_REPORT, suppressions, ["object_id", "case_id", "ticker", "reason", "object_type"])
    write_summary(summary)
    return {**summary, "out": str(out_path), "fields": FIRST100_CANDIDATE_FIELDS, "preflight": preflight}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run first100 deterministic candidate expansion.")
    parser.add_argument("--retrieval-objects", type=Path, default=DEFAULT_RETRIEVAL_OBJECTS)
    parser.add_argument("--first30-candidates", type=Path, default=DEFAULT_FIRST30_CANDIDATES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--target-count", type=int, default=100)
    args = parser.parse_args(argv)
    summary = run_expansion(args.retrieval_objects, args.first30_candidates, args.out, args.target_count)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
