#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine import emotion_benchmark
from signal_engine.adapters import text_emotion as text_emotion_adapter
from signal_engine.dataset_ingestion import (
    build_dataset_card_summary,
    load_jsonl,
    validate_dataset_manifest,
    validate_emotion_fixture_record,
)
from signal_engine.privacy import redact_pii_text, summarize_redactions
from signal_engine.text_emotion_baseline import (
    EMOTION_LABELS,
    batch_classify,
    classify_text_emotion,
)


def _load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    manifest["_manifest_path"] = str(path.resolve())
    return validate_dataset_manifest(manifest)


def _map_transformer_label(
    raw_label: str,
    text: str,
    allowed_labels: list[str],
) -> dict[str, Any]:
    normalized = raw_label.strip().lower()
    if normalized.startswith("label_"):
        normalized = normalized.split("_", 1)[1]

    mapping = {
        "anger": "anger",
        "annoyance": "frustration",
        "frustration": "frustration",
        "disappointment": "concern",
        "disapproval": "concern",
        "fear": "concern",
        "nervousness": "concern",
        "worry": "concern",
        "concern": "concern",
        "confusion": "confusion",
        "curiosity": "confusion",
        "joy": "satisfaction",
        "gratitude": "satisfaction",
        "approval": "satisfaction",
        "relief": "satisfaction",
        "optimism": "satisfaction",
        "satisfaction": "satisfaction",
        "neutral": "neutral",
        "urgency": "urgency",
        "realization": "urgency",
        "desire": "urgency",
        "sadness": "concern",
        "remorse": "concern",
        "surprise": "urgency",
    }
    mapped_label = mapping.get(normalized)
    if mapped_label and mapped_label in allowed_labels:
        return {
            "label": mapped_label,
            "method": "transformers_local_pipeline",
            "evidence_terms": [raw_label],
        }

    fallback = classify_text_emotion(text, allowed_labels=allowed_labels)
    fallback["method"] = "transformers_label_unmapped_fallback"
    fallback["evidence_terms"] = [raw_label, *fallback["evidence_terms"]]
    return fallback


def _build_transformers_classifier(model_id: str):
    text_emotion_adapter.require_available()
    try:
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            pipeline,
        )
    except ImportError as exc:  # pragma: no cover - guarded by adapter
        raise ImportError(text_emotion_adapter.dependency_hint()) from exc

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_id,
            local_files_only=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Model artifacts for '{model_id}' are not available locally. "
            "This benchmark runner will not download model files."
        ) from exc

    return pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        top_k=None,
    )


def _run_transformers_mode(
    records: list[dict[str, Any]],
    *,
    model_id: str,
) -> list[dict[str, Any]]:
    classifier = _build_transformers_classifier(model_id)
    predictions: list[dict[str, Any]] = []
    for record in records:
        outputs = classifier(record["text"], truncation=True)
        if outputs and isinstance(outputs[0], list):
            outputs = outputs[0]
        best = max(outputs, key=lambda item: float(item.get("score", 0.0)))
        mapped = _map_transformer_label(
            str(best.get("label", "")),
            record["text"],
            record["allowed_labels"],
        )
        predictions.append(
            {
                "case_id": record["case_id"],
                "domain": record["domain"],
                "text": record["text"],
                "gold_label": record["gold_label"],
                "allowed_labels": record["allowed_labels"],
                "label": mapped["label"],
                "confidence": round(float(best.get("score", 0.0)), 4),
                "evidence_terms": mapped["evidence_terms"],
                "method": mapped["method"],
            }
        )
    return predictions


def _render_confusion_table(
    confusion_matrix: dict[str, dict[str, int]],
    labels: list[str],
) -> str:
    header = "| true \\ pred | " + " | ".join(labels) + " |"
    divider = "| --- | " + " | ".join("---" for _ in labels) + " |"
    rows = [
        "| "
        + label
        + " | "
        + " | ".join(str(confusion_matrix[label][predicted]) for predicted in labels)
        + " |"
        for label in labels
    ]
    return "\n".join([header, divider, *rows])


def _render_label_distribution_table(support_counts: dict[str, int], labels: list[str]) -> str:
    header = "| label | support |"
    divider = "| --- | --- |"
    rows = [f"| {label} | {support_counts.get(label, 0)} |" for label in labels]
    return "\n".join([header, divider, *rows])


