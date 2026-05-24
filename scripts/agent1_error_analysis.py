#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import csv
import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_counts(path: Path, header: str, counts: Counter[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[header, "count"], lineterminator="\n")
        writer.writeheader()
        for key, count in sorted(counts.items()):
            writer.writerow({header: key, "count": count})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write Agent 1 candidate completeness and false-positive bucket reports.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/agent1_review_queue.jsonl")
    args = parser.parse_args(argv)
    rows = _load_jsonl(Path(args.in_path))
    _write_counts(Path("reports/agent1/false_positive_buckets.csv"), "false_positive_bucket", Counter(str(row.get("false_positive_bucket", "")) or "none" for row in rows))
    _write_counts(Path("reports/agent1_30_call_pilot/false_positive_buckets.csv"), "false_positive_bucket", Counter(str(row.get("false_positive_bucket", "")) or "none" for row in rows))
    completeness = Counter("complete" if row.get("provenance_hash") and row.get("evidence_span_ref") else "missing" for row in rows)
    _write_counts(Path("reports/agent1/evidence_completeness.csv"), "evidence_status", completeness)
    _write_counts(Path("reports/agent1_30_call_pilot/evidence_completeness.csv"), "evidence_status", completeness)
    _write_counts(Path("reports/agent1_30_call_pilot/candidate_counts_by_label.csv"), "signal_type", Counter(str(row.get("signal_type", "unknown")) for row in rows))
    _write_counts(Path("reports/agent1_30_call_pilot/candidate_counts_by_case.csv"), "case_id", Counter(str(row.get("case_id", "unknown")) for row in rows))
    _write_counts(Path("reports/agent1_30_call_pilot/review_priority_queue.csv"), "review_priority", Counter(str(row.get("review_priority", "unknown")) for row in rows))
    Path("reports/agent1_30_call_pilot").mkdir(parents=True, exist_ok=True)
    Path("reports/agent1_30_call_pilot/deduplication_report.csv").write_text("metric,count\ninput_rows,%d\n" % len(rows), encoding="utf-8")
    Path("reports/agent1_30_call_pilot/guidance_comparator_report.csv").write_text("status,count\nnot_run_without_registered_guidance_pairs,1\n", encoding="utf-8")
    Path("reports/agent1_30_call_pilot/qna_pairing_report.csv").write_text("status,count\ncandidate_rows,%d\n" % len(rows), encoding="utf-8")
    Path("reports/agent1_30_call_pilot/error_analysis.md").write_text("# Agent 1 Error Analysis\n\n- Candidate rows: `%d`\n- Canonical gold labels written: `0`\n" % len(rows), encoding="utf-8")
    Path("reports/agent1_30_call_pilot/run_summary.json").write_text(json.dumps({"candidate_rows": len(rows), "gold_written": 0}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Agent 1 error analysis complete: {len(rows)} candidate row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
