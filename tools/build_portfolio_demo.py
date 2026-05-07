#!/usr/bin/env python3
"""Build offline portfolio demo artifacts from committed reports and fixtures."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "demo"
READINESS_PATH = ROOT / "reports" / "evaluation_readiness.json"
SOURCE_QUALITY_PATH = ROOT / "reports" / "source_quality_metric_comparison.md"
ML_BASELINE_PATH = ROOT / "reports" / "experiment_results" / "local_ml_baseline.md"
RETRIEVAL_PATH = ROOT / "reports" / "retrieval_eval.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def metric_subset_from_table(path: Path, subset: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    pattern = re.compile(rf"\| `{re.escape(subset)}` \| (?P<rows>\d+) \| (?P<precision>[\d.]+) \| (?P<recall>[\d.]+) \| (?P<f1>[\d.]+) \|")
    match = pattern.search(path.read_text(encoding="utf-8"))
    if not match:
        return {}
    return {
        "rows": int(match.group("rows")),
        "precision": float(match.group("precision")),
        "recall": float(match.group("recall")),
        "f1": float(match.group("f1")),
    }


def inline_metric(path: Path, label: str) -> float | None:
    if not path.exists():
        return None
    match = re.search(rf"- {re.escape(label)}: `([\d.]+)`", path.read_text(encoding="utf-8"))
    return float(match.group(1)) if match else None


def retrieval_status(path: Path) -> dict[str, str]:
    if not path.exists():
        return {"status": "not_available", "gate": "see reports/"}
    text = path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for key in ("status", "gold_labels", "backend", "recall_at_k", "nearest_neighbor_label_agreement"):
        match = re.search(rf"- {key}: `([^`]+)`", text)
        if match:
            result[key] = match.group(1)
    reason = re.search(r"Reason: (.+)", text)
    if reason:
        result["gate"] = reason.group(1).strip()
    return result


def build_metrics_payload() -> dict[str, Any]:
    readiness = read_json(READINESS_PATH)
    metrics = readiness.get("metrics") if isinstance(readiness.get("metrics"), dict) else {}
    return {
        "generated_at": "from_committed_reports",
        "source_reports": [
            str(READINESS_PATH.relative_to(ROOT)),
            str(SOURCE_QUALITY_PATH.relative_to(ROOT)),
            str(ML_BASELINE_PATH.relative_to(ROOT)),
            str(RETRIEVAL_PATH.relative_to(ROOT)),
        ],
        "gold_labels": readiness.get("gold_labels"),
        "valid_gold_rows_with_text": readiness.get("valid_gold_rows_with_text"),
        "label_counts": readiness.get("label_counts", {}),
        "deterministic": {
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1": metrics.get("f1"),
            "interpretation": "small mixed-provenance benchmark; deterministic transcript-first output remains canonical",
        },
        "human_reviewed_only": metric_subset_from_table(SOURCE_QUALITY_PATH, "human_reviewed"),
        "fixture_excluded": metric_subset_from_table(SOURCE_QUALITY_PATH, "fixture_excluded"),
        "tfidf_logistic_regression": {
            "precision": inline_metric(ML_BASELINE_PATH, "precision"),
            "recall": inline_metric(ML_BASELINE_PATH, "recall"),
            "f1": inline_metric(ML_BASELINE_PATH, "F1"),
            "interpretation": "benchmark-only; no model artifact committed; deterministic remains canonical",
        },
        "retrieval": retrieval_status(RETRIEVAL_PATH),
        "non_claims": [
            "no production readiness claim",
            "no trading-alpha claim",
            "no statistical-significance claim",
            "no automated investment advice",
            "no weak-label auto-promotion",
        ],
    }


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_metrics(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def metric_line(payload: dict[str, Any]) -> str:
    deterministic = payload.get("deterministic", {})
    return (
        f"precision `{deterministic.get('precision')}`, recall `{deterministic.get('recall')}`, "
        f"F1 `{deterministic.get('f1')}`"
    )


def main() -> int:
    payload = build_metrics_payload()
    write_metrics(REPORT_DIR / "portfolio_demo_metrics.json", payload)
    write(
        REPORT_DIR / "portfolio_demo_report.md",
        "\n".join(
            [
                "# Portfolio Demo Report",
                "",
                "Signal Engine 2.0 is a transcript-first evaluation workflow for turning messy business communication into evidence-backed signal candidates, review packets, and benchmark reports.",
                "",
                "## What The Demo Shows",
                "",
                "- Public transcript/source intake is kept separate from label promotion.",
                "- Manual-source intake supports legally usable plaintext transcripts when public pages block automated verification.",
                "- Provenance is preserved before analysis.",
                "- Deterministic extraction produces reviewable candidate signals.",
                "- Weak labels remain suggestions until a human reviewer accepts them.",
                "- Evaluation reports compare deterministic output against reviewed labels.",
                "- ML and retrieval stay benchmark/support layers.",
                "",
                "## Current Metrics",
                "",
                f"- gold labels: `{payload.get('gold_labels')}`",
                f"- deterministic metrics: {metric_line(payload)}",
                f"- human-reviewed-only F1: `{payload.get('human_reviewed_only', {}).get('f1')}`",
                f"- fixture-excluded F1: `{payload.get('fixture_excluded', {}).get('f1')}`",
                f"- TF-IDF/logistic-regression F1: `{payload.get('tfidf_logistic_regression', {}).get('f1')}`",
                f"- retrieval status: `{payload.get('retrieval', {}).get('status')}`",
                "",
                "These are small-benchmark metrics for workflow evaluation, not statistical proof or production ML performance.",
                "",
                "## Review Boundary",
                "",
                "No transcripts or gold labels are auto-promoted by this demo. Human review remains the gate for accepted labels.",
            ]
        ),
    )
    write(
        REPORT_DIR / "portfolio_demo_walkthrough.md",
        "\n".join(
            [
                "# Portfolio Demo Walkthrough",
                "",
                "1. Start with the problem: generic summaries are hard to trust without evidence and repeatable review.",
                "2. Show intake/source discovery as the provenance layer, not as a label generator.",
                "3. Explain the manual-source workflow for public/legal transcripts that cannot be fetched because of robots or blocking.",
                "4. Show deterministic extraction as the canonical transcript-first path.",
                "5. Open the review packet workflow and explain accept/reject/correct decisions.",
                "6. Show `reports/evaluation_readiness.json` and `reports/source_quality_metric_comparison.md`.",
                "7. Explain that TF-IDF/logistic regression and retrieval are support benchmarks only.",
                "8. Close with the scaling step: complete the 100-call corpus and grow to 500-1,000 reviewed labels.",
                "",
                "The useful product pattern is evidence-backed AI output plus measurable human review, not one-shot summarization.",
            ]
        ),
    )
    print(json.dumps({"status": "ok", "artifacts": [str(path.relative_to(ROOT)) for path in sorted(REPORT_DIR.glob("portfolio_demo_*"))]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
