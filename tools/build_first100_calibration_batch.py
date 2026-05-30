#!/usr/bin/env python3
"""Build a metadata-only first100 calibration batch for human adjudication."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
DEFAULT_OUT = ROOT / "data" / "review" / "staging" / "first100_calibration_batch_001.jsonl"
SUMMARY_REPORT = ROOT / "reports" / "review" / "first100_calibration_batch_summary.md"

BUCKETS = [
    ("guidance", {"guidance_revision", "guidance_statement"}, 5),
    ("analyst_pressure", {"analyst_pressure"}, 5),
    ("hedging_uncertainty", {"management_hedging", "uncertainty"}, 5),
    ("reassurance_answer_shift", {"reassurance", "answer_shift"}, 5),
    ("neutral_hard_negative", {"neutral/no_signal"}, 5),
    ("ambiguous_needs_adjudication", set(), 5),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _confidence(row: dict[str, Any]) -> float:
    try:
        return float(row.get("suggested_confidence", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _calibration_row(row: dict[str, Any], bucket: str) -> dict[str, Any]:
    allowed = {
        "candidate_id",
        "case_id",
        "ticker",
        "fiscal_period",
        "suggested_label",
        "suggested_confidence",
        "evidence_object_id",
        "chunk_id",
        "retrieval_object_id",
        "source_path",
        "source_sha256",
        "normalized_transcript_hash",
        "text_hash",
        "provenance_hash",
        "speaker_role",
        "transcript_section",
        "rule_id",
        "rule_version",
        "contamination_flags",
        "gold_status",
        "review_status",
        "raw_text_committed",
    }
    output = {key: row.get(key, "") for key in sorted(allowed)}
    output.update(
        {
            "calibration_bucket": bucket,
            "final_label": "",
            "reviewer": "",
            "rationale": "",
            "adjudicator": "",
            "adjudicated_at": "",
        }
    )
    return output


def build_calibration_batch(candidates_path: Path = DEFAULT_CANDIDATES, out_path: Path = DEFAULT_OUT) -> dict[str, Any]:
    candidates = read_jsonl(candidates_path)
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    shortages: dict[str, int] = {}
    for bucket, labels, target in BUCKETS:
        if labels:
            pool = [row for row in candidates if row.get("suggested_label") in labels and row.get("candidate_id") not in used]
            pool.sort(key=lambda row: (row.get("case_id", ""), -_confidence(row), row.get("candidate_id", "")))
        else:
            pool = [row for row in candidates if row.get("candidate_id") not in used]
            pool.sort(key=lambda row: (abs(_confidence(row) - 0.50), row.get("case_id", ""), row.get("candidate_id", "")))
        chosen = pool[:target]
        if len(chosen) < target:
            shortages[bucket] = target - len(chosen)
        for row in chosen:
            used.add(row.get("candidate_id", ""))
            selected.append(_calibration_row(row, bucket))
    write_jsonl(out_path, selected)
    summary = {
        "calibration_rows": len(selected),
        "target_rows": sum(target for _, _, target in BUCKETS),
        "bucket_counts": dict(sorted(Counter(row["calibration_bucket"] for row in selected).items())),
        "shortages": shortages,
        "gold_labels_created": 0,
        "promoted_to_gold": 0,
        "raw_text_included": False,
        "out": str(out_path),
    }
    write_summary(summary)
    return summary


def write_summary(summary: dict[str, Any], out_path: Path | None = None) -> None:
    out_path = out_path or SUMMARY_REPORT
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Calibration Batch Summary",
        "",
        f"- Calibration rows: {summary['calibration_rows']}",
        f"- Target rows: {summary['target_rows']}",
        f"- Bucket counts: `{json.dumps(summary['bucket_counts'], sort_keys=True)}`",
        f"- Shortages: `{json.dumps(summary['shortages'], sort_keys=True)}`",
        "- Gold labels created: 0",
        "- Promoted to gold: 0",
        "- Raw evidence text included: false",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first100 calibration batch.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(build_calibration_batch(args.candidates, args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
