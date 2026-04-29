from __future__ import annotations

import json
from pathlib import Path

import pytest

from signal_engine.dataset_ingestion import (
    build_dataset_card_summary,
    load_jsonl,
    validate_dataset_manifest,
    validate_emotion_fixture_record,
)
from signal_engine.text_emotion_baseline import EMOTION_LABELS

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "signal_engine_2_0" / "emotion_benchmark" / "sample_emotion_cases.jsonl"
MANIFEST_PATH = ROOT / "data" / "signal_engine_2_0" / "dataset_manifests" / "emotion_benchmark_manifest.json"


def _load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["_manifest_path"] = str(MANIFEST_PATH)
    return manifest


def test_load_jsonl_reads_fixture_records() -> None:
    records = load_jsonl(FIXTURE_PATH)
    assert len(records) == 14
    assert records[0]["case_id"] == "support_anger_001"


def test_validate_emotion_fixture_record_accepts_valid_fixture() -> None:
    record = load_jsonl(FIXTURE_PATH)[0]
    validated = validate_emotion_fixture_record(record)
    assert validated["gold_label"] in EMOTION_LABELS
    assert validated["gold_label"] in validated["allowed_labels"]


def test_validate_emotion_fixture_record_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="gold_label"):
        validate_emotion_fixture_record(
            {
                "case_id": "bad",
                "domain": "support",
                "text": "hello",
                "gold_label": "panic",
                "allowed_labels": ["anger", "neutral"],
            }
        )


def test_validate_dataset_manifest_and_build_summary() -> None:
    manifest = validate_dataset_manifest(_load_manifest())
    assert manifest["dataset_id"] == "signal_engine_2_0_emotion_benchmark_fixture"
    assert len(manifest["resolved_file_paths"]) == 1

    summary = build_dataset_card_summary(_load_manifest())
    assert summary["record_count"] == 14
    assert summary["labels"] == list(EMOTION_LABELS)


def test_validate_dataset_manifest_rejects_missing_files() -> None:
    manifest = _load_manifest()
    manifest["file_paths"] = ["missing.jsonl"]
    with pytest.raises(ValueError, match="does not exist"):
        validate_dataset_manifest(manifest)
