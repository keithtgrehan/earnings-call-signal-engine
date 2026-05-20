#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.review_schema import EVALUATOR_SCHEMA_VERSION, classify_evidence_match, clean_text as schema_clean, utc_now  # noqa: E402
from signal_engine.storage.sqlite_store import init_db, insert_evaluation_run  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def row_payload(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, dict) else row


def row_key(row: dict[str, Any]) -> str:
    row = row_payload(row)
    for key in ("review_id", "candidate_id", "id"):
        value = clean(row.get(key))
        if value:
            return value
    return hashlib.sha1(f"{clean(row.get('case_id'))}|{clean(row.get('evidence_text') or row.get('text'))}".encode("utf-8")).hexdigest()[:16]


def row_signal(row: dict[str, Any]) -> str:
    row = row_payload(row)
    for key in ("signal_type", "signal_family", "label", "weak_label", "suggested_label"):
        value = clean(row.get(key))
        if value:
            return value
    return ""


def row_direction(row: dict[str, Any]) -> str:
    row = row_payload(row)
    for key in ("direction", "predicted_direction", "final_direction", "gold_direction"):
        value = clean(row.get(key))
        if value:
            return value
    return ""


def row_evidence(row: dict[str, Any]) -> str:
    row = row_payload(row)
    for key in ("evidence_text", "text", "matched_text", "segment_text"):
        value = clean(row.get(key))
        if value:
            return value
    return ""


def evaluate(deterministic_rows: list[dict[str, Any]], gold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    predicted_by_key = {row_key(row): row for row in deterministic_rows}
    gold_by_key = {row_key(row): row for row in gold_rows}
    tp = fp = fn = 0
    direction_mismatch = evidence_mismatch = section_mismatch = unresolved_ambiguity = 0
    mismatch_classes: dict[str, int] = {"none": 0, "exact_mismatch": 0, "partial_mismatch": 0, "transcript_missing": 0, "section_mismatch": 0}
    matched: list[dict[str, str]] = []

    for key, prediction in predicted_by_key.items():
        gold = gold_by_key.get(key)
        if gold is None:
            fp += 1
            continue
        if row_signal(prediction) == row_signal(gold):
            tp += 1
        else:
            fp += 1
            fn += 1
        if row_direction(prediction) and row_direction(gold) and row_direction(prediction) != row_direction(gold):
            direction_mismatch += 1
        prediction_payload = row_payload(prediction)
        gold_payload = row_payload(gold)
        section_changed = clean(prediction_payload.get("transcript_section")) != clean(gold_payload.get("transcript_section"))
        mismatch_class = classify_evidence_match(row_evidence(gold), row_evidence(prediction), section_mismatch=section_changed)
        mismatch_classes[mismatch_class] = mismatch_classes.get(mismatch_class, 0) + 1
        if mismatch_class != "none":
            evidence_mismatch += 1
        if section_changed:
            section_mismatch += 1
        if clean(gold.get("reviewer_action")) == "uncertain" or clean(gold.get("review_status")) == "uncertain":
            unresolved_ambiguity += 1
        matched.append({"key": key, "predicted": row_signal(prediction), "gold": row_signal(gold)})

    for key in gold_by_key:
        if key not in predicted_by_key:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "schema_version": EVALUATOR_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "predicted_rows": len(deterministic_rows),
        "gold_rows": len(gold_rows),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "direction_mismatch": direction_mismatch,
        "evidence_mismatch": evidence_mismatch,
        "section_mismatch": section_mismatch,
        "unresolved_ambiguity": unresolved_ambiguity,
        "evidence_mismatch_classes": mismatch_classes,
        "matched_examples": matched[:10],
    }


def write_report(path: Path, metrics: dict[str, Any]) -> None:
    lines = [
        "# Review Evaluation",
        "",
        "This report compares deterministic signal outputs against canonical human-reviewed gold labels.",
        "It is a workflow metric, not a statistical-validity or production-readiness claim.",
        "",
        "## Counts",
        "",
        f"- deterministic_rows: `{metrics['predicted_rows']}`",
        f"- gold_rows: `{metrics['gold_rows']}`",
        f"- TP: `{metrics['tp']}`",
        f"- FP: `{metrics['fp']}`",
        f"- FN: `{metrics['fn']}`",
        "",
        "## Metrics",
        "",
        f"- precision: `{metrics['precision']}`",
        f"- recall: `{metrics['recall']}`",
        f"- f1: `{metrics['f1']}`",
        "",
        "## Review-Specific Mismatches",
        "",
        f"- direction_mismatch: `{metrics['direction_mismatch']}`",
        f"- evidence_mismatch: `{metrics['evidence_mismatch']}`",
        f"- section_mismatch: `{metrics['section_mismatch']}`",
        f"- unresolved_ambiguity: `{metrics['unresolved_ambiguity']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def persist_evaluation_run(db_path: Path, metrics: dict[str, Any], deterministic_path: Path, gold_path: Path, report_path: Path) -> None:
    connection = init_db(db_path)
    insert_evaluation_run(
        connection,
        {
            "schema_version": EVALUATOR_SCHEMA_VERSION,
            "run_type": "deterministic_vs_gold_review",
            "deterministic_output_path": str(deterministic_path),
            "gold_label_path": str(gold_path),
            "metrics": metrics,
            "report_path": str(report_path),
            "review_count": metrics.get("predicted_rows", 0),
            "accepted_count": metrics.get("tp", 0),
            "rejected_count": metrics.get("fp", 0),
            "uncertain_count": metrics.get("unresolved_ambiguity", 0),
            "created_at": schema_clean(metrics.get("generated_at")) or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
    )
    connection.commit()
    connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic review outputs against canonical gold labels.")
    parser.add_argument("--deterministic-jsonl", required=True)
    parser.add_argument("--gold-jsonl", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--metrics-json", default=str(ROOT / "reports" / "review_evaluation_metrics.json"))
    parser.add_argument("--report", default=str(ROOT / "reports" / "review_evaluation.md"))
    parser.add_argument("--db-path", default=str(ROOT / "data" / "review" / "signal_engine.db"))
    args = parser.parse_args(argv)
    deterministic_path = Path(args.deterministic_jsonl)
    gold_path = Path(args.gold_jsonl)
    metrics = evaluate(read_jsonl(deterministic_path), read_jsonl(gold_path))
    write_json(Path(args.metrics_json), metrics)
    report_path = Path(args.report)
    write_report(report_path, metrics)
    try:
        persist_evaluation_run(Path(args.db_path), metrics, deterministic_path, gold_path, report_path)
    except sqlite3.Error as exc:
        raise SystemExit(f"failed to write evaluation run to SQLite: {exc}") from exc
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
