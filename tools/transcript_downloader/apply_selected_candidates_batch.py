#!/usr/bin/env python3
"""Batch-apply selected candidate IDs as draft or human-approved labels."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_selected_gold_labels import (  # noqa: E402
    LABEL_STATUS_OUTPUT,
    build_labels_for_case,
    load_selected,
    validate_selected_row,
    write_labels_for_case,
)
from corpus_common import enforce_exact_root, enforce_repo_safety, write_csv  # noqa: E402

DEFAULT_ROOT = "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-csv", required=True)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--label-status", choices=sorted(LABEL_STATUS_OUTPUT), default="draft_reviewed")
    parser.add_argument("--reviewer", default=None)
    parser.add_argument("--overwrite-human-approved", action="store_true")
    parser.add_argument("--out-dir", default=None, help="Defaults to the selected CSV parent directory.")
    return parser.parse_args()


def group_by_case(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        validate_selected_row(row)
        grouped[row["case_id"].strip()].append(row)
    return grouped


def render_markdown(rows: list[dict[str, Any]], *, label_status: str) -> str:
    written = sum(1 for row in rows if row["status"] == "written")
    failed = sum(1 for row in rows if row["status"] == "failed")
    label_total = sum(int(row.get("label_count", 0)) for row in rows if row["status"] == "written")
    lines = [
        "# Selected Candidates Batch Report",
        "",
        f"- label_status: {label_status}",
        f"- cases_written: {written}",
        f"- cases_failed: {failed}",
        f"- labels_written: {label_total}",
        "",
        "Draft-reviewed labels are not final gold truth. Final benchmark evaluation uses only human-approved gold labels.",
        "",
        "| case_id | status | labels | output_path | notes |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['status']} | {row.get('label_count', 0)} | "
            f"`{row.get('output_path', '')}` | {row.get('notes', '')} |"
        )
    return "\n".join(lines) + "\n"


def apply_batch(
    *,
    root: Path,
    selected_rows: list[dict[str, str]],
    out_dir: Path,
    label_status: str,
    reviewer: str | None = None,
    overwrite_human_approved: bool = False,
) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    grouped = group_by_case(selected_rows)

    report_rows: list[dict[str, Any]] = []
    for case_id, rows in sorted(grouped.items()):
        case_dir = root / case_id
        try:
            labels = build_labels_for_case(
                root,
                case_id,
                rows,
                label_status=label_status,
                reviewer=reviewer,
            )
            out = write_labels_for_case(
                case_dir,
                labels,
                label_status=label_status,
                overwrite_human_approved=overwrite_human_approved,
            )
            report_rows.append(
                {
                    "case_id": case_id,
                    "status": "written",
                    "label_count": len(labels),
                    "output_path": str(out),
                    "notes": "",
                }
            )
        except (Exception, SystemExit) as exc:
            report_rows.append(
                {
                    "case_id": case_id,
                    "status": "failed",
                    "label_count": 0,
                    "output_path": "",
                    "notes": str(exc),
                }
            )

    fields = ["case_id", "status", "label_count", "output_path", "notes"]
    write_csv(out_dir / "selected_candidates_batch_report.csv", report_rows, fields)
    (out_dir / "selected_candidates_batch_report.md").write_text(
        render_markdown(report_rows, label_status=label_status),
        encoding="utf-8",
    )
    return report_rows


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    selected_csv = Path(args.selected_csv)
    out_dir = Path(args.out_dir) if args.out_dir else selected_csv.parent
    selected_rows = load_selected(selected_csv)
    report_rows = apply_batch(
        root=root,
        selected_rows=selected_rows,
        out_dir=out_dir,
        label_status=args.label_status,
        reviewer=args.reviewer,
        overwrite_human_approved=args.overwrite_human_approved,
    )
    failed = [row for row in report_rows if row["status"] == "failed"]
    print(
        "Selected candidates batch apply complete: "
        f"{len(report_rows) - len(failed)} written, {len(failed)} failed."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
