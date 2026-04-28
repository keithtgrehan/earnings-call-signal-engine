#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SECTIONS = (
    "False positives",
    "Missed guidance changes",
    "Bad friction flags",
    "Bad evidence spans",
    "Direction errors",
    "Rule refinement candidates",
)


def load_summary(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def render_report(summary: dict[str, Any] | None) -> str:
    lines = [
        "# Signal Error Analysis",
        "",
        "This is a lightweight review scaffold. It does not prove model quality or statistical significance.",
        "",
    ]
    if summary is None:
        lines.extend(
            [
                "## Counts",
                "",
                "No evaluation JSON was supplied. Run `scripts/evaluate_signal_outputs.py` first, then attach reviewer notes below.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Counts",
                "",
                f"- total_labels: `{summary.get('total_labels', 0)}`",
                f"- matched_labels: `{summary.get('matched_labels', 0)}`",
                f"- unmatched_labels: `{summary.get('unmatched_labels', 0)}`",
                f"- potential_false_positives: `{summary.get('potential_false_positives', 0)}`",
                f"- missing_evidence: `{summary.get('missing_evidence', 0)}`",
                f"- direction_mismatch: `{summary.get('direction_mismatch', 0)}`",
                "",
            ]
        )
    for section in SECTIONS:
        lines.extend(
            [
                f"## {section}",
                "",
                "- Reviewer notes:",
                "- Example case_ids:",
                "- Proposed deterministic rule change:",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a markdown error-analysis report from evaluation counts.")
    parser.add_argument("--evaluation-json", help="Optional JSON summary from evaluate_signal_outputs.py.")
    parser.add_argument("--out", required=True, help="Markdown report output path.")
    args = parser.parse_args(argv)

    summary = load_summary(args.evaluation_json)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_report(summary), encoding="utf-8")
    print(f"Error analysis report written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
