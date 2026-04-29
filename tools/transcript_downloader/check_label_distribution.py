#!/usr/bin/env python3
"""Report conservative gold/weak label distribution checks."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_common import active_case_dirs, enforce_exact_root, enforce_repo_safety, write_csv  # noqa: E402

LABELS = ("guidance_revision", "analyst_pressure", "uncertainty", "commitment", "neutral")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--target-label-count", type=int, default=15)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def count_by_type(rows: list[dict[str, Any]], key: str = "type") -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = str(row.get(key, ""))
        if value:
            counts[value] += 1
    return counts


def warnings_for(case_id: str, gold_rows: list[dict[str, Any]], weak_rows: list[dict[str, Any]], target: int) -> list[str]:
    warnings: list[str] = []
    gold_counts = count_by_type(gold_rows)
    weak_counts = count_by_type(weak_rows)
    total_gold = len(gold_rows)
    if total_gold and gold_counts.get("uncertainty", 0) / total_gold > 0.5:
        warnings.append("uncertainty labels exceed 50% of labeled case")
    if total_gold and gold_counts.get("neutral", 0) == 0:
        warnings.append("neutral labels missing")
    if total_gold and gold_counts.get("analyst_pressure", 0) < 3:
        warnings.append("fewer than 3 analyst_pressure labels in labeled case")
    if total_gold and total_gold < 10:
        warnings.append("fewer than 10 total labels in labeled case")
    if total_gold and total_gold < target:
        warnings.append(f"fewer than target label count ({target})")
    if any(re.search(r"\b(forward-looking|actual results may differ|may disconnect|operator)\b", str(row.get("text_span", "")), re.I) for row in gold_rows):
        warnings.append("legal/operator boilerplate appears in gold labels")
    if total_gold:
        top_label, top_count = gold_counts.most_common(1)[0]
        if top_count / total_gold > 0.6:
            warnings.append(f"one label type dominates labeled case: {top_label}")
    if not total_gold and weak_counts:
        warnings.append("weak labels exist but no gold labels")
    return warnings


def render_markdown(rows: list[dict[str, Any]]) -> str:
    gold_total = sum(int(row["gold_total"]) for row in rows)
    labeled_cases = sum(1 for row in rows if int(row["gold_total"]) > 0)
    warning_total = sum(1 for row in rows if row["warnings"])
    global_counts: Counter[str] = Counter()
    for row in rows:
        for label in LABELS:
            global_counts[label] += int(row[f"gold_{label}"])
    lines = [
        "# Label Distribution Report",
        "",
        "Conservative distribution checks for human gold labels and deterministic weak labels.",
        "",
        f"- labeled_cases: {labeled_cases}",
        f"- total_gold_labels: {gold_total}",
        f"- cases_with_warnings: {warning_total}",
        "",
        "## Gold Counts By Type",
        "",
    ]
    for label in LABELS:
        lines.append(f"- {label}: {global_counts[label]}")
    lines.extend(["", "| case_id | gold_total | weak_total | warnings |", "| --- | ---: | ---: | --- |"])
    for row in rows:
        lines.append(f"| {row['case_id']} | {row['gold_total']} | {row['weak_total']} | {row['warnings']} |")
    lines.extend(
        [
            "",
            "These checks do not imply model performance. They identify benchmark coverage gaps before interpreting weak-vs-gold comparisons.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    rows: list[dict[str, Any]] = []
    for case_dir in active_case_dirs(root):
        gold_rows = load_jsonl(case_dir / "labels" / "gold_labels.jsonl")
        weak_rows = load_jsonl(case_dir / "labels" / "weak_labels.jsonl")
        gold_counts = count_by_type(gold_rows)
        weak_counts = count_by_type(weak_rows)
        row: dict[str, Any] = {
            "case_id": case_dir.name,
            "gold_total": len(gold_rows),
            "weak_total": len(weak_rows),
            "warnings": "; ".join(warnings_for(case_dir.name, gold_rows, weak_rows, args.target_label_count)),
        }
        for label in LABELS:
            row[f"gold_{label}"] = gold_counts[label]
            row[f"weak_{label}"] = weak_counts[label]
        rows.append(row)
    fieldnames = ["case_id", "gold_total", "weak_total", *[f"gold_{label}" for label in LABELS], *[f"weak_{label}" for label in LABELS], "warnings"]
    write_csv(root / "label_distribution_report.csv", rows, fieldnames)
    (root / "label_distribution_report.md").write_text(render_markdown(rows), encoding="utf-8")
    warning_count = sum(1 for row in rows if row["warnings"])
    print(f"Label distribution report complete: {len(rows)} case(s), {warning_count} with warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
