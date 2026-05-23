#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize guidance comparator candidate directions.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/agent1_candidates_deduped.jsonl")
    parser.add_argument("--report", default="reports/agent1_30_call_pilot/guidance_comparator_report.csv")
    args = parser.parse_args(argv)
    rows = [json.loads(line) for line in Path(args.in_path).read_text(encoding="utf-8").splitlines() if line.strip()] if Path(args.in_path).exists() else []
    counts = Counter(str(row.get("suggested_direction", "unknown")) for row in rows if row.get("signal_type") == "guidance_revision")
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("suggested_direction,count\n" + "".join(f"{key},{count}\n" for key, count in sorted(counts.items())), encoding="utf-8")
    print(f"Guidance comparator report written: {sum(counts.values())} guidance candidate(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
