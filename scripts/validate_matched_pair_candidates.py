#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.matched_pair_resolver import MATCHED_PAIR_FIELDS, summarize_matched_pair_rows, validate_matched_pair_row

REPORT_PATH = ROOT / "reports" / "acquisition" / "matched_pair_asset_status.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate_file(path: Path) -> dict[str, object]:
    rows = read_rows(path)
    errors: list[dict[str, object]] = []
    header_errors = [field for field in MATCHED_PAIR_FIELDS if rows and field not in rows[0]]
    for field in header_errors:
        errors.append({"row": 1, "error": f"missing required column {field}"})
    if not header_errors:
        for index, row in enumerate(rows, start=2):
            for error in validate_matched_pair_row(row, repo_root=ROOT):
                errors.append({"row": index, "case_id": row.get("case_id", ""), "error": error})
    summary = summarize_matched_pair_rows(rows)
    summary["errors"] = errors
    return summary


def write_report(summary: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Matched-Pair Asset Status",
        "",
        f"- Candidate rows: {summary['rows']}",
        f"- Validation errors: {len(summary['errors'])}",
        "- Raw transcript/audio committed: false",
        "- Unknown rights fail closed: true",
        "",
        "## Status Counts",
    ]
    for status, count in sorted(dict(summary["statuses"]).items()):
        lines.append(f"- {status or 'blank'}: {count}")
    lines.append("")
    lines.append("## Blocker Counts")
    for blocker, count in sorted(dict(summary["blockers"]).items()):
        lines.append(f"- {blocker or 'blank'}: {count}")
    if summary["errors"]:
        lines.append("")
        lines.append("## Errors")
        for error in summary["errors"]:
            lines.append(f"- row {error.get('row')}: {error.get('case_id', '')} {error.get('error')}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate matched transcript/audio candidate metadata.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    summary = validate_file(args.path)
    write_report(summary)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"matched_pair_candidates rows={summary['rows']} errors={len(summary['errors'])}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
