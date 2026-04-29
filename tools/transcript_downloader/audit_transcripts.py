#!/usr/bin/env python3
"""Audit local earnings-call transcript quality without mutating raw files."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_common import (  # noqa: E402
    EXPECTED_ACTIVE_CASES,
    active_case_dirs,
    contains_block_phrase,
    enforce_exact_root,
    enforce_repo_safety,
    load_sources,
    marker_flags,
    sha256_file,
    source_type_for,
    split_sections,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    return parser.parse_args()


BOILERPLATE_LINE_PATTERNS = (
    "copyright",
    "callstreet",
    "factset",
    "lseg",
    "global market intelligence",
    "all rights reserved",
    "www.",
    "corrected transcript",
    "edited transcript",
    "earnings call |",
    " - q4 2025 ",
    " - q1 2026 ",
)


def repeated_boilerplate_evidence(text: str) -> list[str]:
    counts: dict[str, int] = {}
    for line in text.splitlines():
        line = line.strip().lower()
        if not line or len(line) > 120:
            continue
        if line.endswith(":") or re_looks_like_speaker_name(line):
            continue
        if not any(pattern in line for pattern in BOILERPLATE_LINE_PATTERNS):
            continue
        counts[line] = counts.get(line, 0) + 1
    return [line for line, count in counts.items() if count >= 4][:5]


def re_looks_like_speaker_name(line: str) -> bool:
    words = line.replace(".", "").replace("-", " ").split()
    if not 1 <= len(words) <= 6:
        return False
    title_words = {"chief", "officer", "president", "executive", "chair", "analyst", "director", "founder"}
    if any(word in title_words for word in words):
        return False
    return all(word[:1].isalpha() for word in words)


def audit_case(case_dir: Path, source_map: dict[str, object]) -> dict[str, object]:
    transcript = case_dir / "raw" / "transcript.txt"
    pdf = case_dir / "raw" / "transcript.pdf"
    warnings: list[str] = []
    text = ""
    exists = transcript.exists()
    if exists:
        text = transcript.read_text(encoding="utf-8", errors="replace")
    else:
        warnings.append("transcript missing")
    flags = marker_flags(text)
    if exists and len(text) < 15000:
        warnings.append("transcript < 15,000 chars")
    if exists and not flags["contains_operator"]:
        warnings.append("no Operator marker (host-led call flow possible)")
    if exists and not flags["contains_q_and_a"]:
        inferred = bool(split_sections(text).get("q_and_a"))
        if inferred:
            warnings.append("formal Q&A marker missing (Q&A inferred from transition)")
        else:
            warnings.append("no Q&A marker")
    boilerplate = repeated_boilerplate_evidence(text) if exists else []
    if boilerplate:
        warnings.append("repeated vendor/page boilerplate appears")
    if exists and contains_block_phrase(text):
        warnings.append("critical: login/paywall/block detected")
    likely_complete = bool(
        exists
        and len(text) >= 15000
        and flags["contains_any_earnings_marker"]
        and not contains_block_phrase(text)
    )
    info = source_map.get(case_dir.name)
    return {
        "case_id": case_dir.name,
        "transcript_exists": exists,
        "character_count": len(text),
        "line_count": len(text.splitlines()) if text else 0,
        "pdf_exists": pdf.exists(),
        "source_type": source_type_for(case_dir, info),
        "contains_operator": flags["contains_operator"],
        "contains_q_and_a": flags["contains_q_and_a"],
        "contains_safe_harbor": flags["contains_safe_harbor"],
        "likely_complete": likely_complete,
        "warnings": "; ".join(warnings),
        "sha256": sha256_file(transcript) if exists else "",
    }


def duplicate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_hash: dict[str, list[str]] = {}
    for row in rows:
        digest = str(row.get("sha256") or "")
        if digest:
            by_hash.setdefault(digest, []).append(str(row["case_id"]))
    duplicates: list[dict[str, object]] = []
    for digest, cases in by_hash.items():
        if len(cases) > 1:
            for case_id in cases:
                duplicates.append({"case_id": case_id, "sha256": digest, "duplicate_group": ",".join(cases)})
    return duplicates


def render_markdown(rows: list[dict[str, object]], duplicates: list[dict[str, object]]) -> str:
    passed = sum(1 for row in rows if row["likely_complete"] and not row["warnings"])
    warning = sum(1 for row in rows if row["likely_complete"] and row["warnings"])
    failed = sum(1 for row in rows if not row["likely_complete"])
    lines = [
        "# Transcript Quality Audit",
        "",
        "Transcript-first local audit. Raw transcripts are not modified.",
        "",
        f"- active_cases: {len(rows)}",
        f"- expected_active_cases: {EXPECTED_ACTIVE_CASES}",
        f"- pass: {passed}",
        f"- warning: {warning}",
        f"- fail: {failed}",
        f"- duplicate_transcripts: {len(duplicates)}",
        "",
        "| case_id | chars | pdf | complete | warnings |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['character_count']} | {row['pdf_exists']} | {row['likely_complete']} | {row['warnings']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    source_map = load_sources()
    rows = [audit_case(case_dir, source_map) for case_dir in active_case_dirs(root)]
    duplicates = duplicate_rows(rows)
    write_csv(
        root / "transcript_quality_audit.csv",
        rows,
        [
            "case_id",
            "transcript_exists",
            "character_count",
            "line_count",
            "pdf_exists",
            "source_type",
            "contains_operator",
            "contains_q_and_a",
            "contains_safe_harbor",
            "likely_complete",
            "warnings",
            "sha256",
        ],
    )
    write_csv(root / "duplicate_transcripts.csv", duplicates, ["case_id", "sha256", "duplicate_group"])
    (root / "transcript_quality_audit.md").write_text(render_markdown(rows, duplicates), encoding="utf-8")
    print(f"Audit complete: {len(rows)} active case(s), {len(duplicates)} duplicate row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
