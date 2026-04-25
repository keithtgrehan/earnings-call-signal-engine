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

from signal_engine.emotion_benchmark import (
    confusion_matrix_counts,
    macro_f1,
    precision_recall_f1,
)
from signal_engine.signal_baseline import (
    DEFAULT_RANDOM_SEED,
    DEFAULT_TEST_SIZE,
    HUMAN_REVIEWED_LABELS_RELATIVE_PATH,
    SIGNAL_FAMILY_LABELS,
    load_supervised_examples,
    predict_deterministic_signal_family,
    render_support_markdown_table,
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


def _accuracy(y_true: list[str], y_pred: list[str]) -> float:
    if not y_true:
        return 0.0
    matches = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if truth == pred)
    return matches / len(y_true)


def _label_support(examples: list[dict[str, Any]]) -> dict[str, int]:
    counts = {label: 0 for label in SIGNAL_FAMILY_LABELS}
    for example in examples:
        label = str(example["signal_family"])
        counts[label] += 1
    return counts


def _model_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    return {
        "accuracy": _accuracy(y_true, y_pred),
        "macro_f1": macro_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS),
        "per_label": precision_recall_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS),
        "confusion_matrix": confusion_matrix_counts(y_true, y_pred, SIGNAL_FAMILY_LABELS),
    }


def _load_examples(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Labeled dataset not found: {path}")
    return load_supervised_examples(path)


def _train_pipeline():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "scikit-learn is required for transcript baseline evaluation. "
            "Install the optional `nlp` group if needed."
        ) from exc

    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            (
                "model",
                LogisticRegression(
                    max_iter=500,
                    class_weight="balanced",
                    random_state=DEFAULT_RANDOM_SEED,
                ),
            ),
        ]
    )


def _holdout_ready(counts: dict[str, int], total_examples: int) -> bool:
    test_size = _test_count(total_examples)
    min_support = min(counts.values()) if counts else 0
    train_size = total_examples - test_size
    return (
        total_examples >= 12
        and min_support >= 2
        and test_size >= len(SIGNAL_FAMILY_LABELS)
        and train_size >= len(SIGNAL_FAMILY_LABELS)
    )


def _cross_validation_ready(counts: dict[str, int], total_examples: int) -> bool:
    min_support = min(counts.values()) if counts else 0
    return total_examples >= 12 and min_support >= 2


