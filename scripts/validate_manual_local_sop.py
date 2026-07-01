#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from register_manual_local_batch import _load_rows
from signal_engine.agent5_acquisition import build_manual_local_registry, validate_manual_local_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate manual-local SOP: path/hash only, no raw copies, rights fail closed.")
    parser.add_argument("--batch", default="data/review/staging/manual_local_batch.yml")
    args = parser.parse_args(argv)
    path = Path(args.batch)
    if not path.exists():
        print(f"Manual-local SOP NOT_READY: {path} is missing. No raw files copied.")
        return 0
    rows = build_manual_local_registry(_load_rows(path))
    errors = validate_manual_local_registry(rows)
    for index, row in enumerate(rows, start=1):
        source_path = Path(str(row.get("source_path_ref", "")))
        if not source_path.exists():
            errors.append(f"row {index}: local path must exist")
        if row.get("media_type") == "transcript" and not str(row.get("source_url", row.get("source_url_or_path", ""))).strip():
            errors.append(f"row {index}: source_url is required for transcript registration where available")
        if row.get("raw_file_copied_into_repo") is not False:
            errors.append(f"row {index}: raw_file_copied_into_repo must be false")
    if errors:
        print(f"Manual-local SOP validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Manual-local SOP validation passed: {len(rows)} record(s), raw files not copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
