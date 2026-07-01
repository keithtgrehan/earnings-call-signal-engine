#!/usr/bin/env python3
"""Build a local lexical retrieval index from repo-safe retrieval metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval import build_local_bm25_index, load_retrieval_manifest

DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_OUT = ROOT / ".local" / "signal_engine" / "retrieval" / "indexes" / "nyse100_bm25"
REPORT_PATH = ROOT / "reports" / "retrieval" / "retrieval_readiness.md"


def build_index(*, objects_path: Path, out_dir: Path) -> dict:
    objects = load_retrieval_manifest(objects_path)
    index = build_local_bm25_index(objects, out_dir=out_dir)
    lines = [
        "# Retrieval Readiness",
        "",
        f"- Retrieval objects: {len(objects)}",
        f"- BM25-ready objects: {index['document_count']}",
        f"- Local index path: `{out_dir}`",
        "- Raw text indexed: false",
        "- Embeddings committed: false",
        "- Vector DB committed: false",
        "- Provider APIs called: false",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"objects": len(objects), "document_count": index["document_count"], "out": str(out_dir)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local metadata-only BM25 retrieval index.")
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(build_index(objects_path=args.objects, out_dir=args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
