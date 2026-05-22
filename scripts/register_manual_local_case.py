#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from resource_registry_common import write_json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.corpus.manual_local import build_manual_case_record, validate_manual_case_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register a manually supplied local transcript path without copying raw text.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--rights-tier", default="manual_supplied")
    parser.add_argument("--operator", default="manual_operator")
    parser.add_argument("--commit-allowed", action="store_true")
    parser.add_argument("--out", help="Optional JSON manifest output path. Nothing is written by default.")
    args = parser.parse_args(argv)
    source_path = Path(args.path)
    record = build_manual_case_record(
        case_id=args.case_id,
        source_path=source_path,
        rights_tier=args.rights_tier,
        commit_allowed=args.commit_allowed,
        operator=args.operator,
    )
    errors = validate_manual_case_record(record)
    if args.out:
        write_json(Path(args.out), {"record": record, "errors": errors})
    if errors:
        print(f"Manual-local registration blocked: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Manual-local transcript registration dry-run passed; raw file was not copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
