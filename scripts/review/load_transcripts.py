#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from review.chunking import load_transcript_chunks, stable_hash, write_jsonl  # noqa: E402
from review.storage import INSTALL_GUIDANCE  # noqa: E402


def _records(root: Path, *, chunk_size: int, overlap: int, min_chunk_length: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chunk in load_transcript_chunks(root, chunk_size=chunk_size, overlap=overlap, min_chunk_length=min_chunk_length):
        row = chunk.to_record()
        row["external_id"] = chunk.chunk_id
        row["review_state"] = "pending"
        row["provenance"] = {
            "case_id": chunk.case_id,
            "chunk_id": chunk.chunk_id,
            "provenance_hash": chunk.provenance_hash,
            "text_hash": stable_hash(chunk.text, length=32),
            "source_file": chunk.source_file,
        }
        rows.append(row)
    return rows


def _upload_argilla(dataset_name: str, rows: list[dict[str, Any]]) -> int:
    try:
        import argilla as rg  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Argilla upload requested but Argilla is not installed. {INSTALL_GUIDANCE}") from exc
    client = rg.Argilla(
        api_url=os.environ.get("ARGILLA_API_URL", "http://localhost:6900"),
        api_key=os.environ.get("ARGILLA_API_KEY", "argilla.apikey"),
    )
    workspace = os.environ.get("ARGILLA_WORKSPACE", "signal-engine")
    dataset = client.datasets(name=dataset_name, workspace=workspace)
    if dataset is None:
        raise SystemExit(f"Argilla dataset not found: {workspace}/{dataset_name}. Run make review-bootstrap first.")
    records = [
        rg.Record(
            fields={"text": row["text"]},
            metadata={**row["metadata"], "review_state": row["review_state"]},
            external_id=row["external_id"],
        )
        for row in rows
    ]
    dataset.records.log(records)
    return len(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load deterministic transcript chunks into Argilla-ready JSONL records.")
    parser.add_argument("--root", default=str(ROOT / "data" / "corpus" / "manual_cases"))
    parser.add_argument("--dataset", default=os.environ.get("ARGILLA_DATASET", "earnings-call-review"))
    parser.add_argument("--out", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "argilla_records.jsonl"))
    parser.add_argument("--chunk-size", type=int, default=1800)
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--min-chunk-length", type=int, default=200)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    rows = _records(Path(args.root), chunk_size=args.chunk_size, overlap=args.overlap, min_chunk_length=args.min_chunk_length)
    write_jsonl(Path(args.out), rows)
    uploaded = 0 if args.dry_run or not args.upload else _upload_argilla(args.dataset, rows)
    print(json.dumps({"records": len(rows), "output": args.out, "uploaded": uploaded, "dry_run": args.dry_run}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
