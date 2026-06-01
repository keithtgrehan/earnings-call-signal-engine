#!/usr/bin/env python3
"""Export metadata-only retrieval objects without raw transcript or chunk text."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval.object_metadata import (  # noqa: E402
    FORBIDDEN_METADATA_PAYLOAD_KEYS,
    build_retrieval_object_metadata,
    validate_retrieval_object_metadata_rows,
)

DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_OUT = ROOT / "data" / "retrieval" / "retrieval_object_metadata.jsonl"
DEFAULT_REPORT = ROOT / "reports" / "retrieval" / "retrieval_object_metadata_export.md"

SOURCE_GUARDRAIL_KEYS = {"raw_text_committed", "raw_text_commit_allowed"}
OBJECT_TYPE_MAP = {
    "semantic_chunk": "semantic_chunk_metadata",
    "semantic_fallback": "semantic_chunk_metadata",
    "event_aligned_chunk": "event_aligned_chunk_metadata",
    "evidence_object": "evidence_object_metadata",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _optional_int(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    return int(text)


def _source_payload_errors(row: dict[str, str], row_number: int) -> list[str]:
    errors: list[str] = []
    for key in row:
        if key in SOURCE_GUARDRAIL_KEYS:
            continue
        if key in FORBIDDEN_METADATA_PAYLOAD_KEYS:
            errors.append(f"source row {row_number}: forbidden raw/vector payload key {key}")
    if str(row.get("raw_text_committed", "false")).lower() != "false":
        errors.append(f"source row {row_number}: raw_text_committed must be false")
    if str(row.get("raw_text_commit_allowed", "false")).lower() != "false":
        errors.append(f"source row {row_number}: raw_text_commit_allowed must be false")
    for field in ("case_id", "object_type", "source_type", "source_sha256", "text_sha256", "normalized_transcript_sha256", "provenance_ref", "provenance_hash", "rights_tier"):
        if not str(row.get(field, "")).strip():
            errors.append(f"source row {row_number}: missing {field}")
    if row.get("object_type") not in OBJECT_TYPE_MAP:
        errors.append(f"source row {row_number}: unsupported object_type {row.get('object_type')!r}")
    return errors


def _metadata_from_source_row(row: dict[str, str]) -> dict[str, Any]:
    return build_retrieval_object_metadata(
        object_type=OBJECT_TYPE_MAP[str(row.get("object_type", ""))],
        case_id=row.get("case_id", ""),
        company=row.get("company", ""),
        ticker=row.get("ticker", ""),
        fiscal_period=row.get("fiscal_period", ""),
        source_type=row.get("source_type", ""),
        provenance_ref=row.get("provenance_ref", ""),
        source_hash=row.get("source_sha256", ""),
        text_hash=row.get("text_sha256", ""),
        normalized_transcript_hash=row.get("normalized_transcript_sha256", ""),
        provenance_hash=row.get("provenance_hash", ""),
        section_label=row.get("section", ""),
        speaker_role=row.get("speaker", ""),
        topic=row.get("topic", ""),
        span_start_char=_optional_int(row.get("span_start_char")),
        span_end_char=_optional_int(row.get("span_end_char")),
        rights_tier=row.get("rights_tier", ""),
    )


def _sorted_metadata_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (int(row["retrieval_priority"]), str(row["case_id"]), str(row["object_id"])))


def _summary(rows: list[dict[str, Any]], *, source_manifest: Path, out_path: Path) -> dict[str, Any]:
    return {
        "status_label": "retrieval_object_scaffold_only",
        "source_manifest": str(source_manifest),
        "out_path": str(out_path),
        "object_count": len(rows),
        "counts_by_object_type": dict(sorted(Counter(str(row["object_type"]) for row in rows).items())),
        "counts_by_case_id": dict(sorted(Counter(str(row["case_id"]) for row in rows).items())),
        "content_included": False,
        "embeddings_included": False,
        "vector_db_included": False,
        "evaluated_retrieval_quality": False,
        "production_rag_claim": False,
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Object Metadata Export",
        "",
        "## Run status",
        f"- retrieval_object_status: `{summary['status_label']}`",
        "- Retrieval object scaffold only.",
        "- No embeddings are created or committed.",
        "- No vector DB is created or committed.",
        "- No evaluated retrieval quality or production RAG claims are made.",
        "",
        "## Source and output",
        f"- Source manifest: `{summary['source_manifest']}`",
        f"- Output JSONL: `{summary['out_path']}`",
        f"- Object count: `{summary['object_count']}`",
        "",
        "## Counts by object type",
    ]
    for object_type, count in summary["counts_by_object_type"].items():
        lines.append(f"- {object_type}: `{count}`")
    lines.extend(["", "## Counts by case_id"])
    for case_id, count in summary["counts_by_case_id"].items():
        lines.append(f"- {case_id}: `{count}`")
    lines.extend(
        [
            "",
            "## Safety",
            "- Output records contain metadata, hashes, span coordinates, and provenance references only.",
            "- Raw transcript text, ASR/audio text, chunk body text, embeddings, vector payloads, vector DB files, provider artifacts, labels, adjudication rows, training data, and promotion rows are not produced by this export.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_retrieval_object_metadata(
    *,
    source_manifest: Path = DEFAULT_SOURCE_MANIFEST,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    source_rows = read_csv(source_manifest)
    source_errors: list[str] = []
    metadata_rows: list[dict[str, Any]] = []
    for row_number, row in enumerate(source_rows, start=2):
        errors = _source_payload_errors(row, row_number)
        if errors:
            source_errors.extend(errors)
            continue
        metadata_rows.append(_metadata_from_source_row(row))
    metadata_rows = _sorted_metadata_rows(metadata_rows)
    validation_errors = validate_retrieval_object_metadata_rows(metadata_rows)
    errors = source_errors + validation_errors
    if errors:
        raise ValueError("; ".join(errors))
    write_jsonl(out_path, metadata_rows)
    summary = _summary(metadata_rows, source_manifest=source_manifest, out_path=out_path)
    write_report(summary, report_path)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export metadata-only retrieval objects.")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    try:
        summary = export_retrieval_object_metadata(source_manifest=args.source_manifest, out_path=args.out, report_path=args.report)
    except Exception as exc:
        print(f"Retrieval object metadata export blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
