# Signal Engine NLP Asset Scaling Plan

This plan turns the NLP asset registry into staged Signal Engine 2.0 decisions. It does not claim that gated datasets, model weights, or raw corpora are available.

## 1. Assets Useful Immediately

- SEC company tickers and EDGAR metadata for public-company normalization and source discovery.
- Loughran-McDonald as a manual-review finance lexicon candidate.
- rank-bm25 as a future lexical retrieval baseline.
- RapidFuzz for deterministic fuzzy entity/topic matching.
- textstat for lightweight readability/complexity diagnostics.
- Presidio references for privacy and redaction planning.
- Snorkel as a weak-supervision design reference.
- Ragas as a RAG evaluation reference once evidence spans exist.

## 2. Assets Useful After 30 Transcripts

- Financial PhraseBank and FinBERT as benchmark references, not production proof.
- GoEmotions and DAIR emotion references for label taxonomy comparison.
- Qasper and QMSum for evidence-centric QA/summarization evaluation ideas.
- Promptfoo/OpenAI Evals as eval-harness references if LLM sidecars are added.

## 3. Assets Useful After 100 Transcripts

- Small supervised baselines using finance labels and held-out calls.
- all-MiniLM-L6-v2, all-mpnet-base-v2, and BGE references for local embedding experiments.
- BEIR/MS MARCO methodology for retrieval benchmark design.
- Banking77/CLINC150 only as intent-classification shape references.

## 4. Assets Useful After 500 Transcripts

- Model-family comparisons across lexical, embedding, reranker, and classifier baselines.
- FAISS or Chroma only if retrieval scale and latency justify vector infrastructure.
- Audio/ASR and multimodal assets once legally safe media coverage exists.
- Dialogue and meeting summarization corpora for transfer-learning comparisons, with license review.

## 5. Assets For Weak Labeling

- Loughran-McDonald, RapidFuzz, textstat, Snorkel, YAKE/KeyBERT references.
- Use these to propose candidate labels, never as final gold labels.
- Every weak label needs evidence spans and false-positive review.

## 6. Assets For Supervised Training

- Financial PhraseBank, GoEmotions, Banking77, CLINC150, SQuAD, Qasper, and QMSum are references until licensing and local download status are verified.
- Signal Engine training should prioritize user-reviewed earnings-call labels over generic benchmarks.

## 7. Assets For Retrieval / RAG

- Immediate: lexical retrieval and quote-span evaluation.
- Later: sentence-transformers, MiniLM/mpnet/BGE, rank-bm25, Ragas, BEIR methodology.
- Avoid vector DBs until there is a measured recall/latency need.

## 8. Assets For Audio / Multimodal

- Whisper/faster-whisper, Librosa, openSMILE, pyannote, OpenCV, MediaPipe, CMU-MOSEI/MOSI, MELD, and IEMOCAP are roadmap assets.
- Do not use them for claims until legally safe audio/video exists and text-only baselines are stable.

## 9. Assets To Avoid For Now

- Gated or token-protected datasets.
- License-restricted corpora such as Switchboard/IEMOCAP without manual access approval.
- Large raw benchmark downloads.
- Paid API evaluation loops.
- Facial emotion inference claims.

## 10. Licensing Risks

- Kaggle assets often require account access and dataset-specific terms.
- Hugging Face dataset cards vary by config and upstream source.
- Non-commercial licenses can block portfolio/product use.
- Audio/video emotion datasets carry privacy and ethics risk.
- News/summarization datasets may include copyrighted text.

## 11. Recommended Implementation Order

1. Keep deterministic transcript-first extraction unchanged.
2. Use SEC metadata and finance lexicon review for better provenance and weak labels.
3. Build 30-call evidence-span benchmark.
4. Add lexical retrieval baseline and citation metrics.
5. Compare finance/emotion benchmark references only as side evaluations.
6. Add small local embedding experiments after retrieval labels exist.
7. Add supervised models after 100 reviewed transcripts.
8. Add audio/multimodal only after media rights and labels are solved.