def _evaluate_holdout(examples: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from sklearn.model_selection import train_test_split

    labels = [example["signal_family"] for example in examples]
    test_size = _test_count(len(examples))
    train_examples, eval_examples, train_labels, eval_labels = train_test_split(
        examples,
        labels,
        test_size=test_size,
        random_state=DEFAULT_RANDOM_SEED,
        stratify=labels,
    )

    pipeline = _train_pipeline()
    pipeline.fit([item["text"] for item in train_examples], train_labels)
    classifier_predictions = list(pipeline.predict([item["text"] for item in eval_examples]))
    probabilities = pipeline.predict_proba([item["text"] for item in eval_examples])
    model_labels = list(pipeline.named_steps["model"].classes_)

    return _build_evaluation_payload(
        examples=examples,
        eval_examples=eval_examples,
        eval_labels=eval_labels,
        classifier_predictions=classifier_predictions,
        classifier_probabilities=probabilities,
        classifier_model_labels=model_labels,
        split_strategy="train_test_split",
        split_details={
            "train_size": len(train_examples),
            "test_size": len(eval_examples),
            "random_seed": DEFAULT_RANDOM_SEED,
        },
    )


def _evaluate_cross_validation(examples: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from sklearn.model_selection import StratifiedKFold

    labels = [example["signal_family"] for example in examples]
    min_support = min(Counter(labels).values())
    n_splits = min(3, min_support)
    if n_splits < 2:
        raise ValueError("Cross-validation requires at least two folds.")

    splitter = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=DEFAULT_RANDOM_SEED,
    )
    classifier_predictions = ["" for _ in examples]
    classifier_confidences = [0.0 for _ in examples]
    classifier_score_maps: list[dict[str, float]] = [{} for _ in examples]

    for train_indices, test_indices in splitter.split([item["text"] for item in examples], labels):
        train_examples = [examples[index] for index in train_indices]
        test_examples = [examples[index] for index in test_indices]
        train_labels = [examples[index]["signal_family"] for index in train_indices]
        pipeline = _train_pipeline()
        pipeline.fit([item["text"] for item in train_examples], train_labels)
        fold_predictions = list(pipeline.predict([item["text"] for item in test_examples]))
        probabilities = pipeline.predict_proba([item["text"] for item in test_examples])
        model_labels = list(pipeline.named_steps["model"].classes_)
        for example_index, predicted_label, probability_row in zip(
            test_indices,
            fold_predictions,
            probabilities,
            strict=True,
        ):
            score_map = {
                label: float(score)
                for label, score in zip(model_labels, probability_row, strict=True)
            }
            classifier_predictions[example_index] = str(predicted_label)
            classifier_confidences[example_index] = max(score_map.values())
            classifier_score_maps[example_index] = {
                label: round(score_map.get(label, 0.0), 4) for label in SIGNAL_FAMILY_LABELS
            }

    eval_examples = list(examples)
    eval_labels = [example["signal_family"] for example in eval_examples]
    deterministic_rows = []
    deterministic_predictions = []
    for example in eval_examples:
        rule_prediction = predict_deterministic_signal_family(example["text"], domain=example.get("domain"))
        deterministic_predictions.append(rule_prediction["label"])
        deterministic_rows.append(rule_prediction)

    predictions = []
    for example, gold_label, deterministic_row, predicted_label, confidence, score_map in zip(
        eval_examples,
        eval_labels,
        deterministic_rows,
        classifier_predictions,
        classifier_confidences,
        classifier_score_maps,
        strict=True,
    ):
        predictions.append(
            {
                "id": example["id"],
                "domain": example["domain"],
                "text": example["text"],
                "gold_label": gold_label,
                "deterministic_label": deterministic_row["label"],
                "deterministic_evidence_terms": deterministic_row["evidence_terms"],
                "classifier_label": predicted_label,
                "classifier_confidence": round(float(confidence), 4),
                "classifier_score_by_label": score_map,
                "source_file": example["source_file"],
                "pii_redacted": bool(example.get("pii_redacted", False)),
                "label_source": example.get("label_source", ""),
                "notes": example.get("notes", ""),
                "evaluation_scope": "cross_validation",
            }
        )

    metrics = {
        "status": "ok",
        "task": "signal_family",
        "dataset_kind": "human_reviewed_signal_labels",
        "dataset_size": len(examples),
        "label_support": _label_support(examples),
        "split_strategy": "stratified_kfold",
        "split_details": {
            "n_splits": n_splits,
            "random_seed": DEFAULT_RANDOM_SEED,
        },
        "deterministic_rules": _model_metrics(eval_labels, deterministic_predictions),
        "classifier": _model_metrics(eval_labels, classifier_predictions),
        "classifier_model": "tfidf_logistic_regression",
        "canonical_system": "deterministic_rules",
        "limitations": [
            "This is an early labeled benchmark, not statistical proof.",
            "The classifier is a research benchmark only.",
            "Deterministic rules remain canonical unless the benchmark proves otherwise.",
        ],
    }
    return metrics, predictions


def _build_evaluation_payload(
    *,
    examples: list[dict[str, Any]],
    eval_examples: list[dict[str, Any]],
    eval_labels: list[str],
    classifier_predictions: list[str],
    classifier_probabilities: Any,
    classifier_model_labels: list[str],
    split_strategy: str,
    split_details: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    deterministic_predictions = []
    deterministic_rows = []
    predictions = []

    for example, predicted_label, probability_row, gold_label in zip(
        eval_examples,
        classifier_predictions,
        classifier_probabilities,
        eval_labels,
        strict=True,
    ):
        deterministic_row = predict_deterministic_signal_family(example["text"], domain=example.get("domain"))
        deterministic_predictions.append(deterministic_row["label"])
        deterministic_rows.append(deterministic_row)
        score_map = {
            label: float(score)
            for label, score in zip(classifier_model_labels, probability_row, strict=True)
        }
        predictions.append(
            {
                "id": example["id"],
                "domain": example["domain"],
                "text": example["text"],
                "gold_label": gold_label,
                "deterministic_label": deterministic_row["label"],
                "deterministic_evidence_terms": deterministic_row["evidence_terms"],
                "classifier_label": str(predicted_label),
                "classifier_confidence": round(max(score_map.values()), 4),
                "classifier_score_by_label": {
                    label: round(score_map.get(label, 0.0), 4) for label in SIGNAL_FAMILY_LABELS
                },
                "source_file": example["source_file"],
                "pii_redacted": bool(example.get("pii_redacted", False)),
                "label_source": example.get("label_source", ""),
                "notes": example.get("notes", ""),
                "evaluation_scope": split_strategy,
            }
        )

    metrics = {
        "status": "ok",
        "task": "signal_family",
        "dataset_kind": "human_reviewed_signal_labels",
        "dataset_size": len(examples),
        "label_support": _label_support(examples),
        "evaluation_set_size": len(eval_examples),
        "evaluation_label_support": dict(Counter(eval_labels)),
        "split_strategy": split_strategy,
        "split_details": split_details,
        "deterministic_rules": _model_metrics(eval_labels, deterministic_predictions),
        "classifier": _model_metrics(eval_labels, classifier_predictions),
        "classifier_model": "tfidf_logistic_regression",
        "canonical_system": "deterministic_rules",
        "limitations": [
            "This is an early labeled benchmark, not statistical proof.",
            "The classifier is a research benchmark only.",
            "Deterministic rules remain canonical unless the benchmark proves otherwise.",
        ],
    }
    return metrics, predictions


def _build_insufficient_payload(examples: list[dict[str, Any]], dataset_path: Path) -> dict[str, Any]:
    counts = _label_support(examples)
    return {
        "status": "insufficient_data",
        "task": "signal_family",
        "dataset_kind": "human_reviewed_signal_labels",
        "dataset_path": str(dataset_path),
        "dataset_size": len(examples),
        "label_support": counts,
        "reason": (
            "The current labeled set is too small or too imbalanced for a fair held-out or cross-validated 4-class comparison."
        ),
        "canonical_system": "deterministic_rules",
        "limitations": [
            "This is an early labeled benchmark, not statistical proof.",
            "The classifier is a research benchmark only.",
            "Deterministic rules remain canonical unless the benchmark proves otherwise.",
        ],
    }


def _render_confusion_table(matrix: dict[str, dict[str, int]]) -> list[str]:
    lines = [
        "| true \\ predicted | " + " | ".join(SIGNAL_FAMILY_LABELS) + " |",
        "| --- | " + " | ".join("---" for _ in SIGNAL_FAMILY_LABELS) + " |",
    ]
    for true_label in SIGNAL_FAMILY_LABELS:
        row = [str(matrix[true_label][predicted_label]) for predicted_label in SIGNAL_FAMILY_LABELS]
        lines.append(f"| {true_label} | " + " | ".join(row) + " |")
    return lines


def _render_per_label_table(metrics: dict[str, dict[str, Any]]) -> list[str]:
    lines = [
        "| label | precision | recall | f1 | support |",
        "| --- | --- | --- | --- | --- |",
    ]
    for label in SIGNAL_FAMILY_LABELS:
        row = metrics[label]
        lines.append(
            f"| {label} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['support']} |"
        )
    return lines


def _render_report(metrics: dict[str, Any], *, dataset_path: Path) -> str:
    try:
        dataset_label = str(dataset_path.relative_to(ROOT))
    except ValueError:
        dataset_label = str(dataset_path)

    lines = [
        "# Transcript Baseline Benchmark",
        "",
        "This is an early labeled benchmark, not statistical proof.",
        "The classifier is a research benchmark only.",
        "Deterministic rules remain canonical unless the benchmark proves otherwise.",
        "",
        "## Dataset",
        "",
        f"- path: `{dataset_label}`",
        f"- dataset_size: `{metrics['dataset_size']}`",
        "",
        render_support_markdown_table(metrics["label_support"]),
        "",
    ]

    if metrics["status"] != "ok":
        lines.extend(
            [
                "## Status",
                "",
                f"- status: `{metrics['status']}`",
                f"- reason: {metrics['reason']}",
                "",
                "## Limitations",
                "",
                "- The current labeled set is still useful for review and iteration, but not yet large enough for a fair model comparison.",
                "- Class balance and example diversity should improve before any stronger conclusion is drawn.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Evaluation Setup",
            "",
            f"- split_strategy: `{metrics['split_strategy']}`",
            f"- classifier_model: `{metrics['classifier_model']}`",
            f"- canonical_system: `{metrics['canonical_system']}`",
            f"- evaluation_set_size: `{metrics.get('evaluation_set_size', metrics['dataset_size'])}`",
            "",
            "## Headline Results",
            "",
            "| system | accuracy | macro_f1 |",
            "| --- | --- | --- |",
            f"| deterministic_rules | {metrics['deterministic_rules']['accuracy']:.4f} | {metrics['deterministic_rules']['macro_f1']:.4f} |",
            f"| tfidf_logistic_regression | {metrics['classifier']['accuracy']:.4f} | {metrics['classifier']['macro_f1']:.4f} |",
            "",
            "## Per-Class Metrics: Deterministic Rules",
            "",
            *_render_per_label_table(metrics["deterministic_rules"]["per_label"]),
            "",
            "## Per-Class Metrics: Classifier",
            "",
            *_render_per_label_table(metrics["classifier"]["per_label"]),
            "",
            "## Confusion Summary: Deterministic Rules",
            "",
            *_render_confusion_table(metrics["deterministic_rules"]["confusion_matrix"]),
            "",
            "## Confusion Summary: Classifier",
            "",
            *_render_confusion_table(metrics["classifier"]["confusion_matrix"]),
            "",
            "## Limitations",
            "",
            "- The labeled set is small, hand-seeded, and drawn from committed local fixtures only.",
            "- Many seeded labels were chosen with help from deterministic lexicons, so this benchmark is not independent proof of model superiority.",
            "- The benchmark is useful for reviewer-facing proof, error inspection, and future iteration, not for claims of production readiness or statistical significance.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate deterministic transcript rules against a lightweight classifier on the human-reviewed label seed."
    )
    parser.add_argument(
        "--input-path",
        default=str(ROOT / HUMAN_REVIEWED_LABELS_RELATIVE_PATH),
        help="Path to the labeled JSONL dataset.",
    )
    parser.add_argument(
        "--metrics-path",
        default=str(ROOT / "data" / "nlp_research" / "transcript_baseline_metrics.json"),
        help="Path to the JSON metrics output.",
    )
    parser.add_argument(
        "--predictions-path",
        default=str(ROOT / "data" / "nlp_research" / "transcript_baseline_predictions.jsonl"),
        help="Path to the JSONL predictions output.",
    )
    parser.add_argument(
        "--report-path",
        default=str(ROOT / "docs" / "transcript-baseline-benchmark.md"),
        help="Path to the Markdown benchmark report.",
    )
    args = parser.parse_args(argv)

    dataset_path = Path(args.input_path)
    metrics_path = Path(args.metrics_path)
    predictions_path = Path(args.predictions_path)
    report_path = Path(args.report_path)

    examples = _load_examples(dataset_path)
    counts = _label_support(examples)

    if _holdout_ready(counts, len(examples)):
        metrics, predictions = _evaluate_holdout(examples)
    elif _cross_validation_ready(counts, len(examples)):
        metrics, predictions = _evaluate_cross_validation(examples)
    else:
        metrics = _build_insufficient_payload(examples, dataset_path)
        predictions = []

    metrics["dataset_path"] = str(dataset_path)

    _write_json(metrics_path, metrics)
    _write_jsonl(predictions_path, predictions)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(metrics, dataset_path=dataset_path), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": metrics["status"],
                "dataset_size": metrics["dataset_size"],
                "split_strategy": metrics.get("split_strategy"),
                "metrics_path": str(metrics_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
