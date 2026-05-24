#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _flags(row: dict[str, object]) -> list[str]:
    text = str(row.get("evidence_text", row.get("redacted_preview", ""))).lower()
    source = str(row.get("source_file", "")).lower()
    flags: set[str] = set()
    if row.get("weak_label_only") is True or "weak_labels.jsonl" in source:
        flags.add("weak_label_only")
    if row.get("source_type") == "external_dataset" or "external" in source:
        flags.add("external_dataset_source")
    if not source:
        flags.add("missing_source_file")
    if not text:
        flags.add("missing_evidence_text")
    if len(text) < 40:
        flags.add("too_short_context")
    patterns = {
        "boilerplate_safe_harbor": r"safe harbor|forward-looking statement",
        "non_gaap_disclaimer": r"non-gaap|non gaap",
        "vendor_transcript_disclaimer": r"transcript (?:provided|edited)|copyright|all rights reserved",
        "operator_housekeeping": r"you may now disconnect|operator|press star",
        "marketing_or_email_footer": r"unsubscribe|privacy policy|marketing",
        "analyst_question_only": r"^\s*(could you|can you|would you)",
        "generic_keyword_hit": r"\b(excited|great|pleased)\b",
    }
    for flag, pattern in patterns.items():
        if re.search(pattern, text):
            flags.add(flag)
    return sorted(flags)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preflag review queue contamination risks without writing gold labels.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/first_100_ranked_review_queue.jsonl")
    parser.add_argument("--out", default="data/review/staging/first_100_contamination_flags.jsonl")
    parser.add_argument("--report", default="reports/review/contamination_flags_summary.md")
    args = parser.parse_args(argv)
    rows = []
    for row in _load_jsonl(Path(args.in_path)):
        rows.append({**row, "contamination_preflags": _flags(row)})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    flagged = sum(1 for row in rows if row["contamination_preflags"])
    report.write_text(f"# Contamination Flags Summary\n\n- Rows scanned: `{len(rows)}`\n- Rows with preflags: `{flagged}`\n- Canonical gold labels written: `0`\n", encoding="utf-8")
    print(f"Contamination preflags written: {len(rows)} row(s), {flagged} flagged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
