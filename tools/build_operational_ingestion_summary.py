#!/usr/bin/env python3
"""Build final operational ingestion summary reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE, read_csv, write_json

REPORT_PATH = ROOT / "reports" / "acquisition" / "operational_ingestion_summary.md"


def _rows(path: Path) -> list[dict[str, str]]:
    return read_csv(path)


def build_summary(*, workspace: Path = DEFAULT_WORKSPACE) -> dict[str, Any]:
    audit_dir = workspace / "_audit"
    permitted = _rows(ROOT / "data" / "acquisition" / "nyse_100_user_authorized_permitted_downloads.csv")
    download_log = _rows(audit_dir / "user_authorized_download_log.csv")
    transcript_registry = _rows(ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv")
    audio_registry = _rows(ROOT / "data" / "corpus" / "manual_local_audio_registry.csv")
    normalized = _rows(ROOT / "data" / "corpus" / "normalized_transcript_manifest.csv")
    chunks = _rows(ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv")
    evidence = _rows(ROOT / "data" / "acquisition" / "nyse_100_evidence_objects_manifest.csv")
    retrieval = _rows(ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv")
    audio_rag = _rows(ROOT / "data" / "acquisition" / "nyse_100_user_authorized_audio_rag_manifest.csv")
    download_status = Counter(row.get("download_status", "") for row in download_log)
    transcript_attempts = [row for row in download_log if row.get("asset_type") == "transcript"]
    audio_attempts = [row for row in download_log if row.get("asset_type") == "audio"]
    blockers = []
    if not permitted:
        blockers.append("No permitted download rows.")
    if not transcript_registry:
        blockers.append("No registered transcripts; normalization/chunking remain readiness-only.")
    if not audio_registry:
        blockers.append("No registered audio; audio RAG remains readiness-only.")
    summary = {
        "workspace": str(workspace),
        "companies_processed": len({row.get("ticker", "") for row in permitted if row.get("ticker")}),
        "calls_processed": len({row.get("case_id", "") for row in permitted if row.get("case_id")}),
        "permitted_download_rows": len(permitted),
        "transcript_downloads_attempted": len(transcript_attempts),
        "transcript_downloads_succeeded": sum(1 for row in transcript_attempts if row.get("download_status") == "downloaded"),
        "audio_downloads_attempted": len(audio_attempts),
        "audio_downloads_succeeded": sum(1 for row in audio_attempts if row.get("download_status") == "downloaded"),
        "registered_transcripts": len(transcript_registry),
        "registered_audio": len(audio_registry),
        "normalized_transcripts": len(normalized),
        "transcript_chunks": len(chunks),
        "evidence_objects": len(evidence),
        "retrieval_objects": len(retrieval),
        "audio_rag_records": len(audio_rag),
        "bm25_ready_objects": len(retrieval),
        "download_status_counts": dict(download_status),
        "agent1_readiness": "ready_when_registered_transcripts_exist" if transcript_registry else "blocked_no_registered_transcripts",
        "training_readiness": "blocked_training_rights_not_enabled",
        "raw_files_committed": False,
        "model_training_run": False,
        "embeddings_committed": False,
        "vector_db_committed": False,
        "blockers": blockers,
        "next_manual_actions": [
            "Review blocked download reasons for direct transcript/audio URLs.",
            "Place explicitly approved transcript/audio files in the Desktop workspace when manual-local is needed.",
            "Re-run registration, normalization, chunking, retrieval export, and audio RAG readiness after files are present.",
        ],
    }
    write_reports(summary, audit_dir)
    return summary


def write_reports(summary: dict[str, Any], audit_dir: Path) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Operational Ingestion Summary",
        "",
        f"- Desktop workspace: `{summary['workspace']}`",
        f"- Companies processed: {summary['companies_processed']}",
        f"- Calls processed: {summary['calls_processed']}",
        f"- Permitted download rows: {summary['permitted_download_rows']}",
        f"- Transcript downloads attempted/succeeded: {summary['transcript_downloads_attempted']}/{summary['transcript_downloads_succeeded']}",
        f"- Audio downloads attempted/succeeded: {summary['audio_downloads_attempted']}/{summary['audio_downloads_succeeded']}",
        f"- Registered transcripts: {summary['registered_transcripts']}",
        f"- Registered audio: {summary['registered_audio']}",
        f"- Normalized transcripts: {summary['normalized_transcripts']}",
        f"- Transcript chunks: {summary['transcript_chunks']}",
        f"- Evidence objects: {summary['evidence_objects']}",
        f"- Retrieval objects: {summary['retrieval_objects']}",
        f"- Audio RAG records: {summary['audio_rag_records']}",
        f"- BM25-ready objects: {summary['bm25_ready_objects']}",
        f"- Agent 1 readiness: {summary['agent1_readiness']}",
        f"- Training readiness: {summary['training_readiness']}",
        "- Raw files committed: false",
        "- Model training run: false",
        "- Embeddings/vector DB committed: false",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in summary["blockers"]) if summary["blockers"] else lines.append("- none")
    lines.extend(["", "## Exact Next Manual Actions", ""])
    lines.extend(f"- {action}" for action in summary["next_manual_actions"])
    body = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(body, encoding="utf-8")
    (audit_dir / "user_authorized_ingest_summary.md").write_text(body, encoding="utf-8")
    write_json(audit_dir / "user_authorized_ingest_summary.json", summary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build operational ingestion summary.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args(argv)
    print(json.dumps(build_summary(workspace=args.workspace), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
