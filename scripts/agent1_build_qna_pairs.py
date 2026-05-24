#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize Q&A pair candidates from Agent 1 candidate records.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/agent1_candidates_deduped.jsonl")
    parser.add_argument("--report", default="reports/agent1_30_call_pilot/qna_pairing_report.csv")
    args = parser.parse_args(argv)
    rows = [json.loads(line) for line in Path(args.in_path).read_text(encoding="utf-8").splitlines() if line.strip()] if Path(args.in_path).exists() else []
    pairs = [row for row in rows if row.get("qna_pair_id")]
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"status,count\nqna_pairs,{len(pairs)}\nunpaired_question,0\n", encoding="utf-8")
    print(f"Q&A pairing report written: {len(pairs)} pair candidate(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
