#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation.retrieval_gates import retrieval_gate_report


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run retrieval gate report without embeddings or vector DBs.")
    parser.add_argument("--objects", default="data/review/staging/agent1_retrieval_objects.jsonl")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--out", default="reports/evaluation/retrieval_gate_report.json")
    args = parser.parse_args(argv)
    payload = retrieval_gate_report(evidence_objects=_count_jsonl(Path(args.objects)), registered_sources=_count_jsonl(Path(args.registry)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Retrieval gate report written to {out}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
