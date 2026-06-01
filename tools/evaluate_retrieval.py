#!/usr/bin/env python3
"""Evaluate RAG v0 metadata-only retrieval runs without exposing raw text."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval.evaluate import (  # noqa: E402
    placeholder_expected_ids,
    read_jsonl,
    summarize_retrieval_results,
    validate_eval_query_record,
    validate_no_forbidden_payload_keys,
    validate_retrieval_result_record,
    write_jsonl,
)
from signal_engine.retrieval.evaluate import evaluate_retrieval, evaluate_retrieval_objects  # noqa: E402

DEFAULT_INDEX = ROOT / ".local" / "signal_engine" / "retrieval" / "indexes" / "nyse100_bm25"
DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_QUERIES = ROOT / "data" / "retrieval" / "eval_queries_hd_2025_q4.jsonl"
FIRST30_TEMPLATE_QUERIES = ROOT / "data" / "retrieval" / "eval_queries_first30_template.jsonl"
MATERIALIZED_FIRST30_QUERIES = ROOT / "data" / "retrieval" / "eval_queries_first30_materialized.jsonl"
RESULTS_OUT = ROOT / "data" / "retrieval" / "retrieval_eval_results.jsonl"
SUMMARY_JSON = ROOT / "reports" / "retrieval" / "retrieval_eval_summary.json"
SUMMARY_MD = ROOT / "reports" / "retrieval" / "retrieval_eval_summary.md"
MAX_FALLBACK_OVERUSE_FOR_EVALUATED_RAG = 0.25


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize_first30_queries(objects_path: Path, out_path: Path = MATERIALIZED_FIRST30_QUERIES) -> list[dict[str, Any]]:
    objects = read_csv(objects_path)
    by_case: dict[str, dict[str, str]] = {}
    for object_type in ("evidence_object", "event_aligned_chunk"):
        for row in objects:
            case_id = row.get("case_id", "")
            if case_id and case_id not in by_case and row.get("object_type") == object_type:
                by_case[case_id] = row
    queries: list[dict[str, Any]] = []
    for case_id, row in sorted(by_case.items()):
        if case_id == "hd_2025_q4":
            continue
        ticker = row.get("ticker", "")
        fiscal_period = row.get("fiscal_period", "")
        queries.append(
            {
                "query_id": f"{case_id}_first30_metadata_smoke",
                "query_text": f"{ticker} {case_id} management prepared remarks guidance",
                "query_intent": "first30_materialized_metadata_smoke",
                "target_case_id": case_id,
                "target_ticker": ticker,
                "target_fiscal_period": fiscal_period,
                "expected_object_types": ["evidence_object"] if row.get("object_type") == "evidence_object" else ["event_aligned_chunk"],
                "expected_signal_types": ["guidance"],
                "expected_sections": ["prepared_remarks"],
                "expected_speaker_roles": ["management"],
                "expected_evidence_ids": [row.get("object_id", "")],
                "negative_control": False,
                "abstention_expected": False,
                "rights_required": ["normalized_transcript_manifest", "retrieval_object_manifest"],
                "notes": "Materialized from retrieval object metadata only; reviewer-bound evidence IDs are required before promotion.",
            }
        )
    if by_case:
        first = next(iter(sorted(by_case.values(), key=lambda item: item.get("case_id", ""))))
        queries.append(
            {
                "query_id": "first30_trading_request_negative",
                "query_text": "trading request across first30 earnings calls",
                "query_intent": "trading_request",
                "target_case_id": first.get("case_id", ""),
                "target_ticker": first.get("ticker", ""),
                "target_fiscal_period": first.get("fiscal_period", ""),
                "expected_object_types": [],
                "expected_signal_types": [],
                "expected_sections": [],
                "expected_speaker_roles": [],
                "expected_evidence_ids": [],
                "negative_control": True,
                "abstention_expected": True,
                "rights_required": ["retrieval_object_manifest"],
                "notes": "Must abstain; retrieval eval is not trading advice.",
            }
        )
    write_jsonl(out_path, queries)
    return queries


def _gate_status(summary: dict[str, Any]) -> bool:
    return (
        summary.get("manifest_status") == "completed"
        and summary.get("smoke_metrics") is False
        and summary.get("placeholder_expected_ids", 1) == 0
        and not summary.get("failures")
        and summary.get("recall_at_5", 0.0) > 0.0
        and summary.get("mrr", 0.0) > 0.0
        and summary.get("invalid_citation_rate", 1.0) <= 0.05
        and summary.get("abstention_correctness", 0.0) >= 0.95
        and summary.get("provenance_completeness", 0.0) >= 0.95
        and summary.get("fallback_overuse", 1.0) <= MAX_FALLBACK_OVERUSE_FOR_EVALUATED_RAG
        and summary.get("raw_text_returned") is False
    )


def _format_rate(summary: dict[str, Any], name: str) -> str:
    rate = summary.get("rates", {}).get(name, {"numerator": 0, "denominator": 0, "percentage": 0.0})
    return f"{rate['percentage']:.2f}% ({rate['numerator']}/{rate['denominator']})"


def write_report(summary: dict[str, Any], out_path: Path = SUMMARY_MD) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    evaluated_rag = _gate_status(summary)
    pass_fail = "pass" if evaluated_rag else ("fail" if summary.get("failures") else "warn")
    warnings = summary.get("warnings") or []
    failures = summary.get("failures") or []
    inventory = summary.get("object_inventory_by_type") or {}
    latency = summary.get("latency") or {}
    lines = [
        "# Retrieval Eval Summary",
        "",
        "## Run status",
        f"- smoke_metrics: `{str(summary.get('smoke_metrics', True)).lower()}`",
        f"- evaluated_rag: `{str(evaluated_rag).lower()}`",
        f"- manifest_status: `{summary.get('manifest_status', 'not_provided')}`",
        "",
        "## Corpus status",
        "- Current status label: `smoke_metrics` unless a completed retrieval eval manifest passes all gates.",
        "- Transcript-aligned evidence remains canonical; audio-only objects are excluded until matched to transcript spans.",
        "",
        "## Eval manifest path",
        f"- `{summary.get('eval_manifest_path') or 'not_provided'}`",
        "",
        "## Query file path",
        f"- `{summary.get('query_file_path') or 'not_provided'}`",
        "",
        "## Result file path",
        f"- `{summary.get('result_file_path') or 'not_provided'}`",
        "",
        "## BM25 baseline status",
        "- Metadata-only BM25 smoke path available; no embeddings or vector DB required.",
        "",
        "## Object inventory by type",
    ]
    if inventory:
        lines.extend(f"- {key}: `{value}`" for key, value in inventory.items())
    else:
        lines.append("- none registered for this run")
    lines.extend(
        [
            "",
            "## Q&A/no-Q&A state",
            f"- `{summary.get('qna_state', 'missing')}`",
            "",
            "## Recall@1, recall@3, recall@5",
            f"- recall@1: {_format_rate(summary, 'recall_at_1')}",
            f"- recall@3: {_format_rate(summary, 'recall_at_3')}",
            f"- recall@5: {_format_rate(summary, 'recall_at_5')}",
            "",
            "## MRR",
            f"- MRR: {summary.get('mrr', 0.0):.4f} ({summary.get('mrr_numerator', 0.0):.4f}/{summary.get('mrr_denominator', 0)})",
            "",
            "## Exact evidence ID hit rate",
            f"- {_format_rate(summary, 'exact_evidence_id_hit_rate')}",
            "",
            "## Citation validity rate",
            f"- {_format_rate(summary, 'citation_validity_rate')}",
            "",
            "## Invalid citation rate",
            f"- {_format_rate(summary, 'invalid_citation_rate')}",
            "",
            "## Wrong case/ticker/period rates",
            f"- wrong_case_rate: {_format_rate(summary, 'wrong_case_rate')}",
            f"- wrong_ticker_rate: {_format_rate(summary, 'wrong_ticker_rate')}",
            f"- wrong_period_rate: {_format_rate(summary, 'wrong_period_rate')}",
            "",
            "## Abstention correctness",
            f"- {_format_rate(summary, 'abstention_correctness')}",
            "",
            "## Fallback overuse rate",
            f"- {_format_rate(summary, 'fallback_overuse_rate')}",
            "",
            "## Latency summary",
            f"- p50: `{latency.get('p50')}`",
            f"- p90: `{latency.get('p90')}`",
            f"- p95: `{latency.get('p95')}`",
            f"- max: `{latency.get('max')}`",
            "",
            "## Provenance completeness rate",
            f"- {_format_rate(summary, 'provenance_completeness_rate')}",
            "",
            "## Pass/warn/fail gate result",
            f"- `{pass_fail}`",
            "",
            "## Warnings",
        ]
    )
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- none")
    lines.append("")
    lines.append("## Failures")
    lines.extend(f"- {failure}" for failure in failures) if failures else lines.append("- none")
    lines.extend(
        [
            "",
            "## Reviewer-support-only statement",
            "- RAG v0 is an evidence-first retrieval evaluation scaffold, not a chatbot, trading system, alpha engine, or evaluated production RAG claim.",
            "- No labels, gold labels, adjudication rows, training data, promotion candidates, raw transcript text, raw ASR/audio text, chunk text, embeddings, vector DBs, or provider artifacts are produced by this report.",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validation_failures(queries: list[dict[str, Any]], results: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for index, query in enumerate(queries, start=1):
        failures.extend(f"query row {index}: {error}" for error in validate_eval_query_record(query))
    for index, result in enumerate(results, start=1):
        failures.extend(f"result row {index}: {error}" for error in validate_retrieval_result_record(result))
    return failures


def _load_manifest_results(path: Path) -> tuple[list[dict[str, Any]], str, str | None]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("retrieval run manifest must be a JSON object")
    errors = validate_no_forbidden_payload_keys(payload, context="run_manifest")
    if errors:
        raise ValueError("; ".join(errors))
    status = str(payload.get("status", payload.get("run_status", "not_provided")))
    if isinstance(payload.get("results"), list):
        return [dict(row) for row in payload["results"]], status, None
    results_path = payload.get("results_path") or payload.get("result_file_path")
    if results_path:
        result_file = Path(results_path)
        if not result_file.is_absolute():
            result_file = path.parent / result_file
        return read_jsonl(result_file), status, str(result_file)
    return [], status, None


def _run_summary(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    queries = read_jsonl(args.queries)
    manifest_status = "not_provided"
    eval_manifest_path = str(args.run_manifest) if args.run_manifest else None
    result_file_path: str | None = None
    if args.run_manifest:
        results, manifest_status, result_file_path = _load_manifest_results(args.run_manifest)
        summary = summarize_retrieval_results(
            queries=queries,
            results=results,
            smoke_metrics=args.mode == "smoke",
            eval_manifest_path=eval_manifest_path,
            query_file_path=str(args.queries),
            result_file_path=result_file_path,
            manifest_status=manifest_status,
        )
    elif args.result_file:
        results = read_jsonl(args.result_file)
        result_file_path = str(args.result_file)
        summary = summarize_retrieval_results(
            queries=queries,
            results=results,
            smoke_metrics=args.mode == "smoke",
            query_file_path=str(args.queries),
            result_file_path=result_file_path,
            manifest_status=manifest_status,
        )
    elif args.objects and args.objects.exists():
        summary = evaluate_retrieval_objects(args.objects, args.queries, limit=args.limit)
        summary["query_file_path"] = str(args.queries)
        results = list(summary.get("results", []))
    else:
        summary = evaluate_retrieval(args.index, args.queries, limit=args.limit)
        summary["query_file_path"] = str(args.queries)
        results = list(summary.get("results", []))
    summary["smoke_metrics"] = args.mode == "smoke" or bool(summary.get("smoke_metrics"))
    validation_failures = _validation_failures(queries, results)
    if validation_failures:
        summary.setdefault("failures", []).extend(validation_failures)
    placeholders = placeholder_expected_ids(queries)
    summary["placeholder_expected_ids"] = len(placeholders)
    if placeholders and args.mode == "production":
        summary.setdefault("failures", []).append("production metrics blocked because reviewer placeholder expected evidence IDs remain")
    elif placeholders:
        warning = "reviewer placeholder expected evidence IDs remain; smoke mode only"
        if warning not in summary.setdefault("warnings", []):
            summary["warnings"].append(warning)
    summary["evaluated_rag"] = _gate_status(summary)
    return summary, results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAG v0 metadata-only retrieval runs.")
    parser.add_argument("--mode", choices=["smoke", "production"], default="smoke")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--result-file", type=Path, default=None, help="Strict retrieval result JSONL to evaluate.")
    parser.add_argument("--run-manifest", type=Path, default=None, help="Retrieval run manifest JSON containing status/results path.")
    parser.add_argument("--results-out", type=Path, default=RESULTS_OUT)
    parser.add_argument("--summary-json", "--metrics", dest="summary_json", type=Path, default=SUMMARY_JSON)
    parser.add_argument("--summary-md", "--out", dest="summary_md", type=Path, default=SUMMARY_MD)
    parser.add_argument("--first30-template", type=Path, default=FIRST30_TEMPLATE_QUERIES)
    parser.add_argument("--materialized-first30", type=Path, default=MATERIALIZED_FIRST30_QUERIES)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)

    summary, results = _run_summary(args)
    summary["result_file_path"] = str(args.results_out)
    write_jsonl(args.results_out, results)
    write_json(args.summary_json, {key: value for key, value in summary.items() if key != "results"})
    write_report(summary, args.summary_md)
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2, sort_keys=True))
    return 1 if summary.get("failures") else 0


if __name__ == "__main__":
    raise SystemExit(main())
