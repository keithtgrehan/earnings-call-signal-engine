from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "data" / "gold" / "gold_labels.jsonl"
READINESS_PATH = ROOT / "reports" / "evaluation_readiness.json"
LABEL_COVERAGE_PATH = ROOT / "reports" / "label_coverage.csv"
NEXT_ACTIONS_PATH = ROOT / "reports" / "next_best_actions.md"
BENCHMARK_REPORT_PATH = ROOT / "docs" / "evaluation" / "first_50_benchmark_report.md"
NLP_REGISTRY_PATH = ROOT / "data" / "nlp_assets" / "asset_registry.json"

LABELS = ("risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral")


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def row_label(row: dict[str, Any]) -> str:
    return str(row.get("signal_family") or row.get("label") or "").strip()


def row_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("evidence_text") or row.get("matched_text") or "").strip()


def label_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(label for row in rows if (label := row_label(row)))


def valid_gold_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row_label(row) in LABELS and row_text(row)]


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
    macro_precision = sum(float(row["precision"]) for row in per_label.values()) / len(LABELS)
    macro_recall = sum(float(row["recall"]) for row in per_label.values()) / len(LABELS)
    macro_f1 = sum(float(row["f1"]) for row in per_label.values()) / len(LABELS)
    return {
        "precision": round(macro_precision, 4),
        "recall": round(macro_recall, 4),
        "f1": round(macro_f1, 4),
        "per_label": per_label,
    }


def load_nlp_registry() -> list[dict[str, Any]]:
    if not NLP_REGISTRY_PATH.exists():
        return []
    return json.loads(NLP_REGISTRY_PATH.read_text(encoding="utf-8"))


def phase_for(gold_count: int, readiness: dict[str, Any] | None = None) -> str:
    if gold_count < 50:
        return "<50 labels"
    if gold_count < 100:
        return ">=50 labels (ML allowed)"
    if readiness and readiness.get("metrics_computed"):
        return "advanced benchmarking"
    return "retrieval-ready"


def gate_state(
    *,
    gold_count: int,
    retrieval_experiment_mode: bool = False,
    embedding_baseline_exists: bool = False,
    evaluation_exists: bool = False,
) -> dict[str, bool]:
    ml_allowed = gold_count >= 50
    embeddings_allowed = gold_count >= 100 or retrieval_experiment_mode
    return {
        "deterministic_tools": True,
        "local_ml": ml_allowed,
        "embeddings": embeddings_allowed,
        "datasets": False,
        "rerankers": embeddings_allowed and embedding_baseline_exists,
        "long_context": evaluation_exists,
    }


def write_label_coverage(rows: list[dict[str, Any]], path: Path = LABEL_COVERAGE_PATH) -> None:
    counts = label_counts(rows)
    total = len(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "gold_count", "share", "status"])
        writer.writeheader()
        for label in LABELS:
            count = counts.get(label, 0)
            writer.writerow(
                {
                    "label": label,
                    "gold_count": count,
                    "share": round(count / total, 4) if total else 0.0,
                    "status": "present" if count else "missing",
                }
            )


def write_next_best_actions(
    *,
    gold_count: int,
    readiness: dict[str, Any],
    registry: list[dict[str, Any]],
    path: Path = NEXT_ACTIONS_PATH,
) -> None:
    gates = gate_state(
        gold_count=gold_count,
        retrieval_experiment_mode=False,
        embedding_baseline_exists=(ROOT / "reports" / "retrieval_eval.md").exists(),
        evaluation_exists=bool(readiness.get("metrics_computed")),
    )
    allowed = [name for name, allowed_now in gates.items() if allowed_now]
    blocked = {
        "local ML": "requires >=50 gold labels",
        "embeddings": "requires >=100 gold labels or explicit retrieval experiment mode",
        "external datasets": "requires local verified dataset or safe_local flag",
        "rerankers": "requires embedding baseline first",
        "long-context": "requires completed evaluation first",
    }
    experiments = [
        ("deterministic_baseline", "Run canonical deterministic baseline/status loop.", gates["deterministic_tools"]),
        ("lexicon_comparison", "Compare Loughran-McDonald-style lexicon coverage if lexicon is local.", True),
        ("local_ml_baseline", "TF-IDF + Logistic Regression benchmark.", gates["local_ml"]),
        ("embedding_benchmark", "Local sentence-transformers evidence-span retrieval.", gates["embeddings"]),
        ("dataset_comparison", "Compare locally present dataset label distribution.", gates["datasets"]),
    ]
    high_assets = [entry for entry in registry if entry.get("priority") == "high"][:10]
    lines = [
        "# Next Best Actions",
        "",
        f"- gold_label_count: `{gold_count}`",
        f"- current_phase: `{phase_for(gold_count, readiness)}`",
        "",
        "## Allowed Now",
        "",
        *[f"- {item}" for item in allowed],
        "",
        "## Blocked",
        "",
    ]
    for item, reason in blocked.items():
        if item == "local ML" and gates["local_ml"]:
            continue
        if item == "embeddings" and gates["embeddings"]:
            continue
        if item == "rerankers" and gates["rerankers"]:
            continue
        if item == "long-context" and gates["long_context"]:
            continue
        lines.append(f"- {item}: {reason}")
    lines.extend(["", "## Top 5 Recommended Experiments", ""])
    for name, description, is_allowed in experiments:
        status = "allowed" if is_allowed else "blocked"
        lines.append(f"- `{name}` ({status}): {description}")
    lines.extend(["", "## High-Priority Registry Inputs", ""])
    for asset in high_assets:
        lines.append(f"- `{asset['id']}`: {asset['name']} ({asset['download_status']})")
    lines.extend(
        [
            "",
            "## Enforcement Notes",
            "",
            "- Deterministic outputs remain canonical truth.",
            "- Embeddings and datasets are benchmark layers only.",
            "- No silent dataset downloads or paid APIs are allowed.",
            "- Weak labels are never auto-promoted.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
