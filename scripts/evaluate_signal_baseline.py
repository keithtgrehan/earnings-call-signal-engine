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

from signal_engine.emotion_benchmark import confusion_matrix_counts, macro_f1, precision_recall_f1
from signal_engine.signal_baseline import (
    DEFAULT_RANDOM_SEED,
    DEFAULT_TEST_SIZE,
    HUMAN_REVIEWED_LABELS_RELATIVE_PATH,
    SIGNAL_FAMILY_LABELS,
    load_supervised_examples,
    predict_deterministic_signal_family,
    render_support_markdown_table,
)


EARLY_BENCHMARK_LIMITATIONS = [
    "This is an early labeled benchmark, not statistical proof.",
    "The classifier is a research benchmark only.",
    "Deterministic rules remain canonical unless a larger and independently reviewed benchmark proves otherwise.",
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def _test_count(total_examples: int) -> int:
    return max(len(SIGNAL_FAMILY_LABELS), ceil(total_examples * DEFAULT_TEST_SIZE))


def _label_support(examples: list[dict[str, Any]]) -> dict[str, int]:
    counts = {label: 0 for label in SIGNAL_FAMILY_LABELS}
    for example in examples:
        counts[str(example["signal_family"])] += 1
    return counts


def _accuracy(y_true: list[str], y_pred: list[str]) -> float:
    if not y_true:
        return 0.0
    matches = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if truth == pred)
    return matches / len(y_true)


def _weighted_f1(y_true: list[str], y_pred: list[str]) -> float:
    per_label = precision_recall_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS)
    total_support = sum(int(row["support"]) for row in per_label.values())
    if total_support == 0:
        return 0.0
    return sum(float(row["f1"]) * int(row["support"]) for row in per_label.values()) / total_support


def _model_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    return {
        "accuracy": _accuracy(y_true, y_pred),
        "macro_f1": macro_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS),
        "weighted_f1": _weighted_f1(y_true, y_pred),
        "per_label": precision_recall_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS),
        "confusion_matrix": confusion_matrix_counts(y_true, y_pred, SIGNAL_FAMILY_LABELS),
    }


def _load_examples(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Labeled dataset not found: {path}")
    return load_supervised_examples(path)


def _load_existing_metrics(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _majority_label(labels: list[str]) -> str:
    counts = Counter(labels)
    best_score = max(counts.values()) if counts else 0
    for label in SIGNAL_FAMILY_LABELS:
        if counts.get(label, 0) == best_score:
            return label
    return SIGNAL_FAMILY_LABELS[0]


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


def _variant_specs() -> list[dict[str, Any]]:
    specs = [
        {
            "variant_id": "tfidf_logreg_unigram",
            "label": "TF-IDF + LogisticRegression (1,1)",
            "model_family": "logistic_regression",
            "ngram_range": [1, 1],
            "class_weight": None,
        },
        {
            "variant_id": "tfidf_logreg_bigram",
            "label": "TF-IDF + LogisticRegression (1,2)",
            "model_family": "logistic_regression",
            "ngram_range": [1, 2],
            "class_weight": None,
        },
        {
            "variant_id": "tfidf_logreg_unigram_balanced",
            "label": "TF-IDF + LogisticRegression balanced (1,1)",
            "model_family": "logistic_regression",
            "ngram_range": [1, 1],
            "class_weight": "balanced",
        },
        {
            "variant_id": "tfidf_logreg_bigram_balanced",
            "label": "TF-IDF + LogisticRegression balanced (1,2)",
            "model_family": "logistic_regression",
            "ngram_range": [1, 2],
            "class_weight": "balanced",
        },
    ]
    try:
        from sklearn.svm import LinearSVC  # noqa: F401
    except ImportError:  # pragma: no cover - environment dependent
        return specs

    specs.extend(
        [
            {
                "variant_id": "tfidf_linear_svc_unigram_balanced",
                "label": "TF-IDF + LinearSVC balanced (1,1)",
                "model_family": "linear_svc",
                "ngram_range": [1, 1],
                "class_weight": "balanced",
            },
            {
                "variant_id": "tfidf_linear_svc_bigram_balanced",
                "label": "TF-IDF + LinearSVC balanced (1,2)",
                "model_family": "linear_svc",
                "ngram_range": [1, 2],
                "class_weight": "balanced",
            },
        ]
    )
    return specs


def _train_pipeline(spec: dict[str, Any]):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.svm import LinearSVC

    if spec["model_family"] == "logistic_regression":
        estimator = LogisticRegression(
            max_iter=500,
            class_weight=spec["class_weight"],
            random_state=DEFAULT_RANDOM_SEED,
        )
    elif spec["model_family"] == "linear_svc":
        estimator = LinearSVC(class_weight=spec["class_weight"], random_state=DEFAULT_RANDOM_SEED)
    else:  # pragma: no cover
        raise ValueError(f"Unsupported model family: {spec['model_family']}")

    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=tuple(spec["ngram_range"]), min_df=1)),
            ("model", estimator),
        ]
    )


