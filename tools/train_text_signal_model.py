#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import read_jsonl  # noqa: E402
from signal_engine.evaluation_backbone import model_metrics  # noqa: E402


def training_gate(count: int) -> str:
    if count < 50:
        return "skip_training"
    if count <= 200:
        return "weak_baseline_allowed"
    return "full_baseline_allowed"


def write_model_card(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Text Signal Model Card",
        "",
        f"- gold_labels: `{payload['gold_labels']}`",
        f"- gate: `{payload['gate']}`",
        f"- training_ran: `{payload['training_ran']}`",
        f"- validity: `{payload['validity']}`",
        "",
        "```json",
        json.dumps(payload, indent=2),
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_error_analysis(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Text Signal Error Analysis", ""]
    if not rows:
        lines.append("Training did not run, so no error analysis is available.")
    else:
        lines.extend(["| id | y_true | y_pred | text |", "| --- | --- | --- | --- |"])
        for row in rows[:50]:
            text = str(row.get("text", "")).replace("|", "\\|")[:180]
            lines.append(f"| `{row.get('id')}` | `{row.get('y_true')}` | `{row.get('y_pred')}` | {text} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def train(rows: list[dict[str, Any]], *, model_out: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gate = training_gate(len(rows))
    summary: dict[str, Any] = {
        "gold_labels": len(rows),
        "gate": gate,
        "training_ran": False,
        "validity": "not_trained",
        "models": {},
        "model_path": None,
    }
    if gate == "skip_training":
        summary["validity"] = "invalid_for_training_less_than_50_gold_labels"
        return summary, []

    try:
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
        from sklearn.svm import LinearSVC
    except ImportError as exc:
        summary["validity"] = f"skipped_missing_dependency_{exc}"
        return summary, []

    texts = [str(row["text"]) for row in rows]
    labels = [str(row.get("signal_family") or row.get("label")) for row in rows]
    stratify = labels if min(labels.count(label) for label in set(labels)) >= 2 else None
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )
    candidates = {
        "tfidf_logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        "tfidf_linear_svc": LinearSVC(class_weight="balanced", random_state=42),
    }
    best_name = ""
    best_score = -1.0
    best_model: Any | None = None
    error_rows: list[dict[str, Any]] = []
    for name, estimator in candidates.items():
        model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)), ("model", estimator)])
        model.fit(train_texts, train_labels)
        predictions = [str(value) for value in model.predict(test_texts)]
        metrics = model_metrics(test_labels, predictions)
        summary["models"][name] = metrics
        if float(metrics["macro_f1"]) > best_score:
            best_name = name
            best_score = float(metrics["macro_f1"])
            best_model = model
            error_rows = [
                {"id": index, "y_true": truth, "y_pred": pred, "text": text}
                for index, (truth, pred, text) in enumerate(zip(test_labels, predictions, test_texts, strict=True))
                if truth != pred
            ]
    model_out.parent.mkdir(parents=True, exist_ok=True)
    if best_model is not None:
        joblib.dump(best_model, model_out)
    summary.update(
        {
            "training_ran": True,
            "validity": "weak_baseline" if gate == "weak_baseline_allowed" else "baseline_benchmark",
            "best_model": best_name,
            "best_macro_f1": round(best_score, 4),
            "model_path": str(model_out),
        }
    )
    return summary, error_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train guarded TF-IDF text signal baselines from gold labels.")
    parser.add_argument("--gold", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--model-out", default=str(ROOT / "models" / "text_signal" / "latest.joblib"))
    parser.add_argument("--card-out", default=str(ROOT / "docs" / "model_eval" / "text_signal_model_card.md"))
    parser.add_argument("--errors-out", default=str(ROOT / "docs" / "model_eval" / "text_signal_error_analysis.md"))
    args = parser.parse_args(argv)
    rows = read_jsonl(Path(args.gold))
    summary, errors = train(rows, model_out=Path(args.model_out))
    write_model_card(Path(args.card_out), summary)
    write_error_analysis(Path(args.errors_out), errors)
    print(json.dumps(summary, indent=2))
    return 0 if summary["training_ran"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
