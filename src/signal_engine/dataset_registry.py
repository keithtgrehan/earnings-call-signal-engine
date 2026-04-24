from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetRegistryEntry:
    """Metadata-only card for datasets and benchmark references."""

    id: str
    modality: str
    task: str
    access: str
    expected_use: str
    why_relevant: str
    risks: str
    not_committed_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DATASET_REGISTRY: tuple[DatasetRegistryEntry, ...] = (
    DatasetRegistryEntry(
        id="GoEmotions",
        modality="text",
        task="emotion_classification",
        access="public",
        expected_use="Benchmark transcript-segment emotion classifiers against a widely used public label set.",
        why_relevant="Useful baseline for text emotion scaffolding before any domain-specific annotation investment.",
        risks="Reddit-style emotional language differs from support, sales, and account-management call dynamics.",
        not_committed_reason="Dataset artifacts are intentionally excluded to keep the repo lightweight and deterministic.",
    ),
    DatasetRegistryEntry(
        id="customer-support-sentiment-placeholder",
        modality="text",
        task="sentiment_classification",
        access="license_required",
        expected_use="Placeholder for future customer-support sentiment benchmarks once a vetted dataset is chosen.",
        why_relevant="Support QA needs domain-aware sentiment and frustration signals beyond generic internet text.",
        risks="Licensing, privacy, and annotation quality vary widely across support datasets.",
        not_committed_reason="No dataset was selected or licensed in this run, so only a placeholder card is tracked.",
    ),
    DatasetRegistryEntry(
        id="sales-support-synthetic-fixtures",
        modality="text",
        task="emotion_and_intent_smoke_tests",
        access="public",
        expected_use="Small synthetic fixtures for deterministic smoke tests and rubric alignment checks.",
        why_relevant="Lets the roadmap evolve safely without downloading third-party corpora or exposing customer data.",
        risks="Synthetic fixtures are useful for tests but not representative enough for headline benchmark claims.",
        not_committed_reason="Fixtures should stay tiny and hand-authored rather than storing large generated corpora.",
    ),
    DatasetRegistryEntry(
        id="MSP-Podcast",
        modality="audio",
        task="speech_emotion_recognition",
        access="license_required",
        expected_use="Benchmark optional speech emotion features on longer-form conversational audio.",
        why_relevant="Closer than acted clips to realistic speech variation and turn lengths.",
        risks="Licensing and annotation subjectivity make this unsuitable for bundled repo artifacts.",
        not_committed_reason="Audio datasets are large and license-sensitive, so only the metadata card is included.",
    ),
    DatasetRegistryEntry(
        id="IEMOCAP",
        modality="audio_video_text",
        task="speech_and_multimodal_emotion",
        access="license_required",
        expected_use="Reference benchmark for speech, text, and multimodal emotion experiments.",
        why_relevant="Common cross-modal benchmark covering text, audio, and video interaction signals.",
        risks="Acted data and academic license terms limit direct transfer to production conversation QA.",
        not_committed_reason="Dataset redistribution is restricted and far too large for this repository.",
    ),
    DatasetRegistryEntry(
        id="MSP-IMPROV",
        modality="audio_video_text",
        task="speech_emotion_recognition",
        access="license_required",
        expected_use="Compare speech emotion candidates on improvised dialogue rather than transcript-only text.",
        why_relevant="Provides another SER checkpoint beyond a single benchmark corpus.",
        risks="Label subjectivity and licensing constraints make direct bundling inappropriate.",
        not_committed_reason="License-gated audio/video data is intentionally not committed.",
    ),
    DatasetRegistryEntry(
        id="MELD",
        modality="audio_video_text",
        task="multimodal_emotion_classification",
        access="public",
        expected_use="Benchmark multimodal emotion fusion ideas once transcript and audio baselines are stable.",
        why_relevant="Conversation-oriented multimodal benchmark with text, audio, and emotion labels.",
        risks="TV-dialogue style and annotation conventions differ from enterprise meetings and calls.",
        not_committed_reason="Not downloaded here to avoid dataset bloat and non-essential benchmark assets.",
    ),
    DatasetRegistryEntry(
        id="CMU-MOSEI",
        modality="audio_video_text",
        task="multimodal_sentiment_and_emotion",
        access="license_required",
        expected_use="Reference benchmark for multimodal sentiment and emotion experiments.",
        why_relevant="Widely cited multimodal benchmark for fusion methods and cross-modal comparisons.",
        risks="Opinion-video domain is materially different from support and revenue-critical conversations.",
        not_committed_reason="Large external corpus with access and storage overhead not suitable for this repo.",
    ),
    DatasetRegistryEntry(
        id="CMU-MOSI",
        modality="audio_video_text",
        task="multimodal_sentiment",
        access="license_required",
        expected_use="Compact multimodal sentiment benchmark reference for early fusion experiments.",
        why_relevant="Useful historical baseline when reviewing literature or lightweight benchmark plans.",
        risks="Very different speaking context from enterprise calls and not enough for production claims.",
        not_committed_reason="Benchmark reference only; dataset contents are not bundled.",
    ),
    DatasetRegistryEntry(
        id="MTEB",
        modality="text",
        task="embedding_benchmark_reference",
        access="benchmark_reference",
        expected_use="Compare optional embedding candidates on public benchmark suites before any retrieval rollout.",
        why_relevant="Standard point of reference for embedding and retrieval quality claims.",
        risks="Leaderboard gains may not correlate with evidence retrieval quality on conversation transcripts.",
        not_committed_reason="Benchmark suite spans many datasets and is tracked as a reference only.",
    ),
    DatasetRegistryEntry(
        id="BEIR",
        modality="text",
        task="retrieval_benchmark_reference",
        access="benchmark_reference",
        expected_use="Reference suite for retrieval benchmarking when testing transcript lookup components.",
        why_relevant="Useful external benchmark context for semantic retrieval experiments.",
        risks="Open-domain retrieval settings differ from enterprise transcript evidence workflows.",
        not_committed_reason="Benchmark corpora are external and intentionally not mirrored in-repo.",
    ),
    DatasetRegistryEntry(
        id="Open-ASR-Leaderboard-ESB-reference",
        modality="audio",
        task="automatic_speech_recognition",
        access="benchmark_reference",
        expected_use="Track public ASR benchmark references while keeping transcript-first scoring canonical.",
        why_relevant="Helps compare optional ASR candidates without making ASR mandatory for product truth.",
        risks="Leaderboard wins can hide domain mismatch, token gates, or compute assumptions.",
        not_committed_reason="Reference-only entry; no benchmark payloads or audio are downloaded.",
    ),
    DatasetRegistryEntry(
        id="Open-Speech-Emotion-Recognition-Leaderboard",
        modality="audio",
        task="speech_emotion_recognition",
        access="benchmark_reference",
        expected_use="Reference external SER benchmark results before any optional speech emotion experiments.",
        why_relevant="Keeps roadmap evaluation grounded in public benchmarks rather than anecdotal model picks.",
        risks="Leaderboards do not solve transfer, privacy, or truthfulness concerns for enterprise use cases.",
        not_committed_reason="Leaderboard metadata only; no external assets are committed.",
    ),
)

DATASET_REGISTRY_BY_ID: dict[str, DatasetRegistryEntry] = {
    entry.id: entry for entry in DATASET_REGISTRY
}


def list_dataset_registry() -> list[dict[str, Any]]:
    return [entry.to_dict() for entry in DATASET_REGISTRY]


def get_dataset_registry_entry(dataset_id: str) -> dict[str, Any]:
    try:
        return DATASET_REGISTRY_BY_ID[dataset_id].to_dict()
    except KeyError as exc:
        supported = ", ".join(sorted(DATASET_REGISTRY_BY_ID))
        raise KeyError(
            f"Unknown dataset registry id '{dataset_id}'. Supported ids: {supported}."
        ) from exc
