# Claude + GLM-5.2 Integration Plan

## Objective

Add Claude and GLM-5.2 as optional BYOK model backends for reviewer support, extraction benchmarking, structured evidence generation, and coding/repo automation without weakening the existing deterministic-first architecture.

The system must remain transcript-first, provenance-backed, and gated. LLM outputs are suggestions only. They must never overwrite deterministic outputs, auto-promote gold labels, create trading claims, or bypass source-rights policies.

## Target roles

### Claude

Use Claude for:

- high-quality adjudication support
- reviewer packet summarization
- schema critique
- repo-level implementation work
- final qualitative review of difficult cases
- CI/code-review assistant workflows

### GLM-5.2

Use GLM-5.2 for:

- long-context transcript extraction
- bulk weak-label suggestion generation
- quote-level signal extraction
- cheap model comparison
- local/self-hosted experimentation
- repo-level coding agent experiments

## Required architecture

Add a provider-neutral model layer:

```text
src/signal_engine/llm/
  __init__.py
  config.py
  providers.py
  schemas.py
  prompts.py
  clients/
    __init__.py
    anthropic_client.py
    openai_compatible_client.py
  tasks/
    __init__.py
    extract_signals.py
    review_packet_assist.py
    judge_evidence.py
```

Provider interface:

```python
class LLMProvider(Protocol):
    def complete_json(self, *, task: str, system: str, prompt: str, schema: dict, max_tokens: int) -> dict: ...
```

Environment variables:

```bash
ANTHROPIC_API_KEY=
ZAI_API_KEY=
ZAI_BASE_URL=https://api.z.ai/api/paas/v4
GLM_MODEL=glm-5.2
CLAUDE_MODEL=claude-opus-4-8
SIGNAL_ENGINE_LLM_PROVIDER=none|claude|glm52|openai_compatible
SIGNAL_ENGINE_LLM_MODE=dry_run|suggest|judge|benchmark
```

Config file:

```yaml
llm:
  enabled: false
  provider: none
  mode: dry_run
  allow_network: false
  max_calls: 10
  max_cost_usd: 5.00
  require_quote_evidence: true
  require_json_schema: true
  write_outputs: false
  output_dir: artifacts/llm
  providers:
    claude:
      model: claude-opus-4-8
    glm52:
      model: glm-5.2
      base_url: https://api.z.ai/api/paas/v4
```

## Free tools to add

Use these three first:

1. `promptfoo` — prompt/model regression tests and provider comparison.
2. `opik` — open-source LLM tracing/evaluation observability.
3. `LiteLLM` — provider routing, OpenAI-compatible access, retries, and cost controls.

Keep existing tools already present:

- `pytest`
- `ruff`
- `deepeval`
- `argilla`
- `duckdb`
- `faiss-cpu`

## Implementation phases

### Phase 1 — Safe scaffolding

Add:

- provider-neutral LLM interface
- config loader
- JSON schema validation
- dry-run mode
- redaction of secrets in logs
- no network calls by default
- test fixtures only

Acceptance:

```bash
make capstone-ci
make corpus-safe-check
make training-readiness
```

### Phase 2 — Claude backend

Add:

- Anthropic client wrapper
- strict JSON response parser
- retry/failure handling
- no auto-promotion
- artifact manifest output

Create CLI:

```bash
signal-engine llm extract --provider claude --input tests/fixtures/tiny_realistic_earnings_excerpt.txt --dry-run
signal-engine llm judge --provider claude --candidates artifacts/llm/candidates.jsonl --dry-run
```

### Phase 3 — GLM-5.2 backend

Add:

- OpenAI-compatible client wrapper for Z.ai/GLM-5.2
- optional local endpoint support
- strict JSON response parser
- max-token and max-call safeguards

Create CLI:

```bash
signal-engine llm extract --provider glm52 --input tests/fixtures/tiny_realistic_earnings_excerpt.txt --dry-run
signal-engine llm benchmark --providers claude,glm52 --sample tests/fixtures/tiny_realistic_earnings_excerpt.txt
```

### Phase 4 — Prompt/eval harness

Add:

```text
prompts/
  earnings_signal_extraction.v1.md
  evidence_judge.v1.md
  reviewer_packet_assist.v1.md

evals/
  promptfoo.yaml
  glm52_vs_claude_signal_extraction.yaml
  fixtures/
```

Metrics:

- valid JSON rate
- schema pass rate
- quote evidence present
- label match against existing canonical labels
- unsupported-claim rate
- cost per candidate
- latency
- human review burden

### Phase 5 — Make targets

Add:

