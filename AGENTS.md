# Signal Engine 2.0 Agent Instructions

You are working on Signal Engine 2.0, a transcript-first earnings-call signal engine.

This repository is not a trading system, alpha engine, or live execution platform. Build a narrow, reliable, reviewable earnings-call analysis system for capstone/demo use with deterministic extraction, evidence spans, reproducibility, human review, evaluation, retrieval, long-context review, selective multimodal audit, and future graph reasoning represented in the repo.

Every major layer must have concrete repo representation:
- documented purpose
- schema or contract
- CLI entry point, script, stub, or adapter where appropriate
- tests or validation checks
- clear status: built / scaffolded / gated / planned
- known limitations
- next implementation task

## Core Product Goal

Retail traders struggle to extract reliable signals from earnings-call transcripts quickly. This project helps identify guidance changes, tone shifts, uncertainty, reassurance language, and analyst-management friction from earnings-call transcripts.

## Non-Negotiable Principles

- Transcript-first remains canonical.
- Deterministic extraction is the source of truth.
- LLMs may assist as reviewers, critics, or synthesis layers, but must not replace extraction logic.
- Evidence spans and provenance must be preserved end to end.
- Distinguish clearly between built functionality, scaffolded functionality, gated functionality, and future roadmap.
- Do not claim alpha.
- Do not claim live trading automation.
- Do not claim statistical significance unless backed by sufficient evaluation data.
- Do not auto-promote weak/machine labels to gold labels.
- Machine labels are candidates only.
- Human-reviewed gold labels are required for evaluation claims.
- Keep outputs practical, evidence-backed, and capstone/demo safe.
- Prefer measured improvement over shiny tooling.

## Keith Challenge Protocol

You are not a passive executor. If Keith asks for something that is risky, premature, overbuilt, stale, legally questionable, weakly justified, or likely to waste time, challenge it clearly before implementing.

When challenging a decision, return:
1. Concern
2. Why it matters
3. Safer or stronger alternative
4. What you recommend doing now
5. What can be deferred
6. What Keith must explicitly approve if he still wants the risky path

Examples of decisions to challenge:
- using LLMs before deterministic extraction is stable
- adding agents before tests, schemas, and evaluation gates are solid
- using retrieval to hide weak extraction
- adding graph/KAG before retrieval failure is proven
- scraping sources aggressively
- committing raw transcripts/audio/video
- treating external datasets as gold labels
- claiming model quality without enough reviewed labels
- adding paid APIs or heavy dependencies without optional gating
- overfitting the repo for a demo instead of building reusable workflows
- prioritizing UI polish over corpus/evaluation readiness
- chasing new models without benchmark tasks

## Execution Priority Order

1. Harden deterministic extraction.
2. Improve repo/test/proof hygiene.
3. Ensure every strategic layer has repo representation, even if scaffolded.
4. Scale real earnings-call corpus with strict metadata and provenance.
5. Build human review/gold-label workflow.
6. Build evaluation framework and retail baseline comparison.
7. Add retrieval over evidence objects, event-aligned chunks, and semantic chunks.
8. Add long-context LLM review as bounded reviewer/sanity-check layer.
9. Add audio/video only as selective flagged-moment audit.
10. Add graph/KAG only if retrieval fails on real structured entity/time problems.

## Required Repo Layers

### Layer 1 - Deterministic Core

Must be implemented or actively hardened.

Scope:
- transcript parsing
- section detection
- guidance extraction
- guidance revision matching and direction
- Q&A structure
- analyst pressure/friction markers
- uncertainty/reassurance markers
- transcript-backed evidence spans
- runtime/status observability
- manifest validation
- evaluation packaging

### Layer 2 - Human Review and Gold Labels

Must be represented with schemas, docs, review packets, import/export paths, and validation.

Scope:
- review queue
- candidate labels
- reviewer instructions
- calibration batches
- adjudication workflow
- inter-rater agreement tracking
- gold label validation
- anti-contamination guardrails
- audit trail
- promotion safeguards

### Layer 3 - Evaluation and Retail Baseline

Must be represented with gated metrics, baseline docs, and validation.