def _render_manifest_file_table(files: list[dict[str, Any]]) -> str:
    header = "| path | size_bytes | record_count |"
    divider = "| --- | --- | --- |"
    rows = [
        f"| `{item['path']}` | {item['size_bytes']} | {item['record_count']} |"
        for item in files
    ]
    return "\n".join([header, divider, *rows])


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def run_benchmark(
    *,
    input_path: Path,
    manifest_path: Path,
    mode: str,
    out_dir: Path,
    redact_pii: bool,
    model_id: str | None,
) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    summary = build_dataset_card_summary(manifest)

    resolved_input = input_path.resolve()
    if str(resolved_input) not in manifest["resolved_file_paths"]:
        raise ValueError(
            f"Input file {resolved_input} is not listed in manifest {manifest_path}."
        )

    records = [
        validate_emotion_fixture_record(record)
        for record in load_jsonl(resolved_input)
    ]

    benchmark_records: list[dict[str, Any]] = []
    redaction_records: list[dict[str, Any]] = []
    for record in records:
        processed = dict(record)
        if redact_pii:
            redacted = redact_pii_text(processed["text"])
            processed["text"] = redacted["text"]
            case_redactions = []
            for item in redacted["redactions"]:
                redaction_record = {"case_id": processed["case_id"], **item}
                redaction_records.append(redaction_record)
                case_redactions.append(redaction_record)
            processed["redaction_count"] = len(case_redactions)
        else:
            processed["redaction_count"] = 0
        benchmark_records.append(processed)

    if mode == "deterministic":
        predictions = batch_classify(benchmark_records)
        model_or_baseline = "deterministic_keyword_baseline"
    elif mode == "transformers":
        if not model_id:
            raise ValueError("--model-id is required when --mode transformers is used.")
        predictions = _run_transformers_mode(benchmark_records, model_id=model_id)
        model_or_baseline = model_id
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    prediction_rows: list[dict[str, Any]] = []
    y_true: list[str] = []
    y_pred: list[str] = []
    for record, prediction in zip(benchmark_records, predictions, strict=True):
        y_true.append(record["gold_label"])
        y_pred.append(prediction["label"])
        prediction_rows.append(
            {
                "case_id": record["case_id"],
                "domain": record["domain"],
                "text": record["text"],
                "gold_label": record["gold_label"],
                "allowed_labels": record["allowed_labels"],
                "predicted_label": prediction["label"],
                "confidence": prediction["confidence"],
                "evidence_terms": prediction["evidence_terms"],
                "method": prediction["method"],
                "redaction_count": record["redaction_count"],
            }
        )

    labels = list(manifest["labels"])
    confusion = emotion_benchmark.confusion_matrix_counts(y_true, y_pred, labels)
    per_label = emotion_benchmark.precision_recall_f1(y_true, y_pred, labels)
    macro_f1 = emotion_benchmark.macro_f1(y_true, y_pred, labels)
    support_counts = dict(Counter(y_true))
    redaction_summary = summarize_redactions(redaction_records)

    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "predictions.jsonl"
    metrics_path = out_dir / "metrics.json"
    report_path = out_dir / "report.md"
    redactions_path = out_dir / "redactions.json"

    _write_jsonl(predictions_path, prediction_rows)
    metrics_payload = {
        "mode": mode,
        "model_or_baseline": model_or_baseline,
        "dataset_manifest": summary,
        "label_set": labels,
        "macro_f1": round(macro_f1, 4),
        "per_label": per_label,
        "confusion_matrix_counts": confusion,
        "label_support_counts": support_counts,
        "pii_redaction": {
            "enabled": redact_pii,
            "summary": redaction_summary,
        },
    }
    metrics_path.write_text(
        json.dumps(metrics_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if redact_pii:
        redactions_payload = {
            "enabled": True,
            "summary": redaction_summary,
            "records": redaction_records,
        }
        redactions_path.write_text(
            json.dumps(redactions_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    per_label_rows = "\n".join(
        "| "
        + label
        + " | "
        + f"{per_label[label]['precision']:.4f}"
        + " | "
        + f"{per_label[label]['recall']:.4f}"
        + " | "
        + f"{per_label[label]['f1']:.4f}"
        + " | "
        + str(per_label[label]["support"])
        + " |"
        for label in labels
    )
    report = f"""# Text Emotion Benchmark Report

## Mode

- mode: `{mode}`
- model/baseline used: `{model_or_baseline}`

## Dataset Manifest

- dataset_id: `{summary['dataset_id']}`
- name: {summary['name']}
- source_type: `{summary['source_type']}`
- record_count: {summary['record_count']}
- pii_status: {summary['pii_status']}

{_render_manifest_file_table(summary['files'])}

## Label Set

`{", ".join(labels)}`

## Label Distribution

{_render_label_distribution_table(support_counts, labels)}

## Macro F1

`{macro_f1:.4f}`

## Per-Label Precision/Recall/F1

| label | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
{per_label_rows}

## Confusion Summary

{_render_confusion_table(confusion, labels)}

## PII/Redaction Status

- enabled: `{str(redact_pii).lower()}`
- total redactions: {redaction_summary['total_redactions']}
- by_type: `{json.dumps(redaction_summary['by_type'], sort_keys=True)}`
- unique_hashes: {redaction_summary['unique_hashes']}

## Limitations

- tiny handcrafted fixture
- not production proof
- not psychological diagnosis
- not truth detection
- harness validation only

## Next Steps

- expand fixtures only after rubric review and privacy sign-off
- compare deterministic results against optional local transformer baselines
- keep transcript-first deterministic analysis canonical while audio/video remain adapter-ready roadmap
"""
    report_path.write_text(report + "\n", encoding="utf-8")

    return {
        "predictions_path": str(predictions_path),
        "metrics_path": str(metrics_path),
        "report_path": str(report_path),
        "redactions_path": str(redactions_path) if redact_pii else None,
        "metrics": metrics_payload,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Signal Engine 2.0 text emotion benchmark harness."
    )
    parser.add_argument("--input", required=True, help="Path to the JSONL fixture file.")
    parser.add_argument("--manifest", required=True, help="Path to the dataset manifest JSON.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=("deterministic", "transformers"),
        help="Benchmark mode to run.",
    )
    parser.add_argument("--model-id", help="Optional local model id for transformers mode.")
    parser.add_argument("--out-dir", required=True, help="Directory for benchmark outputs.")
    parser.add_argument(
        "--redact-pii",
        action="store_true",
        help="Apply deterministic redaction before classification and reporting.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_benchmark(
            input_path=Path(args.input),
            manifest_path=Path(args.manifest),
            mode=args.mode,
            out_dir=Path(args.out_dir),
            redact_pii=args.redact_pii,
            model_id=args.model_id,
        )
    except (FileNotFoundError, ImportError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "mode": args.mode,
                "out_dir": str(Path(args.out_dir).resolve()),
                "macro_f1": result["metrics"]["macro_f1"],
                "redactions_enabled": args.redact_pii,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
