#!/usr/bin/env python3
"""Safe staging wrapper for first100 adjudication draft validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_first100_adjudication_file import (
    DEFAULT_ADJUDICATION,
    DEFAULT_CANDIDATES,
    JSON_REPORT_PATH,
    REPORT_PATH,
    validate_adjudication_file,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate first100 staging adjudication JSONL without promotion, gold labels, or training."
    )
    parser.add_argument("--draft", type=Path, default=DEFAULT_ADJUDICATION)
    parser.add_argument("--mode", choices=["staging"], default="staging")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_REPORT_PATH)
    args = parser.parse_args(argv)

    summary = validate_adjudication_file(args.draft, args.out, args.json_out, args.candidates)
    summary["promotion_ready"] = False
    summary["training_ready"] = False
    print(json.dumps(summary, indent=2, sort_keys=True))

    empty_initialized = (
        summary.get("status") == "NOT_READY"
        and summary.get("manifest_exists") is True
        and summary.get("adjudicated_rows") == 0
        and summary.get("error_count") == 0
    )
    return 0 if summary.get("valid") or empty_initialized else 1


if __name__ == "__main__":
    raise SystemExit(main())
