from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .emotion_benchmark import confusion_matrix_counts, macro_f1, precision_recall_f1
from .signal_baseline import SIGNAL_FAMILY_LABELS


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def accuracy_score(y_true: list[str], y_pred: list[str]) -> float:
    if not y_true:
        return 0.0
    matches = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if truth == pred)
    return matches / len(y_true)


def weighted_f1_score(y_true: list[str], y_pred: list[str]) -> float:
    per_label = precision_recall_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS)
    total_support = sum(int(row["support"]) for row in per_label.values())
    if total_support == 0:
        return 0.0
    weighted_total = sum(float(row["f1"]) * int(row["support"]) for row in per_label.values())
    return weighted_total / total_support


def model_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": macro_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS),
        "weighted_f1": weighted_f1_score(y_true, y_pred),
        "per_label": precision_recall_f1(y_true, y_pred, SIGNAL_FAMILY_LABELS),
        "confusion_matrix": confusion_matrix_counts(y_true, y_pred, SIGNAL_FAMILY_LABELS),
    }


def text_length_bucket(text: str) -> str:
    token_count = len(text.split())
    if token_count < 12:
        return "short"
    if token_count < 25:
        return "medium"
    return "long"


def confidence_bucket(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value < 0.40:
        return "low"
    if value < 0.60:
        return "medium"
    return "high"


def top_two_labels(score_map: dict[str, float]) -> list[str]:
    ordered = sorted(score_map.items(), key=lambda item: item[1], reverse=True)
    return [label for label, _ in ordered[:2]]


def top_two_margin(score_map: dict[str, float]) -> float | None:
    ordered = sorted(score_map.values(), reverse=True)
    if len(ordered) < 2:
        return None
    return float(ordered[0] - ordered[1])

