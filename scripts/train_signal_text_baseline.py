#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from math import ceil
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.signal_baseline import (
    DEFAULT_RANDOM_SEED,
    DEFAULT_TEST_SIZE,
    SIGNAL_FAMILY_LABELS,
    build_weak_labeled_examples,
    label_support_counts,
    load_supervised_examples,
    render_support_markdown_table,
    training_readiness,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def _render_report(metrics: dict[str, Any], *, source_kind: str) -> str:
    lines = [
        "# NLP Baseline Report",
        "",
        f"- status: `{metrics['status']}`",
        "- task: `signal_family`",
        f"- source_kind: `{source_kind}`",
        "- model family: `tfidf + logistic_regression`",
        "- interpretation boundary: research benchmark only; deterministic transcript extraction remains canonical",
        "",
        "## Data Sources",
        "",
    ]
    for item in metrics.get("source_paths", []):
        lines.append(f"- `{item}`")

    lines.extend(
        [
            "",
            "## Weak-Label Method",
            "",
            "- `risk_friction`: deterministic support frustration/deflection/escalation, pricing objection, competitor pressure, renewal-risk, and unresolved-issue terms",
            "- `opportunity_commitment`: deterministic resolution, next-step, buyer-intent, owner-commitment, and expansion terms",
            "- `uncertainty_hedging`: deterministic hedge and caution terms",
            "- `neutral`: remaining transcript segments with no matched weak-label terms",
            "",
            "## Label Support",
            "",
            render_support_markdown_table(metrics["label_support"]),
            "",
        ]
    )

    if metrics["status"] == "insufficient_data":
        lines.extend(
            [
                "## Status",
                "",
                metrics["reason"],
                "",
                f"- total_examples: `{metrics['total_examples']}`",
                f"- minimum_total_examples: `{metrics['minimum_total_examples']}`",
                f"- minimum_examples_per_class: `{metrics['minimum_examples_per_class']}`",
                f"- insufficient_labels: `{', '.join(metrics['insufficient_labels']) or 'none'}`",
                "",
                "## Why This Is Still Useful",
                "",
                "- It proves the repo can build a reproducible weak-label corpus from deterministic rules without inventing labels.",
                "- It keeps the modeling workstream honest when the local corpus is too small for a credible split.",
                "- It preserves deterministic extraction as the trustworthy path while still setting up later benchmark work.",
                "",
                "## Limitations",
                "",
                "- Local fixtures are intentionally tiny and architecture-focused.",
                "- Weak labels inherit the blind spots of the deterministic rules that created them.",
                "- No claim is made that this baseline beats deterministic extraction or generalizes to production traffic.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Metrics",
            "",
            f"- accuracy: `{metrics['accuracy']:.4f}`",
            f"- macro_f1: `{metrics['macro_f1']:.4f}`",
            f"- train_size: `{metrics['train_size']}`",
            f"- test_size: `{metrics['test_size']}`",
            "",
            "## Per-Label Metrics",
            "",
            "| label | precision | recall | f1 | support |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for label in SIGNAL_FAMILY_LABELS:
        row = metrics["per_label"][label]
        lines.append(
            f"| {label} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['support']} |"
        )

    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- This baseline is a research scaffold only and does not replace deterministic scoring.",
            "- Weak labels reflect existing rule coverage, not independent human annotation.",
            "- Scores should not be read as proof of production readiness or statistical significance.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _test_count(total_examples: int) -> int:
    return max(len(SIGNAL_FAMILY_LABELS), ceil(total_examples * DEFAULT_TEST_SIZE))


def _build_insufficient_payload(examples: list[dict[str, Any]], reason: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "insufficient_data",
        "task": "signal_family",
        "total_examples": len(examples),
        "label_support": reason["label_support"],
        "minimum_examples_per_class": reason["minimum_examples_per_class"],
        "minimum_total_examples": reason["minimum_total_examples"],
        "insufficient_labels": reason["insufficient_labels"],
        "reason": reason["reason"],
        "source_paths": sorted({str(example["source_path"]) for example in examples}),
    }


def _train_classifier(examples: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "scikit-learn is required for the baseline training path. Install the optional `nlp` group if needed."
        ) from exc

    texts = [example["text"] for example in examples]
    labels = [example["signal_family"] for example in examples]
    test_size = _test_count(len(examples))
    train_examples, test_examples, train_labels, test_labels = train_test_split(
        examples,
        labels,
        test_size=test_size,
        random_state=DEFAULT_RANDOM_SEED,
        stratify=labels,
    )

    pipeline = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            (
                "model",
                LogisticRegression(
                    max_iter=400,
                    class_weight="balanced",
                    random_state=DEFAULT_RANDOM_SEED,
                ),
            ),
        ]
    )
    pipeline.fit([item["text"] for item in train_examples], train_labels)
    predictions = pipeline.predict([item["text"] for item in test_examples])
    probabilities = pipeline.predict_proba([item["text"] for item in test_examples])

    precision, recall, f1, support = precision_recall_fscore_support(
        test_labels,
        predictions,
        labels=list(SIGNAL_FAMILY_LABELS),
        zero_division=0.0,
    )
    per_label = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(SIGNAL_FAMILY_LABELS)
    }
    prediction_rows = []
    class_labels = list(pipeline.named_steps["model"].classes_)
    for example, predicted_label, probs in zip(test_examples, predictions, probabilities, strict=True):
        score_map = {label: float(score) for label, score in zip(class_labels, probs, strict=True)}
        prediction_rows.append(
            {
                "conversation_id": example["conversation_id"],
                "message_index": example["message_index"],
                "domain": example["domain"],
                "text": example["text"],
                "gold_label": example["signal_family"],
                "predicted_label": str(predicted_label),
                "confidence": round(max(score_map.values()), 4),
                "score_by_label": {label: round(score_map.get(label, 0.0), 4) for label in SIGNAL_FAMILY_LABELS},
                "source_path": example["source_path"],
                "evidence_terms": example.get("evidence_terms", []),
            }
        )

    metrics = {
        "status": "ok",
        "task": "signal_family",
        "model": "tfidf_logistic_regression",
        "random_seed": DEFAULT_RANDOM_SEED,
        "total_examples": len(examples),
        "train_size": len(train_examples),
        "test_size": len(test_examples),
        "label_support": label_support_counts(examples),
        "train_label_support": dict(Counter(train_labels)),
        "test_label_support": dict(Counter(test_labels)),
        "accuracy": float(accuracy_score(test_labels, predictions)),
        "macro_f1": float(sum(row["f1"] for row in per_label.values()) / len(SIGNAL_FAMILY_LABELS)),
        "per_label": per_label,
        "source_paths": sorted({str(example["source_path"]) for example in examples}),
    }
    return metrics, prediction_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Train a lightweight transcript-first signal-family baseline from local weak labels."
    )
    parser.add_argument(
        "--examples-path",
        help="Optional JSONL file with labeled examples for testing or controlled experiments.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "data" / "nlp_research"),
        help="Directory for metrics and prediction outputs.",
    )
    parser.add_argument(
        "--report-path",
        default=str(ROOT / "docs" / "nlp-baseline-report.md"),
        help="Path to the Markdown report output.",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    report_path = Path(args.report_path)
    metrics_path = out_dir / "baseline_metrics.json"
    predictions_path = out_dir / "baseline_predictions.jsonl"

    if args.examples_path:
        examples = load_supervised_examples(Path(args.examples_path))
        source_kind = "supervised_examples"
    else:
        examples = build_weak_labeled_examples()
        source_kind = "deterministic_weak_labels"

    readiness = training_readiness(examples)
    if not readiness["ready"]:
        metrics = _build_insufficient_payload(examples, readiness)
        _write_json(metrics_path, metrics)
        _write_jsonl(predictions_path, [])
        report_path.write_text(_render_report(metrics, source_kind=source_kind), encoding="utf-8")
        print(json.dumps({"status": "insufficient_data", "metrics_path": str(metrics_path)}, indent=2))
        return 0

    metrics, predictions = _train_classifier(examples)
    _write_json(metrics_path, metrics)
    _write_jsonl(predictions_path, predictions)
    report_path.write_text(_render_report(metrics, source_kind=source_kind), encoding="utf-8")
    print(json.dumps({"status": "ok", "metrics_path": str(metrics_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
