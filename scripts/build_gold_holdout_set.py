#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation_backbone import write_jsonl
from signal_engine.signal_baseline import HUMAN_REVIEWED_LABELS_RELATIVE_PATH, SIGNAL_FAMILY_LABELS, load_supervised_examples


def _obvious_pii(text: str) -> bool:
    lowered = text.lower()
    return "@" in lowered or "http" in lowered


def _quality_score(row: dict[str, Any]) -> tuple[int, int, int, str]:
    evidence_count = len(list(row.get("evidence_terms") or []))
    rationale_bonus = 2 if row.get("rationale") else 0
    readability_bonus = 2 if 6 <= len(str(row["text"]).split()) <= 28 else 0
    pii_bonus = 0 if _obvious_pii(str(row["text"])) else 2
    return (evidence_count + rationale_bonus + readability_bonus + pii_bonus, -len(str(row["text"]).split()), evidence_count, str(row["id"]))


def build_gold_holdout_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for label in SIGNAL_FAMILY_LABELS:
        candidates = [row for row in rows if row["signal_family"] == label]
        ranked = sorted(candidates, key=_quality_score, reverse=True)
        for row in ranked[:4]:
            selected.append(
                {
                    "id": f"gold_candidate_{row['id']}",
                    "source_label_id": row["id"],
                    "text": row["text"],
                    "signal_family": row["signal_family"],
                    "selection_reason": "Selected for readable length, explicit evidence terms, and low-Pii review suitability.",
                    "gold_status": "candidate_pending_second_review",
                    "locked_for_training": True,
                    "domain": row.get("domain"),
                    "source_file": row.get("source_file"),
                }
            )
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build candidate locked holdout rows from the seeded label set.")
    parser.add_argument("--input-path", default=str(ROOT / HUMAN_REVIEWED_LABELS_RELATIVE_PATH))
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "nlp_research" / "gold_holdout_candidates.jsonl"),
    )
    args = parser.parse_args(argv)

    rows = load_supervised_examples(Path(args.input_path))
    candidates = build_gold_holdout_candidates(rows)
    write_jsonl(Path(args.out), candidates)
    print(json.dumps({"status": "ok", "candidate_count": len(candidates), "out": args.out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