Scope:
- retail baseline comparison
- speed to useful summary
- agreement with gold labels
- evidence citation quality
- false-positive analysis
- false-negative analysis
- confusion matrix where applicable
- event-study packaging where available
- statistical-significance gating
- clear "not enough data yet" reports

### Layer 4 - Corpus and Acquisition

Must be represented with manifest schemas, source-quality flags, acquisition docs, and safe tooling.

Scope:
- canonical corpus manifest
- source provenance
- source reliability scoring
- transcript availability flags
- audio/video availability flags
- blocked cases
- quality flags
- promotion eligibility
- source discovery
- no aggressive scraping
- no paywall bypassing
- no raw bulky data commits

### Layer 5 - Retrieval Foundation

Must be represented now, even if partially scaffolded.

Scope:
- retrieval object schemas
- evidence objects
- event-aligned chunks
- semantic chunks
- corpus export path
- embedding adapter interface
- reranker adapter interface
- retrieval eval set
- recall@k / MRR / latency / cost tracking
- provenance preservation tests

Retrieval priority:
1. evidence objects first
2. event-aligned chunks second
3. semantic chunks last

Do not use retrieval to hide weak extraction.

### Layer 6 - Long-Context Review

Must be represented now as bounded review-bundle infrastructure, even if provider execution is optional/gated.

Scope:
- per-call case bundle builder
- prompt pack
- reviewer model adapter interface
- faithfulness scoring
- citation quality scoring
- hallucination-risk checks
- latency/cost tracking
- comparison across model providers only on fixed bundles

Long-context models are reviewers, not canonical extractors.

### Layer 7 - Selective Multimodal Audit

Must be represented now with schemas, escalation rules, and cost guardrails, even if full processing is gated.

Scope:
- flagged-moment escalation schema
- audio audit package schema
- video/keyframe audit package schema
- ASR metadata path
- diarization/timestamp/confidence fields where available
- pause/prosody placeholders where available
- sparse keyframe/clip metadata
- no full webcast brute-force processing by default
- cost/runtime tracking

Transcript remains canonical.

### Layer 8 - Graph/KAG Readiness

Must be represented as a decision record and minimal schema sketch only unless retrieval failure is proven.

Scope:
- graph trigger conditions
- entity/time relationship pain points
- narrow candidate graph schema
- evidence-linked nodes/edges
- explicit "do not build yet unless justified" guardrail

## Tooling and Dataset Radar

Maintain a repo-level tooling and dataset radar document or registry. It must track candidate tools, datasets, models, status, license/terms risk, implementation cost, expected value, and recommendation.

The radar must include at least:

Human review / annotation:
- Argilla
- Label Studio as fallback/comparison
- lightweight local JSONL/CSV review queue if external tooling is too heavy

Local analytics / metadata:
- DuckDB
- SQLite first for operational state
- Postgres later only if needed
- Parquet as preferred analytical artifact format

Financial data / metadata:
- SEC EDGAR submissions/company facts APIs
- OpenBB Platform where useful and legally permitted
- Financial Modeling Prep only if API terms/costs are acceptable
- official investor relations sources preferred for transcripts
- reputable full-transcript sources only where permitted

NLP / financial-language assets:
- Loughran-McDonald financial sentiment dictionary
- Financial PhraseBank
- MAEC earnings-call dataset
- GoEmotions
- SEC filings / 8-K / 10-Q / 10-K metadata
- project-created real-call gold labels as the highest-value training/eval data

Retrieval / vector tooling:
- LanceDB
- FAISS
- Chroma only if useful for quick local prototyping
- Qdrant only if persistent service deployment is justified
- hybrid search before pure vector-only claims
- reranking before more complex orchestration

Embedding candidates:
- OpenAI text-embedding family
- Voyage embeddings
- Cohere Embed
- Jina embeddings
- strong local sentence-transformer baseline where useful

Reranking candidates:
- Cohere Rerank
- Jina reranker
- local cross-encoder baseline if practical

Long-context / reviewer model slots:
- OpenAI current best long-context model available to the user
- Anthropic current best long-context model available to the user
- Google current best long-context model available to the user
- local/open model only if it can be benchmarked honestly

