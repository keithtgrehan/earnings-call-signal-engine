#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _packet_rows(rows: list[dict[str, object]], start: int, end: int) -> str:
    lines = ["MACHINE CANDIDATES ONLY. Do not promote without human adjudication.", ""]
    for row in rows[start:end]:
        lines.extend(
            [
                f"## {row.get('candidate_id', 'unknown_candidate')}",
                f"- case_id: `{row.get('case_id', '')}`",
                f"- suggested_label: MACHINE CANDIDATE ONLY `{row.get('suggested_label', '')}`",
                f"- evidence_text: {row.get('evidence_text', row.get('redacted_preview', ''))}",
                f"- source_file: `{row.get('source_file', '')}`",
                f"- source_provenance: `{row.get('provenance_hash', '')}`",
                f"- contamination_preflags: `{row.get('contamination_preflags', [])}`",
                "- final_label:",
                "- reviewer:",
                "- rationale:",
                "- confidence:",
                "- adjudicator:",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build markdown reviewer packets from first-100 ranked queue.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/first_100_contamination_flags.jsonl")
    parser.add_argument("--out-dir", default="data/review/packets")
    args = parser.parse_args(argv)
    rows = _load_jsonl(Path(args.in_path))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    packets = {
        "batch_001_calibration.md": (0, min(30, len(rows))),
        "batch_002_first_50.md": (0, min(50, len(rows))),
        "batch_003_second_50.md": (50, min(100, len(rows))),
    }
    for filename, (start, end) in packets.items():
        (out_dir / filename).write_text(_packet_rows(rows, start, end), encoding="utf-8")
    print(f"Reviewer packets written to {out_dir}; canonical gold labels unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
