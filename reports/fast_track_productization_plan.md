# Fast Track Productization Plan

- Build order: transcript ingestion, deterministic evidence, source-quality labels, evaluation, ML benchmark, retrieval benchmark, audio, sparse video.
- Current benchmark: 57 labels with deterministic metrics tracked in the evaluation loop.
- Target quality gate: 100-250 high-quality labels, precision >0.55, F1 >0.55.
- ML role: benchmark and disagreement discovery only.
- Retrieval role: review/search support only.
- Audio phase: after transcript baseline stabilizes.
- Video phase: last and sparse.
- Compute: CPU for deterministic/TF-IDF, T4/L4 for embeddings later, A10/A100 only later for Whisper/audio.
- Useful stack: pandas, sklearn, RapidFuzz, Presidio, sentence-transformers, FAISS, faster-whisper, pyannote, openSMILE.
- Not needed yet: giant transformer finetuning, multimodal hype demos, agents, production vector DB scaling.
