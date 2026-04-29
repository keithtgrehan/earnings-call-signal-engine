#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


OUTPUT_COLUMNS = [
    "id",
    "domain",
    "transcript_text",
    "expected_signal_family",
    "expected_review_action",
    "audio_file_to_add",
    "audio_start_seconds",
    "audio_end_seconds",
    "audio_rights_confirmed",
    "reviewer_notes",
]


def _load_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_intake_rows(pilot_path: Path) -> list[dict[str, str]]:
    cases = _load_rows(pilot_path)
    return [
        {
            "id": case["id"],
            "domain": case["domain"],
            "transcript_text": case["transcript_text"],
            "expected_signal_family": case["expected_signal_family"],
            "expected_review_action": case["expected_review_action"],
            "audio_file_to_add": "",
            "audio_start_seconds": "",
            "audio_end_seconds": "",
            "audio_rights_confirmed": "",
            "reviewer_notes": "",
        }
        for case in cases
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a CSV intake sheet for future aligned audio pilot collection."
    )
    parser.add_argument(
        "--input-path",
        default=str(ROOT / "data" / "multimodal_research" / "multimodal_pilot_cases.jsonl"),
        help="Path to the multimodal pilot case JSONL.",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "multimodal_research" / "audio_pilot_intake.csv"),
        help="Path to the audio intake CSV output.",
    )
    args = parser.parse_args(argv)

    rows = build_intake_rows(Path(args.input_path))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({"status": "ok", "row_count": len(rows), "out": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
