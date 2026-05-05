#!/usr/bin/env python
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "nlp_assets"
DOC_DIR = ROOT / "docs" / "nlp_assets"
REGISTRY_JSON = DATA_DIR / "asset_registry.json"
REGISTRY_CSV = DATA_DIR / "asset_registry.csv"

FIELDNAMES = [
    "id",
    "name",
    "category",
    "source_url",
    "license",
    "download_allowed",
    "download_status",
    "local_path",
    "committed",
    "intended_use",
    "signal_engine_relevance",
    "limitations",
    "priority",
]


def asset(
    id: str,
    name: str,
    category: str,
    source_url: str,
    license: str,
    download_allowed: bool | str,
    download_status: str,
    intended_use: list[str],
    signal_engine_relevance: list[str],
    limitations: list[str],
    priority: str,
    *,
    local_path: str = "",
    committed: bool = False,
    safe_download_url: str | None = None,
    cache_filename: str | None = None,
    safe_download_note: str = "",
) -> dict[str, Any]:
    entry = {
        "id": id,
        "name": name,
        "category": category,
        "source_url": source_url,
        "license": license,
        "download_allowed": download_allowed,
        "download_status": download_status,
        "local_path": local_path,
        "committed": committed,
        "intended_use": intended_use,
        "signal_engine_relevance": signal_engine_relevance,
        "limitations": limitations,
        "priority": priority,
    }
    if safe_download_url:
        entry["safe_download_url"] = safe_download_url
        entry["cache_filename"] = cache_filename or f"{id}.txt"
        entry["safe_download_note"] = safe_download_note
    return entry


