#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import build_rag_index_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build repo-safe RAG chunk index manifest with hashes and local paths only.")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = build_rag_index_manifest(args.workspace, out_path=args.out)
    report = Path("reports/acquisition/rag_readiness_summary.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# RAG Readiness Summary\n\n"
        f"- BM25-ready text chunks: {len(rows)}\n"
        f"- RAG-ready calls: {len({row['case_id'] for row in rows})}\n"
        "- Vector DB created: no\n",
        encoding="utf-8",
    )
    print({"chunks": len(rows), "out": str(args.out)})


if __name__ == "__main__":
    main()
