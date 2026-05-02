from __future__ import annotations

from pathlib import Path
from typing import Any

from data_layer.io import write_json, write_jsonl
from signal_engine.evaluation_backbone import model_metrics
from signal_engine.signal_baseline import (
    HUMAN_REVIEWED_LABELS_RELATIVE_PATH,
    load_supervised_examples,
    training_readiness,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _mlflow_status() -> dict[str, Any]:
    try:
        import mlflow  # noqa: F401
    except ImportError:
        return {"available": False, "reason": "mlflow is not installed"}
    return {"available": True, "reason": None}


def _load_human_examples(root: Path) -> list[dict[str, Any]]:
    labels_path = root / HUMAN_REVIEWED_LABELS_RELATIVE_PATH
    if not labels_path.exists():
        return []
    return load_supervised_examples(labels_path)


def _train_sklearn_text_model(
    examples: list[dict[str, Any]],
    *,
    model_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    try:
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression, SGDClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
        from sklearn.svm import LinearSVC
    except ImportError as exc:
        return {"status": "skipped", "reason": f"sklearn/joblib unavailable: {exc}"}

    texts = [str(row["text"]) for row in examples]
    labels = [str(row["signal_family"]) for row in examples]
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )
    candidates = {
        "tfidf_logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        "tfidf_linear_svc": LinearSVC(class_weight="balanced", random_state=42),
        "tfidf_sgd": SGDClassifier(loss="modified_huber", class_weight="balanced", random_state=42),
    }
    results: dict[str, Any] = {}
    best_name = ""
    best_f1 = -1.0
    best_model: Any | None = None
    for name, estimator in candidates.items():
        model = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                ("model", estimator),
            ]
        )
        model.fit(train_texts, train_labels)
        predictions = [str(value) for value in model.predict(test_texts)]
        metrics = model_metrics(test_labels, predictions)
        results[name] = metrics
        if float(metrics["macro_f1"]) > best_f1:
            best_f1 = float(metrics["macro_f1"])
            best_name = name
            best_model = model

    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "text_signal_baseline.joblib"
    if best_model is not None:
        joblib.dump(best_model, model_path)
    write_json(output_dir / "text_training_metrics.json", {"models": results, "best_model": best_name})
    return {
        "status": "completed",
        "examples": len(examples),
        "best_model": best_name,
        "best_macro_f1": round(best_f1, 4),
        "model_path": str(model_path),
        "models": results,
    }


def _log_mlflow(summary: dict[str, Any], *, output_dir: Path) -> dict[str, Any]:
    status = _mlflow_status()
    if not status["available"]:
        write_json(output_dir / "mlflow_status.json", status)
        return status
    import mlflow

    mlflow.set_tracking_uri(str(output_dir / "mlruns"))
    mlflow.set_experiment("multimodal_signal_engine_v1")
    with mlflow.start_run(run_name="local_v1_training") as run:
        mlflow.log_param("schema_version", "multimodal_signal_engine.v1")
        mlflow.log_param("training_status", summary.get("status"))
        if summary.get("best_macro_f1") is not None:
            mlflow.log_metric("best_macro_f1", float(summary["best_macro_f1"]))
        metrics_path = output_dir / "text_training_metrics.json"
        if metrics_path.exists():
            mlflow.log_artifact(str(metrics_path))
        status = {"available": True, "run_id": run.info.run_id, "tracking_uri": str(output_dir / "mlruns")}
    write_json(output_dir / "mlflow_status.json", status)
    return status


def train_models(
    *,
    root: Path | None = None,
    output_dir: Path,
    model_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    repo_root = root or _repo_root()
    target_model_dir = model_dir or repo_root / "models" / "multimodal_engine"
    examples = _load_human_examples(repo_root)
    readiness = training_readiness(examples)
    if dry_run:
        summary = {"stage": "train", "status": "dry_run", "readiness": readiness, "mlflow": _mlflow_status()}
        return {"summary": summary}
    if not readiness["ready"]:
        summary = {
            "stage": "train",
            "status": "skipped",
            "reason": readiness["reason"],
            "readiness": readiness,
            "mlflow": _log_mlflow({"status": "skipped"}, output_dir=output_dir),
        }
        write_json(output_dir / "training_status.json", summary)
        return {"summary": summary}

    text_summary = _train_sklearn_text_model(examples, model_dir=target_model_dir, output_dir=output_dir)
    summary = {
        "stage": "train",
        "status": text_summary["status"],
        "readiness": readiness,
        "text_model": text_summary,
        "multimodal_models": {
            "logistic_regression": "candidate_registered",
            "random_forest": "candidate_registered",
            "shallow_pytorch_nn": "candidate_registered",
            "status": "not_trained_without_aligned_multimodal_gold_labels",
        },
    }
    summary["mlflow"] = _log_mlflow(text_summary, output_dir=output_dir)
    write_json(output_dir / "training_status.json", summary)
    return {"summary": summary}


def _calibration_error(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    total = 0.0
    for row in rows:
        total += abs(float(row.get("confidence") or 0.0) - float(row.get("correct") or 0.0))
    return round(total / len(rows), 4)


def evaluate_outputs(
    *,
    ensemble_rows: list[dict[str, Any]],
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    evaluation_rows = [
        {
            "segment_id": row.get("segment_id"),
            "y_true": row.get("final_signal"),
            "y_pred": row.get("final_signal"),
            "confidence": row.get("confidence"),
            "correct": 1,
            "domain": "unknown",
        }
        for row in ensemble_rows
    ]
    y_true = [str(row["y_true"]) for row in evaluation_rows]
    y_pred = [str(row["y_pred"]) for row in evaluation_rows]
    metrics = model_metrics(y_true, y_pred) if evaluation_rows else model_metrics([], [])
    report = {
        "stage": "evaluate",
        "status": "completed",
        "dry_run": dry_run,
        "metric_scope": "self-consistency smoke metrics; not a gold-label performance claim",
        "metrics": metrics,
        "calibration_error": _calibration_error(evaluation_rows),
        "false_positives": [],
        "false_negatives": [],
        "multimodal": {
            "uplift_vs_text_only": 0.0,
            "ablation_status": "requires aligned multimodal gold labels",
        },
        "cross_domain": {
            "earnings_to_support": "requires cross-domain gold labels",
            "support_to_sales": "requires cross-domain gold labels",
            "public_to_internal": "requires internal labeled set",
        },
    }
    if not dry_run:
        write_jsonl(output_dir / "evaluation_rows.jsonl", evaluation_rows)
        write_json(output_dir / "evaluation_results.json", report)
    return {"report": report, "rows": evaluation_rows}
