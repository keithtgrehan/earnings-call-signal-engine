from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ModelRegistryEntry:
    """Metadata-only card for optional roadmap models and tools."""

    id: str
    modality: str
    task: str
    required_optional_group: str
    default_enabled: bool
    notes: str
    risks: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MODEL_REGISTRY: tuple[ModelRegistryEntry, ...] = (
    ModelRegistryEntry(
        id="cardiffnlp/twitter-roberta-base-sentiment-latest",
        modality="text",
        task="sentiment_classification",
        required_optional_group="text-emotion",
        default_enabled=False,
        notes="Reference-only text sentiment baseline for transcript experiments and benchmark comparisons.",
        risks="Requires transformer model artifacts and may drift from domain-specific support or sales language.",
    ),
    ModelRegistryEntry(
        id="j-hartmann/emotion-english-distilroberta-base",
        modality="text",
        task="emotion_classification",
        required_optional_group="text-emotion",
        default_enabled=False,
        notes="Common English emotion baseline for transcript-first emotion benchmarking.",
        risks="General-domain emotion labels can overstate confidence on business conversations.",
    ),
    ModelRegistryEntry(
        id="SamLowe/roberta-base-go_emotions",
        modality="text",
        task="emotion_classification",
        required_optional_group="text-emotion",
        default_enabled=False,
        notes="GoEmotions-aligned checkpoint for fine-grained emotion experiments on transcript segments.",
        risks="Fine-grained labels may be sparse, noisy, or mismatched with enterprise review taxonomies.",
    ),
    ModelRegistryEntry(
        id="faster-whisper/whisper-family",
        modality="audio",
        task="automatic_speech_recognition",
        required_optional_group="audio",
        default_enabled=False,
        notes="Offline ASR family placeholder for future audio-to-transcript workflows without changing canonical scoring.",
        risks="Model downloads are heavy and transcription variance can affect downstream deterministic evidence.",
    ),
    ModelRegistryEntry(
        id="WhisperX",
        modality="audio",
        task="automatic_speech_recognition_alignment",
        required_optional_group="audio",
        default_enabled=False,
        notes="Alignment-oriented ASR placeholder for timestamp refinement and speaker-aware review workflows.",
        risks="Heavier runtime, optional diarization coupling, and potential token-gated model paths.",
    ),
    ModelRegistryEntry(
        id="pyannote.audio",
        modality="audio",
        task="speaker_diarization",
        required_optional_group="diarization",
        default_enabled=False,
        notes="Speaker diarization placeholder for future turn attribution when only raw audio is available.",
        risks="Often requires gated assets or tokens and adds substantial runtime complexity.",
    ),
    ModelRegistryEntry(
        id="openSMILE",
        modality="audio",
        task="speech_emotion_features",
        required_optional_group="prosody",
        default_enabled=False,
        notes="Engineered prosody feature extraction candidate for benchmark-only enrichment on flagged segments.",
        risks="Acoustic proxies are not emotion truth and can be confounded by recording quality or accents.",
    ),
    ModelRegistryEntry(
        id="librosa",
        modality="audio",
        task="acoustic_feature_extraction",
        required_optional_group="audio",
        default_enabled=False,
        notes="Lightweight audio feature engineering candidate for pitch, energy, and timing summaries.",
        risks="Feature interpretations are indirect and should remain evidence support rather than final labels.",
    ),
    ModelRegistryEntry(
        id="torchaudio",
        modality="audio",
        task="audio_preprocessing",
        required_optional_group="audio",
        default_enabled=False,
        notes="Audio tensor preprocessing placeholder for future speech and ASR benchmarking pipelines.",
        risks="Torch-backed runtime increases install weight and can complicate CPU-only environments.",
    ),
    ModelRegistryEntry(
        id="sentence-transformers",
        modality="text",
        task="embedding_retrieval",
        required_optional_group="embeddings",
        default_enabled=False,
        notes="Semantic retrieval baseline for benchmark-only transcript lookup and evidence ranking experiments.",
        risks="Embedding recall can look authoritative without providing deterministic source-of-truth reasoning.",
    ),
    ModelRegistryEntry(
        id="FAISS",
        modality="text",
        task="vector_index",
        required_optional_group="embeddings",
        default_enabled=False,
        notes="Local vector index candidate for transcript retrieval experiments and benchmark harnesses.",
        risks="Index quality depends on embedding quality and should never replace direct transcript evidence.",
    ),
    ModelRegistryEntry(
        id="Chroma",
        modality="text",
        task="vector_store",
        required_optional_group="embeddings",
        default_enabled=False,
        notes="Developer-friendly vector store option for optional retrieval prototyping and offline evaluation.",
        risks="Persistence and retrieval heuristics can create false confidence if treated as canonical truth.",
    ),
    ModelRegistryEntry(
        id="MTEB",
        modality="text",
        task="embedding_benchmark_reference",
        required_optional_group="documentation_only",
        default_enabled=False,
        notes="Benchmark reference for evaluating future text embedding candidates without shipping any benchmark data.",
        risks="Benchmark gains may not transfer to support, sales, or account-management conversations.",
    ),
    ModelRegistryEntry(
        id="BEIR",
        modality="text",
        task="retrieval_benchmark_reference",
        required_optional_group="documentation_only",
        default_enabled=False,
        notes="Retrieval benchmark reference for optional evidence lookup experiments.",
        risks="Public retrieval benchmarks differ from enterprise conversation review tasks and privacy constraints.",
    ),
    ModelRegistryEntry(
        id="OpenCV",
        modality="video",
        task="frame_processing",
        required_optional_group="video",
        default_enabled=False,
        notes="Video preprocessing placeholder for keyframe extraction on escalation-only review paths.",
        risks="Frame-level signals are easy to overinterpret and should never become standalone truth claims.",
    ),
    ModelRegistryEntry(
        id="PySceneDetect",
        modality="video",
        task="scene_detection",
        required_optional_group="video",
        default_enabled=False,
        notes="Shot and scene boundary candidate for clipping long videos into reviewable segments.",
        risks="Scene boundaries are a convenience feature, not an emotion inference signal by themselves.",
    ),
    ModelRegistryEntry(
        id="ffmpeg-python",
        modality="video",
        task="media_conversion",
        required_optional_group="audio",
        default_enabled=False,
        notes="Media conversion placeholder for safe audio extraction and clip preparation before optional review.",
        risks="Relies on external ffmpeg binaries and can introduce platform-specific setup variance.",
    ),
)

MODEL_REGISTRY_BY_ID: dict[str, ModelRegistryEntry] = {
    entry.id: entry for entry in MODEL_REGISTRY
}


def list_model_registry() -> list[dict[str, Any]]:
    return [entry.to_dict() for entry in MODEL_REGISTRY]


def get_model_registry_entry(model_id: str) -> dict[str, Any]:
    try:
        return MODEL_REGISTRY_BY_ID[model_id].to_dict()
    except KeyError as exc:
        supported = ", ".join(sorted(MODEL_REGISTRY_BY_ID))
        raise KeyError(
            f"Unknown model registry id '{model_id}'. Supported ids: {supported}."
        ) from exc
