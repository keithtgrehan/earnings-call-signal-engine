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
    clean_text,
    gold_label_from_review,
    normalize_action,
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


def response_value(row: dict[str, Any], name: str) -> str:
    responses = row.get("responses")
    if isinstance(responses, list):
        for response in responses:
            if not isinstance(response, dict):
                continue
            if clean_text(response.get("question_name")) == name:
                values = response.get("values")
                if isinstance(values, list) and values:
                    return clean_text(values[0])
                return clean_text(response.get("value"))
    return ""


def canonical_from_argilla(row: dict[str, Any], *, row_number: int) -> dict[str, Any]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    canonical = {field: metadata.get(field, "") for field in CANONICAL_REVIEW_FIELDS}
    for field in CANONICAL_REVIEW_FIELDS:
        if not clean_text(canonical.get(field)) and field in fields:
            canonical[field] = fields[field]
    if not clean_text(canonical.get("review_id")):
        canonical["review_id"] = clean_text(row.get("id"))
    action = response_value(row, "reviewer_action") or clean_text(row.get("reviewer_action")) or clean_text(canonical.get("reviewer_action"))
    canonical["reviewer_action"] = normalize_action(action)
    canonical["reviewer_notes"] = response_value(row, "reviewer_notes") or clean_text(row.get("reviewer_notes")) or clean_text(canonical.get("reviewer_notes"))
    canonical["reviewer_id"] = clean_text(row.get("reviewer_id")) or clean_text(canonical.get("reviewer_id"))
    canonical["review_status"] = "reviewed"
    canonical["confidence"] = float(canonical.get("confidence") or 0.0)
    issues = validate_canonical_review(canonical, row_number=row_number, require_reviewed=True)
    if issues:
        rendered = "\n".join(f"row {issue.row_number} `{issue.field}`: {issue.message}" for issue in issues)
        raise ValueError(rendered)
    return canonical


def import_reviews(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reviews: list[dict[str, Any]] = []
    gold_labels: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        review = canonical_from_argilla(row, row_number=index)
        reviews.append(review)
        gold = gold_label_from_review(review)
        if gold is not None:
            gold_labels.append(gold)
    return reviews, gold_labels


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import reviewed Argilla JSONL into canonical reviewed rows and gold-label JSONL.")
    parser.add_argument("--input-jsonl", required=True, help="Reviewed Argilla export JSONL.")
    parser.add_argument("--gold-output", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--review-output", default=str(ROOT / "data" / "review" / "canonical_reviews.jsonl"))
    parser.add_argument("--append", action="store_true", help="Append valid gold labels to existing output instead of replacing it.")
    args = parser.parse_args(argv)

    source = Path(args.input_jsonl)
    if not source.exists():
        raise SystemExit(f"review JSONL not found: {source}")
    try:
        reviews, gold_labels = import_reviews(read_jsonl(source))
    except ValueError as exc:
        raise SystemExit(f"Argilla review import failed closed:\n{exc}") from exc

    gold_path = Path(args.gold_output)
    if args.append and gold_path.exists():
        existing = read_jsonl(gold_path)
        gold_labels = [*existing, *gold_labels]
    write_jsonl(gold_path, gold_labels)
    write_jsonl(Path(args.review_output), reviews)
    print(json.dumps({"review_rows": len(reviews), "gold_labels_written": len(gold_labels), "gold_output": str(gold_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
