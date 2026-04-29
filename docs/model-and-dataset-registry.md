# Model And Dataset Registry

This document tracks optional roadmap components only. Nothing in this registry changes the canonical Signal Engine 2.0 rule: deterministic, transcript-first, evidence-backed outputs remain the source of truth.

## Added Now

- metadata-only model registry in `src/signal_engine/model_registry.py`
- metadata-only dataset registry in `src/signal_engine/dataset_registry.py`
- import-safe adapter placeholders in `src/signal_engine/adapters/`
- pure-Python benchmark helpers in `src/signal_engine/emotion_benchmark.py`

## Added Later

- production ASR integration
- diarization pipelines
- text emotion inference
- speech emotion inference
- video emotion inference
- multimodal fusion
- external dataset ingestion
- model downloads and benchmark execution

## Optional Dependency Groups

| Group | Packages | Notes |
| --- | --- | --- |
| `nlp` | `spacy`, `scikit-learn`, `rapidfuzz`, `textstat`, `yake` | deterministic NLP and lightweight benchmarking support |
| `privacy` | `presidio-analyzer`, `presidio-anonymizer` | local PII review and anonymization |
| `embeddings` | `sentence-transformers`, `faiss-cpu`, `chromadb` | benchmark-only semantic retrieval and indexing |
| `text-emotion` | `transformers`, `torch`, `datasets`, `evaluate` | transcript emotion benchmark baselines |
| `audio` | `faster-whisper`, `librosa`, `torchaudio`, `ffmpeg-python` | optional ASR and acoustic features |
| `diarization` | `pyannote.audio` | optional speaker diarization; often gated |
| `video` | `opencv-python`, `scenedetect`, `moviepy` | escalation-only video review |
| `prosody` | `opensmile` | engineered acoustic feature extraction |

## Model And Tool Registry

| ID | Modality | Task | Group | Added Now vs Later | Token / License Notes |
| --- | --- | --- | --- | --- | --- |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | text | sentiment classification | `text-emotion` | later benchmark candidate | model download required |
| `j-hartmann/emotion-english-distilroberta-base` | text | emotion classification | `text-emotion` | later benchmark candidate | model download required |
| `SamLowe/roberta-base-go_emotions` | text | emotion classification | `text-emotion` | later benchmark candidate | model download required |
| `faster-whisper/whisper-family` | audio | ASR | `audio` | later runtime candidate | model download required |
| `WhisperX` | audio | ASR alignment | `audio` | later runtime candidate | may require additional model assets |
| `pyannote.audio` | audio | diarization | `diarization` | later runtime candidate | often needs gated assets or token-backed access |
| `openSMILE` | audio | speech emotion features | `prosody` | later benchmark candidate | local runtime setup required |
| `librosa` | audio | acoustic features | `audio` | later benchmark candidate | local-only Python dependency |
| `torchaudio` | audio | audio preprocessing | `audio` | later benchmark candidate | torch-backed runtime |
| `sentence-transformers` | text | embeddings | `embeddings` | later benchmark candidate | model download required |
| `FAISS` | text | vector index | `embeddings` | later tooling candidate | local index only, not canonical truth |
| `Chroma` | text | vector store | `embeddings` | later tooling candidate | local persistence choice only |
| `MTEB` | text | embedding benchmark reference | benchmark reference only | reference now | no runtime install here |
| `BEIR` | text | retrieval benchmark reference | benchmark reference only | reference now | no runtime install here |
| `OpenCV` | video | frame processing | `video` | later escalation candidate | local native dependency |
| `PySceneDetect` | video | scene detection | `video` | later escalation candidate | local-only tool |
| `ffmpeg-python` | media | conversion and clipping | `audio` | later tooling candidate | requires system `ffmpeg` binary |

## Dataset And Benchmark Registry

| ID | Modality | Task | Access | Added Now vs Later | Why Not Committed |
| --- | --- | --- | --- | --- | --- |
| `GoEmotions` | text | emotion classification | public | reference now | keep repo lightweight and avoid automatic downloads |
| `customer-support sentiment datasets placeholder` | text | sentiment classification | license required | placeholder now | no approved dataset selected in this run |
| `sales/support synthetic fixtures` | text | smoke tests | public | tiny local fixtures later | prefer hand-authored fixtures over large corpora |
| `MSP-Podcast` | audio | speech emotion recognition | license required | reference now | large licensed audio corpus |
| `IEMOCAP` | multimodal | speech and multimodal emotion | license required | reference now | redistribution and size constraints |
| `MSP-IMPROV` | multimodal | speech emotion recognition | license required | reference now | gated academic-style dataset |
| `MELD` | multimodal | multimodal emotion classification | public | reference now | intentionally not downloaded |
| `CMU-MOSEI` | multimodal | multimodal sentiment and emotion | license required | reference now | external corpus not mirrored here |
| `CMU-MOSI` | multimodal | multimodal sentiment | license required | reference now | benchmark reference only |
| `MTEB` | text | embedding benchmark reference | benchmark reference | reference now | large external benchmark suite |
| `BEIR` | text | retrieval benchmark reference | benchmark reference | reference now | large external benchmark suite |
| `Open ASR Leaderboard (ESB-style reference)` | audio | ASR benchmark reference | benchmark reference | reference now | public benchmark metadata only |
| `Open Speech Emotion Recognition Leaderboard` | audio | SER benchmark reference | benchmark reference | reference now | leaderboard metadata only |

## Guardrails

- Benchmark references stay as references until the user provides tokens, licenses, and approved dataset roots.
- No dataset or model download is triggered by importing any registry or adapter module.
- Optional tooling remains off by default.
- Canonical outputs remain deterministic even if future benchmark candidates are added.
