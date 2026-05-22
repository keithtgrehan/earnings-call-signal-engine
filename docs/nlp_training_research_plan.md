# NLP Training Research Plan

Status: training-readiness scaffold only. Real training is currently gated as `NOT_READY` until human-reviewed gold labels validate, rights records permit training, and sample-size thresholds are met. No production model, fine-tune, model weight, provider API call, or external dataset download is part of this plan.

## Canonical Order

1. Deterministic transcript extraction remains the source of truth.
2. Human-reviewed gold labels are the only default supervised training source.
3. External datasets are benchmark or calibration references by default.
4. Weak labels remain candidate rows and cannot become gold without human adjudication.
5. Retrieval and BYOK reviewers can assist review, but cannot override deterministic outputs.

## Candidate Tasks

- guidance revision classification
- analyst pressure and friction detection
- management hedging and uncertainty detection
- Q&A answer-shift detection
- evidence-span faithfulness
- retrieval ranking quality
- summarization support, with citation and factuality checks

## External Source Posture

`configs/nlp_training_sources.example.yml` tracks ECTSum, FinanceBench, Financial PhraseBank, FiQA, FinQA, ConvFinQA, FinMTEB, FinBen, FLaME, Loughran-McDonald, SEC filing metadata, and project human gold labels. External sources default to `benchmark_only` or `calibration_only`, `training_allowed: false`, `writes_gold: false`, and `weak_labels_can_be_gold: false`.

FinanceBench is useful for open-book financial QA/RAG design, not earnings-call signal gold. ECTSum is summarization support, not guidance-revision gold. Financial PhraseBank and FiQA support sentiment calibration only. FinQA and ConvFinQA support numerical QA design. FinMTEB, FinBen, and FLaME are task taxonomy and benchmark-harness references, not proof of Signal Engine model quality.

## Local Dependency Posture

SQLite is sufficient for local review state and audit records. Parquet/DuckDB may be useful for local analytics when already available, but are not required by the scaffold. BM25 should precede dense retrieval. FAISS, managed vector databases, provider embeddings, and fine-tuning are deferred until rights, provenance, and gold-label gates justify them.

## Readiness Result

If real project gold labels are invalid, insufficient, mixed-provenance, or below the configured threshold, readiness must report `NOT_READY` with exact blockers. Synthetic smoke tests can exercise harness mechanics only and must not produce model-quality claims.
