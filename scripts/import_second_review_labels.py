#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.signal_baseline import SIGNAL_FAMILY_LABELS  # noqa: E402


REQUIRED_COLUMNS = [
    "id",
    "text",
    "current_label",
    "reviewer_label",
    "reviewer_confidence",
    "reviewer_notes",
    "evidence_terms",
    "rationale",
]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing required columns {missing}: {path}")
        return [{column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS} for row in reader]


def _validate_rows(rows: list[dict[str, str]]) -> int:
    labeled_count = 0
    for row in rows:
        current_label = row["current_label"]
        reviewer_label = row["reviewer_label"]
        if current_label not in SIGNAL_FAMILY_LABELS:
            raise ValueError(f"Invalid current_label '{current_label}' for row {row['id']}")
        if reviewer_label:
            if reviewer_label not in SIGNAL_FAMILY_LABELS:
                raise ValueError(f"Invalid reviewer_label '{reviewer_label}' for row {row['id']}")
            labeled_count += 1
    return labeled_count


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a second-review label CSV into the canonical import template."
    )
    parser.add_argument(
        "--input-csv",
        default=str(ROOT / "data" / "nlp_research" / "review_packets" / "signal_labels_review_packet.csv"),
        help="Path to the source review CSV.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(ROOT / "data" / "nlp_research" / "second_review_template.csv"),
        help="Path to the normalized second-review CSV.",
    )
    args = parser.parse_args(argv)

    input_csv = Path(args.input_csv)
    output_csv = Path(args.output_csv)
    rows = _read_rows(input_csv)
    labeled_count = _validate_rows(rows)
    _write_rows(output_csv, rows)

    status = {
        "status": "ready_for_agreement" if labeled_count else "blocked",
        "row_count": len(rows),
        "reviewer_label_count": labeled_count,
        "output_csv": str(output_csv),
    }
    if not labeled_count:
        status["reason"] = "No reviewer_label values are filled in yet."
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
