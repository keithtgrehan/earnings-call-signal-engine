#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import SIGNAL_LABELS, review_decision, write_jsonl  # noqa: E402


def build_gold(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    unclear: list[dict[str, object]] = []
    for row in rows:
        decision = review_decision(row)
        final_label = str(row.get("final_label") or "").strip()
        if decision == "accepted" and final_label in SIGNAL_LABELS:
            accepted.append(
                {
                    "id": row.get("candidate_id", ""),
                    "candidate_id": row.get("candidate_id", ""),
                    "case_id": row.get("case_id", ""),
                    "text": row.get("text", ""),
                    "signal_family": final_label,
                    "label_source": "human_gold_review",
                    "weak_label": row.get("weak_label", ""),
                    "reviewer_notes": row.get("reviewer_notes", ""),
                }
            )
        elif decision == "rejected":
            rejected.append(row)
        elif decision == "unclear":
            unclear.append(row)
    return accepted, rejected, unclear


def write_status(path: Path, *, accepted: int, rejected: int, unclear: int, total: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gold Label Status",
        "",
        f"- reviewed_rows: `{total}`",
        f"- gold_labels: `{accepted}`",
        f"- rejected_rows: `{rejected}`",
        f"- unclear_rows: `{unclear}`",
        "",
        "Only accepted rows with valid final labels are written to `data/gold/gold_labels.jsonl`.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build gold_labels.jsonl from accepted reviewed rows only.")
    parser.add_argument("--reviewed", default=str(ROOT / "data" / "labeling" / "reviewed_labels.csv"))
    parser.add_argument("--out", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--rejected-out", default=str(ROOT / "data" / "gold" / "rejected_labels.jsonl"))
    parser.add_argument("--unclear-out", default=str(ROOT / "data" / "gold" / "unclear_labels.jsonl"))
    parser.add_argument("--status-out", default=str(ROOT / "docs" / "labeling" / "gold_label_status.md"))
    args = parser.parse_args(argv)
    source = Path(args.reviewed)
    rows: list[dict[str, str]] = []
    if source.exists():
        with source.open("r", encoding="utf-8", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
    accepted, rejected, unclear = build_gold(rows)
    write_jsonl(Path(args.out), accepted)
    write_jsonl(Path(args.rejected_out), rejected)
    write_jsonl(Path(args.unclear_out), unclear)
    write_status(Path(args.status_out), accepted=len(accepted), rejected=len(rejected), unclear=len(unclear), total=len(rows))
    print(json.dumps({"gold_labels": len(accepted), "rejected": len(rejected), "unclear": len(unclear)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
