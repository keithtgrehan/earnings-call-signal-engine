#!/usr/bin/env python3
"""Validate repo-safe chunk manifests."""

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

from signal_engine.chunking import validate_chunk_manifest_rows
from tools.build_event_chunks import DEFAULT_OUT
from tools.user_authorized_ingest_common import read_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate event chunk manifest guardrails.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    rows = read_csv(args.manifest)
    errors = validate_chunk_manifest_rows(rows, repo_root=ROOT)
    result = {"ok": not errors, "rows": len(rows), "errors": errors}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
