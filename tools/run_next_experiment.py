#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from experiment_common import GOLD_PATH, gate_state, read_jsonl, row_label, valid_gold_rows  # noqa: E402
from evaluation_quality import deterministic_predictions, precision_recall_f1, provenance_quality, row_text, source_group  # noqa: E402

RESULT_DIR = ROOT / "reports" / "experiment_results"


def write_result(name: str, lines: list[str]) -> Path:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULT_DIR / f"{name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def deterministic_baseline(rows: list[dict[str, object]]) -> Path:
    lines = [
        "# Deterministic Baseline Experiment",
        "",
        f"- gold_labels: `{len(rows)}`",
        "- status: `completed_readiness_snapshot`",
        "",
        "Deterministic Signal Engine remains canonical. Metrics are produced only by the gated evaluation loop.",
    ]
    return write_result("deterministic_baseline", lines)


def local_ml_baseline(rows: list[dict[str, object]]) -> Path:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import confusion_matrix
        from sklearn.model_selection import StratifiedKFold, cross_val_predict
        from sklearn.pipeline import Pipeline
    except Exception as exc:
        return write_result("local_ml_baseline", ["# Local ML Baseline", "", "- status: `skipped`", f"- reason: `{exc}`"])

    deterministic = deterministic_predictions([dict(row) for row in rows])
    by_id = {str(row["id"]): row for row in deterministic}
    texts: list[str] = []
    labels: list[str] = []
    for row in rows:
        label = row_label(row)
        prediction = by_id.get(str(row.get("id") or row.get("candidate_id") or ""))
        evidence_terms = " ".join(str(term).replace(" ", "_") for term in (prediction or {}).get("evidence_terms", []))
        deterministic_label = str((prediction or {}).get("deterministic_label") or "unknown")
        feature_text = " ".join(
            [
                row_text(row),
                f"source_group_{source_group(row)}",
                f"quality_{provenance_quality(row)}",
                f"deterministic_{deterministic_label}",
                evidence_terms,
            ]
        )
        texts.append(feature_text)
        labels.append(label)
    if len(set(labels)) < 2:
        return write_result("local_ml_baseline", ["# Local ML Baseline", "", "- status: `skipped`", "- reason: `requires at least two classes`"])
    min_support = min(Counter(labels).values())
    if min_support < 2:
        return write_result(
            "local_ml_baseline",
            ["# Local ML Baseline", "", "- status: `skipped`", "- reason: `every class needs at least two rows for CV`"],
        )
    splits = min(5, min_support)
    pipeline = Pipeline(
        [
            ("features", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ("model", LogisticRegression(max_iter=500, random_state=42, class_weight="balanced")),
        ]
    )
    cv = StratifiedKFold(n_splits=splits, shuffle=True, random_state=42)
    predictions = list(cross_val_predict(pipeline, texts, labels, cv=cv))
    metrics = precision_recall_f1(labels, predictions)
    label_order = sorted(set(labels))
    matrix = confusion_matrix(labels, predictions, labels=label_order)
    deterministic_metrics = precision_recall_f1(
        [str(row["gold_label"]) for row in deterministic],
        [str(row["deterministic_label"]) for row in deterministic],
    )
    disagreement_rows = []
    for row, ml_pred, det_pred in zip(rows, predictions, deterministic, strict=False):
        if ml_pred != det_pred["deterministic_label"]:
            disagreement_rows.append(
                {
                    "id": row.get("id") or row.get("candidate_id") or "",
                    "gold": row_label(row),
                    "deterministic": det_pred["deterministic_label"],
                    "ml": ml_pred,
                    "text": row_text(row)[:140],
                }
            )
    confusion_lines = []
    for truth_label, row_values in zip(label_order, matrix.tolist(), strict=False):
        confusion_lines.append(f"- `{truth_label}`: {dict(zip(label_order, row_values, strict=False))}")
    report_lines = [
        "# Deterministic vs ML",
        "",
        "This is a benchmark-only comparison. Deterministic Signal Engine output remains canonical.",
        "",
        "## Deterministic Metrics",
        "",
        "```json",
        json.dumps(deterministic_metrics, indent=2),
        "```",
        "",
        "## TF-IDF + Logistic Regression Metrics",
        "",
        "- status: `completed_cv_benchmark`",
        f"- rows: `{len(rows)}`",
        f"- cv_splits: `{splits}`",
        "```json",
        json.dumps(metrics, indent=2),
        "```",
        "",
        "## Confusion Matrix Summary",
        "",
        *confusion_lines,
        "",
        "## Strengths And Tradeoffs",
        "",
        "- Deterministic: explainable evidence terms, stable behavior, safe canonical path.",
        "- ML: useful disagreement finder and sanity-check baseline on the current label set.",
        "- Tradeoff: ML explanations are weaker and the dataset is far too small for product claims.",
        "",
        "## Disagreement Examples",
        "",
    ]
    for item in disagreement_rows[:12]:
        report_lines.append(
            f"- `{item['id']}` gold=`{item['gold']}` deterministic=`{item['deterministic']}` ml=`{item['ml']}` text={item['text']}"
        )
    (ROOT / "reports" / "deterministic_vs_ml.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return write_result(
        "local_ml_baseline",
        [
            "# Local ML Baseline",
            "",
            "- status: `completed_cv_benchmark`",
            f"- rows: `{len(rows)}`",
            f"- cv_splits: `{splits}`",
            f"- precision: `{metrics['precision']}`",
            f"- recall: `{metrics['recall']}`",
            f"- F1: `{metrics['f1']}`",
            "- note: `benchmark-only; no model artifact committed; deterministic remains canonical`",
            "",
            "See `reports/deterministic_vs_ml.md` for details.",
        ],
    )


def lexicon_comparison() -> Path:
    lexicon_paths = [ROOT / "data" / "external" / "loughran_mcdonald", ROOT / "data" / "lexicons"]
    exists = any(
        path.exists() and any(child.is_file() and child.name != ".gitkeep" for child in path.iterdir())
        for path in lexicon_paths
    )
    lines = ["# Lexicon Comparison", "", f"- status: `{'available' if exists else 'skipped'}`"]
    if not exists:
        lines.append("- reason: `Loughran-McDonald lexicon is not locally available; manual setup required.`")
    return write_result("lexicon_comparison", lines)


def dataset_comparison(rows: list[dict[str, object]]) -> Path:
    dataset_roots = [ROOT / "data" / "external" / "financial_phrasebank", ROOT / "data" / "external" / "goemotions"]
    local_files = [path for root in dataset_roots if root.exists() for path in root.glob("*") if path.is_file() and path.name != ".gitkeep"]
    lines = ["# Dataset Comparison", ""]
    if not local_files:
        lines.extend(["- status: `skipped`", "- reason: `No verified local dataset files found. No auto-download attempted.`"])
        return write_result("dataset_comparison", lines)
    counts = {}
    for row in rows:
        counts[row_label(row)] = counts.get(row_label(row), 0) + 1
    lines.extend(["- status: `completed_sanity_check`", f"- local_files: `{len(local_files)}`", "", "## Gold Label Distribution"])
    lines.extend(f"- `{label}`: {count}" for label, count in sorted(counts.items()))
    return write_result("dataset_comparison", lines)


def choose_experiment(gold_count: int) -> str:
    gates = gate_state(gold_count=gold_count, retrieval_experiment_mode=False, embedding_baseline_exists=False, evaluation_exists=False)
    if gates["local_ml"]:
        return "local_ml_baseline"
    return "deterministic_baseline"


def main() -> int:
    rows = valid_gold_rows(read_jsonl(GOLD_PATH))
    experiment = choose_experiment(len(rows))
    if experiment == "local_ml_baseline":
        path = local_ml_baseline(rows)
    else:
        path = deterministic_baseline(rows)
    lexicon_path = lexicon_comparison()
    dataset_path = dataset_comparison(rows)
    # Keep embedding benchmark gated and explicit; this call produces a skipped report unless gates are met.
    subprocess.run([sys.executable, str(TOOLS / "run_embedding_benchmark.py")], cwd=ROOT, check=False)
    print(json.dumps({"selected_experiment": experiment, "result": str(path), "lexicon_result": str(lexicon_path), "dataset_result": str(dataset_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
