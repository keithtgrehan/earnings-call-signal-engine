# LLM Tooling Router Master Prompt

Use this prompt when asking Codex to extend the Signal Engine LLM layer.

Signal Engine is deterministic-first. Deterministic transcript extraction remains canonical, and human-reviewed labels are the only gold source.

Implementation rules:

- keep `dry_run` as the default provider
- keep LiteLLM optional and fail closed if missing
- do not add provider calls to normal CI
- require both `SIGNAL_ENGINE_LLM_LIVE=1` and `--live` for live calls
- validate JSON outputs before writing artifacts
- require quote-level transcript evidence
- write generated LLM artifacts only under `artifacts/llm/` or `reports/llm/`
- never log or serialize API key values
- never auto-promote labels
- never make trading, alpha, buy, sell, causal, production ML, or investment claims

Recommended validation:

```bash
python -m py_compile $(find scripts src tools -name "*.py")
python -m pytest
make llm-safe-check
make llm-router-check
make corpus-safe-check
make training-plan-check
make training-readiness
```
