#!/usr/bin/env python3
"""Build event-aligned chunks from registered Desktop transcripts."""

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

from signal_engine.chunking import build_event_chunks_for_text, build_evidence_objects, chunk_quality_summary
from signal_engine.chunking.schemas import EVIDENCE_OBJECT_FIELDS
from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE, TRANSCRIPT_CHUNK_FIELDS, is_relative_to, read_csv, write_csv

DEFAULT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
DEFAULT_EVIDENCE_OUT = ROOT / "data" / "acquisition" / "nyse_100_evidence_objects_manifest.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "rag_chunking_summary.md"
HD_QUALITY_REPORT = ROOT / "reports" / "acquisition" / "chunk_quality_report_hd_2025_q4.md"


def _chunks_dir_for_raw(path: Path) -> Path:
    if path.parent.name == "transcript":
        return path.parent.parent / "chunks" / "transcript"
    return path.parent / "chunks" / "transcript"


def _display_path(path: str) -> str:
    value = Path(path)
    try:
        return str(value.resolve().relative_to(ROOT.resolve()))
    except (OSError, ValueError):
        return path


def _write_chunk_text(chunk: dict[str, Any], chunks_dir: Path) -> dict[str, str]:
    text = str(chunk.pop("_text", ""))
    chunks_dir.mkdir(parents=True, exist_ok=True)
    target = chunks_dir / f"{chunk['chunk_id']}.txt"
    target.write_text(text, encoding="utf-8")
    row = {field: str(chunk.get(field, "")) for field in TRANSCRIPT_CHUNK_FIELDS}
    row["local_chunk_path"] = str(target)
    row["raw_text_committed"] = "false"
    row["rag_eligible"] = "true"
    return row


def build_event_chunks(
    *,
    registry_path: Path,
    workspace: Path,
    out_path: Path = DEFAULT_OUT,
    evidence_out: Path = DEFAULT_EVIDENCE_OUT,
) -> dict[str, Any]:
    registry_rows = read_csv(registry_path)
    chunk_rows: list[dict[str, str]] = []
    quality_rows: dict[str, dict[str, Any]] = {}
    skipped = 0
    for row in registry_rows:
        if row.get("asset_type") != "transcript" or row.get("eval_allowed") != "true" or row.get("commit_allowed") != "false":
            skipped += 1
            continue
        raw_path = Path(row.get("local_path", ""))
        if not raw_path.exists() or not is_relative_to(raw_path, workspace) or is_relative_to(raw_path, ROOT):
            skipped += 1
            continue
        text = raw_path.read_text(encoding="utf-8", errors="replace")
        chunks_dir = _chunks_dir_for_raw(raw_path)
        chunks = build_event_chunks_for_text(
            text,
            case_id=row.get("case_id", ""),
            ticker=row.get("ticker", ""),
            source_sha256=row.get("sha256", ""),
            rights_status=row.get("rights_status", "safe_to_download"),
        )
        quality_rows[row.get("case_id", "")] = chunk_quality_summary(text, chunks)
        for chunk in chunks:
            chunk_rows.append(_write_chunk_text(chunk, chunks_dir))
    evidence_rows = build_evidence_objects(chunk_rows)
    write_csv(out_path, chunk_rows, TRANSCRIPT_CHUNK_FIELDS)
    write_csv(evidence_out, evidence_rows, EVIDENCE_OBJECT_FIELDS)
    audit_dir = workspace / "_audit"
    write_csv(audit_dir / "transcript_chunk_index.csv", chunk_rows, TRANSCRIPT_CHUNK_FIELDS)
    write_csv(audit_dir / "rag_chunk_index.csv", chunk_rows, TRANSCRIPT_CHUNK_FIELDS)
    summary = {
        "registry_rows": len(registry_rows),
        "skipped_rows": skipped,
        "transcript_chunks": len(chunk_rows),
        "evidence_objects": len(evidence_rows),
        "rag_ready_calls": len({row["case_id"] for row in chunk_rows}),
        "retrieval_object_ready_calls": len({row["case_id"] for row in chunk_rows}),
        "bm25_smoke_ready_calls": len({row["case_id"] for row in chunk_rows}),
        "evaluated_rag": False,
        "chunk_manifest": str(out_path),
        "evidence_manifest": str(evidence_out),
        "raw_text_committed": False,
    }
    write_report(summary)
    write_quality_report("hd_2025_q4", quality_rows.get("hd_2025_q4", {}))
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# RAG Chunking Summary",
        "",
        f"- Registry rows: {summary['registry_rows']}",
        f"- Skipped rows: {summary['skipped_rows']}",
        f"- Transcript chunks: {summary['transcript_chunks']}",
        f"- Evidence objects: {summary['evidence_objects']}",
        f"- Retrieval-object ready calls: {summary['retrieval_object_ready_calls']}",
        f"- BM25 smoke-ready calls: {summary['bm25_smoke_ready_calls']}",
        "- evaluated_rag=false",
        "- Retrieval quality proven: false",
        f"- Chunk manifest: `{_display_path(str(summary['chunk_manifest']))}`",
        f"- Evidence manifest: `{_display_path(str(summary['evidence_manifest']))}`",
        "- Chunk text committed: false",
        "- RAG role: reviewer support only",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_quality_report(case_id: str, quality: dict[str, Any]) -> None:
    HD_QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    if not quality:
        text = (
            f"# Chunk Quality Report: {case_id}\n\n"
            "- Status: not_ready\n"
            "- Reason: control fixture transcript not present in registry for this run\n"
            "- evaluated_rag=false\n"
            "- bm25_smoke_ready: false\n"
        )
        HD_QUALITY_REPORT.write_text(text, encoding="utf-8")
        return
    lines = [
        f"# Chunk Quality Report: {case_id}",
        "",
        f"- Section counts: {quality['section_counts']}",
        f"- Speaker turn counts: {quality['speaker_turn_counts']}",
        f"- Q&A pair count: {quality['qa_pair_count']}",
        f"- Chunk count: {quality['chunk_count']}",
        f"- Evidence candidate count: {quality['evidence_candidate_count']}",
        f"- Unknown section ratio: {quality['unknown_section_ratio']:.3f}",
        f"- Unknown speaker ratio: {quality['unknown_speaker_ratio']:.3f}",
        f"- Fallback ratio: {quality['fallback_ratio']:.3f}",
        f"- Suppression counts: {quality['suppression_counts']}",
        f"- Raw-text leak check: {quality['raw_text_leak_check']}",
        f"- large_chunk_warning: {str(quality['large_chunk_warning']).lower()}",
        "- evaluated_rag=false",
        f"- bm25_smoke_ready: {str(quality['bm25_smoke_ready']).lower()}",
    ]
    HD_QUALITY_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build event-aligned transcript chunks under Desktop only.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--evidence-out", type=Path, default=DEFAULT_EVIDENCE_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(build_event_chunks(registry_path=args.registry, workspace=args.workspace, out_path=args.out, evidence_out=args.evidence_out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
