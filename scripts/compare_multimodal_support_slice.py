#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from earnings_call_sentiment.media_support_comparison import evaluate_downstream_decision_cases
from earnings_call_sentiment.media_support_eval import repo_root


CASES_FILE = Path("data/media_support_eval/downstream_decision_eval_cases.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/media_support_eval")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the bounded downstream media-support comparison outputs from the fixed casepack."
    )
    parser.add_argument(
        "--cases-csv",
        default=str(CASES_FILE),
        help="Repo-relative or absolute CSV path for downstream decision comparison cases.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Repo-relative or absolute output directory for the comparison summary and rows.",
    )
    return parser.parse_args(argv)


def _resolve_path(root: Path, value: str) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else root / path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = repo_root()
    cases_path = _resolve_path(root, args.cases_csv)
    output_dir = _resolve_path(root, args.output_dir)

    cases = pd.read_csv(cases_path, dtype=str).fillna("")
    result_frame, summary = evaluate_downstream_decision_cases(cases)
    summary["cases_path"] = str(cases_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "downstream_decision_comparison.json"
    rows_path = output_dir / "downstream_decision_comparison_rows.csv"

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    result_frame.to_csv(rows_path, index=False)

    print(json.dumps(summary, indent=2))
    print(f"wrote {summary_path}")
    print(f"wrote {rows_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
