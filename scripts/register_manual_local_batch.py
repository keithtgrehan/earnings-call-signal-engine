#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import build_manual_local_registry, validate_manual_local_registry


def _load_rows(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix.lower() in {".yml", ".yaml"} else json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("sources") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("manual local batch must be a list or object with sources list")
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register manual-local transcript/audio/video paths by metadata and hash only.")
    parser.add_argument("--batch", default="data/review/staging/manual_local_batch.yml")
    parser.add_argument("--out", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--operator", default="manual_operator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    batch = Path(args.batch)
    if not batch.exists():
        print(f"Manual-local batch NOT_READY: {batch} is missing. No raw files copied.")
        return 0
    rows = build_manual_local_registry(_load_rows(batch), operator=args.operator)
    errors = validate_manual_local_registry(rows)
    if errors:
        print(f"Manual-local batch registration blocked: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    if not args.dry_run:
        _write_jsonl(Path(args.out), rows)
    print(f"Manual-local batch registration passed: {len(rows)} path/hash record(s), raw files not copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
