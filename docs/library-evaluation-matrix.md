# Library Evaluation Matrix

This matrix tracks optional roadmap libraries, models, and benchmark references. Deterministic transcript-first scoring remains canonical even when a row below looks promising.

| Item | Category | Required vs Optional | Why Useful | Risks / Constraints |
| --- | --- | --- | --- | --- |
| `spaCy` | NLP | Optional | tokenization, matchers, NER, and deterministic text processing utilities | model downloads add weight and should stay outside the canonical path |
| `scikit-learn` | NLP | Optional | classic baselines, TF-IDF, calibration helpers, and evaluation support | adds install weight for functionality not needed by the current deterministic engine |
| `rapidfuzz` | NLP | Optional | deterministic fuzzy matching for phrase normalization and taxonomy cleanup | loose thresholds can create false matches |
| `Presidio` | Privacy | Optional | local PII detection and anonymization guardrails | needs domain tuning and may over-redact business terms |
| `YAKE` | NLP | Optional | lightweight keyword extraction for analyst review artifacts | extracted keywords are useful hints, not canonical truth |
| `KeyBERT` | NLP | Document only for now | alternative keyword extraction option if embedding tooling is already enabled | heavier because it depends on embeddings and model artifacts |
| `textstat` | NLP | Optional | readability and complexity proxies for transcript review | transcript formatting can make readability scores noisy |
| `sentence-transformers` | Embeddings | Optional | benchmark-only semantic retrieval baselines | model downloads are heavier and semantic hits can look overconfident |
| `FAISS` | Embeddings | Optional | fast local vector indexing for transcript retrieval experiments | retrieval rank should not replace transcript evidence |
| `Chroma` | Embeddings | Optional | simple local vector store for prototyping | persistence choices can distract from deterministic scoring goals |
| `transformers` emotion models | Text emotion | Optional | reusable runtime for sentiment and emotion benchmark candidates | heavy runtime and model download burden |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | Text sentiment | Optional benchmark candidate | quick public sentiment baseline for transcript slices | generic social-text model mismatch |
| `j-hartmann/emotion-english-distilroberta-base` | Text emotion | Optional benchmark candidate | strong public emotion baseline for English text | emotion labels are subjective and context-sensitive |
| `SamLowe/roberta-base-go_emotions` | Text emotion | Optional benchmark candidate | aligns with GoEmotions label space for fine-grained text experiments | fine-grained labels may not map cleanly to enterprise review needs |
| `MTEB` | Embeddings | Benchmark reference only | public reference for embedding quality claims | benchmark wins may not transfer to support or sales conversations |
| `BEIR` | Retrieval | Benchmark reference only | public retrieval benchmark context | open-domain retrieval differs from transcript evidence lookup |
| `faster-whisper` | Audio / ASR | Optional | practical offline ASR path when raw audio is available | model downloads and runtime cost are non-trivial |
| `WhisperX` | Audio / ASR | Optional | alignment and timestamp refinement for benchmark runs | setup is heavier and often coupled with diarization assets |
| `pyannote.audio` | Diarization | Optional | speaker diarization for raw audio workflows | may require tokens or gated assets and adds complexity |
| `librosa` | Audio features | Optional | pitch, energy, tempo, and acoustic feature extraction | proxies are not direct emotion truth |
| `torchaudio` | Audio features | Optional | audio preprocessing and tensor pipelines | torch dependency increases install footprint |
| `openSMILE` | Prosody | Optional | mature engineered speech feature extraction | platform setup and interpretation risk |
| `OpenCV` | Video | Optional | frame extraction and basic visual preprocessing | easy to overinterpret visual artifacts |
| `PySceneDetect` | Video | Optional | scene and shot boundary detection for escalation review | convenience feature only, not an inference signal by itself |
| `ffmpeg-python` | Media | Optional | clip extraction, resampling, and media conversion | depends on external `ffmpeg` binaries |
| `MoviePy` | Video | Optional | lightweight clip handling in Python | slower and less robust than direct ffmpeg pipelines |
| `GoEmotions` | Dataset | Benchmark reference only | public text emotion benchmark for transcript-model experiments | domain mismatch with enterprise conversations |
| `MSP-Podcast` | Dataset | Benchmark reference only | useful speech emotion benchmark reference | license and size constraints |
| `IEMOCAP` | Dataset | Benchmark reference only | cross-modal speech and emotion reference set | acted data and licensing limits |
| `MSP-IMPROV` | Dataset | Benchmark reference only | additional SER benchmark context | gated and domain-shifted from production calls |
| `MELD` | Dataset | Benchmark reference only | multimodal conversation benchmark reference | scripted-media domain differs from enterprise conversations |
| `CMU-MOSEI` | Dataset | Benchmark reference only | multimodal sentiment and emotion reference | opinion-video domain mismatch |
| `CMU-MOSI` | Dataset | Benchmark reference only | lightweight historical multimodal benchmark | limited transfer to support QA workflows |
| `Open ASR Leaderboard` | Benchmark reference | Benchmark reference only | public reference for comparing optional ASR candidates | leaderboard context can hide domain mismatch or gating |
| `Open Speech Emotion Recognition Leaderboard` | Benchmark reference | Benchmark reference only | public reference for SER candidate comparisons | leaderboards do not solve privacy or truthfulness concerns |

## Built Now

- deterministic transcript normalization and scoring
- buyer demo pack and focused samples
- metadata-only registries for roadmap models and datasets
- pure-Python benchmark helpers
- import-safe adapter placeholders

## Not Required For Canonical Scoring

- any remote API
- any LLM
- any benchmark dataset download
- any embedding model
- any ASR or video runtime
