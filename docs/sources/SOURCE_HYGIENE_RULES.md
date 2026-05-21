# Source Hygiene Rules

These rules define what may become ChatGPT Project Source material for Signal
Engine 2.0.

## May Be Added

- Canonical README and project scope docs.
- Current roadmap and execution roadmap docs.
- Evaluation plans, benchmark summaries, and status reports.
- Label schema, label promotion, and human-review workflow docs.
- Corpus manifest and provenance workflow docs.
- Agent operating docs and `AGENTS.md`.
- Concise decision records that supersede older planning notes.

## Should Not Be Added

- Raw transcripts, audio, video, or copied third-party source material.
- Secrets, credentials, private customer data, or local-only paths that are not
  useful to agents.
- Draft chats, scratch notes, and unresolved brainstorming.
- Duplicate memos that restate a canonical source differently.
- Generated reports unless they are current benchmark or audit artifacts.
- Large files that make Project memory noisy.
- Anything that claims planned work is already built.

## Stale Docs

If a doc is historically useful but no longer canonical, keep it in GitHub but
do not add it to Project Sources. Prefer a current summary source that names the
active decision.

## Duplicate Memos

When two docs disagree, do not add both as Sources. Promote the newer canonical
doc or create a concise decision record that resolves the conflict.

## Draft Chats

Do not add draft chats directly. Convert useful decisions into a short,
GitHub-backed operating doc before adding them as Sources.

## Generated Reports

Generated reports may be added only when they are the current benchmark,
evaluation, audit, or review artifact for a specific workflow. Remove or replace
them when a newer report supersedes them.

## Built-Versus-Planned Claims

Sources must clearly separate:

- Built: implemented in the repo and, where relevant, validated.
- Planned: intended work not yet implemented.
- Candidate: generated or machine-suggested output awaiting review.
- Gold: human-accepted label data protected by promotion safeguards.
