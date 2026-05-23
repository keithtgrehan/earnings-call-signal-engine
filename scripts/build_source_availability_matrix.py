#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import _load_targets, build_source_availability_matrix, write_csv, write_markdown

FIELDS = [
    "case_id",
    "ticker",
    "fiscal_period",
    "transcript_status",
    "audio_status",
    "video_status",
    "slides_status",
    "official_ir_candidate",
    "sec_candidate",
    "webcast_candidate",
    "youtube_metadata_only",
    "manual_local_registered",
    "vendor_blocked",
    "rights_status",
    "blocked_reason_code",
    "provenance_complete",
    "next_manual_action",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build unified source availability matrix.")
    parser.add_argument("--targets", default="data/corpus/nyse_5y_target_universe.example.yml")
    parser.add_argument("--csv-out", default="reports/agent5/source_availability_matrix.csv")
    parser.add_argument("--report", default="reports/agent5/source_availability_matrix.md")
    args = parser.parse_args(argv)
    rows = build_source_availability_matrix(_load_targets(Path(args.targets)))
    write_csv(Path(args.csv_out), rows, FIELDS)
    write_markdown(Path(args.report), "Source Availability Matrix", [f"- Rows: `{len(rows)}`", "- This matrix is metadata/readiness only.", "- Target rows are not proof of transcript availability."])
    print(f"Source availability matrix written: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
