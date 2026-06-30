# Claude and GLM-5.2 Integration Plan

Date: 2026-06-30

Status: implemented as gated reviewer-support and extraction-benchmark scaffolding.

## Decision

Add a provider-neutral LLM package under `src/signal_engine/llm/` with optional Claude and GLM-5.2 wrappers plus an offline dry-run provider.

The integration is opt-in only. Deterministic transcript analysis remains canonical, weak labels remain suggestions, and human-reviewed labels remain the only gold source.

## Alternatives Considered

Claude via Anthropic API:

- reason to include: strong long-context reviewer candidate
- cost/complexity: paid BYOK, live network calls, provider-specific API shape
- implementation choice: direct standard-library API wrapper, disabled by default

GLM-5.2 via OpenAI-compatible endpoint:

- reason to include: useful provider diversity for fixed-bundle bakeoffs
- cost/complexity: BYOK endpoint configuration and model naming vary by account
- implementation choice: OpenAI-compatible chat-completions wrapper, disabled by default

OpenAI/Gemini/local models:

- reason to defer: not required by this task and would widen the provider surface
- implementation choice: leave provider-neutral interface ready for future adapters

## Guardrails

- `configs/llm.example.yml` defaults to disabled.
- Live calls require both `--live` and `SIGNAL_ENGINE_LLM_LIVE=1`.
- Claude requires `ANTHROPIC_API_KEY`.
- GLM-5.2 requires `ZAI_API_KEY` and `ZAI_BASE_URL`; `GLM_MODEL` can override the model name.
- Outputs can write only under `artifacts/llm/` or `reports/llm/`.
- Signal candidates and evidence judgments are validated against JSON Schema contracts.
- Missing quote-level evidence fails validation.
- API key values are not printed or serialized.
- No model output is used as canonical truth.

## Rollback

Remove the LLM package, scripts, `configs/llm.example.yml`, `schemas/llm_*`, prompts, docs, and Make targets. No deterministic extraction, corpus, review, training, or retrieval code depends on these backends.

## Review Status

Ready for local smoke validation. Manual provider setup is still required for live Claude or GLM-5.2 calls.
