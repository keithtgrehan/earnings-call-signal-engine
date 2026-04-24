# Library Evaluation Matrix

| Library / Tool | Purpose | Required vs Optional | Why Useful | Risks / Constraints |
| --- | --- | --- | --- | --- |
| `spaCy` | tokenization, NER, rule patterns | Optional | strong deterministic NLP utilities and matcher support | model downloads can be heavyweight; keep optional |
| `scikit-learn` | TF-IDF and deterministic baselines | Optional | reliable offline baseline features and similarity tooling | adds dependency weight; not needed for basic lexicon rules |
| `rapidfuzz` | deterministic fuzzy matching | Optional | useful for entity or phrase normalization without LLMs | fuzzy matching can overfire if thresholds are loose |
| `Presidio` | PII detection and redaction | Optional | privacy-safe transcript handling | may require domain tuning for false positives |
| `YAKE` | keyword extraction | Optional | lightweight local keyword extraction | not canonical truth for scoring |
| `KeyBERT` | keyword/topic extraction | Optional | can improve analyst review or summaries | embedding dependence makes it heavier than YAKE |
| `textstat` | readability and clarity metrics | Optional | cheap offline proxy for clarity and complexity | readability metrics can be noisy on transcripts |
| `sentence-transformers` | semantic similarity baseline | Optional future baseline only | useful for experiments and local semantic recall | model artifacts are heavier and not canonical scoring |
| `FAISS` | local vector retrieval | Optional | fast local retrieval experiments | retrieval layer should not become canonical truth |
| `Chroma` | local vector store | Optional | simple experimentation for transcript retrieval | keep separate from deterministic scoring |
| `BEIR` | benchmark reference | Benchmark reference only | useful retrieval benchmark context | not a runtime dependency |
| `MTEB` | benchmark reference | Benchmark reference only | benchmark reference for embedding and retrieval evaluation | not a runtime dependency |
| `Ragas` | retrieval / eval framework | Optional future eval only | helpful for future eval workflows | not canonical scoring; can imply LLM-heavy patterns |
| `faster-whisper` | offline ASR | Optional | practical local transcription path | GPU and model downloads may be heavy |
| `WhisperX` | ASR plus alignment | Optional | better alignment and timestamps | heavier setup than transcript-only path |
| `pyannote.audio` | diarization | Optional | better speaker separation | model access and runtime cost can be significant |
| `librosa` | audio features | Optional | useful for simple acoustic review features | not needed for transcript-first scoring |
| `torchaudio` | audio features / I/O | Optional | efficient audio preprocessing | heavyweight if only transcript analysis is needed |
| `openSMILE` | prosody and acoustic features | Optional | mature engineered audio features | extra runtime complexity and platform setup |
| `OpenCV` | frame and keyframe extraction | Optional | useful video preprocessing primitive | not needed unless reviewing flagged moments |
| `PySceneDetect` | shot boundary detection | Optional | efficient keyframe / shot segmentation | only relevant when video is present |
| `ffmpeg` / `ffmpeg-python` | media slicing and conversion | Optional | reliable media conversion and clip extraction | external binary availability can vary |
| `MoviePy` | simple clip handling | Optional | quick lightweight clip operations | slower and less robust than ffmpeg for heavier media work |

## Built Now

- Python stdlib-based transcript normalization
- deterministic lexicon, regex, and turn-structure rules
- tiny local samples and tests

## Not Required For Canonical Scoring

- any remote API
- any LLM
- any embedding model
- any multimodal toolchain
