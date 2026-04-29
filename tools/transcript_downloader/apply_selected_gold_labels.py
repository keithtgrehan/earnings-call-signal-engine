#!/usr/bin/env python3
"""Apply human-approved packet candidate IDs into gold_labels.jsonl."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_common import enforce_exact_root, enforce_repo_safety  # noqa: E402

ALLOWED_TYPES = {"guidance_revision", "analyst_pressure", "uncertainty", "commitment", "neutral"}
ALLOWED_CONFIDENCE = {"high", "medium"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--selected-csv", required=True, help="CSV with case_id,candidate_id,type,confidence,notes")
    parser.add_argument("--reviewer", default="Keith")
    return parser.parse_args()


def parse_packet(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    candidates: dict[str, str] = {}
    pattern = re.compile(r"- candidate_id: `(?P<id>[^`]+)`.*?```text\n(?P<quote>.*?)\n```", re.S)
    for match in pattern.finditer(text):
        quote = re.sub(r"\s+", " ", match.group("quote")).strip()
        candidates[match.group("id")] = quote
    return candidates


def find_quote_span(raw_text: str, quote: str) -> tuple[int, int]:
    exact = raw_text.find(quote)
    if exact >= 0:
        return exact, exact + len(quote)
    normalized_raw = re.sub(r"\s+", " ", raw_text)
    normalized_quote = re.sub(r"\s+", " ", quote).strip()
    idx = normalized_raw.find(normalized_quote)
    if idx < 0:
        raise ValueError("exact quote not found in raw transcript")
    # Map normalized index back by scanning raw text without changing raw content.
    raw_cursor = 0
    norm_cursor = 0
    start = None
    end = None
    while raw_cursor < len(raw_text):
        char = raw_text[raw_cursor]
        token = " " if char.isspace() else char
        if norm_cursor == idx and start is None:
            start = raw_cursor
        if norm_cursor >= idx + len(normalized_quote):
            end = raw_cursor
            break
        raw_cursor += 1
        if token == " ":
            while raw_cursor < len(raw_text) and raw_text[raw_cursor].isspace():
                raw_cursor += 1
            norm_cursor += 1
        else:
            norm_cursor += 1
    if start is None:
        raise ValueError("quote span mapping failed")
    return start, end or raw_cursor


def load_selected(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"case_id", "candidate_id", "type", "confidence", "notes"}
    if not rows:
        raise SystemExit("selected CSV has no rows")
    missing = required - set(rows[0])
    if missing:
        raise SystemExit(f"selected CSV missing column(s): {', '.join(sorted(missing))}")
    return rows


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    selected = load_selected(Path(args.selected_csv))
    by_case: dict[str, list[dict[str, str]]] = {}
    for row in selected:
        label_type = row["type"].strip()
        confidence = row["confidence"].strip()
        if label_type not in ALLOWED_TYPES:
            raise SystemExit(f"invalid type for {row['candidate_id']}: {label_type}")
        if confidence not in ALLOWED_CONFIDENCE:
            raise SystemExit(f"invalid confidence for {row['candidate_id']}: {confidence}")
        by_case.setdefault(row["case_id"].strip(), []).append(row)

    for case_id, rows in by_case.items():
        case_dir = root / case_id
        packet = case_dir / "labels" / "human_labeling_packet.md"
        raw = case_dir / "raw" / "transcript.txt"
        if not packet.exists():
            raise SystemExit(f"packet missing for {case_id}: {packet}")
        if not raw.exists():
            raise SystemExit(f"raw transcript missing for {case_id}: {raw}")
        candidates = parse_packet(packet)
        raw_text = raw.read_text(encoding="utf-8", errors="replace")
        labels: list[dict[str, Any]] = []
        for row in rows:
            candidate_id = row["candidate_id"].strip()
            if candidate_id not in candidates:
                raise SystemExit(f"unknown candidate_id for {case_id}: {candidate_id}")
            quote = candidates[candidate_id]
            start, end = find_quote_span(raw_text, quote)
            labels.append(
                {
                    "type": row["type"].strip(),
                    "text_span": quote,
                    "start_char": start,
                    "end_char": end,
                    "human_label": True,
                    "confidence": row["confidence"].strip(),
                    "reviewer": args.reviewer,
                    "notes": row.get("notes", "").strip(),
                    "candidate_id": candidate_id,
                }
            )
        out = case_dir / "labels" / "gold_labels.jsonl"
        out.write_text("".join(json.dumps(label, ensure_ascii=False) + "\n" for label in labels), encoding="utf-8")
        print(f"Wrote {len(labels)} gold label(s): {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
