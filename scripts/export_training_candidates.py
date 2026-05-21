#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from resource_registry_common import load_csv, load_jsonl, write_json

ROOT = Path(__file__).resolve().parents[1]


def _load_mixed_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.suffix == ".jsonl":
        return load_jsonl(path)
    if path.suffix == ".csv":
        return load_csv(path)
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        for key in ("rows", "examples", "resources", "cases"):
            if isinstance(payload, dict) and isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
    return []


def _expand_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        paths.extend(Path(match) for match in matches)
    return sorted({path for path in paths if path.exists()})


def _tag_rows(rows: list[dict[str, Any]], bucket: str, source_path: Path) -> list[dict[str, Any]]:
    tagged: list[dict[str, Any]] = []
    for row in rows:
        copy = dict(row)
        copy["candidate_bucket"] = bucket
        copy["candidate_source_path"] = str(source_path)
        if bucket != "human_reviewed_gold":
            copy.pop("gold_label", None)
            copy["gold_eligible"] = False
        else:
            copy["gold_eligible"] = True
        tagged.append(copy)
    return tagged


def export_candidates(
    *,
    gold_paths: list[Path],
    weak_paths: list[Path],
    external_paths: list[Path],
    retrieval_paths: list[Path],
    event_study_paths: list[Path],
) -> dict[str, Any]:
    buckets = {
        "human_reviewed_gold": [],
        "weak_labels": [],
        "external_benchmark_rows": [],
        "retrieval_only_records": [],
        "event_study_cases": [],
    }
    for path in gold_paths:
        buckets["human_reviewed_gold"].extend(_tag_rows(_load_mixed_rows(path), "human_reviewed_gold", path))
    for path in weak_paths:
        buckets["weak_labels"].extend(_tag_rows(_load_mixed_rows(path), "weak_labels", path))
    for path in external_paths:
        buckets["external_benchmark_rows"].extend(_tag_rows(_load_mixed_rows(path), "external_benchmark_rows", path))
    for path in retrieval_paths:
        rows = _load_mixed_rows(path)
        if path.suffix == ".json" and not rows:
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows = payload.get("examples", []) if isinstance(payload, dict) else []
        buckets["retrieval_only_records"].extend(_tag_rows(rows, "retrieval_only_records", path))
    for path in event_study_paths:
        buckets["event_study_cases"].extend(_tag_rows(_load_mixed_rows(path), "event_study_cases", path))

    return {
        "export_version": "training_candidates_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "promotion_policy": "Only human-reviewed gold rows are gold eligible. Weak labels and external rows are never promoted by this exporter.",
        "counts": {key: len(value) for key, value in buckets.items()},
        **buckets,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export separated training/evaluation candidate buckets without gold promotion.")
    parser.add_argument("--gold", action="append", default=[])
    parser.add_argument("--weak", action="append", default=[])
    parser.add_argument("--external", action="append", default=[])
    parser.add_argument("--retrieval", action="append", default=[])
    parser.add_argument("--event-study", action="append", default=[])
    parser.add_argument("--out", default=str(ROOT / "data" / "training_candidates.export.json"))
    args = parser.parse_args(argv)

    payload = export_candidates(
        gold_paths=_expand_inputs(args.gold or [str(ROOT / "data" / "nlp_research" / "human_reviewed_signal_labels.jsonl")]),
        weak_paths=_expand_inputs(args.weak or [str(ROOT / "data" / "nlp_research" / "signal_label_candidates.jsonl")]),
        external_paths=_expand_inputs(args.external or [str(ROOT / "data" / "benchmark_external" / "*.jsonl")]),
        retrieval_paths=_expand_inputs(args.retrieval or [str(ROOT / "data" / "nlp_research" / "signal_retrieval_index.json")]),
        event_study_paths=_expand_inputs(args.event_study or [str(ROOT / "data" / "corpus" / "processed" / "chunks" / "*.event_chunks.jsonl")]),
    )
    write_json(Path(args.out), payload)
    print(json.dumps({"status": "ok", "out": args.out, "counts": payload["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
