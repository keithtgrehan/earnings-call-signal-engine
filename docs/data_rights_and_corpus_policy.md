# Data Rights and Corpus Policy

Signal Engine is transcript-first, evidence-backed, and rights-cleared by default. A source is usable only when its rights tier, provenance, storage permissions, and evaluation/training permissions are recorded.

## Rights Tiers

- `public_domain`: government or public-domain material. Still preserve attribution, source URL, access date, and fair-access notes.
- `publicly_available`: visible on the web but not automatically reusable. Treat as metadata-only until terms are checked.
- `official_public_terms_checked`: official company or source-hosted material with robots/site terms checked.
- `open_licensed`: license permits stated reuse. Record exact license, version, attribution, and redistribution/training limits.
- `licensed`: use is governed by a contract or explicit permission. Commit/training/evaluation permissions must be explicit.
- `manual_supplied`: supplied by an operator or user. Requires source URL/path, attestation, license notes, and provenance.
- `restricted`: paywalled, login-gated, subscription, vendor, blocked, or unclear-rights material. Raw bodies are blocked.

## Allowed Use

Resource registry rows must declare `allowed_storage`, `allowed_commit`, `allowed_training_use`, `allowed_eval_use`, `raw_body_allowed`, and `metadata_only`.

| Tier | Default storage | Default commit | Training use | Evaluation use |
| --- | --- | --- | --- | --- |
| `public_domain` | metadata; raw only if source rules allow | metadata allowed | no by default | benchmark/context allowed |
| `publicly_available` | metadata-only | metadata only | no | no or benchmark-only after review |
| `official_public_terms_checked` | metadata; raw only after terms allow | metadata by default | review required | review required |
| `open_licensed` | per license | per license | per license | per license |
| `licensed` | per contract | only if explicit | only if explicit | only if explicit |
| `manual_supplied` | local/manual until attested | only if explicit | review required | review required |
| `restricted` | blocked or metadata-only blocked reference | no raw commit | no | no |

Default posture:

- metadata is allowed only when source terms allow it and provenance is preserved;
- raw transcript/audio/video bodies are blocked unless the rights record explicitly allows storage;
- raw restricted transcript-provider bodies must not be copied, committed, trained on, or used as evaluation truth;
- external datasets can support benchmarks or adapters, but cannot become Signal Engine gold labels;
- weak labels remain candidates until a human reviewer accepts them.

## Official and Government Sources

SEC EDGAR/companyfacts should be used through official SEC APIs and developer guidance, including fair-access behavior and a descriptive user agent. The starter adapter is metadata-only and performs no live downloads by default. See official SEC API entry points at `https://data.sec.gov/` and SEC EDGAR API documentation.

Company investor-relations pages are preferred when terms allow transcript use, but each company page still needs a robots/site terms check. Public availability is not enough.

FRED and macro sources require series-level terms checks. FRED API terms note that source-owner rights and restrictions can still apply to individual series, so Signal Engine records macro sources as metadata/context until terms are confirmed.

## Commit Rules

Run `python scripts/check_restricted_artifacts.py --staged` before committing corpus changes. Raw transcripts, audio, video, provider text, and generated label packets should stay out of commits unless a registry record explicitly allows raw-body commit and provenance.

## Gold and Evaluation

Gold labels require human review. External rows and weak labels are never auto-promoted. Evaluation claims must cite the reviewed-label set and state limitations when sample size is small.

## PR 35 External Benchmark Addendum

This addendum records the rights-safe posture for external finance benchmarks discussed during PR 35 research. These resources are benchmark-design references unless a local rights record explicitly permits more. Do not download datasets, acquire raw transcript/audio/video, call paid/provider APIs, train models, or make trading, alpha, causal, or statistical-significance claims from these resources.

Required fields before any local external-resource use:

- `source_url`
- `license`
- `rights_tier`
- `allowed_storage`
- `allowed_commit`
- `allowed_eval_use`
- `allowed_training_use`
- `raw_body_allowed`
- `metadata_only`
- `access_date`
- `provenance_notes`

Default posture: metadata-only, no raw-body storage, no gold promotion, and no canonical evaluation truth. The notes below are review inputs, not permission grants.

### Resource Notes for Review

