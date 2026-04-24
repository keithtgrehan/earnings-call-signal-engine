from __future__ import annotations

import importlib

import pytest

import signal_engine.adapters as adapter_utils
from signal_engine.dataset_registry import list_dataset_registry
from signal_engine.emotion_benchmark import (
    confusion_matrix_counts,
    inter_rater_agreement_percent,
    macro_f1,
    precision_recall_f1,
    simple_calibration_bins,
)
from signal_engine.model_registry import list_model_registry


ADAPTER_MODULE_NAMES = (
    "signal_engine.adapters.text_emotion",
    "signal_engine.adapters.asr",
    "signal_engine.adapters.diarization",
    "signal_engine.adapters.audio_features",
    "signal_engine.adapters.video_features",
    "signal_engine.adapters.privacy",
    "signal_engine.adapters.retrieval",
)


def test_model_registry_imports_without_loading_optional_runtime() -> None:
    entries = list_model_registry()
    assert entries
    required_fields = {
        "id",
        "modality",
        "task",
        "required_optional_group",
        "default_enabled",
        "notes",
        "risks",
    }
    for entry in entries:
        assert required_fields.issubset(entry)
        assert entry["default_enabled"] is False


def test_dataset_registry_imports_without_downloads() -> None:
    entries = list_dataset_registry()
    assert entries
    required_fields = {
        "id",
        "modality",
        "task",
        "access",
        "expected_use",
        "why_relevant",
        "risks",
        "not_committed_reason",
    }
    allowed_access_values = {"public", "gated", "license_required", "benchmark_reference"}
    for entry in entries:
        assert required_fields.issubset(entry)
        assert entry["access"] in allowed_access_values


def test_benchmark_metrics_match_expected_tiny_example() -> None:
    labels = ["joy", "sad", "anger"]
    y_true = ["joy", "sad", "joy", "anger"]
    y_pred = ["joy", "joy", "joy", "anger"]

    matrix = confusion_matrix_counts(y_true, y_pred, labels)
    assert matrix == {
        "joy": {"joy": 2, "sad": 0, "anger": 0},
        "sad": {"joy": 1, "sad": 0, "anger": 0},
        "anger": {"joy": 0, "sad": 0, "anger": 1},
    }

    metrics = precision_recall_f1(y_true, y_pred, labels)
    assert metrics["joy"]["tp"] == 2
    assert metrics["joy"]["precision"] == pytest.approx(2 / 3)
    assert metrics["joy"]["recall"] == pytest.approx(1.0)
    assert metrics["joy"]["f1"] == pytest.approx(0.8)
    assert metrics["sad"]["support"] == 1
    assert metrics["sad"]["precision"] == pytest.approx(0.0)
    assert metrics["sad"]["recall"] == pytest.approx(0.0)
    assert metrics["sad"]["f1"] == pytest.approx(0.0)
    assert metrics["anger"]["f1"] == pytest.approx(1.0)
    assert macro_f1(y_true, y_pred, labels) == pytest.approx(0.6)


def test_calibration_bins_and_inter_rater_agreement_are_deterministic() -> None:
    calibration = simple_calibration_bins(
        y_true_binary=[1, 0, 1, 0],
        y_score=[0.9, 0.2, 0.6, 0.4],
        n_bins=2,
    )
    assert calibration == [
        {
            "bin_index": 0,
            "bin_start": 0.0,
            "bin_end": 0.5,
            "count": 2,
            "avg_score": pytest.approx(0.3),
            "positive_rate": pytest.approx(0.0),
        },
        {
            "bin_index": 1,
            "bin_start": 0.5,
            "bin_end": 1.0,
            "count": 2,
            "avg_score": pytest.approx(0.75),
            "positive_rate": pytest.approx(1.0),
        },
    ]
    assert inter_rater_agreement_percent(
        ["calm", "frustrated", "confident"],
        ["calm", "uncertain", "confident"],
    ) == pytest.approx(66.6666666667)


def test_adapter_modules_import_safely() -> None:
    for module_name in ADAPTER_MODULE_NAMES:
        module = importlib.import_module(module_name)
        assert hasattr(module, "is_available")
        assert hasattr(module, "require_available")
        assert isinstance(module.is_available(), bool)


def test_missing_optional_dependencies_raise_clear_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    text_emotion = importlib.import_module("signal_engine.adapters.text_emotion")
    privacy = importlib.import_module("signal_engine.adapters.privacy")

    monkeypatch.setattr(adapter_utils, "module_available", lambda module_name: False)

    with pytest.raises(ImportError) as text_exc:
        text_emotion.require_available()
    text_message = str(text_exc.value)
    assert "pip install .[text-emotion]" in text_message
    assert "transformers" in text_message
    assert "datasets" in text_message

    with pytest.raises(ImportError) as privacy_exc:
        privacy.require_available()
    privacy_message = str(privacy_exc.value)
    assert "pip install .[privacy]" in privacy_message
    assert "presidio_analyzer" in privacy_message
