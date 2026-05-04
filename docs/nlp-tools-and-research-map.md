# NLP Tools And Research Map

This map is the evaluation roadmap for Signal Engine 2.0. It tracks practical NLP assets that may help the transcript-first earnings-call signal engine, but it is not product proof. Deterministic extraction remains canonical until reviewed gold labels, error analysis, and benchmark reports justify any model-assisted layer.

No entry below claims production ML, statistical significance, retrieval quality, market correlation, alpha, or validated emotion inference. External datasets, embeddings, rerankers, long-context models, and finance NLP models are candidates for future benchmarking only unless they are explicitly listed under implemented-now.

## What Is Implemented Now

- Transcript-first deterministic extraction remains the canonical scoring path.
- Candidate mining and review-queue generation exist for local committed snippets. See [Signal Label Candidate Mining](signal-label-candidate-mining.md).
- Guided first-50 gold-label review CLI exists: `tools/review_next_batch.py`.
- Reviewed-batch validation exists: `tools/validate_reviewed_batch.py`.
- Guarded gold update workflow exists: `tools/update_gold_from_review.py`.
- Evaluation readiness reporting exists: `tools/report_evaluation_readiness.py`.
- Label coverage report generation exists: `reports/label_coverage.csv`.
- Safe gated evaluation outputs exist: `docs/evaluation/benchmark_status.md`, `docs/evaluation/first_50_benchmark_report.md`, and `reports/evaluation_readiness.json`.
- Deterministic weak-label baselines, corpus validators, model registry checks, training-set registry checks, and NLP tool registry checks exist as local scaffolding and guardrails.
- Lightweight local baseline code exists for guarded TF-IDF plus Logistic Regression / LinearSVC text-signal training, but training is skipped until the gold-label gate passes.

## What Is Scaffolded Only

- Benchmark metrics are gated until reviewed human gold labels exist. With 0 gold labels, precision, recall, F1, uplift, and significance must not be reported.
- Training artifacts are not meaningful until at least 50 accepted gold labels exist, and even then the model card must mark the baseline as weak.
- External NLP dataset connectors and registry rows are tracking surfaces only. They do not mean data has been downloaded, licensed, validated, or mapped into the canonical schema.
- Embedding, reranking, long-context, and transformer references are not part of canonical scoring.
- Emotion and tone datasets are external references only. They do not prove emotion detection on earnings calls, support calls, sales calls, or HR communication.
- Multimodal/audio/video references are out of scope for this text-first evaluation pass unless reviewed local media and segment alignment exist.

## Status Buckets

### Implemented Now

- Transcript-first deterministic extraction.
- First-50 review workflow: `tools/review_next_batch.py`, `tools/validate_reviewed_batch.py`, `tools/update_gold_from_review.py`.
- Evaluation readiness workflow: `tools/report_evaluation_readiness.py`, `reports/label_coverage.csv`, `docs/evaluation/first_50_benchmark_report.md`.
- Safe gated evaluation: `tools/evaluate_gold_labels.py` writes an insufficient-data report instead of computing unsupported metrics.
- Candidate mining and review queues from local committed text artifacts.

### Available Candidate

