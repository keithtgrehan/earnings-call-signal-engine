#!/usr/bin/env python3
"""Build first100 review readiness dashboard."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
NORMALIZED = ROOT / "data" / "corpus" / "normalized_transcript_manifest.csv"
CHUNKS = ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
EVIDENCE = ROOT / "data" / "acquisition" / "nyse_100_evidence_objects_manifest.csv"
RETRIEVAL = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
CALIBRATION = ROOT / "data" / "review" / "staging" / "first100_calibration_batch_001.jsonl"
PROMOTION = ROOT / "reports" / "review" / "first100_promotion_manifest_validation.json"
ADJUDICATION_VALIDATION = ROOT / "reports" / "review" / "first100_adjudication_file_validation.json"
TRAINING = ROOT / "reports" / "review" / "first100_training_readiness.json"
PACKET_DIR = ROOT / "data" / "review" / "packets"
REPORT_PATH = ROOT / "reports" / "review" / "review_readiness_dashboard.md"
JSON_REPORT_PATH = ROOT / "reports" / "review" / "review_readiness_dashboard.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_dashboard(out_path: Path = REPORT_PATH, json_out_path: Path = JSON_REPORT_PATH) -> dict[str, Any]:
    candidates = read_jsonl(CANDIDATES)
    calibration = read_jsonl(CALIBRATION)
    promotion = read_json(PROMOTION)
    adjudication = read_json(ADJUDICATION_VALIDATION)
    training = read_json(TRAINING)
    packets = sorted(PACKET_DIR.glob("first100_batch_*.md"))
    label_counts = Counter(row.get("suggested_label", "") for row in candidates)
    case_counts = Counter(row.get("case_id", "") for row in candidates)
    top_blockers = []
    if len(candidates) < 100:
        top_blockers.append(f"candidate expansion below 100: {len(candidates)}")
    if promotion.get("status") != "PROMOTION_READY":
        top_blockers.append("promotion manifest not ready; human adjudication required")
    if adjudication.get("manifest_exists") and adjudication.get("adjudicated_rows", 0) == 0:
        top_blockers.append("empty adjudication scaffold initialized; manual review still required")
    if training.get("state") not in {"TRAINING_READY_STAGED", "TRAINING_READY_CANONICAL"}:
        top_blockers.append("training not ready; adjudicated labels/training rights missing")
    summary = {
        "registered_transcripts": len(read_csv(TRANSCRIPT_REGISTRY)),
        "normalized_transcripts": len(read_csv(NORMALIZED)),
        "chunks": len(read_csv(CHUNKS)),
        "evidence_objects": len(read_csv(EVIDENCE)),
        "retrieval_objects": len(read_csv(RETRIEVAL)),
        "candidates_total": len(candidates),
        "candidates_by_label": dict(sorted(label_counts.items())),
        "candidates_by_case": dict(sorted(case_counts.items())),
        "packets_generated": len(packets),
        "calibration_rows": len(calibration),
        "adjudication_draft_exists": bool(adjudication.get("manifest_exists", False)),
        "adjudication_draft_status": adjudication.get("status", "NOT_READY"),
        "adjudication_draft_rows": adjudication.get("adjudicated_rows", 0),
        "empty_adjudication_scaffold_initialized": bool(adjudication.get("manifest_exists", False))
        and adjudication.get("adjudicated_rows", 0) == 0,
        "adjudicated_rows": promotion.get("rows", 0) if promotion.get("valid") else 0,
        "promotion_manifest_status": promotion.get("status", "NOT_READY"),
        "promotion_manifest_ready": promotion.get("status") == "PROMOTION_READY",
        "promotion_candidates": promotion.get("rows", 0) if promotion.get("status") == "PROMOTION_READY" else 0,
        "training_readiness_state": training.get("state", "NOT_READY"),
        "valid_adjudicated_labels": training.get("valid_adjudicated_labels", 0),
        "explicit_training_rights": bool(training.get("training_rights_explicit", False)),
        "training_ready": training.get("state") in {"TRAINING_READY_STAGED", "TRAINING_READY_CANONICAL"},
        "top_blockers": top_blockers,
        "raw_text_committed": False,
        "training_performed": False,
    }
    write_reports(summary, out_path, json_out_path)
    return summary


def write_reports(summary: dict[str, Any], out_path: Path, json_out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Review Readiness Dashboard",
        "",
        f"- Registered transcripts: {summary['registered_transcripts']}",
        f"- Normalized transcripts: {summary['normalized_transcripts']}",
        f"- Chunks: {summary['chunks']}",
        f"- Evidence objects: {summary['evidence_objects']}",
        f"- Retrieval objects: {summary['retrieval_objects']}",
        f"- Candidates total: {summary['candidates_total']}",
        f"- Candidates by label: `{json.dumps(summary['candidates_by_label'], sort_keys=True)}`",
        f"- Candidates by case: {len(summary['candidates_by_case'])}",
        f"- Packets generated: {summary['packets_generated']}",
        f"- Calibration rows: {summary['calibration_rows']}",
        f"- Adjudication draft status: {summary['adjudication_draft_status']}",
        f"- Empty adjudication scaffold initialized: {str(summary['empty_adjudication_scaffold_initialized']).lower()}",
        f"- Adjudication draft rows: {summary['adjudication_draft_rows']}",
        f"- Adjudicated rows: {summary['adjudicated_rows']}",
        f"- Valid adjudicated labels: {summary['valid_adjudicated_labels']}",
        f"- Promotion manifest status: {summary['promotion_manifest_status']}",
        f"- Promotion candidates: {summary['promotion_candidates']}",
        f"- Training readiness state: {summary['training_readiness_state']}",
        f"- Training ready: {str(summary['training_ready']).lower()}",
        f"- Explicit training rights: {str(summary['explicit_training_rights']).lower()}",
        "- Raw text committed: false",
        "- Training performed: false",
        "",
        "## Top Blockers",
        "",
    ]
    blockers = summary.get("top_blockers") or []
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    json_out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first100 review readiness dashboard.")
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_REPORT_PATH)
    args = parser.parse_args(argv)
    print(json.dumps(build_dashboard(args.out, args.json_out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
