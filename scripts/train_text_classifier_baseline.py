#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"line {line_number}: expected JSON object")
        rows.append(row)
    return rows


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train an optional local sklearn text baseline from local JSONL only.")
    parser.add_argument("--labels", required=True, help="Local JSONL labels/training rows.")
    parser.add_argument("--text-field", default="evidence_text", help="Text field in each JSONL row.")
    parser.add_argument("--label-field", default="signal_type", help="Label field in each JSONL row.")
    parser.add_argument("--report-out", help="Optional JSON smoke report path.")
    parser.add_argument("--model-out", help="Optional pickle path. No model is written unless this is provided.")
    args = parser.parse_args(argv)

    labels_path = Path(args.labels)
    if not labels_path.exists():
        parser.error(f"--labels does not exist: {labels_path}")

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        message = (
            "scikit-learn is not installed. Optional local training scaffold skipped cleanly; "
            "no model was trained or validated."
        )
        print(message)
        if args.report_out:
            write_report(
                Path(args.report_out),
                {"status": "skipped", "reason": message, "validated": False, "error": str(exc)},
            )
        return 0

    rows = load_jsonl(labels_path)
    texts = [str(row.get(args.text_field, "")).strip() for row in rows]
    labels = [str(row.get(args.label_field, "")).strip() for row in rows]
    pairs = [(text, label) for text, label in zip(texts, labels) if text and label]
    if len(pairs) < 2 or len({label for _, label in pairs}) < 2:
        print("Need at least two non-empty rows across at least two classes for a local smoke train.")
        return 1

    train_texts = [text for text, _ in pairs]
    train_labels = [label for _, label in pairs]
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(lowercase=True)),
            ("classifier", LogisticRegression(max_iter=200, random_state=0)),
        ]
    )
    pipeline.fit(train_texts, train_labels)
    predictions = pipeline.predict(train_texts)
    training_smoke_accuracy = sum(
        int(predicted == expected) for predicted, expected in zip(predictions, train_labels)
    ) / len(train_labels)

    report = {
        "status": "trained_local_smoke_only",
        "row_count": len(pairs),
        "class_count": len(set(train_labels)),
        "training_smoke_accuracy": training_smoke_accuracy,
        "validated": False,
        "notes": "Local smoke metric only. This is not validated ML and does not prove production quality.",
        "model_written": bool(args.model_out),
    }
    if args.report_out:
        write_report(Path(args.report_out), report)
    if args.model_out:
        model_path = Path(args.model_out)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with model_path.open("wb") as handle:
            pickle.dump(pipeline, handle)

    print("Local sklearn smoke training complete. This is not validated ML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
