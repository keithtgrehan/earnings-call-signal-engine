# 500-Call Corpus Automation Plan

This is a scaffold-only plan for rights-safe corpus automation. No real acquisition, raw transcript copying, audio/video download, model training, or external API call has happened in this rollout.

## Automation Path

1. Register candidate calls as metadata records.
2. Classify source rights in `configs/resource_registry.example.yml` or a local registry.
3. Fail closed on unknown, paywalled, login-gated, vendor, or unchecked terms.
4. Register manual-local transcript/audio/video file paths without copying raw files into the repo.
5. Build transcript-first artifacts only after rights and provenance are explicit.
6. Export semantic chunks, event-aligned chunks, and evidence objects with provenance and rights fields.
7. Run deterministic extraction before retrieval, reranking, LLM review, or model benchmarks.

## Agent 5 Acquisition/Ingestion Synthesis

The `500` calls are a target universe for planning, not a forced ingest quota. A case can enter the registry as available, blocked, metadata-only, or manual-local without becoming an ingested transcript.

Every candidate case must carry:

- source type: `official_ir`, `sec_edgar`, `licensed_vendor`, `manual_local`, `youtube_metadata`, or `restricted_paywalled_login`;
- transcript, audio, and video availability flags;
- `source_terms_checked`, `robots_checked`, and paywall/login status;
- `raw_body_allowed`, `commit_allowed`, `training_allowed`, and `eval_allowed`;
- `blocked_reason` when any raw use is blocked.

Acquisition is a metadata workflow first:

1. discover candidate call metadata;
2. classify rights;
3. record blocked cases rather than bypassing restrictions;
4. register manual-local files by path/provenance only;
5. permit raw ingest only when the registry explicitly allows it.

No source bypass is allowed. SEC/EDGAR automation must follow fair-access behavior, including conservative rate-limit configuration at or below the current SEC guidance of `10` requests per second. YouTube remains metadata-only unless explicit authorization and terms review are configured.

## Agent 2 Event-Study Synthesis

Event-study work is exploratory packaging for evaluation context, not a trading, alpha, causal, or statistical-significance claim.

Methodology fields to record before any event-study report:

- event date: earnings-call timestamp/date, with after-hours timing noted when available;
- event windows: examples `[-1,+1]`, `[0,+1]`, `[0,+2]`;
- estimation window: configurable prior trading-day range;
- expected return model: market-adjusted, sector-adjusted, or market model;
- controls: earnings surprise, sector return, market return, size/liquidity, and time-of-day where available;
- outputs: abnormal return, cumulative abnormal return, confidence intervals, and exploratory plots/reports.

Failure modes to track:

- confounding company news;
- simultaneous macro shocks;
- noisy after-hours reactions;
- earnings surprise dominating transcript signal;
- small-sample false positives;
- survivorship or ticker-selection bias.

Readiness metrics:

- coverage by event window;
- missing-price-data rate;
- label/event join success;
- CAR distribution;
- correlation with human-reviewed signals;
- baseline comparison against retail/human review only.

No statistical-significance claim is permitted until sample size, event coverage, controls, and human-reviewed label quality are sufficient.

## Built vs Scaffolded

- Built: safe registry validation, restricted artifact checking, retrieval schema validation, event-study metadata validation, benchmark registry validation, BYOK config validation, and Make check targets.
- Scaffolded: YouTube metadata registration, licensed vendor placeholder, manual-local file registration, benchmark registry, BYOK reviewer config.
- Gated: raw ingest, ASR, sparse video review, retrieval/reranking experiments, BYOK LLM review.

## Not Supported

- No live trading, alpha, execution, production ML, or unsupported statistical-significance claims.
- No full-call multimodal brute force.
- No external dataset or weak-label promotion into gold.
