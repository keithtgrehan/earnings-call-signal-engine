# ChatGPT Control Room LLM Status Handoff

This note summarizes what has been implemented on branch `ai/llm-tooling-router-eval-stack` for the optional LLM reviewer-support and extraction-benchmarking layer.

## Current Status

- Branch: `ai/llm-tooling-router-eval-stack`
- Remote branch: `origin/ai/llm-tooling-router-eval-stack`
- Main purpose: add disabled-by-default LLM backend scaffolding for reviewer support and benchmark comparison only.
- Canonical architecture remains deterministic-first.
- Human-reviewed labels remain the only canonical gold source.
- Weak labels and LLM outputs remain suggestions only.
- No live LLM calls run in tests, CI, or Make targets by default.

## Commits Created

- `9227ba6 feat: add llm router safety scaffolds`
- `7274141 docs: document llm router and eval setup`

## Implemented

- Added provider-neutral LLM package under `src/signal_engine/llm/`.
- Added optional providers:
  - `dry_run` offline fake provider for tests and local smoke checks.
  - Claude provider using `ANTHROPIC_API_KEY`.
  - GLM-5.2 provider through an OpenAI-compatible endpoint using `ZAI_API_KEY`, `ZAI_BASE_URL`, and `GLM_MODEL`.
  - Generic OpenAI-compatible provider using `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`.
- Added LiteLLM router scaffold with dry-run support and fail-closed behavior when optional dependencies or live flags are missing.
- Added strict JSON validation for:
  - signal-candidate outputs
  - evidence-judge outputs
- Added secret redaction helpers so API-key-like values are not printed in provider or router messages.
- Added LLM artifact safety checks that reject:
  - canonical-output markers
  - gold-label promotion markers
  - secret-like strings
- Added example configs and schemas:
  - `configs/llm.example.yml`
  - `configs/opik.example.yml`
  - `schemas/llm_config.schema.json`
  - `schemas/llm_signal_candidates.schema.json`
  - `schemas/llm_evidence_judge.schema.json`
- Added prompts:
  - `prompts/earnings_signal_extraction.v1.md`
  - `prompts/evidence_judge.v1.md`
  - `prompts/reviewer_packet_assist.v1.md`
- Added scripts:
  - `scripts/validate_llm_config.py`
  - `scripts/run_llm_fixture_smoke.py`
  - `scripts/run_llm_bakeoff.py`
  - `scripts/check_llm_artifacts.py`
  - `scripts/check_opik_config.py`
- Added Make targets:
  - `llm-safe-check`
  - `llm-router-check`
  - `llm-claude-smoke`
  - `llm-glm52-smoke`
  - `llm-bakeoff`
  - `promptfoo-check`
  - `opik-check`
- Added Promptfoo scaffold under `evals/promptfoo/`.
- Added Opik disabled-by-default config scaffold.
- Updated LLM docs and README guidance.

## Safety Guarantees Preserved

- LLM usage is opt-in only.
- Default config is disabled and uses `dry_run`.
- Live calls require both:
  - `SIGNAL_ENGINE_LLM_LIVE=1`
  - explicit `--live`
- LLM outputs are not canonical truth.
- LLM outputs do not auto-promote gold labels.
- Restricted transcript bodies are not added or downloaded by the LLM layer.
- Tests do not make live network calls by default.
- LLM artifact outputs are constrained to `artifacts/llm/` or `reports/llm/`.
- Output payloads must include provenance references and quote-level evidence.

## Validation Completed

- `python -m py_compile $(find scripts src tools -name "*.py")` passed.
- `python -m pytest` passed with `523 passed`.
- `make llm-safe-check` passed with dry-run provider and `calls=False`.
- `make llm-router-check` passed with dry-run LiteLLM path and `calls=False`.
- `make corpus-safe-check` passed.
- `make training-plan-check` passed with expected `NOT_READY`.
- `make training-readiness` completed with expected `status: not_ready` and `training_attempted: false`.
- `ruff check .` passed.
- `git status` was clean before the branch was pushed.

## How To Run Live Smokes Manually

Claude smoke:

```bash
ANTHROPIC_API_KEY=... \
CLAUDE_MODEL=<claude-model> \
SIGNAL_ENGINE_LLM_LIVE=1 \
LLM_LIVE_ARGS=--live \
make llm-claude-smoke
```

GLM-5.2 smoke:

```bash
ZAI_API_KEY=... \
ZAI_BASE_URL=<openai-compatible-base-url> \
GLM_MODEL=glm-5.2 \
SIGNAL_ENGINE_LLM_LIVE=1 \
LLM_LIVE_ARGS=--live \
make llm-glm52-smoke
```

Promptfoo scaffold:

```bash
promptfoo eval -c evals/promptfoo/llm_signal_extraction.yaml
```

## Remaining Manual Setup

- Install optional dependencies only where needed:
  - LLM providers/router: `litellm`, `anthropic`, `openai`
  - evaluation/observability: `promptfoo`, `opik`
- Provide BYOK environment variables locally. Do not commit keys.
- Open the pull request from:
  - `https://github.com/keithtgrehan/earnings-call-signal-engine/pull/new/ai/llm-tooling-router-eval-stack`
- Run live smokes only from a trusted local environment with explicit live flags.

