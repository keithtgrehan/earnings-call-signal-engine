#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
import shutil
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]

VALID_LABELS = ("risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral")
REVIEW_COLUMNS = ("review_decision", "final_label", "reviewer", "reviewed_at", "review_notes")
LABEL_DEFINITIONS = {
    "risk_friction": "Real business risk, constraint, pushback, margin/demand/supply/pricing/execution concern.",
    "opportunity_commitment": "Concrete plan, commitment, raised outlook, expansion, or opportunity tied to business impact.",
    "uncertainty_hedging": "Business-relevant uncertainty about demand, supply, pricing, margins, tariffs, timing, or guidance.",
    "neutral": "Factual, admin, or non-signal text useful as a negative example.",
}
DECISION_SHORTCUTS = {
    "a": "accept",
    "accept": "accept",
    "r": "reject",
    "reject": "reject",
    "e": "edit_label",
    "edit": "edit_label",
    "edit_label": "edit_label",
    "u": "unclear",
    "unclear": "unclear",
    "s": "skip",
    "skip": "skip",
    "q": "quit",
    "quit": "quit",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
        return rows, list(reader.fieldnames or [])


def occurrence_keys(rows: list[dict[str, str]]) -> list[tuple[str, int]]:
    counts: defaultdict[str, int] = defaultdict(int)
    keys: list[tuple[str, int]] = []
    for index, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or f"__row_{index}")
        occurrence = counts[candidate_id]
        counts[candidate_id] += 1
        keys.append((candidate_id, occurrence))
    return keys


