#!/usr/bin/env python3
"""Summarize first30 retrieval failure modes from eval outputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "data" / "retrieval" / "retrieval_eval_results.jsonl"
METRICS_PATH = ROOT / "reports" / "retrieval" / "retrieval_eval_summary.json"
REPORT_PATH = ROOT / "reports" / "retrieval" / "retrieval_failure_diagnostics.md"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose_retrieval_failures(*, results_path: Path = RESULTS_PATH, metrics_path: Path = METRICS_PATH, out_path: Path = REPORT_PATH) -> dict[str, Any]:
    rows = read_jsonl(results_path)
    metrics = read_json(metrics_path)
    invalid = [row for row in rows if row.get("retrieval_method") != "abstain" and not row.get("citation_valid")]
    wrong_context = [row for row in invalid if row.get("case_id") or row.get("ticker") or row.get("fiscal_period")]
    by_query = Counter(row.get("query_id", "") for row in invalid)
    summary = {
        "result_rows": len(rows),
        "invalid_citation_rows": len(invalid),
        "wrong_case_ticker_period": metrics.get("wrong_case_ticker_period", 0),
        "citation_validity": metrics.get("citation_validity", 0.0),
        "fallback_overuse": metrics.get("fallback_overuse", 0.0),
        "invalid_by_query": dict(sorted(by_query.items())),
        "raw_text_returned": bool(metrics.get("raw_text_returned", False)),
        "wrong_context_rows_after_filter": len(wrong_context),
    }
    write_report(summary, out_path)
    return summary


def write_report(summary: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Failure Diagnostics",
        "",
        f"- Result rows: {summary['result_rows']}",
        f"- Invalid citation rows: {summary['invalid_citation_rows']}",
        f"- Wrong case/ticker/period rows: {summary['wrong_case_ticker_period']}",
        f"- Citation validity: {summary['citation_validity']:.3f}",
        f"- Fallback overuse: {summary['fallback_overuse']:.3f}",
        f"- Raw text returned: {str(summary['raw_text_returned']).lower()}",
        "",
        "## Invalid Citations By Query",
        "",
    ]
    invalid_by_query = summary.get("invalid_by_query") or {}
    if invalid_by_query:
        for query_id, count in invalid_by_query.items():
            lines.append(f"- `{query_id}`: {count}")
    else:
        lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose retrieval eval failure modes.")
    parser.add_argument("--results", type=Path, default=RESULTS_PATH)
    parser.add_argument("--metrics", type=Path, default=METRICS_PATH)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    print(json.dumps(diagnose_retrieval_failures(results_path=args.results, metrics_path=args.metrics, out_path=args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
