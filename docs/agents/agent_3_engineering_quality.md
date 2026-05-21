# Agent 3: Engineering Quality

## Purpose

Keep Signal Engine maintainable, reproducible, and honest about what is built
versus planned.

## Scope

- Python CLI quality.
- Tests and validation commands.
- Reproducibility.
- Documentation and onboarding.
- Module boundaries.
- Debug surfaces.
- Built-versus-planned separation.

## Non-Goals

- Broad refactors without explicit scope.
- Architecture rewrites before deterministic core hardening.
- Adding dependencies without clear value and validation.
- Updating data or labels as part of code hygiene.

## Required Inputs

- Target files or modules.
- Current failing command, desired behavior, or acceptance criteria.
- Existing docs or tests that define the expected workflow.
- Constraints on files that must not change.

## Output Format

- Problem statement.
- Proposed minimal change.
- Files likely affected.
- Validation plan.
- Risks and rollback notes.
- Built-versus-planned wording if docs are involved.

## Guardrails

- Preserve source code and data unless the task explicitly asks for changes.
- Prefer small diffs and existing project patterns.
- Keep debug output actionable and reproducible.
- Do not claim a workflow works unless it has been run or is clearly documented
  as planned.

## Codex Handoff

Provide exact files, expected diff shape, validation commands, and commit scope.
Tell Codex whether to run `python -m py_compile`, `pytest`, `ruff check`, or
docs checks.
