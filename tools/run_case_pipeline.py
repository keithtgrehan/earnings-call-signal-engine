#!/usr/bin/env python3
"""Run a conservative one-case transcript benchmark workflow."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent / "transcript_downloader"
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from apply_selected_gold_labels import build_labels_for_case, load_selected, write_labels_for_case  # noqa: E402
from build_gold_label_packet import candidates_from_raw, candidates_from_weak_labels, dedupe, load_jsonl, render_packet  # noqa: E402
from run_corpus_analysis import evaluate_case_labels  # noqa: E402
from validate_gold_labels import validate_file  # noqa: E402

DEFAULT_ROOT = Path("/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts")
MIN_WORDS = 1000
STAGES = ("validate", "weak-labels", "packet", "gold", "eval", "manifest")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="Case ID to process, for example AAPL_2026_Q1.")
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--all", action="store_true", help="Run all stages for the case.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--selected-csv")
    parser.add_argument("--target-per-case", type=int, default=15)
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def case_dir(root: Path, case_id: str) -> Path:
    return root / case_id


def raw_transcript_path(root: Path, case_id: str) -> Path:
    return case_dir(root, case_id) / "raw" / "transcript.txt"


def validation_path(root: Path, case_id: str) -> Path:
    return case_dir(root, case_id) / "outputs" / "validation.json"


def labels_dir(root: Path, case_id: str) -> Path:
    return case_dir(root, case_id) / "labels"


def outputs_dir(root: Path, case_id: str) -> Path:
    return case_dir(root, case_id) / "outputs"


def validate_case(root: Path, case_id: str) -> dict[str, Any]:
    directory = case_dir(root, case_id)
    labels = labels_dir(root, case_id)
    outputs = outputs_dir(root, case_id)
    outputs.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)
    transcript = raw_transcript_path(root, case_id)
    metadata = directory / "metadata.json"
    warnings: list[str] = []
    word_count = 0
    exists = transcript.exists()
    if not directory.exists():
        warnings.append("case directory missing")
    if not exists:
        warnings.append("raw transcript missing")
    else:
        text = transcript.read_text(encoding="utf-8", errors="replace")
        word_count = len(text.split())
        if word_count < MIN_WORDS:
            warnings.append(f"transcript word count below {MIN_WORDS}")
    if not metadata.exists():
        warnings.append("metadata missing")
    payload = {
        "case_id": case_id,
        "transcript_exists": exists,
        "transcript_word_count": word_count,
        "metadata_exists": metadata.exists(),
        "labels_dir_exists": labels.exists(),
        "outputs_dir_exists": outputs.exists(),
        "status": "pass" if exists and word_count >= MIN_WORDS else "warning",
        "warnings": warnings,
    }
    validation_path(root, case_id).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def weak_labels_status(root: Path, case_id: str) -> dict[str, Any]:
    path = labels_dir(root, case_id) / "weak_labels.jsonl"
    count = 0
    if path.exists():
        count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return {"status": "present" if count else "missing", "count": count, "path": str(path)}


def build_packet(root: Path, case_id: str, target: int) -> dict[str, Any]:
    transcript = raw_transcript_path(root, case_id)
    if not transcript.exists():
        raise SystemExit(f"raw transcript missing: {transcript}")
    weak_rows = load_jsonl(labels_dir(root, case_id) / "weak_labels.jsonl")
    raw_text = transcript.read_text(encoding="utf-8", errors="replace")
    candidates = candidates_from_weak_labels(case_id, weak_rows)
    candidates.extend(candidates_from_raw(case_id, raw_text, max(0, target - len(candidates))))
    selected = dedupe(candidates, target)
    packet = labels_dir(root, case_id) / "human_labeling_packet.md"
    packet.write_text(render_packet(case_id, selected), encoding="utf-8")
    return {"status": "written", "path": str(packet), "candidate_count": len(selected)}


def apply_selected_for_case(root: Path, case_id: str, selected_csv: Path | None, reviewer: str = "Keith") -> dict[str, Any]:
    if selected_csv is None:
        return {"status": "skipped", "notes": "gold-label conversion skipped: no selected-candidates CSV provided"}
    selected = [row for row in load_selected(selected_csv) if row["case_id"].strip() == case_id]
    if not selected:
        return {"status": "skipped", "notes": f"gold-label conversion skipped: no rows for {case_id}"}
    labels = build_labels_for_case(root, case_id, selected, label_status="human_approved", reviewer=reviewer)
    out = write_labels_for_case(case_dir(root, case_id), labels, label_status="human_approved")
    return {"status": "written", "path": str(out), "gold_label_count": len(labels)}


def gold_status(root: Path, case_id: str) -> dict[str, Any]:
    path = labels_dir(root, case_id) / "gold_labels.jsonl"
    result = validate_file(path)
    return {"status": result["status"], "label_count": int(result["label_count"]), "path": str(path), "errors": result["errors"]}


def evaluate_case(root: Path, case_id: str) -> dict[str, Any]:
    status = gold_status(root, case_id)
    output_dir = outputs_dir(root, case_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "error_analysis.md"
    if status["status"] != "valid" or int(status["label_count"]) <= 0:
        text = "# Case Error Analysis\n\nEvaluation skipped: no valid gold labels.\n"
        output.write_text(text, encoding="utf-8")
        return {"status": "skipped", "notes": "evaluation skipped: no valid gold labels", "path": str(output)}
    row, errors = evaluate_case_labels(case_dir(root, case_id))
    if row is None:
        output.write_text("# Case Error Analysis\n\nEvaluation skipped: no valid gold labels.\n", encoding="utf-8")
        return {"status": "skipped", "notes": "evaluation skipped: no valid gold labels", "path": str(output)}
    lines = [
        "# Case Error Analysis",
        "",
        "Conservative weak-vs-gold overlap review. This is not precision, recall, F1, alpha, or investment advice.",
        "",
    ]
    for key in (
        "gold_label_count",
        "weak_label_count",
        "matched_count",
        "missed_gold_count",
        "extra_weak_count",
        "type_match_count",
        "type_mismatch_count",
        "overlap_match_count",
    ):
        lines.append(f"- {key}: {row.get(key, 0)}")
    if errors:
        lines.extend(["", "## Error Themes"])
        for error in errors[:10]:
            lines.append(f"- {error.get('error_type')}: {str(error.get('evidence_text', ''))[:160]}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"status": "evaluated", "path": str(output), **row}


def update_manifest(root: Path, case_id: str, statuses: dict[str, Any]) -> dict[str, Any]:
    path = root / "corpus_manifest.csv"
    existing: list[dict[str, str]] = []
    fieldnames: list[str] = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            existing = list(reader)
    required = [
        "case_id",
        "has_raw_transcript",
        "has_weak_labels",
        "has_human_packet",
        "has_gold_labels",
        "gold_label_status",
        "gold_label_count",
        "eval_status",
        "last_pipeline_stage",
        "last_pipeline_result",
        "last_pipeline_run",
        "notes",
    ]
    for field in required:
        if field not in fieldnames:
            fieldnames.append(field)
    row = next((item for item in existing if item.get("case_id") == case_id), {"case_id": case_id})
    gold = gold_status(root, case_id)
    weak = weak_labels_status(root, case_id)
    packet = labels_dir(root, case_id) / "human_labeling_packet.md"
    transcript = raw_transcript_path(root, case_id)
    row.update(
        {
            "case_id": case_id,
            "has_raw_transcript": str(transcript.exists()),
            "has_weak_labels": str(weak["count"] > 0),
            "has_human_packet": str(packet.exists()),
            "has_gold_labels": str(gold["label_count"] > 0),
            "gold_label_status": str(gold["status"]),
            "gold_label_count": str(gold["label_count"]),
            "eval_status": str(statuses.get("eval", {}).get("status", "not_run")),
            "last_pipeline_stage": str(statuses.get("last_stage", "")),
            "last_pipeline_result": str(statuses.get("last_result", "")),
            "last_pipeline_run": now_iso(),
            "notes": str(statuses.get("notes", "")),
        }
    )
    updated = [item for item in existing if item.get("case_id") != case_id]
    updated.append(row)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in sorted(updated, key=lambda value: value.get("case_id", "")):
            writer.writerow({field: item.get(field, "") for field in fieldnames})
    return {"status": "updated", "path": str(path)}


def run_stage(args: argparse.Namespace, root: Path, stage: str, statuses: dict[str, Any]) -> dict[str, Any]:
    case_id = args.case
    if stage == "gold" and args.stage == "gold" and not args.selected_csv:
        raise SystemExit("--stage gold requires --selected-csv")
    if stage == "validate":
        result = validate_case(root, case_id)
    elif stage == "weak-labels":
        result = weak_labels_status(root, case_id)
    elif stage == "packet":
        result = build_packet(root, case_id, int(args.target_per_case))
    elif stage == "gold":
        result = apply_selected_for_case(root, case_id, Path(args.selected_csv) if args.selected_csv else None)
    elif stage == "eval":
        result = evaluate_case(root, case_id)
    elif stage == "manifest":
        result = update_manifest(root, case_id, statuses)
    else:
        raise SystemExit(f"unknown stage: {stage}")
    statuses[stage] = result
    statuses["last_stage"] = stage
    statuses["last_result"] = result.get("status", "")
    if result.get("notes"):
        statuses["notes"] = result["notes"]
    print(f"{stage}: {result.get('status')}")
    if result.get("notes"):
        print(result["notes"])
    return result


def default_stages(args: argparse.Namespace) -> list[str]:
    if args.all:
        return list(STAGES)
    if args.stage:
        return [args.stage]
    return ["validate", "weak-labels", "packet", "gold", "eval", "manifest"]


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not case_dir(root, args.case).exists():
        raise SystemExit(f"case directory missing: {case_dir(root, args.case)}")
    statuses: dict[str, Any] = {}
    for stage in default_stages(args):
        run_stage(args, root, stage, statuses)
    if "manifest" not in statuses:
        run_stage(args, root, "manifest", statuses)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
