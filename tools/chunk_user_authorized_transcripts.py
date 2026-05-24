#!/usr/bin/env python3
"""Chunk user-authorized transcript text under Desktop and write repo-safe manifests."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import (
    DEFAULT_WORKSPACE,
    TRANSCRIPT_CHUNK_FIELDS,
    bytes_sha256,
    is_relative_to,
    read_csv,
    slugify,
    write_csv,
)

REPORT_DIR = ROOT / "reports" / "acquisition"
DEFAULT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_transcript_chunks.csv"


def chunk_ranges(text: str, *, chunk_chars: int, overlap_chars: int) -> list[tuple[int, int]]:
    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= chunk_chars:
        raise ValueError("overlap_chars must be non-negative and smaller than chunk_chars")
    ranges: list[tuple[int, int]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        ranges.append((start, end))
        if end >= len(text):
            break
        start = max(0, end - overlap_chars)
    return ranges


def chunk_user_authorized_transcripts(
    *,
    registry_path: Path,
    workspace: Path,
    out_path: Path = DEFAULT_OUT,
    chunk_chars: int = 2500,
    overlap_chars: int = 300,
) -> dict[str, Any]:
    rows = read_csv(registry_path)
    chunk_rows: list[dict[str, str]] = []
    for row in rows:
        if row.get("asset_type") != "transcript" or row.get("eval_allowed") != "true" or row.get("commit_allowed") != "false":
            continue
        transcript = Path(row.get("local_path", ""))
        if not transcript.exists() or not is_relative_to(transcript, workspace) or is_relative_to(transcript, ROOT):
            continue
        text = transcript.read_text(encoding="utf-8", errors="replace")
        chunks_dir = transcript.parent.parent / "chunks" / "transcript"
        chunks_dir.mkdir(parents=True, exist_ok=True)
        for index, (start, end) in enumerate(chunk_ranges(text, chunk_chars=chunk_chars, overlap_chars=overlap_chars), start=1):
            chunk_text = text[start:end]
            chunk_id = f"{slugify(row.get('case_id', 'unknown'))}_transcript_chunk_{index:04d}"
            chunk_path = chunks_dir / f"{chunk_id}.txt"
            chunk_path.write_text(chunk_text, encoding="utf-8")
            chunk_rows.append(
                {
                    "chunk_id": chunk_id,
                    "case_id": row.get("case_id", ""),
                    "ticker": row.get("ticker", ""),
                    "asset_id": f"{row.get('case_id', 'unknown')}_transcript",
                    "asset_type": "transcript",
                    "chunk_type": "transcript_text",
                    "section": "unknown",
                    "speaker_role": "unknown",
                    "source_sha256": row.get("sha256", ""),
                    "text_sha256": bytes_sha256(chunk_text.encode("utf-8")),
                    "local_chunk_path": str(chunk_path),
                    "start_char": str(start),
                    "end_char": str(end),
                    "start_time_sec": "",
                    "end_time_sec": "",
                    "rights_status": row.get("rights_status", "safe_to_download"),
                    "rag_eligible": "true",
                    "raw_text_committed": "false",
                }
            )
    write_csv(out_path, chunk_rows, TRANSCRIPT_CHUNK_FIELDS)
    desktop_index = workspace / "_audit" / "transcript_chunk_index.csv"
    write_csv(desktop_index, chunk_rows, TRANSCRIPT_CHUNK_FIELDS)
    summary = {
        "registry_rows": len(rows),
        "transcript_chunks": len(chunk_rows),
        "rag_ready_calls": len({row["case_id"] for row in chunk_rows}),
        "out_manifest": str(out_path),
        "desktop_index": str(desktop_index),
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "user_authorized_transcript_rag_readiness.md").write_text(
        "# User-Authorized Transcript RAG Readiness\n\n"
        f"- Registry rows: {summary['registry_rows']}\n"
        f"- Transcript chunks: {summary['transcript_chunks']}\n"
        f"- RAG-ready calls: {summary['rag_ready_calls']}\n"
        f"- Repo manifest: `{summary['out_manifest']}`\n"
        f"- Desktop index: `{summary['desktop_index']}`\n"
        "- Raw chunk text committed: false\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chunk user-authorized transcripts under Desktop only.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--chunk-chars", type=int, default=2500)
    parser.add_argument("--overlap-chars", type=int, default=300)
    args = parser.parse_args(argv)
    print(
        chunk_user_authorized_transcripts(
            registry_path=args.registry,
            workspace=args.workspace,
            out_path=args.out,
            chunk_chars=args.chunk_chars,
            overlap_chars=args.overlap_chars,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
