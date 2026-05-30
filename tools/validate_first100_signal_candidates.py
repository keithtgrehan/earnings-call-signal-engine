#!/usr/bin/env python3
"""Validate first100 signal candidates are metadata-only pending review rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.first30_extraction import validate_first100_candidate_rows  # noqa: E402

DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
DEFAULT_RETRIEVAL_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_EVIDENCE = ROOT / "data" / "acquisition" / "nyse_100_evidence_objects_manifest.csv"
DEFAULT_CHUNKS = ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
REPORT_PATH = ROOT / "reports" / "extraction" / "first100_signal_candidate_validation.md"
JSON_REPORT_PATH = ROOT / "reports" / "extraction" / "first100_signal_candidate_validation.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate(
    path: Path = DEFAULT_CANDIDATES,
    retrieval_objects: Path = DEFAULT_RETRIEVAL_OBJECTS,
    evidence_manifest: Path = DEFAULT_EVIDENCE,
    chunk_manifest: Path = DEFAULT_CHUNKS,
    out_path: Path = REPORT_PATH,
    json_out_path: Path = JSON_REPORT_PATH,
) -> dict[str, Any]:
    rows = read_jsonl(path)
    retrieval_ids = {row.get("object_id", "") for row in read_csv(retrieval_objects) if row.get("object_id")}
    evidence_ids = {row.get("evidence_id", "") for row in read_csv(evidence_manifest) if row.get("evidence_id")}
    chunk_ids = {row.get("chunk_id", "") for row in read_csv(chunk_manifest) if row.get("chunk_id")}
    errors = validate_first100_candidate_rows(rows, retrieval_object_ids=retrieval_ids, evidence_ids=evidence_ids, chunk_ids=chunk_ids)
    summary = {
        "candidate_rows": len(rows),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors[:200],
        "gold_labels_created": 0,
        "raw_text_committed": False,
        "weak_labels_promoted": 0,
        "training_performed": False,
    }
    write_report(summary, out_path)
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    json_out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def write_report(summary: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Signal Candidate Validation",
        "",
        f"- Candidate rows: {summary['candidate_rows']}",
        f"- Valid: {str(summary['valid']).lower()}",
        f"- Error count: {summary['error_count']}",
        "- Gold labels created: 0",
        "- Weak labels promoted: 0",
        "- Raw evidence text committed: false",
        "- Training performed: false",
        "",
        "## Errors",
        "",
    ]
    errors = summary.get("errors") or []
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate first100 signal candidate guardrails.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--retrieval-objects", type=Path, default=DEFAULT_RETRIEVAL_OBJECTS)
    parser.add_argument("--evidence-manifest", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--chunk-manifest", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_REPORT_PATH)
    args = parser.parse_args(argv)
    summary = validate(args.candidates, args.retrieval_objects, args.evidence_manifest, args.chunk_manifest, args.out, args.json_out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
