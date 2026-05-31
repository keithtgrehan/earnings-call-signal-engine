#!/usr/bin/env python3
"""Build a copy-safe first100 manual review accelerator spreadsheet."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_first100_weak_model_assist import DEFAULT_CANDIDATES, DEFAULT_OUT as DEFAULT_WEAK_ASSIST, build_weak_model_assist  # noqa: E402

DEFAULT_OUT = ROOT / "reports" / "review" / "first100_review_accelerator.csv"

SPREADSHEET_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "fiscal_period",
    "existing_suggested_label",
    "weak_model_suggested_label",
    "weak_model_confidence",
    "disagreement_flag",
    "review_priority",
    "packet_file",
    "your_label",
    "rationale",
    "done",
]
PACKET_BY_LABEL = {
    "guidance_revision": "data/review/packets/first100_batch_001_guidance.md",
    "guidance_statement": "data/review/packets/first100_batch_001_guidance.md",
    "analyst_pressure": "data/review/packets/first100_batch_002_qa_friction.md",
    "management_hedging": "data/review/packets/first100_batch_003_hedging_uncertainty.md",
    "uncertainty": "data/review/packets/first100_batch_003_hedging_uncertainty.md",
    "reassurance": "data/review/packets/first100_batch_004_reassurance_answer_shift.md",
    "answer_shift": "data/review/packets/first100_batch_004_reassurance_answer_shift.md",
    "neutral/no_signal": "data/review/packets/first100_batch_005_neutral_suppression.md",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SPREADSHEET_FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _packet_file(label: str) -> str:
    return PACKET_BY_LABEL.get(label, "")


def build_review_spreadsheet(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES,
    weak_assist_csv: Path = DEFAULT_WEAK_ASSIST,
    out_csv: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    if not weak_assist_csv.exists():
        build_weak_model_assist(candidates_path=candidates_path, out_csv=weak_assist_csv)
    candidate_ids = {str(row.get("candidate_id", "")) for row in read_jsonl(candidates_path)}
    rows: list[dict[str, str]] = []
    for assist in _read_csv(weak_assist_csv):
        if candidate_ids and assist.get("candidate_id") not in candidate_ids:
            continue
        existing_label = assist.get("existing_suggested_label", "")
        rows.append(
            {
                "candidate_id": assist.get("candidate_id", ""),
                "case_id": assist.get("case_id", ""),
                "ticker": assist.get("ticker", ""),
                "fiscal_period": assist.get("fiscal_period", ""),
                "existing_suggested_label": existing_label,
                "weak_model_suggested_label": assist.get("weak_model_suggested_label", ""),
                "weak_model_confidence": assist.get("weak_model_confidence", ""),
                "disagreement_flag": assist.get("disagreement_flag", ""),
                "review_priority": assist.get("review_priority", ""),
                "packet_file": _packet_file(existing_label),
                "your_label": "",
                "rationale": "",
                "done": "",
            }
        )
    _write_csv(out_csv, rows)
    return {
        "rows": len(rows),
        "out_csv": str(out_csv),
        "raw_text_included": False,
        "final_adjudication_automated": False,
        "gold_labels_created": 0,
        "training_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first100 manual review accelerator spreadsheet.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--weak-assist", type=Path, default=DEFAULT_WEAK_ASSIST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    summary = build_review_spreadsheet(candidates_path=args.candidates, weak_assist_csv=args.weak_assist, out_csv=args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
