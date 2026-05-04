#!/usr/bin/env python3
"""Apply selected packet candidate IDs into draft or human-approved label JSONL."""

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
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
LABEL_STATUS_OUTPUT = {
    "draft_reviewed": "draft_gold_labels.jsonl",
    "human_approved": "gold_labels.jsonl",
}
LABEL_STATUS_REVIEWER = {
    "draft_reviewed": "assistant_draft",
    "human_approved": "Keith",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--selected-csv", required=True, help="CSV with case_id,candidate_id,type,confidence,notes")
    parser.add_argument("--label-status", choices=sorted(LABEL_STATUS_OUTPUT), default="human_approved")
    parser.add_argument("--reviewer", default=None)
    parser.add_argument(
        "--overwrite-human-approved",
        action="store_true",
        help="Allow replacing a non-empty gold_labels.jsonl when --label-status human_approved is used.",
    )
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


def validate_selected_row(row: dict[str, str]) -> None:
    label_type = row["type"].strip()
    confidence = row["confidence"].strip()
    candidate_id = row["candidate_id"].strip()
    if label_type not in ALLOWED_TYPES:
        raise SystemExit(f"invalid type for {candidate_id}: {label_type}")
    if confidence not in ALLOWED_CONFIDENCE:
        raise SystemExit(f"invalid confidence for {candidate_id}: {confidence}")


def group_selected(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_case: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        validate_selected_row(row)
        by_case.setdefault(row["case_id"].strip(), []).append(row)
    return by_case


def build_labels_for_case(
    root: Path,
    case_id: str,
    rows: list[dict[str, str]],
    *,
    label_status: str,
    reviewer: str | None = None,
) -> list[dict[str, Any]]:
    if label_status not in LABEL_STATUS_OUTPUT:
        raise SystemExit(f"invalid label status: {label_status}")
    case_dir = root / case_id
    packet = case_dir / "labels" / "human_labeling_packet.md"
    raw = case_dir / "raw" / "transcript.txt"
    if not packet.exists():
        raise SystemExit(f"packet missing for {case_id}: {packet}")
    if not raw.exists():
        raise SystemExit(f"raw transcript missing for {case_id}: {raw}")

    candidates = parse_packet(packet)
    raw_text = raw.read_text(encoding="utf-8", errors="replace")
    effective_reviewer = reviewer or LABEL_STATUS_REVIEWER[label_status]
    is_human_approved = label_status == "human_approved"
    labels: list[dict[str, Any]] = []
    for row in rows:
        validate_selected_row(row)
        row_case_id = row["case_id"].strip()
        if row_case_id != case_id:
            raise SystemExit(f"row case_id {row_case_id} does not match target case {case_id}")
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
                "human_label": is_human_approved,
                "confidence": row["confidence"].strip(),
                "reviewer": effective_reviewer,
                "notes": row.get("notes", "").strip(),
                "candidate_id": candidate_id,
                "label_status": label_status,
                "needs_human_approval": not is_human_approved,
            }
        )
    return labels


def output_path_for(case_dir: Path, label_status: str) -> Path:
    if label_status not in LABEL_STATUS_OUTPUT:
        raise SystemExit(f"invalid label status: {label_status}")
    return case_dir / "labels" / LABEL_STATUS_OUTPUT[label_status]


def write_labels_for_case(
    case_dir: Path,
    labels: list[dict[str, Any]],
    *,
    label_status: str,
    overwrite_human_approved: bool = False,
) -> Path:
    out = output_path_for(case_dir, label_status)
    if label_status == "human_approved" and out.exists() and out.read_text(encoding="utf-8").strip():
        if not overwrite_human_approved:
            raise SystemExit(
                f"refusing to overwrite existing human-approved labels: {out} "
                "(pass --overwrite-human-approved to replace intentionally)"
            )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(label, ensure_ascii=False) + "\n" for label in labels), encoding="utf-8")
    return out


def apply_selected_rows(
    root: Path,
    rows: list[dict[str, str]],
    *,
    label_status: str,
    reviewer: str | None = None,
    overwrite_human_approved: bool = False,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for case_id, case_rows in group_selected(rows).items():
        case_dir = root / case_id
        labels = build_labels_for_case(root, case_id, case_rows, label_status=label_status, reviewer=reviewer)
        out = write_labels_for_case(
            case_dir,
            labels,
            label_status=label_status,
            overwrite_human_approved=overwrite_human_approved,
        )
        reports.append({"case_id": case_id, "label_count": len(labels), "output_path": str(out), "status": "written"})
    return reports


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    selected = load_selected(Path(args.selected_csv))
    reports = apply_selected_rows(
        root,
        selected,
        label_status=args.label_status,
        reviewer=args.reviewer,
        overwrite_human_approved=args.overwrite_human_approved,
    )
    for report in reports:
        print(f"Wrote {report['label_count']} {args.label_status} label(s): {report['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