- [Financial PhraseBank](https://huggingface.co/datasets/takala/financial_phrasebank) for financial sentiment benchmark comparison.
- [FiQA-SA / FiQA sentiment classification](https://huggingface.co/datasets/TheFinAI/fiqa-sentiment-classification) for finance sentiment snippets.
- [Twitter Financial News Sentiment](https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment) for informal finance sentiment contrast.
- [FinBERT](https://huggingface.co/ProsusAI/finbert) for financial sentiment comparison, not canonical scoring.
- [Loughran-McDonald financial sentiment word lists](https://sraf.nd.edu/loughranmcdonald-master-dictionary/) for lexicon comparison.
- [SEC EDGAR APIs](https://www.sec.gov/edgar/sec-api-documentation) for filing metadata and 8-K context.
- [FINOS earnings-call transcript reference](https://huggingface.co/datasets/finosfoundation/EarningsCallTranscript/tree/main) as a possible transcript reference, subject to license and provenance review.
- [GoEmotions](https://arxiv.org/abs/2005.00547), [DailyDialog](https://arxiv.org/abs/1710.03957), [MELD](https://arxiv.org/abs/1810.02508), [EmotionLines](https://arxiv.org/abs/1802.08379), and [EmpatheticDialogues](https://arxiv.org/abs/1811.00207) as external emotion/tone references only.
- [MTEB](https://huggingface.co/mteb) as an external embedding leaderboard reference.
- [sentence-transformers](https://sbert.net/) as a local embedding baseline candidate.
- [OpenAI embeddings](https://platform.openai.com/docs/guides/embeddings), [Voyage embeddings](https://docs.voyageai.com/docs/embeddings), [Cohere Rerank](https://docs.cohere.com/v2/docs/rerank), [Jina rerankers](https://jina.ai/reranker/), [BGE-M3](https://huggingface.co/BAAI/bge-m3), [Qwen3 embeddings](https://huggingface.co/Qwen/Qwen3-Embedding-4B), and [Nomic embeddings](https://huggingface.co/nomic-ai/nomic-embed-text-v1) as later retrieval candidates.

### Requires Manual Or User-Owned Data

- Earnings-call transcript packets, analyst Q&A labels, and company-specific guidance-change labels.
- User-owned support, sales, account-management, and HR/internal communication exports.
- Any CRM, ticketing, call-recording, or transcript data from HubSpot, Salesforce, Zendesk, Intercom, Gong, Chorus, Gainsight, or similar tools.
- Any 30-call benchmark set or holdout split.
- Any audio/video media for multimodal benchmarking.

### Blocked, License-Gated, Or API-Gated

- Commercial earnings-call transcript providers and paid finance data APIs.
- Financial PhraseBank commercial use, because its Hugging Face card lists a non-commercial Creative Commons license.
- API-based embedding and reranking services until keys, privacy constraints, cost controls, and benchmark fixtures exist.
- Large Hugging Face datasets until license, provenance, size, and local-cache rules are explicit.
- Any dataset that carries redistribution restrictions, personal data, or unclear provenance.

### Not Appropriate For Current Phase

- Transformer fine-tuning before stable reviewed gold labels and baseline error analysis.
- Long-context model review before deterministic evidence objects and reviewer rubrics are stable.
- Embedding retrieval bakeoffs before retrieval objects and relevance labels exist.
- Reranker bakeoffs before a lexical or embedding retrieval baseline exists.
- Emotion/tone model claims before mapped labels, domain validation, and human review exist.
- Market-correlation or alpha testing. This repo is not a trading system.

## Decision Matrix

| Asset/tool | Purpose | Relevance to Signal Engine | Data/access requirement | License/risk notes | Implementation effort | Expected value | Current status | Recommended phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Guided first-50 CLI | Human review of candidate snippets | Creates first valid gold labels | Local `data/labeling/next_review_batch.csv` | No auto-acceptance; reviewer decision required | Low | High | Implemented now | Phase 1 |
| Evaluation readiness report | Gate benchmark claims | Prevents unsupported metrics | Local gold labels and reviewed batch | Must not claim metrics below threshold | Low | High | Implemented now | Phase 1 |
| Label coverage CSV | Show class balance | Makes missing labels visible | Local gold labels | Empty file is valid when no gold exists | Low | High | Implemented now | Phase 1 |
| Deterministic extractor | Canonical scoring | Core transcript-first signal engine | Local transcript text | Rule evidence must remain inspectable | Already built | High | Implemented now | Phase 1 |
| sklearn TF-IDF + Logistic Regression | Lightweight baseline | First model comparison after gold labels | >=50 valid gold labels | Weak baseline only below larger benchmark sizes | Low | Medium | Scaffolded only | Phase 2 |
| sentence-transformers local baseline | Local embedding comparison | Later evidence retrieval baseline | Evidence objects and relevance labels | Model license varies by checkpoint | Medium | Medium | Available candidate | Phase 4 |
| Financial PhraseBank | Finance sentiment benchmark | Compare financial sentiment labels | Local/cacheable HF dataset | CC BY-NC-SA; commercial caution | Low-medium | Medium | Available candidate | Phase 3 |
| FiQA-SA | Finance sentiment snippets | Contrast PhraseBank with finance Q&A/social text | HF dataset/local cache | Verify license/provenance before use | Low-medium | Medium | Available candidate | Phase 3 |
| Twitter Financial News Sentiment | Informal finance sentiment | Stress-test finance sentiment mismatch | HF dataset/local cache | Tweets can be noisy and platform-sensitive | Low-medium | Low-medium | Available candidate | Phase 3 |
| FinBERT | Finance sentiment model | Compare against deterministic labels on snippets | HF model weights if used locally | Not proof of guidance/risk detection | Medium | Medium | Available candidate | Phase 3 |
| Loughran-McDonald lexicon | Finance sentiment lexicon | Transparent finance-tone comparison | Local licensed word list | Must cite and respect source terms | Low | Medium | Available candidate | Phase 3 |
| SEC EDGAR / 8-K metadata | Filing context | Align calls with filings and events | Official SEC APIs, no key | Must follow SEC access policy | Medium | Medium | Available candidate | Phase 3 |
| FINOS earnings-call transcript reference | Transcript source reference | Possible corpus expansion | Manual license/provenance review | Upstream terms must be checked | Medium | Medium | Requires manual/user-owned data | Phase 3 |
| User-owned 30-call benchmark | Domain benchmark | First serious evaluation set | Keith-provided transcripts and reviews | Preserve raw transcripts and provenance | Medium | High | Requires manual/user-owned data | Phase 1 before Phase 3 |
| GoEmotions | Emotion label reference | Weak external mapping only | Public dataset / paper | Reddit domain mismatch | Low | Low | Available candidate | Phase 3 reference only |
| DailyDialog | Dialogue act/emotion reference | Conversation-intent reference | Public dataset / paper | Daily-life domain mismatch | Low | Low-medium | Available candidate | Phase 3 reference only |
| MELD | Multimodal emotion reference | Later audio/video emotion benchmark context | Dataset access and media handling | Entertainment-domain mismatch | Medium | Low-medium | Available candidate | Later multimodal phase |
| EmotionLines | Text emotion in dialogue | Emotion taxonomy reference | Public paper/dataset access | Fiction/chat domain mismatch | Low-medium | Low | Available candidate | Phase 3 reference only |
| EmpatheticDialogues | Empathy/tone reference | Support/HR tone comparison | Public dataset access | Generation-focused dataset; not business proof | Low-medium | Low | Available candidate | Phase 3 reference only |
| OpenAI embeddings | API embedding baseline | Later evidence retrieval comparison | API key and privacy review | API-gated; cost and data controls required | Medium | Medium | API-gated | Phase 4 |
| Voyage embeddings | API embedding baseline | Later evidence retrieval comparison | API key and privacy review | API-gated; cost and data controls required | Medium | Medium | API-gated | Phase 4 |
| Cohere embeddings/rerank | API retrieval/reranking | Later reranker bakeoff | API key and relevance labels | API-gated; privacy review required | Medium | Medium | API-gated | Phase 5 |
| Jina embeddings/rerank | API/local retrieval/reranking | Later reranker bakeoff | API or local model setup | License and cost vary by model/API | Medium | Medium | Available/API-gated candidate | Phase 5 |
| BGE / Qwen / Nomic local embeddings | Local embedding candidates | Later retrieval bakeoff without external API | Local model weights and hardware | License/model size review needed | Medium | Medium | Available candidate | Phase 4 |
| Long-context review models | Human review assist | Later second-pass evaluator only | Stable evidence objects and prompts | API/local costs; hallucination risk | Medium-high | Medium | Not appropriate now | Phase 6 |
| Optional ML model training | Model-assisted signal classification | Only after gold labels stabilize | Sufficient train/dev/test split | Overfitting risk at low label counts | Medium-high | Medium | Not appropriate now | Phase 7 |

## Recommended Sequencing

### Phase 1: Gold Labels Plus Deterministic Evaluation

1. Review the first 50 candidate rows with `python tools/review_next_batch.py --reviewer Keith`.
2. Validate the reviewed batch with `python tools/validate_reviewed_batch.py`.
3. Promote only accepted or edited rows with `python tools/update_gold_from_review.py`.
4. Generate readiness and coverage outputs with `python tools/report_evaluation_readiness.py`.
5. Keep deterministic extraction canonical and record every rejection/unclear row.

### Phase 2: Local Baselines

1. Train TF-IDF plus Logistic Regression only after the >=50 accepted gold-label gate passes.
2. Keep LinearSVC/SGD variants as local comparisons.
3. Report weak-baseline status until labels are larger and balanced.

### Phase 3: Financial NLP Benchmark Comparison

1. Compare deterministic labels against Financial PhraseBank, FiQA-SA, Twitter Financial News Sentiment, FinBERT, and Loughran-McDonald only after local gold labels exist.
2. Keep external labels separate from human gold.
3. Use SEC EDGAR / 8-K metadata only as context, not as a proxy label.

### Phase 4: Retrieval Objects Plus Embedding Benchmark

1. Define evidence-object schema and relevance labels.
2. Build lexical/BM25 baseline first.
3. Compare local sentence-transformers, BGE, Qwen, Nomic, and API embeddings only after retrieval labels exist.

### Phase 5: Reranking

1. Run rerankers only after baseline retrieval has measurable recall/precision.
2. Compare Cohere, Jina, BGE/Qwen reranker candidates against the same relevance set.
3. Track latency and cost separately from quality.

### Phase 6: Long-Context Review

1. Use long-context models only as reviewer aids against locked evidence bundles.
2. Require prompt/version logging and human acceptance.
3. Do not let long-context outputs become canonical labels.

### Phase 7: Optional ML Model Training

1. Train only when train/dev/test splits and error-analysis loops are stable.
2. Preserve deterministic rules as baseline and fallback.
3. Publish model cards that disclose label counts, class balance, skipped gates, and failure modes.

## Do Not Do Yet

- Do not run embeddings before evidence objects and relevance labels exist. Otherwise retrieval quality cannot be measured.
- Do not add rerankers before a retrieval baseline exists. A reranker cannot fix an unmeasured candidate pool.
- Do not use long-context models before the reviewer rubric and evidence bundle format are stable.
- Do not fine-tune transformers or train heavier ML before gold labels and error analysis are stable.
- Do not use external finance or emotion labels as gold for this project.
- Do not run market-correlation tests, alpha tests, or stock-return claims.
- Do not download large datasets, add API keys, or commit model weights.

## Safe Experiment Backlog

- TF-IDF plus Logistic Regression baseline after >=50 valid accepted gold labels.
- FinBERT comparison on financial sentiment snippets after local gold labels exist.
- Loughran-McDonald lexicon comparison against deterministic evidence and human-reviewed labels.
- GoEmotions mapping only as a weak external reference, never as gold.
- Embedding retrieval bakeoff on evidence objects after retrieval schema and relevance labels exist.
- Reranker bakeoff only after lexical or embedding retrieval baseline exists.
- Sentence-transformers local baseline before any paid/API embedding run.
- SEC EDGAR / 8-K metadata enrichment after transcript provenance and call identifiers are stable.

## Source Links

- Financial PhraseBank: <https://huggingface.co/datasets/takala/financial_phrasebank>
- FiQA sentiment classification: <https://huggingface.co/datasets/TheFinAI/fiqa-sentiment-classification>
- Twitter Financial News Sentiment: <https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment>
- FinBERT: <https://huggingface.co/ProsusAI/finbert>
- SEC EDGAR APIs: <https://www.sec.gov/edgar/sec-api-documentation>
- FINOS EarningsCallTranscript reference: <https://huggingface.co/datasets/finosfoundation/EarningsCallTranscript/tree/main>
- Loughran-McDonald word lists: <https://sraf.nd.edu/loughranmcdonald-master-dictionary/>
- GoEmotions: <https://arxiv.org/abs/2005.00547>
- DailyDialog: <https://arxiv.org/abs/1710.03957>
- MELD: <https://arxiv.org/abs/1810.02508>
- EmotionLines: <https://arxiv.org/abs/1802.08379>
- EmpatheticDialogues: <https://arxiv.org/abs/1811.00207>
- MTEB: <https://huggingface.co/mteb>
- sentence-transformers: <https://sbert.net/>
- OpenAI embeddings: <https://platform.openai.com/docs/guides/embeddings>
- Voyage embeddings: <https://docs.voyageai.com/docs/embeddings>
- Cohere rerank: <https://docs.cohere.com/v2/docs/rerank>
- Jina rerank: <https://jina.ai/reranker/>
- BGE-M3: <https://huggingface.co/BAAI/bge-m3>
- Qwen3 embeddings: <https://huggingface.co/Qwen/Qwen3-Embedding-4B>
- Nomic embeddings: <https://huggingface.co/nomic-ai/nomic-embed-text-v1>
