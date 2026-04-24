from __future__ import annotations

import contextlib
from pathlib import Path
import wave

import numpy as np

from .schemas import EvidenceWindow, ModalityFeatureSet, SignalFeature


def _unsupported(path: str | None, reason: str) -> ModalityFeatureSet:
    return ModalityFeatureSet(
        modality="audio",
        available=False,
        source_path=path,
        limitations=[reason, "Audio cues are optional support only and never canonical truth."],
        adapter_used="lightweight_audio_proxy",
    )


def _strength(value: float, medium: float, high: float) -> str:
    if value >= high:
        return "high"
    if value >= medium:
        return "medium"
    return "low"


def _signal_window(duration_seconds: float | None) -> EvidenceWindow:
    if duration_seconds is None:
        return EvidenceWindow(start_seconds=None, end_seconds=None, description="Whole audio file")
    return EvidenceWindow(start_seconds=0.0, end_seconds=round(duration_seconds, 3), description="Whole audio file")


def _from_wav(path: Path) -> ModalityFeatureSet:
    with contextlib.closing(wave.open(str(path), "rb")) as handle:
        frame_rate = handle.getframerate()
        frame_count = handle.getnframes()
        sample_width = handle.getsampwidth()
        channel_count = handle.getnchannels()
        raw_frames = handle.readframes(frame_count)

    dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
    dtype = dtype_map.get(sample_width)
    if dtype is None:
        return _unsupported(str(path), f"Unsupported WAV sample width: {sample_width}")

    samples = np.frombuffer(raw_frames, dtype=dtype).astype(np.float32)
    if channel_count > 1:
        samples = samples.reshape(-1, channel_count).mean(axis=1)
    if not len(samples):
        return _unsupported(str(path), "Audio file contains no samples.")

    peak = max(float(np.max(np.abs(samples))), 1.0)
    normalized = samples / peak
    duration_seconds = frame_count / max(frame_rate, 1)
    rms = np.sqrt(np.mean(np.square(normalized)))
    frame_size = max(int(frame_rate * 0.05), 1)
    frame_rms = []
    for start in range(0, len(normalized), frame_size):
        chunk = normalized[start : start + frame_size]
        if len(chunk):
            frame_rms.append(float(np.sqrt(np.mean(np.square(chunk)))))
    rms_values = np.array(frame_rms, dtype=np.float32) if frame_rms else np.array([rms], dtype=np.float32)
    silence_ratio = float(np.mean(rms_values < 0.02))
    activity_ratio = 1.0 - silence_ratio
    rms_std = float(np.std(rms_values))

    signals = []
    if silence_ratio >= 0.18:
        signals.append(
            SignalFeature(
                signal_name="pause_length",
                modality="audio",
                strength=_strength(silence_ratio, 0.18, 0.35),
                confidence=min(0.72, 0.4 + silence_ratio),
                reason="High proportion of low-energy windows suggests pauses or silence clusters worth review.",
                recommended_review_action="Review the surrounding transcript and waveform before inferring hesitation.",
                evidence_window=_signal_window(duration_seconds),
                measurements={"silence_ratio": round(silence_ratio, 4)},
            )
        )
    if rms_std >= 0.05:
        signals.append(
            SignalFeature(
                signal_name="volume_intensity_change",
                modality="audio",
                strength=_strength(rms_std, 0.05, 0.12),
                confidence=min(0.7, 0.42 + (rms_std * 2.0)),
                reason="RMS variability suggests an intensity shift worth checking against transcript context.",
                recommended_review_action="Check whether intensity changes align with escalation, emphasis, or poor recording quality.",
                evidence_window=_signal_window(duration_seconds),
                measurements={"rms_std": round(rms_std, 4)},
            )
        )

    return ModalityFeatureSet(
        modality="audio",
        available=True,
        source_path=str(path),
        measurements={
            "duration_seconds": round(duration_seconds, 4),
            "sample_rate": frame_rate,
            "channel_count": channel_count,
            "rms_mean": round(float(rms), 4),
            "rms_std": round(rms_std, 4),
            "silence_ratio": round(silence_ratio, 4),
            "activity_ratio": round(activity_ratio, 4),
        },
        signals=signals,
        limitations=[
            "These are bounded acoustic proxies, not hidden-state inference.",
            "Speech-rate and pitch-change review remain future optional enhancements.",
        ],
        adapter_used="wave_numpy_proxy",
    )


def extract_audio_feature_set(path: str | Path | None) -> ModalityFeatureSet:
    if path is None:
        return _unsupported(None, "No audio file was provided.")

    file_path = Path(path)
    if not file_path.exists():
        return _unsupported(str(file_path), "Audio file does not exist.")

    if file_path.suffix.lower() == ".wav":
        return _from_wav(file_path)

    try:
        import librosa
    except ImportError:
        return _unsupported(
            str(file_path),
            "Only `.wav` files are supported without optional audio libraries. Install librosa for broader format support.",
        )

    samples, sample_rate = librosa.load(str(file_path), sr=None, mono=True)
    if len(samples) == 0:
        return _unsupported(str(file_path), "Audio file contains no decodable samples.")
    duration_seconds = len(samples) / max(sample_rate, 1)
    rms_values = librosa.feature.rms(y=samples)[0]
    silence_ratio = float(np.mean(rms_values < 0.02))
    rms_std = float(np.std(rms_values))
    rms_mean = float(np.mean(rms_values))

    signals = [
        SignalFeature(
            signal_name="pause_length",
            modality="audio",
            strength=_strength(silence_ratio, 0.18, 0.35),
            confidence=min(0.72, 0.4 + silence_ratio),
            reason="Low-energy windows suggest pause clusters worth review.",
            recommended_review_action="Review the corresponding transcript before inferring hesitation or uncertainty.",
            evidence_window=_signal_window(duration_seconds),
            measurements={"silence_ratio": round(silence_ratio, 4)},
        )
    ]
    if rms_std >= 0.05:
        signals.append(
            SignalFeature(
                signal_name="volume_intensity_change",
                modality="audio",
                strength=_strength(rms_std, 0.05, 0.12),
                confidence=min(0.7, 0.42 + (rms_std * 2.0)),
                reason="RMS variability suggests intensity changes worth checking.",
                recommended_review_action="Check whether the change reflects emphasis, interruption, or recording quality.",
                evidence_window=_signal_window(duration_seconds),
                measurements={"rms_std": round(rms_std, 4)},
            )
        )

    return ModalityFeatureSet(
        modality="audio",
        available=True,
        source_path=str(file_path),
        measurements={
            "duration_seconds": round(duration_seconds, 4),
            "sample_rate": sample_rate,
            "rms_mean": round(rms_mean, 4),
            "rms_std": round(rms_std, 4),
            "silence_ratio": round(silence_ratio, 4),
            "activity_ratio": round(1.0 - silence_ratio, 4),
        },
        signals=signals,
        limitations=[
            "These are bounded acoustic proxies, not claims about emotion or intent certainty.",
            "Broader format support depends on optional audio libraries.",
        ],
        adapter_used="librosa_proxy",
    )


__all__ = ["extract_audio_feature_set"]
