#!/usr/bin/env python3
"""Build metadata-only first100 review packets from signal candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
PACKET_DIR = ROOT / "data" / "review" / "packets"
SUMMARY_REPORT = ROOT / "reports" / "review" / "first100_review_packet_summary.md"

PACKETS = [
    ("first100_batch_001_guidance.md", {"guidance_revision", "guidance_statement"}),
    ("first100_batch_002_qa_friction.md", {"analyst_pressure"}),
    ("first100_batch_003_hedging_uncertainty.md", {"management_hedging", "uncertainty"}),
    ("first100_batch_004_reassurance_answer_shift.md", {"reassurance", "answer_shift"}),
    ("first100_batch_005_neutral_suppression.md", {"neutral/no_signal"}),
]

PACKET_COLUMNS = [
    "candidate_id",
    "case_id",
    "ticker",
    "fiscal_period",
    "suggested_label",
    "evidence_object_id",
    "chunk_id",
    "source_hashes",
    "metadata",
    "review_blanks",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _packet_lines(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        f"# {title}",
        "",
        "- Review mode: metadata-only first100 signal candidates",
        "- Suggested label status: MACHINE CANDIDATE ONLY",
        "- Gold labels in this packet: 0",
        "- Raw evidence text included: false",
        "- Decision options: accept_candidate, reject_candidate, needs_source_review, needs_adjudication",
        "",
        "| Candidate | Case | Ticker | Period | Suggested Label | Evidence/Chunk | Source/Hashes | Section/Speaker/Flags | Review Fields |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        evidence = f"evidence={row.get('evidence_object_id', '')}<br>chunk={row.get('chunk_id', '')}<br>retrieval={row.get('retrieval_object_id', '')}"
        hashes = (
            f"source_path={row.get('source_path', '')}<br>"
            f"source_sha256={row.get('source_sha256', '')}<br>"
            f"normalized={row.get('normalized_transcript_hash', '')}<br>"
            f"text_hash={row.get('text_hash', '')}<br>"
            f"provenance_hash={row.get('provenance_hash', '')}"
        )
        metadata = (
            f"section={row.get('transcript_section', '')}<br>"
            f"speaker={row.get('speaker_role', '')}<br>"
            f"rule={row.get('rule_id', '')}@{row.get('rule_version', '')}<br>"
            f"flags={row.get('contamination_flags', '')}"
        )
        review_blanks = "final_label=<br>reviewer=<br>rationale=<br>adjudicator=<br>adjudicated_at="
        lines.append(
            "| {candidate_id} | {case_id} | {ticker} | {period} | MACHINE CANDIDATE ONLY: {label} ({confidence}) | {evidence} | {hashes} | {metadata} | {review_blanks} |".format(
                candidate_id=_escape(row.get("candidate_id", "")),
                case_id=_escape(row.get("case_id", "")),
                ticker=_escape(row.get("ticker", "")),
                period=_escape(row.get("fiscal_period", "")),
                label=_escape(row.get("suggested_label", "")),
                confidence=_escape(row.get("suggested_confidence", "")),
                evidence=_escape(evidence),
                hashes=_escape(hashes),
                metadata=_escape(metadata),
                review_blanks=review_blanks,
            )
        )
    if not rows:
        lines.append("| none |  |  |  |  |  |  |  |  |")
    return lines


def build_packets(candidates_path: Path = DEFAULT_CANDIDATES, packet_dir: Path = PACKET_DIR) -> dict[str, Any]:
    rows = read_jsonl(candidates_path)
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_summaries: list[dict[str, Any]] = []
    for filename, labels in PACKETS:
        packet_rows = [row for row in rows if row.get("suggested_label") in labels]
        target = packet_dir / filename
        title = filename.removesuffix(".md").replace("_", " ").title()
        target.write_text("\n".join(_packet_lines(title, packet_rows)) + "\n", encoding="utf-8")
        packet_summaries.append({"packet": str(target), "candidate_count": len(packet_rows), "labels": sorted(labels)})
    summary = {
        "candidate_count": len(rows),
        "packet_count": len(packet_summaries),
        "packets": packet_summaries,
        "label_counts": dict(sorted(Counter(row.get("suggested_label", "") for row in rows).items())),
        "gold_labels_created": 0,
        "raw_text_included": False,
        "columns": PACKET_COLUMNS,
    }
    write_summary(summary)
    return summary


def write_summary(summary: dict[str, Any], out_path: Path = SUMMARY_REPORT) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Review Packet Summary",
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
    parser = argparse.ArgumentParser(description="Build first100 review packets.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    args = parser.parse_args(argv)
    print(json.dumps(build_packets(args.candidates, args.packet_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
