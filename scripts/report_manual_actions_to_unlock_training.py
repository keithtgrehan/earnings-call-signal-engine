#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_report_payload(
    *,
    discovery_path: Path,
    batch_path: Path,
    registry_path: Path,
    repair_path: Path,
    gold_path: Path,
) -> dict[str, Any]:
    discovery = _load_jsonl(discovery_path)
    batch = _load_csv(batch_path)
    registry = _load_jsonl(registry_path)
    repair = _load_jsonl(repair_path)
    gold_rows = _load_jsonl(gold_path)
    repair_counts = Counter(str(row.get("repair_status", "unknown")) for row in repair)
    path_hash_ready = [
        row for row in discovery if row.get("status") == "candidate_metadata_only" and str(row.get("sha256", "")).startswith("sha256:")
    ]
    registry_ready = [
        row
        for row in batch
        if row.get("local_path") and row.get("rights_tier") not in {"", "unknown", "restricted"} and row.get("source_url")
    ]
    rights_review = [row for row in discovery if row.get("rights_status") in {"", "unknown", None}]
    next_actions: list[str] = []
    prioritized = sorted(
        discovery,
        key=lambda row: (
            0 if "transcript" in Path(str(row.get("path_ref", ""))).stem.lower() else 1,
            str(row.get("path_ref", "")),
        ),
    )
    for row in prioritized[:20]:
        next_actions.append(f"Review rights/source URL for `{row.get('candidate_case_id', '')}` at `{row.get('path_ref', '')}`.")
    if not next_actions:
        next_actions.append("Place transcripts under `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/` and rerun discovery.")
    return {
        "transcript_paths_discovered": len(discovery),
        "path_hash_ready": len(path_hash_ready),
        "registry_ready": len(registry_ready),
        "requiring_rights_review": len(rights_review),
        "registered": len(registry),
        "gold_rows_total": len(gold_rows),
        "gold_rows_repairable": repair_counts.get("repairable_with_registered_source", 0) + repair_counts.get("repairable_schema_only", 0),
        "gold_rows_blocked": sum(count for status, count in repair_counts.items() if status not in {"repairable_with_registered_source", "repairable_schema_only"}),
        "labels_needed_to_reach_100": max(0, 100 - repair_counts.get("repairable_with_registered_source", 0)),
        "next_20_manual_actions": next_actions[:20],
        "expected_local_folder": "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/",
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Manual Actions To Unlock Training",
        "",
        f"- Transcript paths discovered: `{payload['transcript_paths_discovered']}`",
        f"- Path/hash candidate rows: `{payload['path_hash_ready']}`",
        f"- Registry-ready approved rows: `{payload['registry_ready']}`",
        f"- Rows requiring rights review: `{payload['requiring_rights_review']}`",
        f"- Registered rows: `{payload['registered']}`",
        f"- Gold rows repairable: `{payload['gold_rows_repairable']}`",
        f"- Gold rows blocked: `{payload['gold_rows_blocked']}`",
        f"- Labels needed to reach 100 valid adjudicated labels: `{payload['labels_needed_to_reach_100']}`",
        f"- Expected local folder: `{payload['expected_local_folder']}`",
        "",
        "## Next 20 Manual Actions",
        "",
    ]
    lines.extend(f"{index}. {action}" for index, action in enumerate(payload["next_20_manual_actions"], start=1))
    lines.extend(["", "Training readiness remains `NOT_READY` until at least 100 valid adjudicated labels pass validation."])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the manual action dashboard for unlocking training readiness.")
    parser.add_argument("--discovery", default="data/review/staging/manual_local_discovery_candidates.jsonl")
    parser.add_argument("--batch", default="data/review/staging/manual_local_batch_candidate.csv")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--repair", default="data/review/staging/gold_provenance_repair_candidates.jsonl")
    parser.add_argument("--gold", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--report", default="reports/manual_actions_to_unlock_training.md")
    args = parser.parse_args(argv)
    payload = build_report_payload(
        discovery_path=Path(args.discovery),
        batch_path=Path(args.batch),
        registry_path=Path(args.registry),
        repair_path=Path(args.repair),
        gold_path=Path(args.gold),
    )
    _write_report(Path(args.report), payload)
    print("Manual actions dashboard written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