```make
llm-safe-check:
	$(PYTHON) scripts/validate_llm_config.py --path configs/llm.example.yml
	$(PYTHON) scripts/run_llm_fixture_smoke.py --provider dry_run

llm-claude-smoke:
	SIGNAL_ENGINE_LLM_PROVIDER=claude $(PYTHON) scripts/run_llm_fixture_smoke.py --require-network

llm-glm52-smoke:
	SIGNAL_ENGINE_LLM_PROVIDER=glm52 $(PYTHON) scripts/run_llm_fixture_smoke.py --require-network

llm-bakeoff:
	$(PYTHON) scripts/run_llm_bakeoff.py --providers claude,glm52 --fixtures tests/fixtures --out reports/llm_bakeoff.md
```

Add `llm-safe-check` to CI only. Do not add live provider calls to CI unless secrets are configured and explicitly gated.

## Codex execution prompt

```text
You are working in keithtgrehan/earnings-call-signal-engine.

Goal: implement Claude and GLM-5.2 as optional BYOK model backends for reviewer-support and extraction benchmarking only. Do not weaken deterministic-first architecture. Do not add trading/alpha/buy/sell claims. Do not auto-promote gold labels. Do not download or commit restricted transcript bodies. Do not make live network calls in tests or CI by default.

Repository facts to preserve:
- Deterministic transcript analysis remains canonical.
- Weak labels are suggestions only.
- Human-reviewed labels are the only canonical gold source.
- ML/retrieval/LLM layers are benchmark/support layers only.
- Retrieval/embedding/training remain gated by reviewed-label volume and provenance.
- Source rights, restricted artifact checks, and corpus-safe checks must continue to fail closed.

Implement in small commits:

1. Inspect existing CLI, config, scripts, schemas, tests, and Makefile.
2. Add provider-neutral LLM package under src/signal_engine/llm/.
3. Add config support for disabled-by-default LLM usage:
   - configs/llm.example.yml
   - schemas/llm_config.schema.json
   - scripts/validate_llm_config.py
4. Add provider wrappers:
   - Claude via Anthropic SDK/API, using ANTHROPIC_API_KEY.
   - GLM-5.2 via OpenAI-compatible endpoint, using ZAI_API_KEY, ZAI_BASE_URL, GLM_MODEL.
   - No key should ever be printed.
5. Add dry-run fake provider for tests.
6. Add strict JSON-schema output validation for signal candidates and evidence-judge outputs.
7. Add prompts:
   - prompts/earnings_signal_extraction.v1.md
   - prompts/evidence_judge.v1.md
   - prompts/reviewer_packet_assist.v1.md
8. Add scripts:
   - scripts/run_llm_fixture_smoke.py
   - scripts/run_llm_bakeoff.py
   - scripts/validate_llm_config.py
9. Add Make targets:
   - llm-safe-check
   - llm-claude-smoke
   - llm-glm52-smoke
   - llm-bakeoff
10. Add tests proving:
   - default LLM state is disabled
   - dry-run provider works offline
   - invalid JSON fails closed
   - missing evidence quote fails validation
   - live provider calls are skipped unless explicit env flags are set
   - no API keys appear in logs
11. Add docs:
   - docs/llm_backends.md
   - docs/codex/claude_glm52_integration_plan.md if missing or update it if present
12. Run:
   - python -m py_compile $(find scripts src tools -name "*.py")
   - python -m pytest
   - make corpus-safe-check
   - make training-plan-check
   - make training-readiness
   - make llm-safe-check

Acceptance criteria:
- All tests pass locally.
- LLM usage is opt-in only.
- No live network call runs unless explicitly requested.
- All LLM artifacts write only to artifacts/llm/ or reports/llm/.
- Outputs include provenance references and quote-level evidence.
- No model output is used as canonical truth.
- No raw restricted transcript bodies are added to git.
- README/docs clearly state Claude and GLM-5.2 are reviewer-support/benchmark backends only.

After implementation, produce a PR summary with:
- files changed
- commands run
- safety gates added
- how to run Claude smoke
- how to run GLM-5.2 smoke
- remaining manual setup required
```

## Local install commands

Claude Code:

```bash
curl -fsSL https://claude.ai/install.sh | bash
cd earnings-call-signal-engine
claude
```

Python/dev setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e ".[dev,evaluation,review,retrieval]"
pip install anthropic openai litellm opik promptfoo
```

GLM-5.2 API mode:

```bash
export ZAI_API_KEY="..."
export ZAI_BASE_URL="https://api.z.ai/api/paas/v4"
export GLM_MODEL="glm-5.2"
```

Claude API mode:

```bash
export ANTHROPIC_API_KEY="..."
export CLAUDE_MODEL="claude-opus-4-8"
```

Do not attempt full local GLM-5.2 inference on a normal laptop. Use Z.ai API or an OpenAI-compatible hosted endpoint first. Local/self-hosted GLM-5.2 should be a later infra task using vLLM/SGLang on proper GPU hardware.

## Immediate next command

Run this from the repo root after pulling the branch:

```bash
claude -p "Read docs/codex/claude_glm52_integration_plan.md and implement Phase 1 and Phase 2 only. Stop before live GLM-5.2 network calls. Keep all provider calls opt-in and offline-safe by default."
```
