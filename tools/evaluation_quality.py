from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "data" / "gold" / "gold_labels.jsonl"
EVIDENCE_OBJECTS_PATH = ROOT / "data" / "evaluation" / "evidence_objects.jsonl"
LABELS = ("risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral")

TOKEN_RE = re.compile(r"[a-z0-9']+")
HEDGE_TERMS = {
    "if",
    "whether",
    "probably",
    "maybe",
    "might",
    "may",
    "could",
    "unclear",
    "confused",
    "concerned",
    "depends",
    "later",
    "once",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def row_label(row: dict[str, Any]) -> str:
    return str(row.get("signal_family") or row.get("label") or "").strip()


def row_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("evidence_text") or row.get("matched_text") or "").strip()


def metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    return value if isinstance(value, dict) else {}


def source_group(row: dict[str, Any]) -> str:
    source_file = str(row.get("source_file") or "")
    source_schema = str(row.get("source_schema") or "")
    case_id = str(row.get("case_id") or "")
    notes = str(metadata(row).get("notes") or row.get("notes") or "").lower()
    if "data/gold_guidance_calls" in source_file:
        return "imported_guidance"
    if source_schema == "human_reviewed_jsonl":
        fixture_markers = ("synthetic", "emotion benchmark", "fixture", "sample_")
        if case_id.startswith("sample_") or any(marker in notes for marker in fixture_markers):
            return "fixture"
        return "human_reviewed"
    if "fixture" in source_file or "sample" in case_id:
        return "fixture"
    return "unknown"


def provenance_quality(row: dict[str, Any]) -> str:
    group = source_group(row)
    if group == "human_reviewed":
        return "high"
    if group == "imported_guidance":
        return "medium"
    if group == "fixture":
        return "low"
    return "unknown"


def requires_manual_review(row: dict[str, Any]) -> bool:
    return source_group(row) in {"imported_guidance", "unknown"} or provenance_quality(row) != "high"


def annotated_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "source_group": source_group(row),
        "provenance_quality": provenance_quality(row),
        "requires_manual_review": requires_manual_review(row),
    }


def valid_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row_label(row) in LABELS and row_text(row)]


def label_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(row_label(row) for row in rows if row_label(row))


def precision_recall_f1(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    per_label: dict[str, dict[str, float | int]] = {}
    for label in LABELS:
        tp = sum(1 for truth, pred in zip(y_true, y_pred, strict=False) if truth == label and pred == label)
        fp = sum(1 for truth, pred in zip(y_true, y_pred, strict=False) if truth != label and pred == label)
        fn = sum(1 for truth, pred in zip(y_true, y_pred, strict=False) if truth == label and pred != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(1 for truth in y_true if truth == label),
        }
    return {
        "precision": round(sum(float(row["precision"]) for row in per_label.values()) / len(LABELS), 4),
        "recall": round(sum(float(row["recall"]) for row in per_label.values()) / len(LABELS), 4),
        "f1": round(sum(float(row["f1"]) for row in per_label.values()) / len(LABELS), 4),
        "per_label": per_label,
    }


def deterministic_predictions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from signal_engine.signal_baseline import predict_deterministic_signal_family

    predictions: list[dict[str, Any]] = []
    for row in valid_rows(rows):
        prediction = predict_deterministic_signal_family(row_text(row))
        predictions.append(
            {
                "id": row.get("id") or row.get("candidate_id") or "",
                "case_id": row.get("case_id") or "",
                "text": row_text(row),
                "gold_label": row_label(row),
                "deterministic_label": str(prediction.get("label") or ""),
                "deterministic_score": float(prediction.get("confidence") or 0.0),
                "evidence_terms": list(prediction.get("evidence_terms") or []),
                "score_by_label": prediction.get("score_by_label") or {},
                "suppressed_terms": list(prediction.get("suppressed_terms") or []),
                "source_group": source_group(row),
                "provenance_quality": provenance_quality(row),
                "requires_manual_review": requires_manual_review(row),
                "metadata": metadata(row),
                "source_file": row.get("source_file") or "",
            }
        )
    return predictions


def evaluate_predictions(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    y_true = [str(row["gold_label"]) for row in predictions]
    y_pred = [str(row["deterministic_label"]) for row in predictions]
    metrics = precision_recall_f1(y_true, y_pred)
    confusion = Counter((truth, pred) for truth, pred in zip(y_true, y_pred, strict=False))
    errors = [row for row in predictions if row["gold_label"] != row["deterministic_label"]]
    metrics["confusion"] = {f"{truth}->{pred}": count for (truth, pred), count in sorted(confusion.items())}
    metrics["error_count"] = len(errors)
    return metrics


def evaluate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return evaluate_predictions(deterministic_predictions(rows))


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text or "").lower())


def phrase_hits(text: str, phrases: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    lowered = str(text or "").lower()
    hits: list[str] = []
    for phrase in phrases:
        phrase_text = str(phrase).lower()
        if " " in phrase_text:
            if phrase_text in lowered:
                hits.append(phrase)
        elif re.search(rf"\b{re.escape(phrase_text)}\b", lowered):
            hits.append(phrase)
    return hits


def error_groups(predictions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        if row["gold_label"] != row["deterministic_label"]:
            grouped[f"{row['gold_label']}->{row['deterministic_label']}"].append(row)
    return dict(grouped)


def render_metric_summary(metrics: dict[str, Any]) -> list[str]:
    return [
        f"- precision: `{metrics.get('precision', 0.0)}`",
        f"- recall: `{metrics.get('recall', 0.0)}`",
        f"- F1: `{metrics.get('f1', 0.0)}`",
    ]
