# Portfolio Product V1 Decision Log

Record decisions that change architecture, scope, evidence, cost, security, or
public claims. Do not use this log for routine implementation details.

## 2026-08-24 — D001: Existing Repository, Fresh Checkout

- Status: accepted.
- Decision: build Portfolio V1 inside the existing Signal Engine repository from
  a fresh checkout of current `origin/main`.
- Alternatives: reuse an old local feature checkout; create a second product repo.
- Reason: the existing deterministic, provenance, review, and evaluation work is
  the strongest proof and should remain one auditable history.
- Risk: the repo is broad and document-heavy.
- Mitigation: one bounded `docs/portfolio_v1/` control-room index and dedicated
  `codex/portfolio-v1-*` branches.
- Rollback: remove the additive Portfolio V1 surface before integration; legacy
  core behavior remains unchanged.

## 2026-08-24 — D002: AWS Serverless-First V1

- Status: accepted for design; deployment requires approval.
- Decision: use AWS CDK, CloudFront/S3, Cognito, API Gateway, Lambda, SQS,
  DynamoDB, Secrets Manager, Bedrock, and CloudWatch/X-Ray/Budgets.
- Alternatives: always-on containers; Kubernetes; managed all-in-one AI platform.
- Reason: produces strong cloud/operations evidence with low idle cost and avoids
  fixed infrastructure not justified by an invite-only demo.
- Risk: Lambda duration/package limits.
- Rollback: move only the measured worker workload to a container service while
  retaining API, storage, auth, queue, and contracts.

## 2026-08-24 — D003: Models Are Reviewers

- Status: accepted.
- Decision: compare models only on fixed immutable evidence bundles. The
  deterministic extractor stays canonical and human decisions stay separate.
- Alternatives: end-to-end LLM extraction; agentic research pipeline.
- Reason: preserves auditability and makes quality/cost trade-offs measurable.
- Risk: the demo may look less magical than generic AI products.
- Mitigation: make disagreement, evidence, and human control the product value.

## 2026-08-24 — D004: Codex Desktop Owns Worktrees

- Status: accepted.
- Decision: one issue maps to one Codex-managed worktree. Do not build a second
  custom worktree lifecycle script.
- Alternatives: scripted permanent worktrees and automated branch cleanup.
- Reason: Codex Desktop already creates, hands off, restores, and cleans managed
  worktrees; duplicating that control would create branch ownership conflicts.
- Risk: one manual selection is required when starting a focused task.
- Mitigation: the issue contract is ready to paste and names the base branch.

## Decision Template

### YYYY-MM-DD — DXXX: Title

- Status: proposed / accepted / superseded / rejected.
- Decision:
- Alternatives:
- Reason:
- Risk:
- Rollback:
- Approval required:
