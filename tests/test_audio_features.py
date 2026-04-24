from __future__ import annotations

import math
from pathlib import Path
import wave

import numpy as np

from signal_engine.multimodal.audio_features import extract_audio_feature_set


def _write_wav(path: Path) -> None:
    sample_rate = 16000
    tone = [math.sin(2.0 * math.pi * 440.0 * (index / sample_rate)) for index in range(sample_rate // 4)]
    silence = [0.0] * (sample_rate // 8)
    signal = np.array(tone + silence + tone, dtype=np.float32)
    pcm = np.int16(signal * 32767)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def test_extract_audio_feature_set_from_tiny_wav(tmp_path: Path) -> None:
    audio_path = tmp_path / "tiny.wav"
    _write_wav(audio_path)

    feature_set = extract_audio_feature_set(audio_path)

    assert feature_set.available is True
    assert feature_set.measurements["duration_seconds"] > 0.0
    assert "silence_ratio" in feature_set.measurements


def test_extract_audio_feature_set_handles_missing_file() -> None:
    feature_set = extract_audio_feature_set("/tmp/not-a-real-file.wav")
    assert feature_set.available is False
    assert "does not exist" in " ".join(feature_set.limitations)