Do not hardcode model hype into claims. Use adapters and benchmark results.

## Bleeding-Edge Requirement

For tools, datasets, and models, do not assume the current repo choices are optimal. Before adding or expanding a major layer, check whether a better current option exists.

For any major tool/model/dataset decision, produce:
1. current choice
2. stronger alternative candidates
3. why each candidate matters
4. cost / complexity / terms risk
5. whether it should be implemented now, scaffolded, or rejected
6. final recommendation

This does not mean using every tool blindly. It means no relevant tool class should be ignored without a documented reason.

## Implementation Style

- Prefer small, safe, reviewable diffs.
- Prefer tests and docs with each meaningful implementation.
- Prefer deterministic code over LLM-dependent logic.
- Prefer simple Python modules and CLI workflows.
- Avoid over-abstraction.
- Avoid large framework rewrites unless explicitly requested.
- Do not introduce paid APIs, heavy installs, or vendor lock-in unless gated and optional.
- Optional provider integrations must not break default local/core tests.
- Keep default path lightweight and reproducible.
- Add interfaces before committing to vendors.
- Add registries before heavy downloads.
- Add validation before claims.

## Repository Hygiene

- Never force-push.
- Never hard-reset.
- Never merge to main unless explicitly asked.
- Never delete user work unless explicitly approved.
- Never commit raw transcripts, audio, video, secrets, API keys, caches, or bulky runtime artifacts.
- Respect .gitignore and add missing ignores where needed.
- Keep generated artifacts clearly separated from source.
- If repo state is dirty, classify changes before editing.
- If unrelated local changes exist, avoid touching them.
- If uncertain, create a safety branch or limit work to docs/tests/scaffolds.

## Branch and PR Behavior

Use focused branches named like:
- codex/deterministic-core-hardening
- codex/gold-review-workflow
- codex/evaluation-readiness
- codex/corpus-intake-manifest
- codex/retrieval-object-schema
- codex/tooling-dataset-radar
- codex/long-context-review-bundles
- codex/selective-multimodal-audit

Make one logical commit per task.

PR descriptions must include:
- what changed
- why it changed
- validation commands run
- known limitations
- files intentionally not touched
- risk notes
- whether the work is implemented, scaffolded, or gated

## Validation Requirements

Before finalizing any implementation, run the strongest available lightweight validation:
- `python -m py_compile $(find src tools scripts -name "*.py")`
- `pytest`
- `ruff check .`
- `python scripts/check_markdown_links.py`, if present
- project-specific validators if relevant:
  - validate corpus manifest
  - validate gold labels
  - validate evaluation outputs
  - validate retrieval object schemas
  - validate review queue exports/imports
  - validate generated reports
  - run targeted tests for modified modules

If a command fails:
- Report exact failing command.
- Explain likely cause.
- Fix if within scope.
- If not fixable, leave clear next step and do not claim success.

For docs-only changes, do not run the full test suite unless the docs change also modifies code, config, generated data, or test expectations.

## Documentation Expectations

Update docs whenever behavior changes.

Docs must separate:
- built now
- implemented but limited
- scaffolded
- gated
- planned
- explicitly not supported
- known limitations

README and docs should avoid hype. Use clear capstone/demo-safe language.

## Evaluation Rules

- Do not compute or report meaningful model quality unless gold labels meet the required threshold.
- If insufficient gold labels exist, evaluation must be gated/skipped with an explicit report.
- Report early metrics as early/non-production only.
- Use retail baseline comparison as evaluation framing, not as trading proof.
- Event-study work may measure correlation/market reaction, but must not imply causality or alpha.
- Always include false positives, false negatives, evidence citation quality, and reviewer agreement where possible.

## Gold Label and Review Rules

- Weak labels and model labels are candidates only.
- Human adjudication is required for gold labels.
- Preserve reviewer, timestamp, confidence, notes, evidence_text, signal_type, speaker_role, transcript_section, topic, and direction fields where applicable.
- Avoid accidental gold-label contamination.
- Review exports/imports must be auditable and reversible.
- Promotion to gold requires explicit human-reviewed status.
- Calibration batches must exist before scaling review.
- Inter-rater agreement should be tracked once multiple reviewers exist.

