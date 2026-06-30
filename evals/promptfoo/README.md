# Promptfoo LLM Eval Scaffold

This directory is an optional scaffold for later LLM prompt evaluation.

Default behavior is dry-run/local fixture only. Do not run live provider evals until provider calls have been deliberately enabled and reviewed.

Run once promptfoo is installed:

```bash
promptfoo eval -c evals/promptfoo/llm_signal_extraction.yaml
```

Rules:

- no provider API calls by default
- no gold-label writes
- no canonical model outputs
- no restricted transcript bodies
- every checked output must keep `canonical_output: false`
