#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
for path in (SRC, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_duckdb_analytics import analytics_payload, load_optional_duckdb, persist_duckdb, write_csv_summary, write_report as write_analytics_report  # noqa: E402
from export_argilla_dataset import export_reviews, read_jsonl, write_jsonl  # noqa: E402
from import_argilla_reviews import import_reviews  # noqa: E402
from run_review_evaluation import evaluate, persist_evaluation_run, write_json, write_report as write_eval_report  # noqa: E402
from signal_engine.review_schema import PROVENANCE_EVENT_SCHEMA_VERSION, build_export_manifest, utc_now  # noqa: E402
from signal_engine.storage.sqlite_store import init_db, insert_gold_label, insert_provenance_event, insert_review_record  # noqa: E402

DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "review_workflow" / "deterministic_outputs.jsonl"
DEFAULT_OUT = ROOT / "data" / "review" / "runtime" / "dryrun"


def write_manifest(path: Path, rows: list[dict[str, Any]], *, source_path: Path, output_path: Path) -> dict[str, Any]:
    manifest = build_export_manifest(rows, source_path=str(source_path), output_path=str(output_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def simulate_reviewed_export(exported_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reviewed: list[dict[str, Any]] = []
    actions = ["accept", "uncertain"]
    for index, row in enumerate(exported_rows):
        item = json.loads(json.dumps(row))
        item["reviewer_id"] = "dryrun_reviewer"
        item["responses"] = [{"question_name": "reviewer_action", "value": actions[index % len(actions)]}]
        reviewed.append(item)
    return reviewed


def persist_reviews(db_path: Path, reviews: list[dict[str, Any]], gold: list[dict[str, Any]], *, source_path: Path) -> None:
    connection = init_db(db_path)
    try:
        for review in reviews:
            insert_review_record(connection, review)
            insert_provenance_event(
                connection,
                {
                    "schema_version": PROVENANCE_EVENT_SCHEMA_VERSION,
                    "provenance_id": review["provenance_id"],
                    "review_id": review["review_id"],
                    "case_id": review["case_id"],
                    "event_type": "dryrun_review_imported",
                    "source_path": str(source_path),
                    "source_url": review.get("source_url", ""),
                    "payload": {
                        "review_status": review.get("review_status", ""),
                        "evidence_mismatch_class": review.get("evidence_mismatch_class", ""),
                    },
                    "created_at": utc_now(),
                },
            )
        for label in gold:
            insert_gold_label(connection, label)
        connection.commit()
    finally:
        connection.close()


def run_dryrun(fixture: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    deterministic_path = out_dir / "deterministic_outputs.jsonl"
    shutil.copyfile(fixture, deterministic_path)
    deterministic_rows = read_jsonl(deterministic_path)
    exported = export_reviews(deterministic_rows)
    export_path = out_dir / "argilla_export.jsonl"
    write_jsonl(export_path, exported)
    manifest = write_manifest(out_dir / "argilla_export.manifest.json", [row["metadata"] for row in exported], source_path=deterministic_path, output_path=export_path)

    reviewed = simulate_reviewed_export(exported)
    reviewed_path = out_dir / "argilla_reviewed.jsonl"
    write_jsonl(reviewed_path, reviewed)

    canonical_reviews, gold = import_reviews(reviewed, export_manifest=manifest)
    canonical_path = out_dir / "canonical_reviews.jsonl"
    gold_path = out_dir / "gold_labels.jsonl"
    write_jsonl(canonical_path, canonical_reviews)
    write_jsonl(gold_path, gold)

    db_path = out_dir / "signal_engine.db"
    persist_reviews(db_path, canonical_reviews, gold, source_path=reviewed_path)

    metrics = evaluate([row["metadata"] for row in exported], gold)
    metrics_path = out_dir / "review_evaluation_metrics.json"
    eval_report = out_dir / "review_evaluation.md"
    write_json(metrics_path, metrics)
    write_eval_report(eval_report, metrics)
    persist_evaluation_run(db_path, metrics, deterministic_path, gold_path, eval_report)

    analytics = analytics_payload(canonical_reviews, gold, metrics)
    analytics_report = out_dir / "duckdb_review_analytics.md"
    analytics_csv = out_dir / "review_analytics_summary.csv"
    duckdb = load_optional_duckdb()
    duckdb_path = out_dir / "review_analytics.duckdb"
    if duckdb is not None:
        persist_duckdb(duckdb_path, analytics, duckdb_module=duckdb)
    write_csv_summary(analytics_csv, analytics)
    write_analytics_report(
        analytics_report,
        analytics,
        duckdb_available=duckdb is not None,
        duckdb_path=str(duckdb_path) if duckdb is not None else "",
        csv_output=str(analytics_csv),
    )
    summary = {
        "fixture": str(fixture),
        "out_dir": str(out_dir),
        "deterministic_rows": len(deterministic_rows),
        "exported_rows": len(exported),
        "reviewed_rows": len(canonical_reviews),
        "gold_labels": len(gold),
        "sqlite_db": str(db_path),
        "evaluation_report": str(eval_report),
        "analytics_report": str(analytics_report),
        "duckdb_created": duckdb is not None,
    }
    (out_dir / "dryrun_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an offline deterministic review workflow dry-run.")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)
    summary = run_dryrun(Path(args.fixture), Path(args.out_dir))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
