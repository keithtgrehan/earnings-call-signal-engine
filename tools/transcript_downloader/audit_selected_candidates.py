#!/usr/bin/env python3
"""Audit selected-candidate CSV files before any label conversion."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_selected_gold_labels import ALLOWED_CONFIDENCE, ALLOWED_TYPES, parse_packet  # noqa: E402
from corpus_common import active_case_dirs, enforce_exact_root, enforce_repo_safety, write_csv  # noqa: E402

DEFAULT_ROOT = "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
REQUIRED_COLUMNS = ("case_id", "candidate_id", "type", "confidence", "notes")
CASE_ID_RE = re.compile(r"^[A-Z]+_[0-9]{4}_Q[1-4]$")
BOILERPLATE_RE = re.compile(
    r"\b("
    r"operator|you may disconnect|forward-looking|actual results may differ|safe harbor|"
    r"replay|webcast|copyright|welcome to|conference coordinator"
    r")\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-csv", required=True)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--out-dir", default=None, help="Defaults to the selected CSV parent directory.")
    return parser.parse_args()


def read_selected(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    return rows, missing


def valid_candidate_id(case_id: str, candidate_id: str) -> bool:
    return bool(re.fullmatch(re.escape(case_id) + r"_CAND_[0-9]{2,3}", candidate_id))


def load_packet_candidates(root: Path, case_id: str) -> dict[str, str]:
    packet = root / case_id / "labels" / "human_labeling_packet.md"
    if not packet.exists():
        return {}
    return parse_packet(packet)


def audit_rows(rows: list[dict[str, str]], *, root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    active_cases = {path.name for path in active_case_dirs(root)} if root.exists() else set()
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    candidate_counts = Counter((row.get("case_id", "").strip(), row.get("candidate_id", "").strip()) for row in rows)
    packet_cache: dict[str, dict[str, str]] = {}
    for row in rows:
        by_case[row.get("case_id", "").strip()].append(row)

    case_level_warnings: dict[str, list[str]] = {}
    for case_id, case_rows in by_case.items():
        warnings: list[str] = []
        neutral_count = sum(1 for row in case_rows if row.get("type", "").strip() == "neutral")
        if len(case_rows) < 5:
            warnings.append("case_has_fewer_than_5_rows")
        if len(case_rows) > 15:
            warnings.append("case_has_more_than_15_rows")
        if neutral_count > 5 or (case_rows and neutral_count / len(case_rows) > 0.5):
            warnings.append("too_many_neutral_rows")
        case_level_warnings[case_id] = warnings

    audited: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=2):
        case_id = row.get("case_id", "").strip()
        candidate_id = row.get("candidate_id", "").strip()
        label_type = row.get("type", "").strip()
        confidence = row.get("confidence", "").strip()
        notes = row.get("notes", "").strip()
        warnings = list(case_level_warnings.get(case_id, []))

        if not CASE_ID_RE.fullmatch(case_id):
            warnings.append("invalid_case_id_format")
        if active_cases and case_id not in active_cases:
            warnings.append("case_not_found_in_active_corpus")
        if label_type not in ALLOWED_TYPES:
            warnings.append("invalid_type")
        if confidence not in ALLOWED_CONFIDENCE:
            warnings.append("invalid_confidence")
        if not notes:
            warnings.append("missing_notes")
        if not valid_candidate_id(case_id, candidate_id):
            warnings.append("invalid_candidate_id_format")
        if candidate_counts[(case_id, candidate_id)] > 1:
            warnings.append("duplicate_candidate_id")

        if case_id not in packet_cache:
            packet_cache[case_id] = load_packet_candidates(root, case_id)
        packet_candidates = packet_cache[case_id]
        quote = packet_candidates.get(candidate_id, "")
        if packet_candidates and candidate_id not in packet_candidates:
            warnings.append("candidate_not_found_in_packet")
        if quote and label_type != "neutral" and BOILERPLATE_RE.search(quote):
            warnings.append("likely_boilerplate_mapped_to_signal")

        audited.append(
            {
                "row_number": index,
                "case_id": case_id,
                "candidate_id": candidate_id,
                "type": label_type,
                "confidence": confidence,
                "notes_present": bool(notes),
                "duplicate_candidate_id": candidate_counts[(case_id, candidate_id)] > 1,
                "valid_case_id": bool(CASE_ID_RE.fullmatch(case_id)),
                "case_exists": case_id in active_cases if active_cases else "",
                "valid_candidate_id": valid_candidate_id(case_id, candidate_id),
                "candidate_in_packet": candidate_id in packet_candidates if packet_candidates else "",
                "boilerplate_warning": "likely_boilerplate_mapped_to_signal" in warnings,
                "warnings": "; ".join(dict.fromkeys(warnings)),
                "status": "warning" if warnings else "pass",
            }
        )

    summary = {
        "row_count": len(rows),
        "case_count": len(by_case),
        "warning_rows": sum(1 for row in audited if row["warnings"]),
        "duplicate_rows": sum(1 for row in audited if row["duplicate_candidate_id"]),
        "cases_fewer_than_5": sum(1 for warnings in case_level_warnings.values() if "case_has_fewer_than_5_rows" in warnings),
        "cases_more_than_15": sum(1 for warnings in case_level_warnings.values() if "case_has_more_than_15_rows" in warnings),
        "cases_too_many_neutral": sum(1 for warnings in case_level_warnings.values() if "too_many_neutral_rows" in warnings),
        "case_level_warnings": case_level_warnings,
    }
    return audited, summary


def render_markdown(rows: list[dict[str, Any]], summary: dict[str, Any], missing_columns: list[str]) -> str:
    warning_counts: Counter[str] = Counter()
    for row in rows:
        for warning in str(row["warnings"]).split("; "):
            if warning:
                warning_counts[warning] += 1
    lines = [
        "# Selected Candidates Audit",
        "",
        "This audit checks selected candidate CSVs before conversion. Assistant-reviewed selections remain draft unless explicitly converted with human approval.",
        "",
        f"- rows: {summary['row_count']}",
        f"- cases: {summary['case_count']}",
        f"- warning_rows: {summary['warning_rows']}",
        f"- duplicate_candidate_rows: {summary['duplicate_rows']}",
    ]
    if missing_columns:
        lines.append(f"- missing_columns: {', '.join(missing_columns)}")
    lines.extend(["", "## Warning Counts", ""])
    if warning_counts:
        for warning, count in warning_counts.most_common():
            lines.append(f"- {warning}: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Case Row Counts", "", "| case_id | rows | warnings |", "| --- | ---: | --- |"])
    by_case = Counter(str(row["case_id"]) for row in rows)
    for case_id in sorted(by_case):
        warnings = "; ".join(summary["case_level_warnings"].get(case_id, []))
        lines.append(f"| {case_id} | {by_case[case_id]} | {warnings} |")
    lines.extend(
        [
            "",
            "Rows with warnings should be reviewed before conversion. This report does not create or promote gold labels.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    selected_csv = Path(args.selected_csv)
    out_dir = Path(args.out_dir) if args.out_dir else selected_csv.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, missing_columns = read_selected(selected_csv)
    if missing_columns:
        audited: list[dict[str, Any]] = []
        summary = {
            "row_count": len(rows),
            "case_count": 0,
            "warning_rows": len(rows),
            "duplicate_rows": 0,
            "case_level_warnings": {},
        }
    else:
        audited, summary = audit_rows(rows, root=root)
    fields = [
        "row_number",
        "case_id",
        "candidate_id",
        "type",
        "confidence",
        "notes_present",
        "duplicate_candidate_id",
        "valid_case_id",
        "case_exists",
        "valid_candidate_id",
        "candidate_in_packet",
        "boilerplate_warning",
        "warnings",
        "status",
    ]
    write_csv(out_dir / "selected_candidates_audit.csv", audited, fields)
    (out_dir / "selected_candidates_audit.md").write_text(
        render_markdown(audited, summary, missing_columns),
        encoding="utf-8",
    )
    print(
        "Selected candidates audit complete: "
        f"{summary['row_count']} row(s), {summary['warning_rows']} warning row(s)."
    )
    return 1 if missing_columns else 0


if __name__ == "__main__":
    raise SystemExit(main())
