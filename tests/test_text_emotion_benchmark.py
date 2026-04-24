from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from signal_engine.dataset_ingestion import load_jsonl
from signal_engine.text_emotion_baseline import EMOTION_LABELS, batch_classify, classify_text_emotion

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "signal_engine_2_0" / "emotion_benchmark" / "sample_emotion_cases.jsonl"
MANIFEST_PATH = ROOT / "data" / "signal_engine_2_0" / "dataset_manifests" / "emotion_benchmark_manifest.json"
SCRIPT_PATH = ROOT / "scripts" / "run_text_emotion_benchmark.py"


def test_fixture_loads_and_classifier_returns_valid_labels() -> None:
    records = load_jsonl(FIXTURE_PATH)
    prediction = classify_text_emotion(records[0]["text"], allowed_labels=records[0]["allowed_labels"])
    assert prediction["label"] in EMOTION_LABELS
    assert prediction["evidence_terms"]
    assert prediction["method"] == "deterministic_keyword_baseline"


def test_batch_classify_returns_rows_for_fixture_records() -> None:
    records = load_jsonl(FIXTURE_PATH)[:3]
    predictions = batch_classify(records)
    assert len(predictions) == 3
    assert all(item["label"] in EMOTION_LABELS for item in predictions)


def test_benchmark_runner_writes_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "benchmark_outputs"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(FIXTURE_PATH),
            "--manifest",
            str(MANIFEST_PATH),
            "--mode",
            "deterministic",
            "--redact-pii",
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        check=True,
    )

    predictions_path = out_dir / "predictions.jsonl"
    metrics_path = out_dir / "metrics.json"
    report_path = out_dir / "report.md"
    redactions_path = out_dir / "redactions.json"

    assert predictions_path.exists()
    assert metrics_path.exists()
    assert report_path.exists()
    assert redactions_path.exists()

    prediction_rows = load_jsonl(predictions_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    redactions = json.loads(redactions_path.read_text(encoding="utf-8"))

    assert len(prediction_rows) == 14
    assert metrics["macro_f1"] >= 0.0
    assert metrics["pii_redaction"]["enabled"] is True
    assert "Text Emotion Benchmark Report" in report
    assert redactions["summary"]["total_redactions"] >= 1
