#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from resource_registry_common import read_structured

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval import build_retrieval_objects_from_manifest, serialize_retrieval_objects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build retrieval objects from synthetic/manual-local metadata.")
    parser.add_argument("--path", default="configs/rag_build_policy.example.yml")
    parser.add_argument("--out", help="Optional JSONL output path. Nothing is written by default.")
    args = parser.parse_args(argv)
    payload = read_structured(Path(args.path))
    rows = payload.get("synthetic_manifest", []) if isinstance(payload, dict) else []
    try:
        objects = build_retrieval_objects_from_manifest(rows)
        serialize_retrieval_objects(objects, out_path=Path(args.out) if args.out else None)
    except Exception as exc:
        print(f"Retrieval object build blocked: {exc}")
        return 1
    print(f"Retrieval object build dry-run passed: {len(objects)} object(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
