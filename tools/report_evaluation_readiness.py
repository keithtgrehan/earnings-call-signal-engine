#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluate_gold_labels import gate_for_count  # noqa: E402
from labeling_common import SIGNAL_LABELS, read_jsonl  # noqa: E402
from train_text_signal_model import training_gate  # noqa: E402


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def label_for(row: dict[str, Any]) -> str:
    return str(row.get("signal_family") or row.get("label") or "").strip()


def duplicate_ids(rows: list[dict[str, Any]]) -> list[str]:
    ids = [str(row.get("id") or row.get("candidate_id") or "").strip() for row in rows]
    counts = Counter(item for item in ids if item)
    return sorted(item for item, count in counts.items() if count > 1)


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def reviewed_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    decisions = Counter(str(row.get("review_decision") or "").strip().lower() for row in rows)
    return {
        "accepted": decisions["accept"] + decisions["edit_label"],
        "rejected": decisions["reject"],
        "unclear": decisions["unclear"],
        "skipped": decisions["skip"],
        "unreviewed": decisions[""],
    }


def readiness_payload(*, gold_rows: list[dict[str, Any]], reviewed_rows: list[dict[str, str]]) -> dict[str, Any]:
    label_counts = Counter(label_for(row) for row in gold_rows)
    duplicate_gold_ids = duplicate_ids(gold_rows)
    invalid_label_rows = [
        str(row.get("id") or row.get("candidate_id") or "")
        for row in gold_rows
        if label_for(row) not in SIGNAL_LABELS
    ]
    evaluation_gate, metrics_allowed = gate_for_count(len(gold_rows))
    training_status = training_gate(len(gold_rows))
    counts = reviewed_counts(reviewed_rows)
    return {
        "gold_labels": len(gold_rows),
        "label_counts": {label: label_counts.get(label, 0) for label in sorted(SIGNAL_LABELS)},
        "missing_labels": sorted(label for label in SIGNAL_LABELS if label_counts.get(label, 0) == 0),
        "duplicate_gold_ids": duplicate_gold_ids,
        "invalid_label_rows": invalid_label_rows,
        "reviewed_batch": counts,
        "evaluation_gate": evaluation_gate,
        "metrics_allowed": metrics_allowed,
        "training_gate": training_status,
        "training_allowed": training_status != "skip_training",
        "benchmark_claims_allowed": metrics_allowed and not duplicate_gold_ids and not invalid_label_rows,
    }


def write_label_coverage_csv(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total = int(payload["gold_labels"])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "gold_count", "share", "status"])
        writer.writeheader()
        for label, count in dict(payload["label_counts"]).items():
            share = round(count / total, 4) if total else 0.0
            status = "present" if count else "missing"
            writer.writerow({"label": label, "gold_count": count, "share": share, "status": status})


def write_benchmark_template(path: Path, payload: dict[str, Any], *, coverage_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First 50 Benchmark Report",
        "",
        "This report is a readiness template. It must not claim precision, recall, F1, uplift, significance, or production validity until metrics are computed from valid human gold labels.",
        "",
        "## Current Gate",
        "",
        f"- gold_labels: `{payload['gold_labels']}`",
        f"- evaluation_gate: `{payload['evaluation_gate']}`",
        f"- metrics_allowed: `{payload['metrics_allowed']}`",
        f"- training_gate: `{payload['training_gate']}`",
        f"- training_allowed: `{payload['training_allowed']}`",
        f"- benchmark_claims_allowed: `{payload['benchmark_claims_allowed']}`",
        f"- label_coverage_csv: `{display_path(coverage_path)}`",
        "",
        "## Label Coverage",
        "",
    ]
    for label, count in dict(payload["label_counts"]).items():
        lines.append(f"- `{label}`: {count}")
    lines.extend(
        [
            "",
            f"- missing_labels: `{', '.join(payload['missing_labels']) or 'none'}`",
            f"- duplicate_gold_ids: `{', '.join(payload['duplicate_gold_ids']) or 'none'}`",
            f"- invalid_label_rows: `{', '.join(payload['invalid_label_rows']) or 'none'}`",
            "",
            "## Reviewed Batch Status",
            "",
        ]
    )
    for key, count in dict(payload["reviewed_batch"]).items():
        lines.append(f"- {key}: `{count}`")
    lines.extend(
        [
            "",
            "## Claims Boundary",
            "",
            "- Transcript-first deterministic extraction remains canonical.",
            "- Weak labels and model suggestions are not gold labels.",
            "- Rejected, unclear, skipped, and unreviewed rows are excluded from gold.",
            "- Below 20 gold labels, metrics are intentionally skipped.",
            "- Below 50 gold labels, text model training remains gated.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readiness_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def report_readiness(
    *,
    gold_path: Path,
    reviewed_path: Path,
    coverage_out: Path,
    report_out: Path,
    json_out: Path,
) -> dict[str, Any]:
    payload = readiness_payload(gold_rows=read_jsonl(gold_path), reviewed_rows=read_csv_rows(reviewed_path))
    write_label_coverage_csv(coverage_out, payload)
    write_benchmark_template(report_out, payload, coverage_path=coverage_out)
    write_readiness_json(json_out, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report gold-label evaluation readiness without inventing or promoting labels.")
    parser.add_argument("--gold", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--reviewed", default=str(ROOT / "data" / "labeling" / "reviewed_next_batch.csv"))
    parser.add_argument("--coverage-out", default=str(ROOT / "reports" / "label_coverage.csv"))
    parser.add_argument("--report-out", default=str(ROOT / "docs" / "evaluation" / "first_50_benchmark_report.md"))
    parser.add_argument("--json-out", default=str(ROOT / "reports" / "evaluation_readiness.json"))
    args = parser.parse_args(argv)
    payload = report_readiness(
        gold_path=Path(args.gold),
        reviewed_path=Path(args.reviewed),
        coverage_out=Path(args.coverage_out),
        report_out=Path(args.report_out),
        json_out=Path(args.json_out),
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
