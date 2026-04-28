#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"Expected JSON object in {path}")
            rows.append(row)
    return rows


def key_for(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("case_id", "")), str(row.get("signal_type", "")))


def evaluate(gold_rows: list[dict[str, Any]], prediction_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gold_by_key = {key_for(row): row for row in gold_rows}
    predictions_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in prediction_rows:
        predictions_by_key.setdefault(key_for(row), []).append(row)

    matched_labels = 0
    unmatched_labels = 0
    missing_evidence = 0
    direction_mismatch = 0
    matched_keys: set[tuple[str, str]] = set()

    for key, gold in gold_by_key.items():
        predictions = predictions_by_key.get(key) or []
        if not predictions:
            unmatched_labels += 1
            continue
        matched_labels += 1
        matched_keys.add(key)
        prediction = predictions[0]
        if not str(prediction.get("evidence_text", "")).strip():
            missing_evidence += 1
        if str(prediction.get("direction", "")) != str(gold.get("direction", "")):
            direction_mismatch += 1

    potential_false_positives = 0
    for key, predictions in predictions_by_key.items():
        if key not in gold_by_key:
            potential_false_positives += len(predictions)
        elif key in matched_keys and len(predictions) > 1:
            potential_false_positives += len(predictions) - 1

    return {
        "total_labels": len(gold_rows),
        "matched_labels": matched_labels,
        "unmatched_labels": unmatched_labels,
        "potential_false_positives": potential_false_positives,
        "missing_evidence": missing_evidence,
        "direction_mismatch": direction_mismatch,
    }


def render_markdown(summary: dict[str, Any], *, gold_path: str, predictions_path: str) -> str:
    lines = [
        "# Signal Output Evaluation",
        "",
        "This report is a first-pass scaffold. It is not statistical proof and does not validate production ML.",
        "",
        "## Inputs",
        "",
        f"- gold_labels: `{gold_path}`",
        f"- predictions: `{predictions_path}`",
        "",
        "## Counts",
        "",
        "| metric | count |",
        "| --- | ---: |",
    ]
    for key in (
        "total_labels",
        "matched_labels",
        "unmatched_labels",
        "potential_false_positives",
        "missing_evidence",
        "direction_mismatch",
    ):
        lines.append(f"| {key} | {summary[key]} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- unmatched labels are likely false negatives or missing predictions",
            "- potential false positives need reviewer confirmation",
            "- missing evidence and direction mismatch are rule-quality issues before they are model-quality issues",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare predicted Signal Engine JSONL outputs against gold labels.")
    parser.add_argument("--gold-labels", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--report-out", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    gold_rows = load_jsonl(Path(args.gold_labels))
    prediction_rows = load_jsonl(Path(args.predictions))
    summary = evaluate(gold_rows, prediction_rows)

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_markdown(summary, gold_path=args.gold_labels, predictions_path=args.predictions),
        encoding="utf-8",
    )

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(
        "Signal output evaluation complete: "
        f"{summary['matched_labels']} matched, {summary['unmatched_labels']} unmatched, "
        f"{summary['potential_false_positives']} potential false positive(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
