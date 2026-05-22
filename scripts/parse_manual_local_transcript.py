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
    parser = argparse.ArgumentParser(description="Parse explicit manual-local transcript into metadata spans.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--rights-tier", default="manual_supplied")
    parser.add_argument("--operator", default="manual_operator")
    parser.add_argument("--commit-allowed", action="store_true")
    parser.add_argument("--out", required=True, help="JSON output path for metadata only.")
    args = parser.parse_args(argv)
    record = build_manual_case_record(
        case_id=args.case_id,
        source_path=Path(args.path),
        rights_tier=args.rights_tier,
        commit_allowed=args.commit_allowed,
        operator=args.operator,
    )
    errors = validate_manual_case_record(record)
    write_json(Path(args.out), {"record": record, "errors": errors})
    if errors:
        print(f"Manual-local parse blocked: {len(errors)} error(s).")
        return 1
    print("Manual-local parse wrote metadata only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