| Resource | Source | Observed posture | Safe Signal Engine use | Do not do | Local validator or fixture idea |
| --- | --- | --- | --- | --- | --- |
| ECTSum | `https://github.com/rajdeep345/ECTSum` | Repository advertises a GPL-3.0 license and contains dataset/code for bullet-point summarization of long earnings-call transcripts. The related paper describes transcripts paired with Reuters-derived summaries, so raw row rights need extra review beyond the repo license. | Use as a summarization-task design reference: compact bullets, factual consistency, number/entity preservation, and long-transcript evidence coverage. Build synthetic earnings-call snippets and synthetic bullet summaries instead of importing rows. | Do not download, vendor, commit, train on, or evaluate against raw ECTSum transcripts or Reuters-derived summaries unless source rights, downstream license effects, and storage permissions are explicitly recorded. | Synthetic transcript with three cited numerical facts; expected bullets must cite the exact evidence IDs and preserve all numbers exactly. |
| FinanceBench | `https://huggingface.co/datasets/PatronusAI/financebench` | Hugging Face lists the sample as CC-BY-NC-4.0 with 150 rows. Fields include company, document metadata, question, answer, justification, evidence, and document link. The full FinanceBench corpus is larger and not fully open through this page. | Use as an open-book QA/RAG schema reference: question, answer, evidence text, document metadata, reasoning type, and citation validation. Create synthetic SEC-style snippets and synthetic QA rows locally. | Do not treat sample rows as gold labels, do not import evidence strings as canonical corpus, and do not imply coverage of the full closed dataset. | Fixture with one supported answer, one impossible answer, and one arithmetic answer; evaluator checks answer support, evidence-ID hit, and refusal when evidence is missing. |
| Financial PhraseBank | `https://huggingface.co/datasets/takala/financial_phrasebank` | Hugging Face lists CC-BY-NC-SA-3.0. The card describes 4,840 financial-news sentences with positive, negative, or neutral labels and agreement-based configurations. | Use only as a sentiment-calibration reference and lexicon sanity-check target after a local rights record exists. Keep it separate from earnings-call guidance, friction, uncertainty, and gold-label workflows. | Do not merge PhraseBank labels into Signal Engine gold, do not present it as evidence of earnings-call performance, and do not use it for commercial or redistribution-sensitive workflows without license review. | Synthetic financial-news sentence set with positive/negative/neutral labels; validator confirms the adapter reports `benchmark_only` and `writes_gold=false`. |
| FiQA | `https://sites.google.com/view/fiqa/home` | Official challenge page says train/test data are non-commercial and describes aspect-based sentiment plus opinion-based QA over financial text. Source mixture includes microblogs, reports, news, StackExchange, Reddit, and StockTwits. | Use as a task-design reference for aspect sentiment, opinion QA, ranking metrics, NDCG/MRR, and source-mixed rights warnings. Build local synthetic question-answer ranking fixtures. | Do not import social/forum text, do not assume forum/platform reuse rights, and do not use FiQA rows as earnings-call analyst-friction labels. | Synthetic ranking set with one question and five answer candidates; validator computes MRR/NDCG and requires source-type metadata on each candidate. |
| FinQA | `https://github.com/czyssrs/FinQA` | Repository is MIT-licensed and describes JSON entries with pre-text, post-text, table, question, reasoning program, supporting facts, and execution answer. The content is derived from financial-report material, so dataset content rights still need tracking. | Use as a numeric-reasoning schema reference: table-plus-text evidence, supporting-fact IDs, executable calculations, and arithmetic result checking. | Do not treat MIT code licensing as blanket permission for every derived data row; do not train or benchmark on imported rows without rights review. | Synthetic mini 10-K table with revenue, operating income, and margin question; validator checks calculation trace and rejects unsupported operations. |
| ConvFinQA | `https://github.com/czyssrs/ConvFinQA` | Repository is MIT-licensed and describes conversation-level and turn-level financial numerical QA built from FinQA-style data. | Use as a design reference for multi-turn dependencies, carry-forward context, turn-level supporting facts, and conversational arithmetic checks. | Do not treat conversations as earnings-call Q&A friction, guidance-revision labels, or gold labels. Do not import rows without rights review. | Synthetic three-turn conversation where turn 2 depends on turn 1 and turn 3 changes denominator; validator checks context carry-forward and evidence support per turn. |
| FinMTEB | `https://huggingface.co/FinanceMTEB` | Hugging Face organization describes a finance embedding benchmark with 64 finance-domain datasets across seven task families. Individual dataset licenses vary. | Use as an embedding-evaluation taxonomy reference: retrieval, pair classification, STS, clustering, summarization, and multilingual task separation. Keep local tests synthetic and provenance-preserving. | Do not bulk-load FinMTEB datasets or assume a single license applies across tasks. Do not claim dense embeddings are better without local evidence-object recall tests. | Synthetic evidence-object retrieval suite with exact expected evidence IDs; compare BM25, dense, and hybrid only on recall@k/MRR/latency. |
| FinBen | `https://github.com/The-FinAI/FinBen` | Repository says MIT license and presents a financial benchmark suite/harness for LLM evaluation. Component tasks and datasets still require separate rights review. | Use as a harness-organization reference: task registry, metric recording, result file structure, and reproducible benchmark grouping. | Do not add heavy evaluation dependencies, provider model flows, or imported task data until there is a concrete local need and rights record. | Synthetic benchmark registry with two local tasks: evidence citation and numeric reasoning; validator ensures each task declares `writes_gold=false`. |
| FLaME | `https://github.com/gtfintechlab/FLaME` | Repository states CC-BY-NC-SA-4.0 and includes provider/API-key configuration paths plus local Ollama development guidance. | Use as a reporting and prompt/evaluation organization reference. Keep any reviewer mode local, stubbed, or BYOK-gated, with cost/latency logging and no canonical-output authority. | Do not copy provider workflows into default execution, do not require API keys, and do not use FLaME outputs for training or production claims. | Stub reviewer fixture returns fixed JSON for faithfulness, citation quality, and hallucination-risk checks; validator confirms deterministic extraction remains canonical. |
| Open Financial LLM Leaderboard | `https://github.com/finos-labs/Open-Financial-LLMs-Leaderboard` | Repository metadata lists Apache-2.0 and describes financial LLM task categories including information extraction, textual analysis, QA, generation, risk management, forecasting, and decision-making. | Use only as a taxonomy reference for organizing task categories and result cards. Keep Signal Engine limited to evidence-backed transcript analysis and reviewer-support benchmarks. | Do not import forecasting, stock-movement, credit-risk, decision-making, or trading-oriented labels into Signal Engine claims. Do not imply real-world financial readiness from leaderboard-style task names. | Claims-policy validator rejects `alpha`, `trading`, `forecasting`, `decision-making`, and `statistical_significance` report flags unless explicitly allowed by a separate gate. |

