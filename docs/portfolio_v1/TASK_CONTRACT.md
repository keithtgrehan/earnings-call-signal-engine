# Portfolio Product V1 Task Contract

One issue is one measurable outcome, one focused Codex task, and one managed
worktree. If the scope expands, create a follow-up issue instead of widening the
current task.

## Reusable Contract

```markdown
# [Portfolio V1] Short outcome

## Outcome
One measurable customer or engineering result.

## Context to read
- AGENTS.md
- docs/portfolio_v1/README.md
- docs/portfolio_v1/STATUS.md
- Relevant product/evaluation/security document

## Base and workstream
- Base branch: codex/portfolio-v1-integration
- Workstream: evaluation / platform / UI / model review / release proof

## In scope
- Exact files, folders, or components allowed to change.

## Out of scope
- Explicit exclusions.

## Acceptance criteria
1. Observable behaviour or artifact.
2. Automated and manual validation condition.
3. Security, privacy, rights, or claim condition.
4. Required documentation update.

## Validation
- Exact commands to run.
- Expected result.

## Approval gates
- State whether credentials, spend, real data, public deployment, publication,
  push/PR, or main merge is permitted.
- Only Keith may provide approval evidence. Include his dated issue comment or
  state `Not applicable` when the task crosses no gate.

## Handoff
- Summary and files changed.
- Exact validation results.
- Limitations and residual risk.
- Rollback path.
- Files intentionally not touched.
- One recommended next dependency.
```

## Focused Codex Prompt

> Implement only the attached Portfolio Product V1 task contract. Read all
> listed context first. Inspect repository state before editing. Preserve user
> work and deterministic/evidence boundaries. Use one writer for this worktree.
> If scope expands or an approval gate is reached, stop and document the next
> issue instead of assuming permission. Run the exact validation, independently
> review the diff, and return the required handoff. Do not update
> `docs/portfolio_v1/STATUS.md`; the control room updates it after validation.

## Control-Room Acceptance

The control room accepts a handoff only when:

- the diff matches the allowed scope;
- acceptance criteria have concrete evidence;
- exact validation results are present;
- data rights, security, privacy, and claims were reviewed;
- limitations and rollback are explicit;
- no unrelated user work was changed.
