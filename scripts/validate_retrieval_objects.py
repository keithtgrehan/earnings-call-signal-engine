#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from resource_registry_common import load_jsonl, write_json

REQUIRED_RETRIEVAL_FIELDS = {
    "object_id",
    "object_type",
    "case_id",
    "company",
    "fiscal_period",
    "source_type",
    "source_ref",
    "section",
    "speaker",
    "topic",
    "span_hints",
    "evidence_text",
    "redacted_evidence_preview",
    "provenance",
    "rights_tier",
    "raw_text_commit_allowed",
}

VALID_OBJECT_TYPES = {"semantic_chunk", "event_aligned_chunk", "evidence_object"}


def validate_schema(path: Path) -> list[str]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    required = set(schema.get("required", []))
    missing = sorted(REQUIRED_RETRIEVAL_FIELDS - required)
    errors = [f"schema missing required field {field}" for field in missing]
    object_type = schema.get("properties", {}).get("object_type", {})
    enum_values = set(object_type.get("enum", []))
    for value in sorted(VALID_OBJECT_TYPES - enum_values):
        errors.append(f"schema missing object_type enum {value}")
    provenance = schema.get("properties", {}).get("provenance", {})
    if "provenance_hash" not in set(provenance.get("required", [])):
        errors.append("schema provenance must require provenance_hash")
    return errors


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        missing = sorted(REQUIRED_RETRIEVAL_FIELDS - set(row))
        for field in missing:
            errors.append(f"row {index}: missing required field {field}")
        if row.get("object_type") not in VALID_OBJECT_TYPES:
            errors.append(f"row {index}: invalid object_type {row.get('object_type')!r}")
        provenance = row.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("source_path") or not provenance.get("provenance_hash"):
            errors.append(f"row {index}: missing provenance source_path or provenance_hash")
        if row.get("object_type") == "evidence_object" and int(row.get("retrieval_priority", 1)) > 1:
            errors.append(f"row {index}: evidence_object should have highest retrieval priority")
        if row.get("deterministic_output_override_allowed") is True:
            errors.append(f"row {index}: retrieval objects must not override deterministic extraction")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate retrieval object schema and optional JSONL rows.")
    parser.add_argument("--schema", default="schemas/retrieval_object.schema.json")
    parser.add_argument("--path", help="Optional retrieval-object JSONL file to validate.")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    errors = validate_schema(Path(args.schema))
    row_count = 0
    if args.path:
        rows = load_jsonl(Path(args.path))
        row_count = len(rows)
        errors.extend(validate_rows(rows))
    summary = {"status": "valid" if not errors else "invalid", "row_count": row_count, "errors": errors}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if errors:
        print(f"Retrieval object validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Retrieval object validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