Local dependency posture:

- Use SQLite for review queues, audit state, promotion records, and operational state.
- Use Parquet plus DuckDB for local analytics and evaluation reports.
- Use BM25 before dense retrieval.
- Use FAISS only as an optional local or ephemeral dense-retrieval experiment after provenance and reviewed-label gates are met.
- Defer Postgres until multi-user operational need exists.
- Defer Qdrant or managed vector databases until persistent service deployment is justified.
- Do not use provider embeddings, paid APIs, or fine-tuning as part of this posture.

Synthetic validators to implement locally:

- external rows cannot write to gold labels;
- missing rights records block ingestion;
- raw transcript, audio, and video acquisition paths are rejected;
- evidence spans require source ID, offsets, text hash, and provenance;
- guidance revision fixtures cover raised, lowered, maintained, withdrawn, and no-guidance cases;
- neutral Q&A fixtures do not trigger analyst-friction false positives;
- numeric reasoning fixtures verify arithmetic and reject unsupported calculations;
- retrieval outputs evidence IDs and provenance, not unregistered raw bodies;
- summary bullets cannot introduce uncited numbers or entities;
- evaluation reports below label-volume gates emit `not enough data for claims`.

Evaluation design:

- A/B tests compare deterministic baseline outputs against proposed deterministic changes on identical synthetic and reviewed fixtures. Report deltas, precision/recall/F1 only where gold exists, evidence-hit rate, and failure buckets. Do not use significance language.
- Retrieval tests compare BM25 evidence objects, BM25 event chunks, and optional FAISS dense evidence objects. Track recall@k, MRR, exact evidence-ID hit, citation validity, latency, and blocked-source count.
- Multivariate tests may vary chunk type (`evidence`, `event`, `semantic`), ranker (`BM25`, `dense`, `hybrid`), and reviewer mode (`off`, `stub-local`). Accept only configurations that preserve provenance and never override canonical deterministic outputs.
