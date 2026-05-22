#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from resource_registry_common import read_structured, write_json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.training.sources import build_training_candidate_manifest, validate_training_source_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build training-candidate manifest without importing external rows.")
    parser.add_argument("--path", default="configs/nlp_training_sources.example.yml")
    parser.add_argument("--out", default="/tmp/signal_engine_training_source_manifest.json")
    args = parser.parse_args(argv)
    payload = read_structured(Path(args.path))
    rows = payload.get("sources", []) if isinstance(payload, dict) else []
    errors = validate_training_source_rows(rows)
    manifest = build_training_candidate_manifest(rows)
    write_json(Path(args.out), {"status": "valid" if not errors else "invalid", "errors": errors, "manifest": manifest})
    if errors:
        print("Training-candidate manifest blocked by validation errors.")
        return 1
    print(f"Training-candidate manifest written to {args.out}; external rows remain benchmark-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
