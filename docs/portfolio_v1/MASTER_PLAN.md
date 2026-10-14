# Portfolio Product V1 Master Plan

Time budget: 20 focused hours per week for nine weeks.

The target is an authenticated, invite-only AWS application plus a public proof
package. The live application is not an unauthenticated public playground.

| Week | Outcome | Exit gate |
|---|---|---|
| 1 | Control room, scope, data-rights register, evaluation contract | Baseline checks pass; scope and claims are explicit |
| 2 | AWS CDK, CI, OIDC design, IAM, secrets and budget controls | Infrastructure synthesizes; no static credentials |
| 3 | Private storage, persistent jobs, queue/retry path, deterministic invocation | API and failure-path tests pass |
| 4 | Cognito roles, analyst/reviewer UI, first private deployment | Reviewer can sign in and approve/edit/reject |
| 5 | Two fixed-bundle model reviewers and cost/latency ledger | Models cannot alter canonical extraction |
| 6 | Monitoring, audit trail, retention/deletion and threat mitigations | One analysis is traceable end to end |
| 7 | Human adjudication and locked holdout | Provenance hashes and reviewer records are complete |
| 8 | Reproducible scorecard, diagram, demo and executive brief | Claims match evidence and limitations |
| 9 | Independent review, remediation and release PR | Release checklist passes |

## Weekly Time Split

- 12 hours: implementation with Codex.
- 4 hours: human review and evaluation decisions.
- 2 hours: product and usability testing.
- 1 hour: documentation and demo evidence.
- 1 hour: planning and integration review.

## Parallel Work Rules

Safe in parallel:

- evaluation-data preparation and AWS foundation;
- UI wireframes and stable API-contract review;
- security, UX, and cost reviews of an existing diff.

Sequential:

- product/evaluation contract before model claims;
- identity and job-state contract before review UI implementation;
- private deployment before public release proof;
- validated handoff before `STATUS.md` changes.

No more than two implementation worktrees should be active simultaneously.
Research/review agents may run in addition when their scopes do not overlap.

## Completion Definition

Portfolio V1 is complete only when all of these exist and agree:

- authenticated analyst/reviewer workflow;
- infrastructure as code and reproducible deployment instructions;
- secrets, permissions, retention, audit and monitoring controls;
- locked, human-reviewed evaluation set with recorded provenance;
- two-model scorecard covering quality, latency and cost per successful analysis;
- architecture diagram and threat model;
- six-minute demonstration;
- one-page executive business case;
- explicit limitations and rollback path;
- passing release checklist.

A plan, scaffold, local smoke test, or attractive UI alone is not completion.
