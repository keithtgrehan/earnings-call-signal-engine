#!/usr/bin/env python3
"""Validate human gold-label JSONL scaffolds without creating labels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_common import active_case_dirs, enforce_exact_root, enforce_repo_safety, write_csv  # noqa: E402

REQUIRED_FIELDS = {"type", "text_span", "start_char", "end_char"}
ALLOWED_TYPES = {"guidance_revision", "uncertainty", "analyst_pressure", "commitment", "neutral"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    return parser.parse_args()


def validate_row(row: dict[str, Any], *, line_no: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(row))
    if missing:
        errors.append(f"line {line_no}: missing fields {','.join(missing)}")
    if row.get("type") not in ALLOWED_TYPES:
        errors.append(f"line {line_no}: invalid type")
    if row.get("human_label") is not True:
        errors.append(f"line {line_no}: human_label must be true for final gold labels")
    if not str(row.get("text_span", "")).strip():
        errors.append(f"line {line_no}: empty text_span")
    start = row.get("start_char")
    end = row.get("end_char")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
        errors.append(f"line {line_no}: invalid char span")
    return errors


def validate_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"gold_label_path": str(path), "status": "missing", "label_count": 0, "errors": "gold_labels.jsonl missing"}
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {"gold_label_path": str(path), "status": "needs_human_labeling", "label_count": 0, "errors": ""}
    errors: list[str] = []
    count = 0
    for line_no, line in enumerate(lines, start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: JSONL row must be an object")
            continue
        count += 1
        errors.extend(validate_row(row, line_no=line_no))
    return {
        "gold_label_path": str(path),
        "status": "invalid" if errors else "valid",
        "label_count": count,
        "errors": "; ".join(errors),
    }


def render_markdown(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row["status"])] = counts.get(str(row["status"]), 0) + 1
    lines = [
        "# Gold Label Validation",
        "",
        "Gold labels must be human-reviewed. Weak labels are never promoted to gold labels by this tool.",
        "",
    ]
    for status in ("valid", "needs_human_labeling", "missing", "invalid"):
        lines.append(f"- {status}: {counts.get(status, 0)}")
    lines.extend(["", "| case_id | status | labels | errors |", "| --- | --- | ---: | --- |"])
    for row in rows:
        lines.append(f"| {row['case_id']} | {row['status']} | {row['label_count']} | {row['errors']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    rows: list[dict[str, Any]] = []
    for case_dir in active_case_dirs(root):
        path = case_dir / "labels" / "gold_labels.jsonl"
        if not path.exists():
            continue
        rows.append({"case_id": case_dir.name, **validate_file(path)})
    write_csv(root / "gold_label_validation.csv", rows, ["case_id", "gold_label_path", "status", "label_count", "errors"])
    (root / "gold_label_validation.md").write_text(render_markdown(rows), encoding="utf-8")
    invalid = sum(1 for row in rows if row["status"] == "invalid")
    print(f"Gold label validation complete: {len(rows)} scaffold(s), {invalid} invalid, {sum(1 for row in rows if row['status'] == 'needs_human_labeling')} need human labeling.")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
