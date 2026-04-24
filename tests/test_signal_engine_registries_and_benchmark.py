from __future__ import annotations

import importlib

import pytest

import signal_engine.adapters as adapter_helpers
from signal_engine.dataset_registry import DATASET_REGISTRY, list_dataset_registry
from signal_engine.emotion_benchmark import (
    confusion_matrix_counts,
    inter_rater_agreement_percent,
    macro_f1,
    precision_recall_f1,
    simple_calibration_bins,
)
from signal_engine.model_registry import MODEL_REGISTRY, list_model_registry


MODEL_FIELDS = {
    "id",
    "modality",
    "task",
    "required_optional_group",
    "default_enabled",
    "notes",
    "risks",
}
DATASET_FIELDS = {
    "id",
    "modality",
    "task",
    "access",
    "expected_use",
    "why_relevant",
    "risks",
    "not_committed_reason",
}
ADAPTER_MODULES = [
    "signal_engine.adapters.text_emotion",
    "signal_engine.adapters.asr",
    "signal_engine.adapters.diarization",
    "signal_engine.adapters.audio_features",
    "signal_engine.adapters.video_features",
    "signal_engine.adapters.privacy",
    "signal_engine.adapters.retrieval",
]


def test_model_registry_imports_without_optional_deps() -> None:
    assert MODEL_REGISTRY
    rows = list_model_registry()
    assert rows
    for row in rows:
        assert MODEL_FIELDS <= set(row)
        assert row["default_enabled"] is False
        assert row["notes"]
        assert row["risks"]


def test_dataset_registry_imports_without_downloads() -> None:
    assert DATASET_REGISTRY
    rows = list_dataset_registry()
    assert rows
    for row in rows:
        assert DATASET_FIELDS <= set(row)
        assert row["access"] in {
            "public",
            "gated",
            "license_required",
            "benchmark_reference",
        }
        assert row["not_committed_reason"]


def test_confusion_precision_recall_and_macro_f1() -> None:
    y_true = ["joy", "sad", "joy", "anger"]
    y_pred = ["joy", "sad", "anger", "anger"]
    labels = ["joy", "sad", "anger"]

    matrix = confusion_matrix_counts(y_true, y_pred, labels)
    assert matrix == {
        "joy": {"joy": 1, "sad": 0, "anger": 1},
        "sad": {"joy": 0, "sad": 1, "anger": 0},
        "anger": {"joy": 0, "sad": 0, "anger": 1},
    }

    metrics = precision_recall_f1(y_true, y_pred, labels)
    assert metrics["joy"]["precision"] == pytest.approx(1.0)
    assert metrics["joy"]["recall"] == pytest.approx(0.5)
    assert metrics["joy"]["f1"] == pytest.approx(2 / 3)
    assert metrics["sad"]["f1"] == pytest.approx(1.0)
    assert metrics["anger"]["precision"] == pytest.approx(0.5)
    assert metrics["anger"]["recall"] == pytest.approx(1.0)
    assert macro_f1(y_true, y_pred, labels) == pytest.approx(7 / 9)


def test_simple_calibration_bins_and_inter_rater_agreement() -> None:
    bins = simple_calibration_bins([1, 0, 1, 0], [0.1, 0.2, 0.8, 0.9], n_bins=2)
    assert bins == [
        {
            "bin_index": 0,
            "bin_start": 0.0,
            "bin_end": 0.5,
            "count": 2,
            "avg_score": pytest.approx(0.15),
            "positive_rate": pytest.approx(0.5),
        },
        {
            "bin_index": 1,
            "bin_start": 0.5,
            "bin_end": 1.0,
            "count": 2,
            "avg_score": pytest.approx(0.85),
            "positive_rate": pytest.approx(0.5),
        },
    ]
    assert inter_rater_agreement_percent(
        ["joy", "sad", "joy", "anger"],
        ["joy", "sad", "anger", "anger"],
    ) == pytest.approx(75.0)


def test_adapter_modules_import_safely() -> None:
    for module_name in ADAPTER_MODULES:
        module = importlib.import_module(module_name)
        assert hasattr(module, "is_available")
        assert hasattr(module, "require_available")
        assert isinstance(module.is_available(), bool)


@pytest.mark.parametrize(
    ("module_name", "install_hint", "missing_package"),
    [
        ("signal_engine.adapters.text_emotion", "pip install .[text-emotion]", "transformers"),
        ("signal_engine.adapters.audio_features", "pip install .[audio,prosody]", "opensmile"),
        ("signal_engine.adapters.retrieval", "pip install .[embeddings]", "sentence-transformers"),
    ],
)
def test_missing_optional_dependencies_produce_clear_install_hints(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    install_hint: str,
    missing_package: str,
) -> None:
    module = importlib.import_module(module_name)
    monkeypatch.setattr(
        adapter_helpers,
        "missing_dependencies",
        lambda dependencies: list(dependencies),
    )

    with pytest.raises(ImportError) as exc_info:
        module.require_available()

    message = str(exc_info.value)
    assert install_hint in message
    assert missing_package in message
    assert "Missing modules:" in message
    assert "Missing packages:" in message
