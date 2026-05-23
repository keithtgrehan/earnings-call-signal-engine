#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

LABEL_BUCKETS = [
    ("guidance_revision", 5),
    ("analyst_pressure", 5),
    ("management_hedging", 3),
    ("uncertainty", 2),
    ("reassurance", 3),
    ("answer_shift", 2),
    ("hard_negative", 5),
    ("ambiguous_needs_adjudication", 5),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build 30-row calibration batch scaffold.")
    parser.add_argument("--out", default="data/review/staging/calibration_batch_001.jsonl")
    parser.add_argument("--report", default="reports/review/calibration_batch_001_summary.md")
    args = parser.parse_args(argv)
    rows = []
    for label, count in LABEL_BUCKETS:
        for item in range(count):
            rows.append(
                {
                    "candidate_id": f"calibration_{label}_{item + 1:02d}",
                    "bucket": label,
                    "suggested_label": label if label not in {"hard_negative", "ambiguous_needs_adjudication"} else "neutral/no_signal",
                    "machine_candidate_only": True,
                    "gold_status": "not_gold",
                    "review_status": "pending_human_review",
                    "final_label": "",
                    "reviewer": "",
                    "adjudicator": "",
                }
            )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f"# Calibration Batch 001 Summary\n\n- Rows: `{len(rows)}`\n- Canonical gold labels written: `0`\n", encoding="utf-8")
    print(f"Calibration batch written: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
