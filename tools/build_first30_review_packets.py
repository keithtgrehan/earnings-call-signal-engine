#!/usr/bin/env python3
"""Build metadata-only first30 human-review packets from signal candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first30_signal_candidates.jsonl"
PACKET_DIR = ROOT / "data" / "review" / "packets"
SUMMARY_REPORT = ROOT / "reports" / "review" / "first30_review_packet_summary.md"

PACKETS = [
    ("first30_batch_001_guidance.md", {"guidance_revision", "guidance_statement"}),
    ("first30_batch_002_qa_friction.md", {"analyst_pressure", "answer_shift"}),
    ("first30_batch_003_hedging_uncertainty_reassurance.md", {"management_hedging", "uncertainty", "reassurance", "neutral/no_signal"}),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _packet_lines(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        f"# {title}",
        "",
        "- Review mode: metadata-only first30 signal candidates",
        "- Gold labels in this packet: 0",
        "- Raw evidence text included: false",
        "- Decision options: accept_candidate, reject_candidate, needs_source_review",
        "",
        "| Candidate | Case | Ticker | Period | Label | Source Object | Span | Hash |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        span = f"{row.get('span_start_char', '')}-{row.get('span_end_char', '')}"
        lines.append(
            "| {candidate_id} | {case_id} | {ticker} | {period} | {label} | {object_id} | {span} | {hash} |".format(
                candidate_id=row.get("candidate_id", ""),
                case_id=row.get("case_id", ""),
                ticker=row.get("ticker", ""),
                period=row.get("fiscal_period", ""),
                label=row.get("label", ""),
                object_id=row.get("retrieval_object_id", ""),
                span=span,
                hash=row.get("provenance_hash", ""),
            )
        )
    if not rows:
        lines.append("| none |  |  |  |  |  |  |  |")
    return lines


def build_packets(candidates_path: Path = DEFAULT_CANDIDATES, packet_dir: Path = PACKET_DIR) -> dict[str, Any]:
    rows = read_jsonl(candidates_path)
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_summaries: list[dict[str, Any]] = []
    for filename, labels in PACKETS:
        packet_rows = [row for row in rows if row.get("label") in labels]
        target = packet_dir / filename
        title = filename.removesuffix(".md").replace("_", " ").title()
        target.write_text("\n".join(_packet_lines(title, packet_rows)) + "\n", encoding="utf-8")
        packet_summaries.append({"packet": str(target), "candidate_count": len(packet_rows), "labels": sorted(labels)})
    summary = {
        "candidate_count": len(rows),
        "packet_count": len(packet_summaries),
        "packets": packet_summaries,
        "label_counts": dict(sorted(Counter(row.get("label", "") for row in rows).items())),
        "gold_labels_created": 0,
        "raw_text_included": False,
    }
    write_summary(summary)
    return summary


def write_summary(summary: dict[str, Any], out_path: Path = SUMMARY_REPORT) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Review Packet Summary",
        "",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Packet count: {summary['packet_count']}",
        f"- Label counts: `{json.dumps(summary['label_counts'], sort_keys=True)}`",
        "- Gold labels created: 0",
        "- Raw evidence text included: false",
        "",
        "## Packets",
        "",
    ]
    for packet in summary["packets"]:
        lines.append(f"- `{packet['packet']}`: {packet['candidate_count']} candidates")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first30 review packets.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    args = parser.parse_args(argv)
    print(json.dumps(build_packets(args.candidates, args.packet_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
