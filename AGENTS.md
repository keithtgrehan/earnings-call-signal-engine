# Signal Engine 2.0 Agent Instructions

This repository is Signal Engine 2.0. Treat it as an evaluation-ready,
transcript-first signal extraction project, not as a trading system, alpha
engine, or live execution platform.

## Canonical Principles

- Transcript-first deterministic extraction is canonical.
- LLM outputs are reviewer and candidate layers only.
- Machine labels, weak labels, and LLM labels must never be auto-promoted to
  gold.
- Evidence spans, provenance, and reproducibility are mandatory for every
  signal claim.
- Codex must keep built functionality separate from planned or proposed work.
- Codex must avoid broad agentic orchestration before the deterministic core,
  provenance workflow, and evaluation loop are hardened.

## Built Versus Planned

When editing docs, prompts, reports, or implementation tasks:

- Describe implemented behavior only when it is already present in the repo.
- Mark future work as planned, proposed, optional, or backlog.
- Do not imply live trading, alpha generation, automated investment decisions,
  or unsupported statistical proof.
- Keep LLM, retrieval, audio, video, and agent layers subordinate to the
  transcript-first evidence path unless code and evaluation show otherwise.

## Validation Expectations

Run validation that matches the change scope:

- Run `python -m py_compile` on changed Python files if any Python files change.
- Run `pytest` if code changes happen.
- Run `ruff check` if available.
- Run markdown formatting checks if available when Markdown files change.
- Run markdown link checks if available when documentation links change.

For docs-only changes, do not run the full test suite unless the docs change
also modifies code, config, generated data, or test expectations.

## Git Safety Rules

- No force push.
- No hard reset.
- No raw transcript, audio, or video commits.
- No broad refactors without explicit instruction.
- Do not stage unrelated local changes.
- Do not rewrite, delete, or move existing docs unless explicitly necessary.
- Prefer small, reviewable commits with explicit paths staged.
