# Project Operating Model

Signal Engine 2.0 uses a layered operating model so ChatGPT Project agents and
Codex execution stay aligned without overstating what the repository can do.

## Layers

- Project: the shared ChatGPT workspace where project memory, specialist chats,
  and Codex tasks are coordinated.
- Sources: the canonical memory supplied to Project chats. Sources should be
  small, current, and authoritative.
- Chats: specialist agent threads that reason about one workstream at a time.
- Control Room: the orchestration layer that routes requests, selects sources,
  and decides whether Codex implementation is needed.
- Codex: the implementation layer for safe repository changes, validation, git
  branches, commits, and push operations.
- GitHub: the source of truth for repository state, reviewed changes, and
  durable project history.

## Six-Agent Structure

1. Agent 1, NLP Signal Extraction: transcript-first signal definitions,
   evidence spans, false-positive reduction, and deterministic candidate logic.
2. Agent 2, Evaluation / Event Study: evaluation design, abnormal return
   windows, baselines, confounds, and statistical caveats.
3. Agent 3, Engineering Quality: CLI quality, reproducibility, tests, docs,
   onboarding, and module boundaries.
4. Agent 4, Human Review / Argilla: reviewer workflows, calibration, audit
   trails, and label promotion safeguards.
5. Agent 5, Acquisition / Ingestion: source discovery, transcript provenance,
   source hygiene, and legally usable intake paths.
6. Agent 6, Codex Execution: conversion of scoped research decisions into safe,
   validated repository changes.

## What Belongs In ChatGPT Project Sources

Use Project Sources for compact, stable references:

- Current README and project scope.
- Roadmap and execution roadmap.
- Evaluation plan and benchmark summaries.
- Gold-label schema and label promotion workflow.
- Argilla or human-review workflow docs.
- Corpus manifest and provenance docs.
- Agent operating docs and `AGENTS.md`.
- Current status docs that separate built behavior from planned work.

## What Belongs In GitHub

Use GitHub for durable project artifacts:

- Source code, tests, configs, and CLIs.
- Canonical docs and operating docs.
- Human-review schemas, validation rules, and reproducible workflows.
- Lightweight manifests and reports that are appropriate to version.
- Issue, branch, commit, and pull request history.

Do not commit raw transcripts, audio, video, secrets, local caches, model
artifacts, or large generated outputs unless the project explicitly defines a
safe, legal, and reviewable path for them.

## What Belongs In Codex Prompts

Codex prompts should include:

- The exact repository path and branch expectations.
- Files allowed to change and files that must not change.
- Whether the task is docs-only, code, data, tests, or validation.
- Acceptance criteria and required validation commands.
- Built-versus-planned boundaries.
- Git instructions, including staging scope, commit message, push behavior, and
  whether a pull request should be opened.

## What Should Not Be Treated As Proven

Do not treat the following as proven without repo-backed evidence:

- Trading, alpha, live execution, or investment decision claims.
- Causal claims from event studies or benchmark correlations.
- LLM outputs as gold labels.
- Weak labels as human-reviewed labels.
- Roadmap items as implemented behavior.
- Multimodal, retrieval, or agent orchestration layers as canonical unless the
  deterministic transcript-first path and evaluation evidence support them.