ASSETS: list[dict[str, Any]] = [
    asset("loughran_mcdonald_lexicon", "Loughran-McDonald Master Dictionary", "finance", "https://sraf.nd.edu/loughranmcdonald-master-dictionary/", "Site terms/manual review required before redistributing dictionary files.", "unknown", "manual_required", ["finance sentiment lexicon", "uncertainty weak labels"], ["finance", "weak_labeling", "evaluation"], ["Dictionary counts need context; terms can overfire in long transcripts."], "high"),
    asset("financial_phrasebank", "Financial PhraseBank", "finance", "https://huggingface.co/datasets/takala/financial_phrasebank", "Dataset card/license review required; do not redistribute without checking source terms.", "unknown", "manual_required", ["finance sentiment benchmark"], ["finance", "supervised_training", "evaluation"], ["Sentence-level labels are weak proxies for earnings-call Q&A signals."], "high"),
    asset("prosus_finbert", "ProsusAI FinBERT model card", "finance", "https://huggingface.co/ProsusAI/finbert", "Model card and underlying data terms require review; no weights committed.", False, "skipped", ["finance sentiment model reference"], ["finance", "supervised_training"], ["Model card only; model availability is not validation on earnings calls."], "high"),
    asset("flang_finance_lm", "FLANG finance language model references", "finance", "https://huggingface.co/SALT-NLP/FLANG-ELECTRA", "Model license/model-card terms require manual review.", False, "skipped", ["finance language-model reference"], ["finance", "supervised_training"], ["Reference only; no model weights downloaded."], "medium"),
    asset("sec_company_tickers", "SEC company tickers JSON", "finance", "https://www.sec.gov/files/company_tickers.json", "SEC public data; respect SEC fair-access policies.", True, "skipped", ["public company metadata", "ticker/CIK normalization"], ["finance", "retrieval", "metadata"], ["Ticker metadata is not transcript data and may require refresh."], "high", safe_download_url="https://www.sec.gov/files/company_tickers.json", cache_filename="sec_company_tickers.json", safe_download_note="Small public SEC JSON cached locally; raw cache ignored."),
    asset("sec_edgar_submissions_api", "SEC EDGAR submissions API", "finance", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", "SEC public API documentation; use fair-access headers and rate limits.", True, "skipped", ["filing metadata", "8-K/source discovery"], ["finance", "metadata", "retrieval"], ["Metadata only; does not provide earnings-call transcripts."], "high"),
    asset("finos_earnings_references", "FINOS financial data / AI readiness references", "finance", "https://www.finos.org/", "FINOS project-specific licenses vary; manual review required.", "unknown", "manual_required", ["financial NLP ecosystem reference"], ["finance"], ["No verified reusable earnings-call transcript dataset found here."], "medium"),
    asset("public_earnings_call_dataset_candidates", "Public earnings-call transcript dataset candidates", "finance", "https://www.kaggle.com/search?q=earnings+call+transcripts+in%3Adatasets", "Kaggle and vendor dataset licenses vary; often gated/manual.", False, "gated", ["candidate transcript corpora"], ["finance", "supervised_training"], ["Do not download silently; redistribution and source provenance are uncertain."], "high"),
    asset("company_8k_press_release_metadata", "Company 8-K / press release metadata sources", "finance", "https://www.sec.gov/edgar/search-and-access", "SEC public access; source documents need per-use provenance.", True, "skipped", ["8-K metadata", "press release source discovery"], ["finance", "metadata", "retrieval"], ["Metadata is not a clean label source by itself."], "high"),
    asset("goemotions", "GoEmotions", "sentiment_emotion", "https://github.com/google-research/google-research/tree/master/goemotions", "Apache-2.0 code/data repo; verify current dataset terms before bulk use.", True, "skipped", ["emotion benchmark"], ["emotion", "evaluation", "supervised_training"], ["Reddit labels are not business-call labels; demographic/content bias risk."], "high"),
    asset("stanford_sentiment_treebank", "Stanford Sentiment Treebank", "sentiment_emotion", "https://nlp.stanford.edu/sentiment/", "Stanford dataset terms require manual review.", "unknown", "manual_required", ["sentiment benchmark"], ["emotion", "evaluation"], ["Movie-review phrase sentiment does not map to earnings-call intent."], "medium"),
    asset("imdb_sentiment", "IMDB Large Movie Review Dataset", "sentiment_emotion", "https://ai.stanford.edu/~amaas/data/sentiment/", "Dataset terms require attribution/review; raw archive is large.", True, "skipped", ["sentiment benchmark"], ["emotion", "supervised_training"], ["Movie reviews are domain-mismatched and large raw data stays ignored."], "low"),
    asset("tweeteval", "TweetEval", "sentiment_emotion", "https://github.com/cardiffnlp/tweeteval", "Repository license/dataset licenses require task-level review.", True, "skipped", ["sentiment/emotion benchmark"], ["emotion", "evaluation"], ["Social media language is noisy and domain-mismatched."], "medium"),
    asset("dair_ai_emotion", "DAIR.AI Emotion dataset", "sentiment_emotion", "https://huggingface.co/datasets/dair-ai/emotion", "Dataset card license review required.", "unknown", "manual_required", ["emotion benchmark"], ["emotion", "supervised_training"], ["Small/general emotion labels are not validated for finance calls."], "medium"),
    asset("empathetic_dialogues", "EmpatheticDialogues", "sentiment_emotion", "https://github.com/facebookresearch/EmpatheticDialogues", "CC BY-NC 4.0; non-commercial restriction.", False, "manual_required", ["empathy/dialogue reference"], ["emotion", "dialogue"], ["Non-commercial restriction and domain mismatch."], "medium"),
    asset("banking77", "Banking77", "intent", "https://huggingface.co/datasets/PolyAI/banking77", "Dataset card/license review required.", "unknown", "manual_required", ["intent classification reference"], ["intent", "supervised_training"], ["Banking support intents are not earnings-call signals."], "medium"),
    asset("clinc150", "CLINC150", "intent", "https://github.com/clinc/oos-eval", "Dataset license/terms require review.", "unknown", "manual_required", ["intent and out-of-scope classification"], ["intent", "evaluation"], ["Assistant intents differ from transcript evidence tasks."], "medium"),
    asset("cnn_dailymail", "CNN/DailyMail", "qa_retrieval", "https://huggingface.co/datasets/cnn_dailymail", "News content licensing is complex; reference only unless terms are clear.", False, "skipped", ["summarization reference"], ["summarization", "evaluation"], ["Do not bulk download/redistribute news text without license review."], "low"),
    asset("qasper", "Qasper", "qa_retrieval", "https://allenai.org/data/qasper", "Dataset license requires review; public research dataset.", "unknown", "manual_required", ["long-document QA"], ["retrieval", "evaluation"], ["Scientific QA differs from finance calls but good for evidence retrieval."], "high"),
    asset("squad", "SQuAD", "qa_retrieval", "https://rajpurkar.github.io/SQuAD-explorer/", "CC BY-SA 4.0; attribution/share-alike considerations.", True, "skipped", ["extractive QA benchmark"], ["retrieval", "evaluation"], ["Wikipedia QA is not transcript QA."], "medium"),
    asset("natural_questions", "Natural Questions", "qa_retrieval", "https://ai.google.com/research/NaturalQuestions", "License and storage requirements require review; large dataset.", False, "skipped", ["open-domain QA reference"], ["retrieval", "evaluation"], ["Large, web-search-oriented benchmark; not immediate."], "low"),
    asset("ms_marco", "MS MARCO", "qa_retrieval", "https://microsoft.github.io/msmarco/", "Microsoft dataset terms/manual review required.", False, "manual_required", ["passage ranking benchmark"], ["retrieval", "rag"], ["Large and domain-mismatched; useful later for retrieval method literacy."], "medium"),
    asset("beir", "BEIR", "qa_retrieval", "https://github.com/beir-cellar/beir", "Benchmark wrapper; component dataset licenses vary.", False, "manual_required", ["retrieval benchmark suite"], ["retrieval", "evaluation"], ["Do not assume all BEIR datasets can be redistributed."], "high"),
    asset("hotpotqa", "HotpotQA", "qa_retrieval", "https://hotpotqa.github.io/", "CC BY-SA 4.0; verify current terms.", True, "skipped", ["multi-hop QA reference"], ["retrieval", "evaluation"], ["Multi-hop Wikipedia QA only indirectly maps to transcript evidence."], "medium"),
    asset("multiwoz", "MultiWOZ", "dialogue", "https://github.com/budzianowski/multiwoz", "Dataset license/versions require manual review.", "unknown", "manual_required", ["dialogue state tracking"], ["dialogue", "intent"], ["Task-oriented assistant dialogues are unlike earnings calls."], "low"),
    asset("switchboard", "Switchboard", "dialogue", "https://catalog.ldc.upenn.edu/LDC97S62", "LDC paid/restricted access.", False, "gated", ["conversation/speech reference"], ["dialogue", "audio"], ["License-restricted; do not download."], "low"),
    asset("ami_meeting_corpus", "AMI Meeting Corpus", "dialogue", "https://groups.inf.ed.ac.uk/ami/corpus/", "AMI license/manual access terms require review.", "unknown", "manual_required", ["meeting dialogue/multimodal reference"], ["dialogue", "multimodal", "audio"], ["Meeting data differs from earnings calls; access terms matter."], "medium"),
    asset("meetingbank", "MeetingBank", "dialogue", "https://github.com/Yale-LILY/MeetingBank", "Repository/dataset license review required.", "unknown", "manual_required", ["meeting summarization"], ["dialogue", "summarization"], ["Public meeting domain; not finance calls."], "medium"),
    asset("samsum", "SAMSum", "dialogue", "https://huggingface.co/datasets/Samsung/samsum", "Dataset card/license review required.", "unknown", "manual_required", ["dialogue summarization"], ["dialogue", "summarization"], ["Chat-style summaries may not preserve evidence spans."], "medium"),
    asset("dialogsum", "DialogSum", "dialogue", "https://github.com/cylnlp/DialogSum", "Dataset license requires review.", "unknown", "manual_required", ["dialogue summarization"], ["dialogue", "summarization"], ["Casual dialogues are domain-mismatched."], "medium"),
    asset("qmsum", "QMSum", "dialogue", "https://github.com/Yale-LILY/QMSum", "Dataset license/manual review required.", "unknown", "manual_required", ["query-based meeting summarization"], ["dialogue", "retrieval", "summarization"], ["Relevant structure, but meeting domain and access terms need review."], "high"),
    asset("customer_support_kaggle_candidates", "Customer support public dataset candidates", "dialogue", "https://www.kaggle.com/search?q=customer+support+in%3Adatasets", "Kaggle licenses vary; gated/manual.", False, "gated", ["support benchmark candidates"], ["dialogue", "intent", "emotion"], ["Do not download silently; privacy and licensing risk."], "medium"),
    asset("snorkel", "Snorkel", "weak_labeling", "https://www.snorkel.org/", "Apache-2.0 project; package dependency optional.", True, "skipped", ["weak supervision framework"], ["weak_labeling", "evaluation"], ["Framework does not solve label quality; optional dependency only."], "high"),
    asset("deepeval", "DeepEval", "evaluation_safety", "https://github.com/confident-ai/deepeval", "Apache-2.0 project; may integrate with model providers depending on use.", True, "skipped", ["LLM evaluation reference"], ["evaluation"], ["Avoid paid/API evaluation paths unless explicitly configured."], "medium"),
    asset("promptfoo", "Promptfoo", "evaluation_safety", "https://www.promptfoo.dev/", "Open-source project; provider usage may require API keys.", True, "skipped", ["prompt/eval harness reference"], ["evaluation"], ["Not relevant until LLM sidecars exist."], "medium"),
    asset("helm", "HELM", "evaluation_safety", "https://crfm.stanford.edu/helm/latest/", "Stanford HELM; benchmark/data licenses vary.", False, "skipped", ["evaluation methodology reference"], ["evaluation", "safety"], ["Methodology reference, not immediate tooling."], "medium"),
    asset("bigbench", "BIG-bench", "evaluation_safety", "https://github.com/google/BIG-bench", "Apache-2.0 repository; benchmark tasks vary.", True, "skipped", ["capability benchmark reference"], ["evaluation", "safety"], ["General capability tasks do not validate finance signals."], "low"),
    asset("openai_evals", "OpenAI Evals", "evaluation_safety", "https://github.com/openai/evals", "MIT; using OpenAI models may require paid API.", True, "skipped", ["eval design reference"], ["evaluation"], ["No paid API use in this repo branch."], "medium"),
    asset("ragas", "Ragas", "evaluation_safety", "https://github.com/explodinggradients/ragas", "Apache-2.0 project; provider integrations may require keys.", True, "skipped", ["RAG evaluation reference"], ["retrieval", "evaluation"], ["RAG metrics need gold evidence spans to be meaningful."], "high"),
    asset("trulens", "TruLens", "evaluation_safety", "https://github.com/truera/trulens", "Open-source project; integrations vary.", True, "skipped", ["LLM/RAG observability reference"], ["retrieval", "evaluation"], ["Optional later; avoid telemetry/API assumptions."], "medium"),
    asset("sentence_transformers", "Sentence Transformers", "embeddings_retrieval_tools", "https://www.sbert.net/", "Apache-2.0 library; model licenses vary.", True, "skipped", ["local embeddings framework"], ["retrieval", "rag"], ["Optional dependency; no model downloads committed."], "high"),
    asset("all_minilm_l6_v2", "all-MiniLM-L6-v2", "embeddings_retrieval_tools", "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2", "Apache-2.0 model card; no weights committed.", False, "skipped", ["small local embedding candidate"], ["retrieval", "rag"], ["Model card reference only until explicitly downloaded."], "high"),
    asset("all_mpnet_base_v2", "all-mpnet-base-v2", "embeddings_retrieval_tools", "https://huggingface.co/sentence-transformers/all-mpnet-base-v2", "Apache-2.0 model card; no weights committed.", False, "skipped", ["higher-quality local embedding candidate"], ["retrieval", "rag"], ["Model card reference only; bigger than MiniLM."], "high"),
    asset("bge_small_en", "BAAI bge-small-en", "embeddings_retrieval_tools", "https://huggingface.co/BAAI/bge-small-en-v1.5", "Model card/license review required; no weights committed.", False, "skipped", ["small local embedding candidate"], ["retrieval", "rag"], ["Model availability is not retrieval validation."], "high"),
    asset("bge_base_en", "BAAI bge-base-en", "embeddings_retrieval_tools", "https://huggingface.co/BAAI/bge-base-en-v1.5", "Model card/license review required; no weights committed.", False, "skipped", ["local embedding candidate"], ["retrieval", "rag"], ["Heavier than small models; evaluate only after labels."], "medium"),
    asset("faiss", "FAISS", "embeddings_retrieval_tools", "https://github.com/facebookresearch/faiss", "MIT; optional dependency.", True, "skipped", ["vector search backend"], ["retrieval", "rag"], ["Do not add until retrieval metrics justify vector infra."], "medium"),
    asset("chroma", "Chroma", "embeddings_retrieval_tools", "https://github.com/chroma-core/chroma", "Apache-2.0; optional dependency.", True, "skipped", ["local vector DB candidate"], ["retrieval", "rag"], ["Avoid operational complexity before retrieval benchmark."], "medium"),
    asset("rank_bm25", "rank-bm25", "embeddings_retrieval_tools", "https://github.com/dorianbrown/rank_bm25", "Apache-2.0; optional dependency.", True, "skipped", ["lexical retrieval baseline"], ["retrieval", "evaluation"], ["Strong immediate baseline, but package not required by core."], "high"),
    asset("rapidfuzz", "RapidFuzz", "local_nlp_tools", "https://github.com/rapidfuzz/RapidFuzz", "MIT; optional dependency.", True, "skipped", ["fuzzy matching/entity normalization"], ["weak_labeling", "metadata"], ["Useful deterministic helper; still needs thresholds and tests."], "high"),
    asset("yake", "YAKE", "local_nlp_tools", "https://github.com/LIAAD/yake", "GPL-3.0; license compatibility review required.", "unknown", "manual_required", ["keyword extraction candidate"], ["weak_labeling", "retrieval"], ["GPL license may be unsuitable for direct dependency."], "medium"),
    asset("keybert", "KeyBERT", "local_nlp_tools", "https://github.com/MaartenGr/KeyBERT", "MIT; optional dependency with embedding model requirements.", True, "skipped", ["keyword extraction candidate"], ["retrieval", "weak_labeling"], ["Depends on embeddings; avoid until retrieval labels exist."], "medium"),
    asset("textstat", "textstat", "local_nlp_tools", "https://github.com/textstat/textstat", "MIT; optional dependency.", True, "skipped", ["readability/complexity features"], ["weak_labeling", "evaluation"], ["Readability features can be superficial without validation."], "medium"),
    asset("presidio_analyzer", "Presidio Analyzer", "privacy", "https://github.com/microsoft/presidio", "MIT; optional dependency and models may vary.", True, "skipped", ["PII detection"], ["privacy", "evaluation"], ["False positives/negatives require audit before automated redaction."], "high"),
    asset("presidio_anonymizer", "Presidio Anonymizer", "privacy", "https://github.com/microsoft/presidio", "MIT; optional dependency.", True, "skipped", ["PII redaction"], ["privacy"], ["Only useful with reviewed analyzer configuration."], "high"),
    asset("whisper", "Whisper", "audio_asr_prosody", "https://github.com/openai/whisper", "MIT; model weights downloaded separately if used.", False, "skipped", ["ASR reference"], ["audio", "multimodal"], ["No audio/model weights downloaded; ASR quality must be measured."], "high"),
    asset("faster_whisper", "faster-whisper", "audio_asr_prosody", "https://github.com/SYSTRAN/faster-whisper", "MIT; CTranslate2/model license review required.", False, "skipped", ["local ASR candidate"], ["audio", "multimodal"], ["Optional heavy runtime; no models committed."], "high"),
    asset("whisperx", "WhisperX", "audio_asr_prosody", "https://github.com/m-bain/whisperX", "BSD-style/project terms; dependencies/models vary.", False, "skipped", ["ASR alignment/diarization candidate"], ["audio", "multimodal"], ["Heavy dependency stack; gated diarization models may require tokens."], "medium"),
    asset("librosa", "librosa", "audio_asr_prosody", "https://librosa.org/doc/latest/index.html", "ISC; optional dependency.", True, "skipped", ["audio feature extraction"], ["audio", "multimodal"], ["Audio features need legally safe media and task labels."], "medium"),
    asset("opensmile", "openSMILE", "audio_asr_prosody", "https://audeering.github.io/opensmile-python/", "License/manual review required for some use cases.", "unknown", "manual_required", ["prosody/acoustic features"], ["audio", "multimodal"], ["License and feature interpretation need review."], "high"),
    asset("pyannote_audio", "pyannote.audio", "audio_asr_prosody", "https://github.com/pyannote/pyannote-audio", "MIT code; many pretrained models are gated on Hugging Face.", False, "gated", ["diarization candidate"], ["audio", "multimodal"], ["Do not download gated models silently."], "medium"),
    asset("common_voice", "Common Voice", "audio_asr_prosody", "https://commonvoice.mozilla.org/en/datasets", "CC0 and variant terms by release/language; large download.", True, "skipped", ["ASR data reference"], ["audio", "evaluation"], ["Large and not earnings-call domain."], "low"),
    asset("librispeech", "LibriSpeech", "audio_asr_prosody", "https://www.openslr.org/12", "CC BY 4.0; large corpus.", True, "skipped", ["ASR benchmark reference"], ["audio", "evaluation"], ["Read speech, not earnings calls; large raw data ignored."], "low"),
    asset("tedlium", "TED-LIUM", "audio_asr_prosody", "https://www.openslr.org/51", "CC BY-NC-ND 3.0; non-commercial/no-derivatives restrictions.", False, "manual_required", ["ASR benchmark reference"], ["audio", "evaluation"], ["License restrictions and domain mismatch."], "low"),
    asset("opencv", "OpenCV", "video_multimodal", "https://opencv.org/", "Apache-2.0; optional dependency.", True, "skipped", ["video/frame feature extraction"], ["video", "multimodal"], ["Visual features require legally safe video and labels."], "medium"),
    asset("mediapipe", "MediaPipe", "video_multimodal", "https://github.com/google-ai-edge/mediapipe", "Apache-2.0; optional dependency/models vary.", True, "skipped", ["face/pose feature candidate"], ["video", "multimodal"], ["Can overclaim behavioral inference without evaluation."], "medium"),
    asset("deepface", "DeepFace", "video_multimodal", "https://github.com/serengil/deepface", "MIT; model/data ethics review required.", True, "skipped", ["face analysis reference"], ["video", "multimodal"], ["High ethical/privacy risk; avoid emotion claims."], "low"),
    asset("cmu_mosei", "CMU-MOSEI", "video_multimodal", "http://multicomp.cs.cmu.edu/resources/cmu-mosei-dataset/", "Dataset license/manual request terms required.", False, "manual_required", ["multimodal sentiment benchmark"], ["video", "audio", "multimodal"], ["Access/licensing and domain mismatch."], "medium"),
    asset("cmu_mosi", "CMU-MOSI", "video_multimodal", "http://multicomp.cs.cmu.edu/resources/cmu-mosi-dataset/", "Dataset license/manual request terms required.", False, "manual_required", ["multimodal sentiment benchmark"], ["video", "audio", "multimodal"], ["Small benchmark; not earnings calls."], "medium"),
    asset("avec", "AVEC challenges", "video_multimodal", "https://avec-challenge.github.io/", "Challenge data terms vary; often manual/restricted.", False, "manual_required", ["affective computing reference"], ["audio", "video", "multimodal"], ["Clinical/affect tasks are high-risk and not business signals."], "low"),
    asset("meld", "MELD", "video_multimodal", "https://affective-meld.github.io/", "Dataset license/manual review required; derived from TV content.", False, "manual_required", ["multimodal emotion reference"], ["emotion", "video", "audio"], ["TV dialogue licensing/domain mismatch; do not treat as business proof."], "medium"),
    asset("iemocap", "IEMOCAP", "video_multimodal", "https://sail.usc.edu/iemocap/", "USC license/manual access; restricted.", False, "gated", ["emotion/audio-video reference"], ["audio", "video", "emotion"], ["Restricted access; acted emotion domain."], "low"),
]


def write_registry(assets: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_JSON.write_text(json.dumps(assets, indent=2) + "\n", encoding="utf-8")
    with REGISTRY_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for entry in assets:
            writer.writerow(
                {
                    key: json.dumps(entry[key]) if isinstance(entry.get(key), list) else entry.get(key, "")
                    for key in FIELDNAMES
                }
            )


def write_docs(assets: list[dict[str, Any]]) -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for entry in assets:
        counts[entry["category"]] = counts.get(entry["category"], 0) + 1
    downloaded = [entry for entry in assets if entry["download_status"] == "downloaded"]
    manual = [entry for entry in assets if entry["download_status"] in {"manual_required", "gated"}]
    high = [entry for entry in assets if entry["priority"] == "high"]

    (DOC_DIR / "README.md").write_text(
        "# NLP Assets Registry\n\n"
        "This registry tracks datasets, lexicons, model references, benchmark suites, and local NLP tooling for Signal Engine 2.0. "
        "It is an audit and preparation layer, not proof that every asset is downloaded, licensed for redistribution, or validated.\n\n"
        "Raw data and bulky source artifacts belong in ignored local cache paths under `data/nlp_assets/cache/` or `data/nlp_assets/raw/`. "
        "Committed files are manifests, docs, and validation summaries only.\n\n"
        "## Category Counts\n\n"
        + "\n".join(f"- `{category}`: {count}" for category, count in sorted(counts.items()))
        + "\n\n## CLI\n\n"
        "```bash\n"
        "python tools/nlp_asset_map.py --list\n"
        "python tools/nlp_asset_map.py --category finance\n"
        "python tools/nlp_asset_map.py --downloaded\n"
        "python tools/nlp_asset_map.py --manual-required\n"
        "python tools/nlp_asset_map.py --signal-engine-area weak_labeling\n"
        "python tools/nlp_asset_map.py --priority high\n"
        "python tools/nlp_asset_map.py --validate\n"
        "```\n",
        encoding="utf-8",
    )

    (DOC_DIR / "download_status.md").write_text(
        "# NLP Asset Download Status\n\n"
        "Downloaded means a small public metadata/reference artifact was cached locally by safe tooling. It does not imply raw dataset availability unless the asset says so explicitly.\n\n"
        "## Downloaded\n\n"
        + ("\n".join(f"- {entry['name']} -> `{entry['local_path']}`" for entry in downloaded) or "- None yet. Run `python tools/nlp_assets/download_assets.py --safe-only`.")
        + "\n\n## Manual Or Gated\n\n"
        + "\n".join(f"- {entry['name']} (`{entry['download_status']}`): {entry['license']}" for entry in manual)
        + "\n",
        encoding="utf-8",
    )

    (DOC_DIR / "license_and_usage_notes.md").write_text(
        "# License And Usage Notes\n\n"
        "- Do not commit raw large datasets, model weights, gated resources, or license-restricted corpora.\n"
        "- Treat Hugging Face and Kaggle entries as references until exact dataset cards and terms are reviewed.\n"
        "- SEC metadata is public but should be fetched with fair-access headers and refreshed as metadata, not as product proof.\n"
        "- Non-commercial datasets are not suitable for unrestricted portfolio/product use without legal review.\n"
        "- Audio/video affect datasets carry extra privacy and ethics risk; avoid emotion claims without human-reviewed evaluation.\n\n"
        "## High-Priority Manual Reviews\n\n"
        + "\n".join(f"- {entry['name']}: {entry['license']}" for entry in high if entry["download_status"] in {"manual_required", "gated"})
        + "\n",
        encoding="utf-8",
    )

    (DOC_DIR / "signal_engine_asset_strategy.md").write_text(
        "# Signal Engine Asset Strategy\n\n"
        "The immediate path is not to train large models. It is to combine finance lexicons, SEC metadata, deterministic transcript labels, lexical retrieval, and explicit evaluation gates. "
        "After 30 transcripts, the registry supports weak-label audits and benchmark design. After 100 transcripts, it supports small supervised baselines and retrieval experiments. "
        "After 500 transcripts, it supports model-family comparisons, audio/prosody pilots, and multimodal ablations.\n\n"
        "## Recommended Order\n\n"
        "1. SEC metadata and Loughran-McDonald review.\n"
        "2. Evidence-span labels and weak-label error analysis.\n"
        "3. Financial PhraseBank/FinBERT as benchmark references only.\n"
        "4. BM25/rapidfuzz/textstat deterministic helpers.\n"
        "5. Small local embedding candidates after retrieval labels exist.\n"
        "6. Audio/video assets only after legally safe media is available.\n",
        encoding="utf-8",
    )


def main() -> int:
    write_registry(ASSETS)
    write_docs(ASSETS)
    print(f"Audited {len(ASSETS)} NLP assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
