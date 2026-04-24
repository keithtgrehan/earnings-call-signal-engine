from __future__ import annotations

import importlib

import pytest

import signal_engine.adapters as adapter_helpers

ADAPTER_MODULES = [
    "signal_engine.adapters.text_emotion",
    "signal_engine.adapters.asr",
    "signal_engine.adapters.diarization",
    "signal_engine.adapters.audio_features",
    "signal_engine.adapters.video_features",
    "signal_engine.adapters.privacy",
    "signal_engine.adapters.retrieval",
]


def test_optional_adapters_import_safely_and_expose_dependency_hints() -> None:
    for module_name in ADAPTER_MODULES:
        module = importlib.import_module(module_name)
        assert hasattr(module, "is_available")
        assert hasattr(module, "require_available")
        assert hasattr(module, "dependency_hint")
        hint = module.dependency_hint()
        assert "pip install" in hint
        assert isinstance(module.is_available(), bool)


@pytest.mark.parametrize(
    ("module_name", "expected_install_hint"),
    [
        ("signal_engine.adapters.text_emotion", "pip install .[text-emotion]"),
        ("signal_engine.adapters.asr", "pip install .[audio]"),
        ("signal_engine.adapters.audio_features", "pip install .[audio,prosody]"),
        ("signal_engine.adapters.video_features", "pip install .[video]"),
        ("signal_engine.adapters.privacy", "pip install .[privacy]"),
        ("signal_engine.adapters.retrieval", "pip install .[embeddings]"),
    ],
)
def test_missing_optional_dependencies_raise_clear_hints(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    expected_install_hint: str,
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
    assert expected_install_hint in message
    assert "Missing modules:" in message
    assert "Missing packages:" in message
