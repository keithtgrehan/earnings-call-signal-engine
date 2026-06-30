# LLM Router And Eval Stack

Status: implemented as safe scaffolding.

Codex remains the main implementation agent. The LLM layer is a bounded reviewer-support and extraction-benchmark layer.

## Stack Order

1. `dry_run`: default provider for tests, local smoke checks, and safe Make targets.
2. LiteLLM router scaffold: optional routing abstraction in `src/signal_engine/llm/router.py`.
3. Claude API: optional second-stage reviewer/judge backend.
4. GLM-5.2: optional third-stage long-context or bulk extraction benchmark backend through an OpenAI-compatible endpoint.
5. promptfoo and Opik: optional eval/observability scaffolds after real provider calls exist.

## Implementation

- `LLMRouter(router="direct")` uses provider wrappers directly.
- `LLMRouter(router="litellm")` uses the LiteLLM scaffold.
- `dry_run` never requires LiteLLM or API keys.
- non-dry live providers require `--live` and `SIGNAL_ENGINE_LLM_LIVE=1`.
- missing optional dependencies or keys fail closed with skipped/error status.

## Safe Commands

```bash
make llm-safe-check
make llm-router-check
make llm-bakeoff
```

These commands do not make live provider calls by default.

## Live Commands

Claude:

```bash
ANTHROPIC_API_KEY=... CLAUDE_MODEL=claude-opus-4-8 SIGNAL_ENGINE_LLM_LIVE=1 LLM_LIVE_ARGS=--live make llm-claude-smoke
```

GLM-5.2:

```bash
ZAI_API_KEY=... ZAI_BASE_URL=https://your-openai-compatible-endpoint GLM_MODEL=glm-5.2 SIGNAL_ENGINE_LLM_LIVE=1 LLM_LIVE_ARGS=--live make llm-glm52-smoke
```

## Guardrails

- deterministic transcript extraction remains canonical
- human-reviewed labels remain the only gold source
- all LLM artifacts must keep `canonical_output: false`
- artifacts can write only to `artifacts/llm/` or `reports/llm/`
- API keys must never be printed, serialized, logged, or committed
- promptfoo and Opik are optional and should only be used after real provider calls exist
