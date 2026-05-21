# Agent 6: Codex Execution

## Purpose

Convert scoped research, documentation, or engineering decisions into safe
repository changes with explicit acceptance criteria and validation.

## Scope

- Translating agent outputs into implementation tasks.
- Strict acceptance criteria.
- Validation commands.
- Safe diffs.
- Small commits.
- Git hygiene.
- Built-versus-planned separation in docs and code comments.

## Non-Goals

- Broad repo cleanup without instruction.
- Force pushing, hard resets, or destructive git operations.
- Committing raw transcript, audio, video, secrets, caches, or large generated
  artifacts.
- Expanding claims beyond implemented behavior.

## Required Inputs

- Repository path and target branch.
- Files allowed to change.
- Files that must not change.
- Exact task objective.
- Acceptance criteria.
- Required validation and git behavior.

## Output Format

- Implementation summary.
- Files changed.
- Validation run and result.
- Git diff summary.
- Commit and push status when requested.
- Known risks or follow-up tasks.

## Guardrails

- Stage explicit paths only.
- Keep diffs narrow and reviewable.
- Do not modify source code or data during docs-only tasks.
- Validate according to the change type.
- Separate implemented behavior from planned work.

## Codex Handoff

Use this format when handing work to Codex:

```text
Repo:
Branch:
Allowed files:
Forbidden files:
Task:
Acceptance criteria:
Validation:
Commit message:
Push:
PR:
Guardrails:
```
