from __future__ import annotations

from typing import Iterable


def _validate_lengths(left: Iterable[object], right: Iterable[object], *, left_name: str, right_name: str) -> tuple[list[object], list[object]]:
    left_list = list(left)
    right_list = list(right)
    if len(left_list) != len(right_list):
        raise ValueError(
            f"{left_name} and {right_name} must have the same length: "
            f"{len(left_list)} != {len(right_list)}."
        )
    return left_list, right_list


def confusion_matrix_counts(
    y_true: Iterable[str],
    y_pred: Iterable[str],
    labels: Iterable[str],
) -> dict[str, dict[str, int]]:
    """Return deterministic confusion counts keyed by true label then predicted label."""

    true_values, pred_values = _validate_lengths(y_true, y_pred, left_name="y_true", right_name="y_pred")
    label_list = list(labels)
    counts = {
        true_label: {pred_label: 0 for pred_label in label_list}
        for true_label in label_list
    }
    known_labels = set(label_list)

    for true_label, pred_label in zip(true_values, pred_values):
        if true_label not in known_labels:
            raise ValueError(f"Unknown true label '{true_label}'. Expected one of {label_list}.")
        if pred_label not in known_labels:
            raise ValueError(f"Unknown predicted label '{pred_label}'. Expected one of {label_list}.")
        counts[true_label][pred_label] += 1
    return counts


def precision_recall_f1(
    y_true: Iterable[str],
    y_pred: Iterable[str],
    labels: Iterable[str],
) -> dict[str, dict[str, float | int]]:
    """Compute per-label precision, recall, and F1 without sklearn."""

    label_list = list(labels)
    matrix = confusion_matrix_counts(y_true, y_pred, label_list)
    metrics: dict[str, dict[str, float | int]] = {}
    for label in label_list:
        tp = matrix[label][label]
        fp = sum(matrix[other_label][label] for other_label in label_list if other_label != label)
        fn = sum(matrix[label][other_label] for other_label in label_list if other_label != label)
        support = sum(matrix[label].values())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        metrics[label] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return metrics


def macro_f1(y_true: Iterable[str], y_pred: Iterable[str], labels: Iterable[str]) -> float:
    label_list = list(labels)
    if not label_list:
        raise ValueError("labels must not be empty.")
    metrics = precision_recall_f1(y_true, y_pred, label_list)
    return sum(float(metrics[label]["f1"]) for label in label_list) / len(label_list)


def simple_calibration_bins(
    y_true_binary: Iterable[int | bool],
    y_score: Iterable[float],
    n_bins: int = 10,
) -> list[dict[str, float | int]]:
    """Group binary outcomes into equally spaced score bins on [0, 1]."""

    if n_bins <= 0:
        raise ValueError("n_bins must be positive.")
    true_values, score_values = _validate_lengths(
        y_true_binary,
        y_score,
        left_name="y_true_binary",
        right_name="y_score",
    )

    bins: list[list[tuple[int, float]]] = [[] for _ in range(n_bins)]
    for raw_true, raw_score in zip(true_values, score_values):
        score = float(raw_score)
        if score < 0.0 or score > 1.0:
            raise ValueError(f"Scores must be in [0, 1]. Received {score}.")
        truth = 1 if bool(raw_true) else 0
        if score == 1.0:
            index = n_bins - 1
        else:
            index = int(score * n_bins)
        bins[index].append((truth, score))

    bin_width = 1.0 / n_bins
    payload: list[dict[str, float | int]] = []
    for index, items in enumerate(bins):
        start = index * bin_width
        end = start + bin_width
        count = len(items)
        avg_score = sum(score for _, score in items) / count if count else 0.0
        positive_rate = sum(truth for truth, _ in items) / count if count else 0.0
        payload.append(
            {
                "bin_index": index,
                "bin_start": start,
                "bin_end": end,
                "count": count,
                "avg_score": avg_score,
                "positive_rate": positive_rate,
            }
        )
    return payload


def inter_rater_agreement_percent(
    rater_a: Iterable[str],
    rater_b: Iterable[str],
) -> float:
    """Return simple percent agreement on a 0-100 scale."""

    left_values, right_values = _validate_lengths(
        rater_a,
        rater_b,
        left_name="rater_a",
        right_name="rater_b",
    )
    if not left_values:
        raise ValueError("At least one rating pair is required.")
    agreements = sum(1 for left, right in zip(left_values, right_values) if left == right)
    return (agreements / len(left_values)) * 100.0
