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


def _test_count(total_examples: int) -> int:
    return max(len(SIGNAL_FAMILY_LABELS), ceil(total_examples * DEFAULT_TEST_SIZE))


def _train_if_possible(examples: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "scikit-learn is required for the multimodal-era baseline path. Install the optional `nlp` group if needed."
        ) from exc

    labels = [example["signal_family"] for example in examples]
    train_examples, test_examples, train_labels, test_labels = train_test_split(
        examples,
        labels,
        test_size=_test_count(len(examples)),
        random_state=DEFAULT_RANDOM_SEED,
        stratify=labels,
    )
    pipeline = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("model", LogisticRegression(max_iter=400, class_weight="balanced", random_state=DEFAULT_RANDOM_SEED)),
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
    class_labels = list(pipeline.named_steps["model"].classes_)
    prediction_rows = []
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
            }
        )

    metrics = {
        "status": "ok",
        "mode": "transcript_only_wrapper",
        "multimodal_training_ready": False,
        "task": "signal_family",
        "model": "tfidf_logistic_regression",
        "total_examples": len(examples),
        "label_support": label_support_counts(examples),
        "accuracy": float(accuracy_score(test_labels, predictions)),
        "macro_f1": float(sum(f1) / len(SIGNAL_FAMILY_LABELS)),
        "per_label": {
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(SIGNAL_FAMILY_LABELS)
        },
        "source_paths": sorted({str(example["source_path"]) for example in examples}),
        "train_label_support": dict(Counter(train_labels)),
        "test_label_support": dict(Counter(test_labels)),
    }
    return metrics, prediction_rows


def _render_report(status_payload: dict[str, Any]) -> str:
    lines = [
        "# Signal Baseline Report",
        "",
        "- scope: transcript-first wrapper for future multimodal evaluation",
        f"- status: `{status_payload['status']}`",
        "- multimodal_training_ready: `false`",
        "- canonical path: deterministic transcript extraction",
        "",
        "## Current Reality",
        "",
        "- The repo does not yet include aligned text + audio + video fixtures with gold labels for a real multimodal lift study.",
        "- This script therefore defaults to a transcript-only wrapper around the same weak-label baseline task used in the NLP tranche.",
        "",
    ]

    if "label_support" in status_payload:
        lines.extend(
            [
                "## Label Support",
                "",
                render_support_markdown_table(status_payload["label_support"]),
                "",
            ]
        )

    if status_payload["status"] == "ok":
        lines.extend(
            [
                "## Benchmark Snapshot",
                "",
                f"- accuracy: `{status_payload['accuracy']:.4f}`",
                f"- macro_f1: `{status_payload['macro_f1']:.4f}`",
                "",
                "## Limitations",
                "",
                "- Training still uses transcript-only weak labels.",
                "- No claim is made that this beats deterministic rules or validates multimodal fusion.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Status",
                "",
                status_payload["reason"],
                "",
                "## Limitations",
                "",
                "- No aligned multimodal gold fixtures are committed in this Signal Engine 2.0 path.",
                "- Local transcript weak labels remain too small or imbalanced for a stronger benchmark by default.",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Train or scaffold a transcript-first baseline in the multimodal research workspace."
    )
    parser.add_argument("--examples-path", help="Optional JSONL file with labeled examples.")
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "data" / "multimodal_research"),
        help="Directory for baseline status and optional metric outputs.",
    )
    parser.add_argument(
        "--report-path",
        default=str(ROOT / "docs" / "signal-baseline-report.md"),
        help="Path to the Markdown report.",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    report_path = Path(args.report_path)
    status_path = out_dir / "baseline_status.json"
    metrics_path = out_dir / "baseline_metrics.json"
    predictions_path = out_dir / "baseline_predictions.jsonl"

    if args.examples_path:
        examples = load_supervised_examples(Path(args.examples_path))
        source_mode = "supervised_examples"
    else:
        examples = build_weak_labeled_examples()
        source_mode = "transcript_only_weak_labels"

    readiness = training_readiness(examples)
    if not readiness["ready"]:
        status_payload = {
            "status": "transcript_only_scaffold",
            "source_mode": source_mode,
            "transcript_only": True,
            "multimodal_training_ready": False,
            "label_support": readiness["label_support"],
            "reason": "No aligned multimodal fixtures are committed, and the local transcript-only weak-label corpus is not strong enough for an honest 4-class split.",
            "source_paths": sorted({str(example["source_path"]) for example in examples}),
        }
        _write_json(status_path, status_payload)
        _write_json(metrics_path, {"status": "not_run", "reason": status_payload["reason"]})
        _write_jsonl(predictions_path, [])
        report_path.write_text(_render_report(status_payload), encoding="utf-8")
        print(json.dumps({"status": status_payload["status"], "status_path": str(status_path)}, indent=2))
        return 0

    metrics, predictions = _train_if_possible(examples)
    status_payload = {
        "status": "ok",
        "source_mode": source_mode,
        "transcript_only": True,
        "multimodal_training_ready": False,
        "label_support": metrics["label_support"],
        "reason": "Training succeeded, but the corpus is still transcript-only and does not validate multimodal lift.",
        "source_paths": metrics["source_paths"],
    }
    _write_json(status_path, status_payload)
    _write_json(metrics_path, metrics)
    _write_jsonl(predictions_path, predictions)
    report_path.write_text(_render_report({**status_payload, **metrics}), encoding="utf-8")
    print(json.dumps({"status": "ok", "status_path": str(status_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
