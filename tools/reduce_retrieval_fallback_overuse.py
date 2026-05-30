#!/usr/bin/env python3
"""Report retrieval fallback overuse and evidence-priority mitigation status."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_METRICS = ROOT / "data" / "retrieval" / "first30_eval_metrics.json"
DEFAULT_REPORT = ROOT / "reports" / "retrieval" / "retrieval_fallback_diagnostics.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def diagnose(objects_path: Path = DEFAULT_OBJECTS, metrics_path: Path = DEFAULT_METRICS, out_path: Path = DEFAULT_REPORT) -> dict[str, Any]:
    objects = read_csv(objects_path)
    metrics = read_json(metrics_path)
    by_type = Counter(row.get("object_type", "") for row in objects)
    semantic_by_case = Counter(row.get("case_id", "") for row in objects if row.get("object_type") == "semantic_chunk")
    evidence_ready_cases = {
        row.get("case_id", "")
        for row in objects
        if row.get("object_type") in {"evidence_object", "event_aligned_chunk"}
    }
    semantic_only_cases = sorted(case_id for case_id, _ in semantic_by_case.items() if case_id not in evidence_ready_cases)
    summary = {
        "retrieval_objects": len(objects),
        "object_type_counts": dict(sorted(by_type.items())),
        "evidence_ready_cases": len(evidence_ready_cases),
        "semantic_only_cases": semantic_only_cases,
        "fallback_overuse": float(metrics.get("fallback_overuse", 0.0) or 0.0),
        "evaluated_rag": bool(metrics.get("evaluated_rag", False)),
        "mitigation": "case_prefilter_evidence_required_queries_exclude_semantic_fallback_when_nonsemantic_evidence_exists",
        "raw_text_returned": False,
    }
    write_report(summary, out_path)
    return summary


def write_report(summary: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Fallback Diagnostics",
        "",
        f"- Retrieval objects: {summary['retrieval_objects']}",
        f"- Object type counts: `{json.dumps(summary['object_type_counts'], sort_keys=True)}`",
        f"- Evidence-ready cases: {summary['evidence_ready_cases']}",
        f"- Semantic-only cases: {len(summary['semantic_only_cases'])}",
        f"- Fallback overuse: {summary['fallback_overuse']:.3f}",
        f"- evaluated_rag={str(summary['evaluated_rag']).lower()}",
        "- Raw text returned: false",
        f"- Mitigation: `{summary['mitigation']}`",
        "",
        "## Semantic-Only Cases",
        "",
    ]
    semantic_only = summary.get("semantic_only_cases") or []
    lines.extend(f"- `{case_id}`" for case_id in semantic_only) if semantic_only else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose retrieval fallback overuse.")
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    print(json.dumps(diagnose(args.objects, args.metrics, args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
