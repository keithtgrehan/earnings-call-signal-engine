#!/usr/bin/env python3
"""Export repo-safe retrieval object manifests from chunk metadata."""

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

from signal_engine.retrieval.objects import retrieval_priority_for_type
from tools.user_authorized_ingest_common import read_csv, stable_hash, write_csv

DEFAULT_CHUNK_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
DEFAULT_OUT = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
REPORT_PATH = ROOT / "reports" / "retrieval" / "retrieval_readiness.md"

RETRIEVAL_MANIFEST_FIELDS = [
    "object_id",
    "object_type",
    "case_id",
    "ticker",
    "company",
    "fiscal_period",
    "source_type",
    "source_ref",
    "section",
    "speaker",
    "topic",
    "span_start_char",
    "span_end_char",
    "source_sha256",
    "text_sha256",
    "rights_tier",
    "retrieval_priority",
    "commit_allowed",
    "raw_text_commit_allowed",
    "raw_text_committed",
]


def _object_type_for_chunk(chunk_type: str) -> str:
    if chunk_type == "evidence_object":
        return "evidence_object"
    if chunk_type in {"prepared_remarks", "guidance_statement", "guidance_revision_candidate", "qa_question", "qa_answer", "qa_pair"}:
        return "event_aligned_chunk"
    return "semantic_chunk"


def export_retrieval_objects(*, chunk_manifest: Path, out_path: Path = DEFAULT_OUT) -> dict[str, Any]:
    rows = read_csv(chunk_manifest)
    objects: list[dict[str, str]] = []
    for row in rows:
        if row.get("raw_text_committed") != "false" or row.get("rag_eligible") not in {"true", True}:
            continue
        object_type = _object_type_for_chunk(row.get("chunk_type", ""))
        object_id = stable_hash({"chunk_id": row.get("chunk_id"), "object_type": object_type})[:32]
        objects.append(
            {
                "object_id": object_id,
                "object_type": object_type,
                "case_id": row.get("case_id", ""),
                "ticker": row.get("ticker", ""),
                "company": "",
                "fiscal_period": "",
                "source_type": "manual_local_transcript_chunk",
                "source_ref": row.get("local_chunk_path", ""),
                "section": row.get("section", ""),
                "speaker": row.get("speaker_role", ""),
                "topic": row.get("chunk_type", ""),
                "span_start_char": row.get("start_char", ""),
                "span_end_char": row.get("end_char", ""),
                "source_sha256": row.get("source_sha256", ""),
                "text_sha256": row.get("text_sha256", ""),
                "rights_tier": row.get("rights_status", ""),
                "retrieval_priority": str(retrieval_priority_for_type(object_type)),
                "commit_allowed": "false",
                "raw_text_commit_allowed": "false",
                "raw_text_committed": "false",
            }
        )
    write_csv(out_path, objects, RETRIEVAL_MANIFEST_FIELDS)
    summary = {
        "chunk_rows": len(rows),
        "retrieval_objects": len(objects),
        "bm25_ready_objects": len(objects),
        "out_manifest": str(out_path),
        "embeddings_committed": False,
        "vector_db_committed": False,
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Readiness",
        "",
        f"- Chunk rows: {summary['chunk_rows']}",
        f"- Retrieval objects: {summary['retrieval_objects']}",
        f"- BM25-ready objects: {summary['bm25_ready_objects']}",
        f"- Manifest: `{summary['out_manifest']}`",
        "- Embeddings committed: false",
        "- Vector DB committed: false",
        "- Retrieval role: reviewer support only",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export repo-safe retrieval object metadata.")
    parser.add_argument("--chunk-manifest", type=Path, default=DEFAULT_CHUNK_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(export_retrieval_objects(chunk_manifest=args.chunk_manifest, out_path=args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
