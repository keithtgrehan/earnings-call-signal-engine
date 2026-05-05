# Next Best Actions

- gold_label_count: `0`
- current_phase: `<50 labels`

## Allowed Now

- deterministic_tools

## Blocked

- local ML: requires >=50 gold labels
- embeddings: requires >=100 gold labels or explicit retrieval experiment mode
- external datasets: requires local verified dataset or safe_local flag
- rerankers: requires embedding baseline first
- long-context: requires completed evaluation first

## Top 5 Recommended Experiments

- `deterministic_baseline` (allowed): Run canonical deterministic baseline/status loop.
- `lexicon_comparison` (allowed): Compare Loughran-McDonald-style lexicon coverage if lexicon is local.
- `local_ml_baseline` (blocked): TF-IDF + Logistic Regression benchmark.
- `embedding_benchmark` (blocked): Local sentence-transformers evidence-span retrieval.
- `dataset_comparison` (blocked): Compare locally present dataset label distribution.

## High-Priority Registry Inputs

- `loughran_mcdonald_lexicon`: Loughran-McDonald Master Dictionary (manual_required)
- `financial_phrasebank`: Financial PhraseBank (manual_required)
- `prosus_finbert`: ProsusAI FinBERT model card (skipped)
- `sec_company_tickers`: SEC company tickers JSON (downloaded)
- `sec_edgar_submissions_api`: SEC EDGAR submissions API (skipped)
- `public_earnings_call_dataset_candidates`: Public earnings-call transcript dataset candidates (gated)
- `company_8k_press_release_metadata`: Company 8-K / press release metadata sources (skipped)
- `goemotions`: GoEmotions (skipped)
- `qasper`: Qasper (manual_required)
- `beir`: BEIR (manual_required)

## Enforcement Notes

- Deterministic outputs remain canonical truth.
- Embeddings and datasets are benchmark layers only.
- No silent dataset downloads or paid APIs are allowed.
- Weak labels are never auto-promoted.