def _score_map_from_probabilities(model_labels: list[str], probability_row: Any) -> dict[str, float]:
    return {
        label: round(float(score), 4)
        for label, score in zip(model_labels, probability_row, strict=True)
    }


def _evaluate_holdout(
    examples: list[dict[str, Any]],
    *,
    existing_metrics: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from sklearn.model_selection import train_test_split

    labels = [example["signal_family"] for example in examples]
    test_size = _test_count(len(examples))
    train_examples, eval_examples = train_test_split(
        examples,
        test_size=test_size,
        random_state=DEFAULT_RANDOM_SEED,
        stratify=labels,
    )

    train_labels = [example["signal_family"] for example in train_examples]
    eval_labels = [example["signal_family"] for example in eval_examples]
    train_ids = [example["id"] for example in train_examples]
    test_ids = [example["id"] for example in eval_examples]

    majority_label = _majority_label(train_labels)
    majority_predictions = [majority_label for _ in eval_examples]
    majority_metrics = _model_metrics(eval_labels, majority_predictions)

    deterministic_rows = [
        predict_deterministic_signal_family(example["text"], domain=example.get("domain"))
        for example in eval_examples
    ]
    deterministic_predictions = [row["label"] for row in deterministic_rows]
    deterministic_metrics = _model_metrics(eval_labels, deterministic_predictions)

    benchmark_runs = [
        {
            "variant_id": "majority_baseline",
            "label": "Majority baseline",
            "system_type": "baseline",
            "canonical": False,
            "exploratory": False,
            "model_family": "majority_class",
            "ngram_range": None,
            "class_weight": None,
            "metrics": majority_metrics,
        },
        {
            "variant_id": "deterministic_rules",
            "label": "Deterministic rules",
            "system_type": "rules",
            "canonical": True,
            "exploratory": False,
            "model_family": "deterministic_lexical_rules",
            "ngram_range": None,
            "class_weight": None,
            "metrics": deterministic_metrics,
        },
    ]

    train_texts = [example["text"] for example in train_examples]
    train_y = train_labels
    eval_texts = [example["text"] for example in eval_examples]
    variant_predictions: dict[str, list[str]] = {}
    variant_score_maps: dict[str, dict[str, dict[str, float]]] = {}

    for spec in _variant_specs():
        pipeline = _train_pipeline(spec)
        pipeline.fit(train_texts, train_y)
        predicted = [str(value) for value in pipeline.predict(eval_texts)]
        metrics = _model_metrics(eval_labels, predicted)
        benchmark_runs.append(
            {
                "variant_id": spec["variant_id"],
                "label": spec["label"],
                "system_type": "classifier",
                "canonical": False,
                "exploratory": True,
                "model_family": spec["model_family"],
                "ngram_range": spec["ngram_range"],
                "class_weight": spec["class_weight"],
                "metrics": metrics,
            }
        )
        variant_predictions[spec["variant_id"]] = predicted
        if hasattr(pipeline.named_steps["model"], "predict_proba"):
            probabilities = pipeline.predict_proba(eval_texts)
            model_labels = list(pipeline.named_steps["model"].classes_)
            variant_score_maps[spec["variant_id"]] = {
                example["id"]: _score_map_from_probabilities(model_labels, probability_row.tolist())
                for example, probability_row in zip(eval_examples, probabilities, strict=True)
            }
        else:
            variant_score_maps[spec["variant_id"]] = {}

    classifier_runs = [row for row in benchmark_runs if row["system_type"] == "classifier"]
    selected_classifier = max(
        classifier_runs,
        key=lambda row: (
            float(row["metrics"]["macro_f1"]),
            float(row["metrics"]["weighted_f1"]),
            float(row["metrics"]["accuracy"]),
        ),
    )
    classifier_variant_id = str(selected_classifier["variant_id"])
    classifier_predictions = variant_predictions[classifier_variant_id]
    classifier_metrics = _model_metrics(eval_labels, classifier_predictions)

    predictions = []
    variant_ids = list(variant_predictions.keys())
    selected_score_maps = variant_score_maps.get(classifier_variant_id, {})
    for index, (example, deterministic_row, classifier_label) in enumerate(
        zip(eval_examples, deterministic_rows, classifier_predictions, strict=True)
    ):
        score_map = selected_score_maps.get(example["id"], {})
        confidence = max(score_map.values()) if score_map else None
        predictions.append(
            {
                "id": example["id"],
                "domain": example["domain"],
                "text": example["text"],
                "gold_label": example["signal_family"],
                "majority_label": majority_label,
                "deterministic_label": deterministic_row["label"],
                "deterministic_evidence_terms": deterministic_row["evidence_terms"],
                "classifier_label": classifier_label,
                "classifier_model": classifier_variant_id,
                "classifier_confidence": round(float(confidence), 4) if confidence is not None else None,
                "classifier_score_by_label": score_map,
                "variant_predictions": {variant_id: variant_predictions[variant_id][index] for variant_id in variant_ids},
                "source_file": example["source_file"],
                "pii_redacted": bool(example.get("pii_redacted", False)),
                "label_source": example.get("label_source", ""),
                "notes": example.get("notes", ""),
                "evaluation_scope": "train_test_split",
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
        "split_strategy": "train_test_split",
        "split_details": {
            "train_size": len(train_examples),
            "test_size": len(eval_examples),
            "random_seed": DEFAULT_RANDOM_SEED,
            "train_ids": train_ids,
            "test_ids": test_ids,
        },
        "majority_baseline": {**majority_metrics, "majority_label": majority_label},
        "deterministic_rules": deterministic_metrics,
        "classifier": classifier_metrics,
        "classifier_model": classifier_variant_id,
        "selected_classifier": {
            "variant_id": classifier_variant_id,
            "label": selected_classifier["label"],
            "selection_metric": "macro_f1",
            "exploratory": True,
        },
        "canonical_system": "deterministic_rules",
        "benchmark_runs": benchmark_runs,
        "historical_context": _historical_context(existing_metrics),
        "limitations": EARLY_BENCHMARK_LIMITATIONS
        + [
            "The dataset is small, hand-seeded, and drawn from committed local fixtures only.",
            "Exploratory variants improve error analysis context, not product certainty.",
        ],
    }
    return metrics, predictions


def _historical_context(existing_metrics: dict[str, Any] | None) -> dict[str, Any] | None:
    if not existing_metrics or existing_metrics.get("status") != "ok":
        return None
    return {
        "note": "The earlier first-proof report compared deterministic rules with a single TF-IDF + LogisticRegression classifier. This refreshed report adds a majority baseline and multiple exploratory variants.",
    }


def _build_insufficient_payload(examples: list[dict[str, Any]], dataset_path: Path) -> dict[str, Any]:
    return {
        "status": "insufficient_data",
        "task": "signal_family",
        "dataset_kind": "human_reviewed_signal_labels",
        "dataset_path": str(dataset_path),
        "dataset_size": len(examples),
        "label_support": _label_support(examples),
        "reason": (
            "The current labeled set is too small or too imbalanced for a fair held-out 4-class comparison with multiple baselines."
        ),
        "canonical_system": "deterministic_rules",
        "limitations": EARLY_BENCHMARK_LIMITATIONS
        + [
            "Variant comparison and confusion analysis need a larger or more evenly balanced set.",
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


def _render_run_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| system | type | accuracy | macro_f1 | weighted_f1 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        metrics = row["metrics"]
        lines.append(
            f"| {row['variant_id']} | {row['system_type']} | {metrics['accuracy']:.4f} | {metrics['macro_f1']:.4f} | {metrics['weighted_f1']:.4f} |"
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
        *EARLY_BENCHMARK_LIMITATIONS,
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

    historical_context = metrics.get("historical_context")
    if historical_context:
        lines.extend(
            [
                "## Historical Context",
                "",
                f"- {historical_context['note']}",
                "",
            ]
        )

    headline_rows = [
        next(row for row in metrics["benchmark_runs"] if row["variant_id"] == "majority_baseline"),
        next(row for row in metrics["benchmark_runs"] if row["variant_id"] == "deterministic_rules"),
        next(row for row in metrics["benchmark_runs"] if row["variant_id"] == metrics["classifier_model"]),
    ]

    lines.extend(
        [
            "## Evaluation Setup",
            "",
            f"- split_strategy: `{metrics['split_strategy']}`",
            f"- selected_classifier: `{metrics['classifier_model']}`",
            f"- canonical_system: `{metrics['canonical_system']}`",
            f"- evaluation_set_size: `{metrics['evaluation_set_size']}`",
            f"- warning: small benchmark; treat exploratory variants as benchmark aids only",
            "",
            "## Headline Results",
            "",
            *_render_run_table(headline_rows),
            "",
            "See `docs/signal-error-analysis.md` for failure-mode review and `docs/gold-holdout-set-guide.md` for holdout discipline.",
            "",
            "## Exploratory Model Variant Comparison",
            "",
            *_render_run_table(metrics["benchmark_runs"]),
            "",
            "## Selected Classifier Per-Class Metrics",
            "",
            *_render_per_label_table(metrics["classifier"]["per_label"]),
            "",
            "## Deterministic Rules Per-Class Metrics",
            "",
            *_render_per_label_table(metrics["deterministic_rules"]["per_label"]),
            "",
            "## Selected Classifier Confusion Matrix",
            "",
            *_render_confusion_table(metrics["classifier"]["confusion_matrix"]),
            "",
            "## Deterministic Rules Confusion Matrix",
            "",
            *_render_confusion_table(metrics["deterministic_rules"]["confusion_matrix"]),
            "",
            "## Train/Test IDs",
            "",
            f"- train_ids: `{', '.join(metrics['split_details']['train_ids'])}`",
            f"- test_ids: `{', '.join(metrics['split_details']['test_ids'])}`",
            "",
            "## Limitations",
            "",
            "- The labeled set is small, hand-seeded, and drawn from committed local fixtures only.",
            "- Many seeded labels were chosen with help from deterministic lexicons, so this benchmark is not independent proof of model superiority.",
            "- The majority baseline and exploratory variants improve context, not certainty.",
            "- Gold holdout candidates and second-review prioritization are now scaffolded, but final gold status still requires second reviewer input.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate deterministic transcript rules against lightweight classifier variants on the human-reviewed label seed."
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
    existing_metrics = _load_existing_metrics(metrics_path)

    if _holdout_ready(counts, len(examples)):
        metrics, predictions = _evaluate_holdout(examples, existing_metrics=existing_metrics)
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
                "classifier_model": metrics.get("classifier_model"),
                "metrics_path": str(metrics_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
