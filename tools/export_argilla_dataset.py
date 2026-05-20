#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.review_schema import (  # noqa: E402
    CANONICAL_REVIEW_FIELDS,
    canonical_review_from_signal,
    validate_canonical_review,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(item)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def argilla_record(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": review["review_id"],
        "fields": {
            "case_id": review["case_id"],
            "signal_type": review["signal_type"],
            "topic": review["topic"],
            "transcript_section": review["transcript_section"],
            "speaker_role": review["speaker_role"],
            "evidence_text": review["evidence_text"],
            "predicted_direction": review["predicted_direction"],
            "source_url": review["source_url"],
            "transcript_path": review["transcript_path"],
        },
        "metadata": {field: review[field] for field in CANONICAL_REVIEW_FIELDS},
        "suggestions": [
            {
                "question_name": "reviewer_action",
                "value": "uncertain",
                "agent": "deterministic_signal_engine",
                "score": review["confidence"],
            }
        ],
        "responses": [],
    }


def export_reviews(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exported: list[dict[str, Any]] = []
    issues: list[str] = []
    for index, row in enumerate(rows, start=1):
        review = canonical_review_from_signal(row, row_number=index)
        row_issues = validate_canonical_review(review, row_number=index)
        if row_issues:
            issues.extend(f"row {issue.row_number} `{issue.field}`: {issue.message}" for issue in row_issues)
            continue
        exported.append(argilla_record(review))
    if issues:
        raise ValueError("Argilla export validation failed:\n" + "\n".join(issues))
    return exported


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export deterministic signal JSONL rows to an Argilla-ready local JSONL dataset.")
    parser.add_argument("--input-jsonl", required=True, help="Deterministic signal output JSONL.")
    parser.add_argument("--output-jsonl", required=True, help="Argilla-ready review JSONL.")
    args = parser.parse_args(argv)

    source = Path(args.input_jsonl)
    if not source.exists():
        raise SystemExit(f"input JSONL not found: {source}")
    rows = read_jsonl(source)
    exported = export_reviews(rows)
    write_jsonl(Path(args.output_jsonl), exported)
    print(json.dumps({"input_rows": len(rows), "exported_rows": len(exported), "output": args.output_jsonl}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
