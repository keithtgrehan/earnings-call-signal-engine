from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .context import TranscriptIndex, resolve_transcript_files
from .parsers import parse_files, resolve_input_files
from .priority import priority_for, rule_family
from .schema import ReviewQueueRow, normalize_label, validate_row
from .writers import write_outputs

DEFAULT_OUT = "artifacts/gold_review"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a human adjudication queue from labeling packets and weak-label outputs.")
    parser.add_argument("--packets", nargs="+", action="append", required=True, help="Packet paths, globs, directories, or weak-label JSONL files.")
    parser.add_argument("--transcripts", nargs="+", action="append", default=[], help="Transcript paths, globs, or directories.")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output directory.")
    parser.add_argument("--context-chars", type=int, default=500, help="Approximate characters before and after evidence span.")
    parser.add_argument("--context-sentences", type=int, default=2, help="Approximate sentence window before and after evidence span.")
    parser.add_argument("--strict", action="store_true", help="Fail after writing outputs if rows are parse-incomplete or schema-invalid.")
    parser.add_argument("--include-jsonl", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include-csv", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verbose", action="store_true", help="Print parser and matcher detail.")
    return parser.parse_args(argv)


def flatten(values: list[list[str]] | None) -> list[str]:
    return [item for group in values or [] for item in group]


def build_queue(
    *,
    packet_values: list[str],
    transcript_values: list[str],
    context_chars: int = 500,
    context_sentences: int = 2,
    verbose: bool = False,
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    packet_files = resolve_input_files(packet_values)
    transcript_files = resolve_transcript_files(transcript_values)
    rows = parse_files(packet_files)
    transcript_index = TranscriptIndex(transcript_files)
    for row in rows:
        row["normalized_label"] = normalize_label(row.get("suggested_label", ""))
        row["rule_family"] = rule_family(row.get("reason", ""), row.get("source_type", ""))
        match = transcript_index.match(
            row.get("case_id", ""),
            row.get("evidence_span", ""),
            context_chars=context_chars,
            context_sentences=context_sentences,
        )
        row["context_before"] = match.context_before
        row["context_after"] = match.context_after
        row["surrounding_context"] = match.surrounding_context
        row["transcript_file_if_matched"] = match.transcript_file_if_matched
        row["evidence_match_status"] = match.evidence_match_status
        row["needs_context_lookup"] = "no" if match.transcript_file_if_matched else "yes"
        priority, reason, boilerplate = priority_for(row)
        row["likely_review_priority"] = priority
        row["priority_reason"] = reason
        row["is_likely_boilerplate"] = "yes" if boilerplate else "no"
    normalized_rows = [ReviewQueueRow.from_mapping(row).to_dict() for row in rows]
    validation_issues = [issue.to_dict() for row in normalized_rows for issue in validate_row(row)]
    metadata = {
        "packet_files": [str(path) for path in packet_files],
        "transcript_files": [str(path) for path in transcript_files],
        "row_count": len(normalized_rows),
        "validation_issue_count": len(validation_issues),
        "parser_warning_count": sum(1 for row in normalized_rows if row.get("parser_warning")),
    }
    if verbose:
        print(json.dumps(metadata, indent=2))
    return normalized_rows, validation_issues, metadata


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows, validation_issues, metadata = build_queue(
        packet_values=flatten(args.packets),
        transcript_values=flatten(args.transcripts),
        context_chars=args.context_chars,
        context_sentences=args.context_sentences,
        verbose=args.verbose,
    )
    out_dir = Path(args.out)
    write_outputs(out_dir, rows, validation_issues, include_csv=args.include_csv, include_jsonl=args.include_jsonl)
    summary = {
        "status": "ok",
        "out": str(out_dir),
        **metadata,
    }
    print(json.dumps(summary, indent=2))
    if args.strict and (metadata["parser_warning_count"] or validation_issues):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
