#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluation_quality import (  # noqa: E402
    GOLD_PATH,
    deterministic_predictions,
    evaluate_predictions,
    label_counts,
    provenance_quality,
    read_jsonl,
    requires_manual_review,
    source_group,
    valid_rows,
    write_jsonl,
)

VALID_GROUPS = {"human_reviewed", "imported_guidance", "fixture", "unknown"}
VALID_QUALITIES = {"high": 3, "medium": 2, "low": 1, "unknown": 0}


def annotate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for row in rows:
        annotated.append(
            {
                **row,
                "source_group": source_group(row),
                "provenance_quality": provenance_quality(row),
                "requires_manual_review": requires_manual_review(row),
            }
        )
    return annotated


def filter_rows(
    rows: list[dict[str, Any]],
    *,
    source: str | None = None,
    exclude: str | None = None,
    min_quality: str | None = None,
) -> list[dict[str, Any]]:
    output = annotate(valid_rows(rows))
    if source:
        output = [row for row in output if row["source_group"] == source]
    if exclude:
        output = [row for row in output if row["source_group"] != exclude]
    if min_quality:
        threshold = VALID_QUALITIES[min_quality]
        output = [row for row in output if VALID_QUALITIES.get(str(row["provenance_quality"]), 0) >= threshold]
    return output


def _subset_metrics(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"subset": name, "row_count": 0, "metrics": None}
    return {"subset": name, "row_count": len(rows), "metrics": evaluate_predictions(deterministic_predictions(rows))}


def write_reports(rows: list[dict[str, Any]]) -> None:
    annotated = annotate(valid_rows(rows))
    by_source = Counter(row["source_group"] for row in annotated)
    by_quality = Counter(row["provenance_quality"] for row in annotated)
    label_by_source = Counter((row["source_group"], row.get("signal_family") or row.get("label")) for row in annotated)

    breakdown = [
        "# Source Quality Breakdown",
        "",
        "Canonical gold labels are not modified by source-quality filtering.",
        "",
        "## Counts By Source Group",
        "",
        *[f"- `{key}`: {count}" for key, count in sorted(by_source.items())],
        "",
        "## Counts By Quality",
        "",
        *[f"- `{key}`: {count}" for key, count in sorted(by_quality.items())],
        "",
        "## Label Counts By Source",
        "",
    ]
    for (group, label), count in sorted(label_by_source.items()):
        breakdown.append(f"- `{group}` / `{label}`: {count}")
    breakdown.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `fixture` rows are useful for regression safety but can make metrics look cleaner or stranger than real transcripts.",
            "- `imported_guidance` rows are valuable but conservatively mapped and should be reviewed before strong product claims.",
            "- `human_reviewed` rows are the best current quality tier, though the count remains small.",
        ]
    )
    (ROOT / "reports" / "source_quality_breakdown.md").write_text("\n".join(breakdown) + "\n", encoding="utf-8")

    subsets = {
        "all": annotated,
        "human_reviewed": filter_rows(rows, source="human_reviewed"),
        "fixture_excluded": filter_rows(rows, exclude="fixture"),
        "high_quality": filter_rows(rows, min_quality="high"),
        "imported_guidance": filter_rows(rows, source="imported_guidance"),
        "fixture": filter_rows(rows, source="fixture"),
    }
    comparison = [_subset_metrics(name, subset_rows) for name, subset_rows in subsets.items()]
    lines = [
        "# Source Quality Metric Comparison",
        "",
        "| subset | rows | precision | recall | F1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in comparison:
        metrics = item["metrics"] or {}
        lines.append(
            f"| `{item['subset']}` | {item['row_count']} | {metrics.get('precision', 'n/a')} | "
            f"{metrics.get('recall', 'n/a')} | {metrics.get('f1', 'n/a')} |"
        )
    lines.extend(
        [
            "",
            "## Are Imported Or Fixture Labels Poisoning Metrics?",
            "",
            "They are not poisoning the canonical file, but they do change interpretation. Fixture rows dominate the current gold set, "
            "while imported guidance rows expose important finance-language gaps. Product claims should be based on high-quality "
            "human-reviewed and fixture-excluded subsets as the label set grows.",
            "",
            "```json",
            json.dumps(comparison, indent=2),
            "```",
        ]
    )
    (ROOT / "reports" / "source_quality_metric_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def output_name(args: argparse.Namespace) -> str:
    parts = ["gold"]
    if args.source:
        parts.append(args.source)
    if args.exclude:
        parts.append(f"exclude_{args.exclude}")
    if args.min_quality:
        parts.append(f"min_{args.min_quality}")
    return "_".join(parts) + ".jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create source-quality filtered gold-label subsets without mutating canonical labels.")
    parser.add_argument("--gold", default=str(GOLD_PATH))
    parser.add_argument("--source", choices=sorted(VALID_GROUPS))
    parser.add_argument("--exclude", choices=sorted(VALID_GROUPS))
    parser.add_argument("--min-quality", choices=sorted(VALID_QUALITIES))
    parser.add_argument("--out")
    parser.add_argument("--write-reports", action="store_true")
    args = parser.parse_args(argv)

    rows = read_jsonl(Path(args.gold))
    filtered = filter_rows(rows, source=args.source, exclude=args.exclude, min_quality=args.min_quality)
    out = Path(args.out) if args.out else ROOT / "data" / "evaluation" / output_name(args)
    write_jsonl(out, filtered)
    if args.write_reports:
        write_reports(rows)
    payload = {
        "status": "ok",
        "source": args.source,
        "exclude": args.exclude,
        "min_quality": args.min_quality,
        "rows": len(filtered),
        "labels": dict(label_counts(filtered)),
        "out": str(out),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
