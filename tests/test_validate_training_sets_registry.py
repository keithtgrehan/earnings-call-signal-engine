from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_training_sets_registry.py"
EXPECTED_DATASET_IDS = {
    "30_call_manual_gold_corpus",
    "100_150_call_benchmark_corpus",
    "gold_labels_example",
    "tiny_signal_predictions_fixture",
    "financial_phrasebank_candidate",
    "fiqa_sentiment_candidate",
    "sec_8k_guidance_candidate",
    "sec_edgar_filings_metadata_candidate",
    "kaggle_earnings_call_candidate",
    "motley_fool_manual_transcripts_candidate",
    "seeking_alpha_manual_transcripts_candidate",
    "maec_multimodal_later_candidate",
    "synthetic_support_examples",
    "synthetic_sales_examples",
    "synthetic_account_management_examples",
    "flame_finance_eval_candidate",
    "open_finllm_candidate",
    "finos_earnings_call_transcript_candidate",
    "sec_edgar_metadata_candidate",
    "motley_fool_candidate",
    "seeking_alpha_candidate",
    "kaggle_earnings_calls_candidate",
    "maec_multimodal_candidate",
    "hubspot_export_candidate",
    "salesforce_export_candidate",
    "gong_export_candidate",
    "chorus_export_candidate",
    "intercom_export_candidate",
    "zendesk_export_candidate",
    "freshdesk_export_candidate",
    "gainsight_export_candidate",
    "churn_labels_candidate",
    "escalation_labels_candidate",
    "objection_labels_candidate",
    "goemotions_candidate",
    "dair_ai_candidate",
    "daily_dialog_candidate",
    "meld_candidate",
    "emotionlines_candidate",
    "empathetic_dialogues_candidate",
}


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_valid_training_set_csv_passes() -> None:
    result = run_validator("--path", "data/training_sets_registry.example.csv")

    assert result.returncode == 0, result.stdout + result.stderr
    with (ROOT / "data/training_sets_registry.example.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["dataset_id"] for row in rows} == EXPECTED_DATASET_IDS


def test_valid_training_set_json_passes() -> None:
    result = run_validator("--path", "data/training_sets_registry.example.json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads((ROOT / "data/training_sets_registry.example.json").read_text(encoding="utf-8"))
    assert {row["dataset_id"] for row in payload["datasets"]} == EXPECTED_DATASET_IDS


def test_invalid_training_set_boolean_fails(tmp_path: Path) -> None:
    source = ROOT / "data" / "training_sets_registry.example.csv"
    rows = list(csv.DictReader(source.open(newline="", encoding="utf-8")))
    rows[0]["license_check_required"] = "maybe"
    path = tmp_path / "bad_bool.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "invalid boolean license_check_required" in result.stdout


def test_duplicate_training_set_id_fails(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "data/training_sets_registry.example.json").read_text(encoding="utf-8"))
    payload["datasets"][1]["dataset_id"] = payload["datasets"][0]["dataset_id"]
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "duplicate dataset_id" in result.stdout
