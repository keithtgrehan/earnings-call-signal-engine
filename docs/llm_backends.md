# Optional LLM Backends

Status: implemented as gated reviewer-support and extraction-benchmark infrastructure.

Claude and GLM-5.2 are optional BYOK backends. They do not replace deterministic transcript analysis, do not create canonical labels, and do not promote weak labels to gold. Human-reviewed labels remain the only canonical gold source.

## Scope

Allowed use:

- reviewer-support notes for fixed evidence packets
- extraction-benchmark candidates for comparison against deterministic outputs
- evidence-judge checks that require quote-level transcript support

Not allowed:

- trading, alpha, buy, sell, hold, or investment advice claims
- live provider calls in CI or tests by default
- canonical extraction or gold-label writes
- raw restricted transcript body downloads or commits
- retrieval, embedding, or training shortcuts that bypass reviewed-label and provenance gates

## Config

The default config is `configs/llm.example.yml`.

Defaults:

- `enabled: false`
- `allow_live_provider_calls: false`
- `canonical_output_allowed: false`
- `auto_promote_gold: false`
- outputs restricted to `artifacts/llm/` and `reports/llm/`

Validate it:

```bash
python scripts/validate_llm_config.py --path configs/llm.example.yml --require-disabled-default
```

## Providers

`dry_run` is the offline fake provider used by tests and `make llm-safe-check`.

`claude` uses Anthropic's Messages API. Required for a live smoke:

- `ANTHROPIC_API_KEY`
- optional `ANTHROPIC_MODEL`
- optional `ANTHROPIC_BASE_URL`

`glm52` uses an OpenAI-compatible chat-completions endpoint. Required for a live smoke:

- `ZAI_API_KEY`
- `ZAI_BASE_URL`
- optional `GLM_MODEL`

No script prints API key values. Skip reasons mention only environment variable names.

## Commands

Offline safety check:

```bash
make llm-safe-check
```

Claude smoke, skipped by default:

```bash
make llm-claude-smoke
```

Claude live smoke:

```bash
ANTHROPIC_API_KEY=... SIGNAL_ENGINE_LLM_LIVE=1 LLM_LIVE_ARGS=--live make llm-claude-smoke
```

GLM-5.2 smoke, skipped by default:

```bash
make llm-glm52-smoke
```

GLM-5.2 live smoke:

```bash
ZAI_API_KEY=... ZAI_BASE_URL=https://your-openai-compatible-endpoint GLM_MODEL=glm-5.2 SIGNAL_ENGINE_LLM_LIVE=1 LLM_LIVE_ARGS=--live make llm-glm52-smoke
```

Bakeoff on the fixed fixture:

```bash
make llm-bakeoff
```

To include live providers in the bakeoff, set the provider keys, endpoint/model variables, `SIGNAL_ENGINE_LLM_LIVE=1`, and `LLM_LIVE_ARGS=--live`.

## Output Contracts

LLM signal candidates validate against `schemas/llm_signal_candidates.schema.json`.

Evidence-judge outputs validate against `schemas/llm_evidence_judge.schema.json`.

Both contracts require:

- `canonical_output: false`
- provider and model provenance
- quote-level evidence
- source/provenance references

Invalid JSON, missing evidence quotes, and schema mismatches fail closed.

## Safety Notes

Provider output is a support artifact only. It can help a reviewer inspect evidence faster, but it cannot become canonical truth without human review and the existing gold-label promotion workflow.

All generated LLM artifacts must stay under `artifacts/llm/` or `reports/llm/`. Do not commit raw restricted transcript bodies, secrets, provider logs containing keys, or bulky runtime artifacts.