def merge_existing_reviews(input_rows: list[dict[str, str]], existing_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    existing_by_key = dict(zip(occurrence_keys(existing_rows), existing_rows, strict=False))
    merged: list[dict[str, str]] = []
    for key, row in zip(occurrence_keys(input_rows), input_rows, strict=True):
        item = dict(row)
        existing = existing_by_key.get(key, {})
        for column in REVIEW_COLUMNS:
            item[column] = str(existing.get(column) or row.get(column) or "")
        merged.append(item)
    return merged


def fieldnames_for(input_fields: list[str], output_fields: list[str] | None = None) -> list[str]:
    fields: list[str] = []
    for field in [*input_fields, *(output_fields or []), *REVIEW_COLUMNS]:
        if field and field not in fields:
            fields.append(field)
    return fields


def load_review_state(input_path: Path, output_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    input_rows, input_fields = read_csv(input_path)
    output_fields: list[str] = []
    if output_path.exists():
        existing_rows, output_fields = read_csv(output_path)
        rows = merge_existing_reviews(input_rows, existing_rows)
    else:
        rows = []
        for row in input_rows:
            item = dict(row)
            for column in REVIEW_COLUMNS:
                item.setdefault(column, "")
            rows.append(item)
    return rows, fieldnames_for(input_fields, output_fields)


def backup_existing(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.bak")
    shutil.copy2(path, backup)
    return backup


def write_review_state(path: Path, rows: list[dict[str, str]], fieldnames: list[str], *, backup: bool = True) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = backup_existing(path) if backup else None
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return backup_path


def is_unreviewed(row: dict[str, str]) -> bool:
    return not str(row.get("review_decision") or "").strip()


def counts_for(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        decision = str(row.get("review_decision") or "").strip().lower()
        if decision:
            counts[decision] += 1
        else:
            counts["unreviewed"] += 1
    return counts


def print_summary(rows: list[dict[str, str]], *, input_path: Path, output_path: Path) -> None:
    counts = counts_for(rows)
    print(f"input: {input_path}")
    print(f"output: {output_path}")
    print(f"total rows: {len(rows)}")
    print(f"accepted: {counts['accept']}")
    print(f"edited: {counts['edit_label']}")
    print(f"rejected: {counts['reject']}")
    print(f"unclear: {counts['unclear']}")
    print(f"skipped: {counts['skip']}")
    print(f"unreviewed: {counts['unreviewed']}")


def print_label_definitions() -> None:
    print("Labels:")
    for label in VALID_LABELS:
        print(f"  {label}: {LABEL_DEFINITIONS[label]}")


def render_row(row: dict[str, str], *, index: int, total: int) -> None:
    print("\n" + "=" * 80)
    print(f"Row {index + 1} / {total}")
    print(f"candidate_id: {row.get('candidate_id', '')}")
    print(f"case_id: {row.get('case_id', '')}")
    print(f"weak_label: {row.get('weak_label', '')}")
    print(f"confidence: {row.get('confidence', '')}")
    noise = str(row.get("noise_flag") or row.get("noise_flags") or "").strip()
    if noise:
        print(f"noise_flag: {noise}")
    priority = str(row.get("priority_score") or "").strip()
    if priority:
        print(f"priority_score: {priority}")
    selection_reason = str(row.get("selection_reason") or row.get("priority_reason") or "").strip()
    if selection_reason:
        print(f"selection_reason: {selection_reason}")
    print("\nText:")
    print(str(row.get("text") or "").strip())
    print()
    print_label_definitions()
    print("\nChoose: [a]ccept weak label, [r]eject/no signal, [e]dit label, [u]nclear, [s]kip, [q]uit/save")


def prompt_label(input_func: Callable[[str], str]) -> str:
    print("Valid labels:")
    for index, label in enumerate(VALID_LABELS, start=1):
        print(f"  {index}. {label}")
    while True:
        choice = input_func("Final label: ").strip()
        if choice.isdigit():
            position = int(choice)
            if 1 <= position <= len(VALID_LABELS):
                return VALID_LABELS[position - 1]
        if choice in VALID_LABELS:
            return choice
        print("Invalid label. Choose one of the listed labels.")


def apply_decision(row: dict[str, str], *, decision: str, reviewer: str, input_func: Callable[[str], str]) -> bool:
    if decision == "accept":
        weak_label = str(row.get("weak_label") or "").strip()
        if weak_label not in VALID_LABELS:
            print("The weak label is missing or invalid. Use edit_label, reject, unclear, or skip.")
            return False
        final_label = weak_label
    elif decision == "edit_label":
        final_label = prompt_label(input_func)
    else:
        final_label = ""

    row["review_decision"] = decision
    row["final_label"] = final_label
    row["reviewer"] = reviewer
    row["reviewed_at"] = utc_now()
    if decision != "skip":
        row["review_notes"] = input_func("Notes (optional, Enter to leave blank): ").strip()
    else:
        row["review_notes"] = ""
    return True


def review_rows(
    rows: list[dict[str, str]],
    *,
    reviewer: str,
    input_func: Callable[[str], str] = input,
) -> None:
    start_index = next((index for index, row in enumerate(rows) if is_unreviewed(row)), len(rows))
    index = start_index
    while index < len(rows):
        row = rows[index]
        render_row(row, index=index, total=len(rows))
        raw_choice = input_func("Decision: ").strip().lower()
        decision = DECISION_SHORTCUTS.get(raw_choice)
        if not decision:
            print("Unknown choice. Use a, r, e, u, s, or q.")
            continue
        if decision == "quit":
            print("Saved progress through the last completed row.")
            break
        if apply_decision(row, decision=decision, reviewer=reviewer, input_func=input_func):
            index += 1
    if index >= len(rows):
        print("Review batch complete.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guided CLI for reviewing the next first-50 gold-label batch.")
    parser.add_argument("--input", default=str(ROOT / "data" / "labeling" / "next_review_batch.csv"))
    parser.add_argument("--output", default=str(ROOT / "data" / "labeling" / "reviewed_next_batch.csv"))
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--summary", action="store_true", help="Print a read-only review status summary and exit.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    rows, fieldnames = load_review_state(input_path, output_path)

    if args.summary:
        print_summary(rows, input_path=input_path, output_path=output_path)
        return 0

    reviewer = str(args.reviewer or "").strip() or input("Reviewer name: ").strip() or "unknown"
    review_rows(rows, reviewer=reviewer)
    backup_path = write_review_state(output_path, rows, fieldnames)
    print(f"wrote: {output_path}")
    if backup_path:
        print(f"backup: {backup_path}")
    print_summary(rows, input_path=input_path, output_path=output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
