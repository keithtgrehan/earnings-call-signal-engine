#!/usr/bin/env python3
"""Build repo-safe RAG chunk manifests from rights-cleared local transcripts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "acquisition"
ALLOWED_CHUNK_RIGHTS = {"safe_to_download", "manual_local_review_only", "rights_cleared"}

CHUNK_FIELDS = [
    "chunk_id",
    "case_id",
    "ticker",
    "asset_id",
    "asset_type",
    "chunk_type",
    "source_sha256",
    "text_sha256",
    "local_chunk_path",
    "start_char",
    "end_char",
    "start_time_sec",
    "end_time_sec",
    "rights_status",
    "rag_eligible",
    "raw_text_committed",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def slugify(value: str) -> str:
    import re

    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_") or "unknown"


def chunk_ranges(text: str, *, chunk_chars: int, overlap_chars: int) -> list[tuple[int, int]]:
    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= chunk_chars:
        raise ValueError("overlap_chars must be non-negative and smaller than chunk_chars")
    ranges: list[tuple[int, int]] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_chars, length)
        ranges.append((start, end))
        if end >= length:
            break
        start = max(0, end - overlap_chars)
    return ranges


def call_folder_from_audit(row: dict[str, str], transcript_path: Path, workspace: Path) -> Path:
    folder = str(row.get("folder_path", "")).strip()
    if folder:
        return Path(folder)
    try:
        transcript_path.relative_to(workspace)
        return transcript_path.parents[1]
    except ValueError:
        return workspace / f"{slugify(row.get('ticker', 'UNKNOWN'))}_{slugify(row.get('company_name', 'Unknown'))}" / row.get(
            "case_id", "unknown"
        )


def build_chunks(
    *,
    workspace: Path,
    audit_path: Path,
    out_manifest: Path,
    desktop_index: Path,
    chunk_chars: int = 2500,
    overlap_chars: int = 300,
) -> dict[str, Any]:
    audit_rows = read_csv(audit_path)
    chunk_rows: list[dict[str, Any]] = []
    for row in audit_rows:
        if row.get("asset_type") != "transcript":
            continue
        if row.get("download_status") != "downloaded":
            continue
        if row.get("rights_status") not in ALLOWED_CHUNK_RIGHTS:
            continue
        transcript_path = Path(row.get("transcript_local_path") or row.get("local_path") or "")
        if not transcript_path.exists() or not transcript_path.is_file():
            continue
        text = transcript_path.read_text(encoding="utf-8", errors="replace")
        source_sha = row.get("sha256") or file_sha256(transcript_path)
        call_folder = call_folder_from_audit(row, transcript_path, workspace)
        chunks_dir = call_folder / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)
        for index, (start, end) in enumerate(chunk_ranges(text, chunk_chars=chunk_chars, overlap_chars=overlap_chars), start=1):
            chunk_text = text[start:end]
            chunk_bytes = chunk_text.encode("utf-8")
            chunk_id = f"{slugify(row.get('case_id', 'unknown'))}_{slugify(row.get('asset_id', 'asset'))}_chunk_{index:04d}"
            chunk_path = chunks_dir / f"{chunk_id}.txt"
            chunk_path.write_text(chunk_text, encoding="utf-8")
            chunk_rows.append(
                {
                    "chunk_id": chunk_id,
                    "case_id": row.get("case_id", ""),
                    "ticker": row.get("ticker", ""),
                    "asset_id": row.get("asset_id", ""),
                    "asset_type": "transcript",
                    "chunk_type": "transcript_text",
                    "source_sha256": source_sha,
                    "text_sha256": sha256_bytes(chunk_bytes),
                    "local_chunk_path": str(chunk_path),
                    "start_char": start,
                    "end_char": end,
                    "start_time_sec": "",
                    "end_time_sec": "",
                    "rights_status": row.get("rights_status", ""),
                    "rag_eligible": "true",
                    "raw_text_committed": "false",
                }
            )
    write_csv(out_manifest, chunk_rows, CHUNK_FIELDS)
    write_csv(desktop_index, chunk_rows, CHUNK_FIELDS)
    summary = {
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "audit_rows": len(audit_rows),
        "chunks_created": len(chunk_rows),
        "rag_ready_calls": len({row["case_id"] for row in chunk_rows}),
        "rights_status_counts": dict(Counter(row.get("rights_status", "") for row in chunk_rows)),
        "out_manifest": str(out_manifest),
        "desktop_index": str(desktop_index),
        "raw_text_committed": False,
        "embeddings_created": False,
        "vector_db_created": False,
    }
    write_reports(summary)
    return summary


def write_reports(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "rag_chunking_summary.md").write_text(
        "\n".join(
            [
                "# RAG Chunking Summary",
                "",
                f"- Audit rows read: {summary['audit_rows']}",
                f"- Chunks created: {summary['chunks_created']}",
                f"- RAG-ready calls: {summary['rag_ready_calls']}",
                f"- Repo manifest: {summary['out_manifest']}",
                f"- Desktop index: {summary['desktop_index']}",
                "- Raw chunk text committed: false",
                "- Embeddings/vector DB created: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORT_DIR / "rag_chunking_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build local transcript chunks and repo-safe NYSE 100 RAG chunk manifests.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--out-manifest", required=True)
    parser.add_argument("--desktop-index", required=True)
    parser.add_argument("--chunk-chars", type=int, default=2500)
    parser.add_argument("--overlap-chars", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_chunks(
        workspace=Path(args.workspace),
        audit_path=Path(args.audit),
        out_manifest=Path(args.out_manifest),
        desktop_index=Path(args.desktop_index),
        chunk_chars=args.chunk_chars,
        overlap_chars=args.overlap_chars,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
