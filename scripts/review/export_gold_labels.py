#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from review.chunking import stable_hash  # noqa: E402
from review.export_gold import export_gold_labels, read_jsonl, write_jsonl  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export explicit human-reviewed Argilla rows to gold-label JSONL.")
    parser.add_argument("--reviewed", required=True)
    parser.add_argument("--existing-gold", default="")
    parser.add_argument("--out", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "gold_labels.review_export.jsonl"))
    parser.add_argument("--rejected-out", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "gold_labels.rejected.jsonl"))
    parser.add_argument("--mode", choices=["new", "append", "merge"], default="new")
    args = parser.parse_args(argv)
    existing = read_jsonl(Path(args.existing_gold)) if args.existing_gold else []
    rows, rejected = export_gold_labels(read_jsonl(Path(args.reviewed)), existing_rows=existing, mode=args.mode)
    write_jsonl(Path(args.out), rows)
    write_jsonl(Path(args.rejected_out), rejected)
    print(
        json.dumps(
            {
                "export_id": stable_hash(args.reviewed, args.out, len(rows), length=16),
                "gold_rows": len(rows),
                "rejected_rows": len(rejected),
                "output": args.out,
                "mode": args.mode,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
