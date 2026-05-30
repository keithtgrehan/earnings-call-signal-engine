#!/usr/bin/env python3
"""Link first100 review candidates to retrieval metadata for reviewer support."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
DEFAULT_RETRIEVAL_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_METRICS = ROOT / "data" / "retrieval" / "first30_eval_metrics.json"
OUT_CSV = ROOT / "data" / "retrieval" / "first100_candidate_retrieval_links.csv"
REPORT_PATH = ROOT / "reports" / "retrieval" / "first100_retrieval_support_summary.md"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_links(
    candidates_path: Path = DEFAULT_CANDIDATES,
    retrieval_objects: Path = DEFAULT_RETRIEVAL_OBJECTS,
    metrics_path: Path = DEFAULT_METRICS,
    out_csv: Path = OUT_CSV,
    out_report: Path = REPORT_PATH,
) -> dict[str, Any]:
    candidates = read_jsonl(candidates_path)
    retrieval_by_id = {row.get("object_id", ""): row for row in read_csv(retrieval_objects)}
    metrics = read_json(metrics_path)
    rows: list[dict[str, Any]] = []
    missing = 0
    for candidate in candidates:
        object_id = candidate.get("retrieval_object_id", "")
        retrieval = retrieval_by_id.get(object_id, {})
        if not retrieval:
            missing += 1
        rows.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "case_id": candidate.get("case_id", ""),
                "ticker": candidate.get("ticker", ""),
                "fiscal_period": candidate.get("fiscal_period", ""),
                "suggested_label": candidate.get("suggested_label", ""),
                "retrieval_object_id": object_id,
                "retrieval_object_type": retrieval.get("object_type", candidate.get("object_type", "")),
                "retrieval_priority": retrieval.get("retrieval_priority", ""),
                "evidence_object_id": candidate.get("evidence_object_id", ""),
                "chunk_id": candidate.get("chunk_id", ""),
                "source_sha256": candidate.get("source_sha256", ""),
                "normalized_transcript_hash": candidate.get("normalized_transcript_hash", ""),
                "provenance_hash": candidate.get("provenance_hash", ""),
                "raw_text_returned": "false",
            }
        )
    fields = [
        "candidate_id",
        "case_id",
        "ticker",
        "fiscal_period",
        "suggested_label",
        "retrieval_object_id",
        "retrieval_object_type",
        "retrieval_priority",
        "evidence_object_id",
        "chunk_id",
        "source_sha256",
        "normalized_transcript_hash",
        "provenance_hash",
        "raw_text_returned",
    ]
    write_csv(out_csv, rows, fields)
    summary = {
        "candidate_count": len(candidates),
        "linked_count": len(rows) - missing,
        "missing_retrieval_links": missing,
        "object_type_counts": dict(sorted(Counter(row["retrieval_object_type"] for row in rows).items())),
        "retrieval_metrics": {
            "recall_at_1": metrics.get("recall_at_1"),
            "recall_at_3": metrics.get("recall_at_3"),
            "recall_at_5": metrics.get("recall_at_5"),
            "mrr": metrics.get("mrr"),
            "citation_validity": metrics.get("citation_validity"),
            "wrong_case_ticker_period": metrics.get("wrong_case_ticker_period"),
            "fallback_overuse": metrics.get("fallback_overuse"),
            "evaluated_rag": metrics.get("evaluated_rag", False),
        },
        "raw_text_returned": False,
        "out": str(out_csv),
    }
    write_report(summary, out_report)
    return summary


def write_report(summary: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = summary.get("retrieval_metrics", {})
    def metric(name: str, default: float = 0.0) -> float:
        value = metrics.get(name, default)
        return default if value is None else float(value)

    lines = [
        "# First100 Retrieval Support Summary",
        "",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Linked candidates: {summary['linked_count']}",
        f"- Missing retrieval links: {summary['missing_retrieval_links']}",
        f"- Object type counts: `{json.dumps(summary['object_type_counts'], sort_keys=True)}`",
        f"- recall@1: {metric('recall_at_1'):.3f}",
        f"- recall@3: {metric('recall_at_3'):.3f}",
        f"- recall@5: {metric('recall_at_5'):.3f}",
        f"- MRR: {metric('mrr'):.3f}",
        f"- Citation validity: {metric('citation_validity'):.3f}",
        f"- Wrong case/ticker/period: {metrics.get('wrong_case_ticker_period', 0)}",
        f"- Fallback overuse: {metric('fallback_overuse'):.3f}",
        f"- evaluated_rag: {str(metrics.get('evaluated_rag', False)).lower()}",
        "- Retrieval role: reviewer support only",
        "- Raw text returned: false",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first100 candidate retrieval support links.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--retrieval-objects", type=Path, default=DEFAULT_RETRIEVAL_OBJECTS)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--out", type=Path, default=OUT_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    print(json.dumps(build_links(args.candidates, args.retrieval_objects, args.metrics, args.out, args.report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
