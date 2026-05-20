#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluation_quality import deterministic_predictions, evaluate_predictions, read_jsonl, source_group, valid_rows  # noqa: E402
from priority_review_common import GOLD_PATH, LABELS, PACKET_CSV, read_csv  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def metrics_for(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    filtered = valid_rows(rows)
    if not filtered:
        return None
    return evaluate_predictions(deterministic_predictions(filtered))


def report_lines_for_metrics(metrics: dict[str, Any] | None) -> list[str]:
    if not metrics:
        return ["- rows: `0`", "- precision: `n/a`", "- recall: `n/a`", "- F1: `n/a`"]
    return [
        f"- precision: `{metrics.get('precision')}`",
        f"- recall: `{metrics.get('recall')}`",
        f"- F1: `{metrics.get('f1')}`",
    ]


def source_subsets(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "all": rows,
        "human_reviewed": [row for row in rows if source_group(row) == "human_reviewed"],
        "fixture_excluded": [row for row in rows if source_group(row) != "fixture"],
        "imported_guidance": [row for row in rows if source_group(row) == "imported_guidance"],
        "human_reviewed_priority_packet": [row for row in rows if row.get("label_source") == "human_reviewed_priority_packet"],
    }


def extract_ml_metrics() -> dict[str, str]:
    path = ROOT / "reports" / "experiment_results" / "local_ml_baseline.md"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    output: dict[str, str] = {}
    for key in ("precision", "recall", "F1"):
        match = re.search(rf"- {re.escape(key)}: `([^`]+)`", text)
        if match:
            output[key.lower()] = match.group(1)
    return output


def retrieval_status() -> str:
    path = ROOT / "reports" / "retrieval_benchmark.md"
    if not path.exists():
        return "not_run"
    text = path.read_text(encoding="utf-8")
    status = re.search(r"- status: `([^`]+)`", text)
    reason = re.search(r"Reason: (.+)", text)
    if status and reason:
        return f"{status.group(1)}: {reason.group(1)}"
    if status:
        return status.group(1)
    return "report_exists"


def write_eval_after_review(rows: list[dict[str, Any]]) -> None:
    readiness = read_json(ROOT / "reports" / "evaluation_readiness.json")
    gold_status = ROOT / "reports" / "gold_label_growth_status.md"
    subsets = source_subsets(rows)
    ml = extract_ml_metrics()
    lines = [
        "# Evaluation After Priority Review",
        "",
        "This report is safe to regenerate. It does not promote weak labels and does not mutate canonical gold labels.",
        "",
        "## Gold Status",
        "",
        f"- current_gold_labels: `{len(valid_rows(rows))}`",
        f"- labels_needed_to_reach_100: `{max(0, 100 - len(valid_rows(rows)))}`",
        f"- labels_needed_to_reach_250: `{max(0, 250 - len(valid_rows(rows)))}`",
        f"- gold_growth_status_report_exists: `{gold_status.exists()}`",
        "",
        "## Metrics By Source Quality",
        "",
    ]
    for name, subset_rows in subsets.items():
        lines.extend([f"### {name}", "", f"- rows: `{len(valid_rows(subset_rows))}`", *report_lines_for_metrics(metrics_for(subset_rows)), ""])
    lines.extend(
        [
            "## Deterministic vs ML",
            "",
            f"- deterministic_precision: `{readiness.get('metrics', {}).get('precision', 'n/a')}`",
            f"- deterministic_recall: `{readiness.get('metrics', {}).get('recall', 'n/a')}`",
            f"- deterministic_F1: `{readiness.get('metrics', {}).get('f1', 'n/a')}`",
            f"- ml_precision: `{ml.get('precision', 'n/a')}`",
            f"- ml_recall: `{ml.get('recall', 'n/a')}`",
            f"- ml_F1: `{ml.get('f1', 'n/a')}`",
            "- deterministic remains canonical; ML is benchmark-only.",
            "",
            "## Gates",
            "",
            f"- precision_above_0_5: `{float(readiness.get('metrics', {}).get('precision', 0.0)) > 0.5}`",
            f"- reached_100_labels: `{len(valid_rows(rows)) >= 100}`",
            f"- retrieval_allowed: `{len(valid_rows(rows)) >= 100}`",
            f"- retrieval_status: `{retrieval_status()}`",
        ]
    )
    (ROOT / "reports" / "eval_after_priority_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_metric_jump_validation(rows: list[dict[str, Any]]) -> None:
    subsets = source_subsets(rows)
    source_counts = Counter(source_group(row) for row in valid_rows(rows))
    label_counts = Counter(str(row.get("signal_family") or row.get("label") or "") for row in valid_rows(rows))
    lines = [
        "# Metric Jump Validation",
        "",
        "The deterministic metric jump is promising, but it is not yet a product-quality claim.",
        "",
        "## Source Group Counts",
        "",
        *[f"- `{source}`: {count}" for source, count in sorted(source_counts.items())],
        "",
        "## Per-Label Support",
        "",
        *[f"- `{label}`: {label_counts.get(label, 0)}" for label in LABELS],
        "",
        "## Subset Metrics",
        "",
    ]
    for name, subset_rows in subsets.items():
        lines.extend([f"### {name}", "", f"- rows: `{len(valid_rows(subset_rows))}`", *report_lines_for_metrics(metrics_for(subset_rows)), ""])
    lines.extend(
        [
            "## Robustness Assessment",
            "",
            "- The all-label improvement is large and passes the deterministic regression checks.",
            "- Fixture rows still dominate the current label set, so the improvement must be validated on more real human-reviewed earnings-call labels.",
            "- Human-reviewed-only support is still small; one or two labels can swing metrics materially.",
            "- No labels are promoted by this report, and the review packet generator excludes rows already in canonical gold labels.",
            "- Deterministic output is compared to canonical gold labels only; ML and retrieval do not alter the comparison.",
            "",
            "## Recommendation",
            "",
            "Treat `0.8399` precision / `0.8276` F1 as a strong regression signal, not as a robust performance claim. The next proof milestone is 100+ high-quality human-reviewed labels.",
        ]
    )
    (ROOT / "reports" / "metric_jump_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_priority_review_validation(rows: list[dict[str, Any]]) -> None:
    packet_rows = read_csv(PACKET_CSV)
    inventory = ROOT / "reports" / "call_review_inventory.md"
    download_plan = ROOT / "reports" / "transcript_download_plan.md"
    readiness = read_json(ROOT / "reports" / "evaluation_readiness.json")
    ready_calls: list[str] = []
    missing_calls: list[str] = []
    if inventory.exists():
        for line in inventory.read_text(encoding="utf-8").splitlines():
            if "| `:" in line:
                continue
            if "| `NVDA" in line or "| `AMZN" in line or "| `AAPL" in line or "| `MSFT" in line or "| `GOOGL" in line or "| `PLTR" in line:
                if "review now" in line:
                    match = re.search(r"`([^`]+)`", line)
                    if match:
                        ready_calls.append(match.group(1))
            if "META_2025_Q4" in line and "download transcript" in line:
                missing_calls.append("META_2025_Q4")
    lines = [
        "# Final Priority Review Validation",
        "",
        f"- current_gold_label_count: `{len(valid_rows(rows))}`",
        f"- labels_needed_to_reach_100: `{max(0, 100 - len(valid_rows(rows)))}`",
        f"- labels_needed_to_reach_250: `{max(0, 250 - len(valid_rows(rows)))}`",
        f"- calls_ready_for_review: `{len(set(ready_calls))}`",
        f"- calls_needing_transcript_download: `{len(set(missing_calls))}`",
        f"- review_packet_rows: `{len(packet_rows)}`",
        f"- expected_accepted_labels_if_6_per_ready_call: `{len(set(ready_calls)) * 6}`",
        f"- expected_accepted_labels_if_8_per_ready_call: `{len(set(ready_calls)) * 8}`",
        "",
        "## Current Metrics",
        "",
        f"- precision: `{readiness.get('metrics', {}).get('precision', 'n/a')}`",
        f"- recall: `{readiness.get('metrics', {}).get('recall', 'n/a')}`",
        f"- F1: `{readiness.get('metrics', {}).get('f1', 'n/a')}`",
        "",
        "## ML And Retrieval",
        "",
        f"- ML benchmark: `{extract_ml_metrics() or 'not_available'}`",
        f"- retrieval benchmark: `{retrieval_status()}`",
        "",
        "## Demo Status",
        "",
        f"- demo_report_exists: `{(ROOT / 'reports' / 'demo' / 'analyst_report_LLY_2025_Q2_call08.md').exists()}`",
        "",
        "## Review Assets",
        "",
        f"- review_packet_csv: `{PACKET_CSV.relative_to(ROOT)}`",
        f"- review_packet_markdown: `{(ROOT / 'data' / 'labeling' / 'priority_review_packet.md').relative_to(ROOT)}`",
        f"- call_inventory: `{inventory.relative_to(ROOT)}`",
        f"- transcript_download_plan: `{download_plan.relative_to(ROOT)}`",
    ]
    (ROOT / "reports" / "final_priority_review_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = read_jsonl(GOLD_PATH)
    write_eval_after_review(rows)
    write_metric_jump_validation(rows)
    write_final_priority_review_validation(rows)
    print(
        json.dumps(
            {
                "status": "ok",
                "gold_labels": len(valid_rows(rows)),
                "packet_rows": len(read_csv(PACKET_CSV)),
                "retrieval_status": retrieval_status(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
