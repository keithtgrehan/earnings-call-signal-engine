#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def load_optional_duckdb() -> Any | None:
    try:
        import duckdb  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return None
    return duckdb


def analytics_payload(reviews: list[dict[str, Any]], gold: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    actions = Counter(clean(row.get("reviewer_action")) or "missing" for row in reviews)
    sections = Counter(clean(row.get("transcript_section")) or "unknown" for row in gold)
    reviewers = Counter(clean(row.get("reviewer_id")) or "unknown" for row in reviews)
    uncertainty = actions.get("uncertain", 0)
    reviewed = sum(count for action, count in actions.items() if action not in {"", "missing"})
    return {
        "review_rows": len(reviews),
        "gold_rows": len(gold),
        "tp": int(metrics.get("tp", 0)),
        "fp": int(metrics.get("fp", 0)),
        "fn": int(metrics.get("fn", 0)),
        "direction_mismatch": int(metrics.get("direction_mismatch", 0)),
        "evidence_mismatch": int(metrics.get("evidence_mismatch", 0)),
        "section_mismatch": int(metrics.get("section_mismatch", 0)),
        "unresolved_ambiguity": int(metrics.get("unresolved_ambiguity", uncertainty)),
        "uncertainty_rate": round(uncertainty / reviewed, 4) if reviewed else 0.0,
        "reviewer_counts": dict(sorted(reviewers.items())),
        "review_action_counts": dict(sorted(actions.items())),
        "section_counts": dict(sorted(sections.items())),
    }


def write_report(path: Path, payload: dict[str, Any], *, duckdb_available: bool) -> None:
    lines = [
        "# DuckDB Review Analytics",
        "",
        "This local analytics report summarizes review outcomes and evaluator mismatches.",
        "It remains deterministic and reads JSONL/CSV artifacts directly.",
        "",
        f"- duckdb_available: `{duckdb_available}`",
        f"- review_rows: `{payload['review_rows']}`",
        f"- gold_rows: `{payload['gold_rows']}`",
        f"- TP / FP / FN: `{payload['tp']} / {payload['fp']} / {payload['fn']}`",
        f"- direction_mismatch: `{payload['direction_mismatch']}`",
        f"- evidence_mismatch: `{payload['evidence_mismatch']}`",
        f"- section_mismatch: `{payload['section_mismatch']}`",
        f"- unresolved_ambiguity: `{payload['unresolved_ambiguity']}`",
        f"- uncertainty_rate: `{payload['uncertainty_rate']}`",
        "",
        "## Reviewer Throughput",
        "",
    ]
    lines.extend(f"- `{reviewer}`: {count}" for reviewer, count in payload["reviewer_counts"].items())
    if not payload["reviewer_counts"]:
        lines.append("- No reviewer rows found.")
    lines.extend(["", "## Review Actions", ""])
    lines.extend(f"- `{action}`: {count}" for action, count in payload["review_action_counts"].items())
    if not payload["review_action_counts"]:
        lines.append("- No review actions found.")
    lines.extend(["", "## Corpus Composition By Section", ""])
    lines.extend(f"- `{section}`: {count}" for section, count in payload["section_counts"].items())
    if not payload["section_counts"]:
        lines.append("- No gold-label section data found.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local DuckDB-style analytics for deterministic review evaluation artifacts.")
    parser.add_argument("--reviews-jsonl", default="data/review/canonical_reviews.jsonl")
    parser.add_argument("--gold-jsonl", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--metrics-json", default="reports/review_evaluation_metrics.json")
    parser.add_argument("--output", default="reports/duckdb_review_analytics.md")
    parser.add_argument("--review-csv", default="", help="Optional CSV review rows to include in action counts.")
    args = parser.parse_args(argv)

    duckdb = load_optional_duckdb()
    reviews = read_jsonl(Path(args.reviews_jsonl))
    if args.review_csv:
        reviews.extend(read_csv(Path(args.review_csv)))
    gold = read_jsonl(Path(args.gold_jsonl))
    metrics = {}
    metrics_path = Path(args.metrics_json)
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    payload = analytics_payload(reviews, gold, metrics)
    write_report(Path(args.output), payload, duckdb_available=duckdb is not None)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