Preferred label concepts:
- guidance_revision
- guidance_direction
- analyst_pressure
- management_hedging
- uncertainty
- reassurance
- opportunity_commitment
- risk_friction
- neutral / no_signal

## False-Positive Guardrails

- Generic optimism is not guidance revision.
- Generic caution is not analyst pressure.
- Uncertainty wording alone is not a risk signal without context.
- A summary paragraph is not evidence unless tied to transcript span.
- Machine-generated text cannot become evidence without transcript support.
- External datasets can support experiments but cannot replace project-specific gold labels.

## Corpus and Intake Rules

- Every case should have metadata completeness status.
- Every source should preserve provenance.
- Track blocked cases explicitly.
- Prefer quality and provenance over volume.
- Target 30-50 manually reviewed real calls first.
- Later target 100-150 calls with balanced sectors, revision/no-revision mix, clean/messy transcript mix, and Q&A pressure diversity.
- Use external datasets to benchmark and pretrain ideas, not as a substitute for reviewed earnings-call labels.

## Acquisition Rules

- Prefer official investor relations sources where possible.
- Otherwise use reputable full-transcript sources.
- Respect robots/paywalls/site rules.
- Do not scrape aggressively.
- Validate transcript markers before accepting a source.
- Do not lower quality standards just to increase corpus size.
- Log source reliability and acquisition status.

## LLM and Provider Rules

- Core repo must work without paid provider keys.
- Provider integrations must be optional.
- Add config-driven adapters only where useful.
- Benchmark providers only on fixed tasks.
- Do not add every new model just because it is new.
- Long-context models are reviewers/synthesizers only.
- Their outputs must be scored for faithfulness, evidence citation quality, hallucination risk, latency, and cost.

## Training and Fine-Tuning Rules

- Do not fine-tune before gold label quality is sufficient.
- Do not train on contaminated labels.
- Do not mix weak labels and gold labels without explicit fields.
- Track dataset version, row count, label source, reviewer status, and hash.
- Every training/eval split must be reproducible.
- Prefer baselines first:
  1. deterministic rules
  2. lexicon features
  3. classical ML baseline
  4. embedding/retrieval baseline
  5. LLM reviewer
  6. fine-tuning only if justified

## Required Decision Records

Create or update lightweight decision records for:
- tool choices
- dataset choices
- model choices
- architecture changes
- evaluation thresholds
- rejected options
- Keith-overridden recommendations

Each decision record should include:
- date
- decision
- alternatives considered
- reason
- risk
- rollback path
- review status

## Codex Output Format

At the end of every task, return:

1. Summary
- concise description of what changed

2. Files changed
- bullet list with purpose of each file

3. Validation
- commands run
- pass/fail result

4. Challenge notes
- any questionable assumptions
- any stronger alternatives
- anything Keith should reconsider

5. Risks / limitations
- anything not proven
- any assumptions
- any skipped validation

6. Next recommended action
- one concrete next step

When asked for planning only:
- Do not edit files.
- Return a phased plan.
- Include exact files likely to change.
- Include validation commands.
- Include rollback/safety notes.
- Include challenge notes if the request is premature or suboptimal.

When asked for implementation:
- Inspect repo first.
- Classify dirty state.
- Avoid unrelated changes.
- Implement the smallest safe version.
- Add/adjust tests.
- Update docs.
- Validate.
- Commit only if explicitly requested or if the task clearly asks for GitHub/PR completion.

## Tone and Style for Generated Docs

- concise
- direct
- evidence-backed
- no generic AI hype
- no unsupported investor/trading claims
- clear built vs planned separation
- clear warnings when something is scaffolded but not proven

## Final Operating Rule

Do not try to become an everything-AI system.

Become a narrow, hard, reviewable earnings-call analysis system with:
- deterministic extraction first
- human review and gold labels
- evaluation gates
- retrieval over evidence-backed objects
- long-context review as a bounded critic
- selective multimodal audit
- graph reasoning only when justified by proven retrieval/entity-time failure

Make sure every layer is represented in the repo now through contracts, docs, validation, and safe scaffolds, even if full implementation is gated.
