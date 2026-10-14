# Portfolio Product V1 Control Room

This folder is the authoritative operating pack for converting the existing
Signal Engine research and evaluation system into one authenticated,
cloud-deployed, customer-style case study.

Portfolio V1 does not replace the deterministic Signal Engine core. It adds a
bounded product surface around it: durable jobs, authentication, permissions,
model reviewers, human approval, monitoring, cost evidence, and release proof.

## Current State

Read [STATUS.md](STATUS.md) first. It is the single source of truth for the
current milestone, validated work, blockers, and next three tasks.

The canonical remote is `keithtgrehan/earnings-call-signal-engine`. Portfolio
work integrates through `codex/portfolio-v1-integration`; do not work directly
on `main`.

## Document Map

- [MASTER_PLAN.md](MASTER_PLAN.md): nine-week delivery sequence and gates.
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md): customer, workflow, scope, and acceptance.
- [ARCHITECTURE.md](ARCHITECTURE.md): planned AWS architecture and trust boundaries.
- [EVALUATION_CONTRACT.md](EVALUATION_CONTRACT.md): locked evaluation rules and metrics.
- [THREAT_MODEL.md](THREAT_MODEL.md): assets, threats, mitigations, and residual risk.
- [DECISIONS.md](DECISIONS.md): dated architecture and operating decisions.
- [TASK_CONTRACT.md](TASK_CONTRACT.md): reusable GitHub issue and Codex prompt contract.
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md): evidence required before publication.

Repository-wide data-rights, evidence, claim, and gold-label rules remain
authoritative. This folder links to those rules rather than duplicating them.

## Codex Operating Loop

1. The persistent control-room task reads this index and `STATUS.md`.
2. It selects the highest-value unblocked outcome from the master plan.
3. A GitHub issue is created from the Portfolio V1 issue template.
4. In Codex Desktop, start a **Worktree** chat from
   `codex/portfolio-v1-integration` and paste the complete issue contract.
5. The implementation task changes only its permitted area, validates, and
   returns a handoff.
6. The control room reviews the diff and evidence before integrating it.
7. Only after validation does the control room update `STATUS.md`.

Codex Desktop owns managed-worktree creation, handoff, and cleanup. Do not add a
second script that runs `git worktree add` or removes Codex-managed worktrees.

## One-Time Codex Desktop Setup

1. Add the clean repository checkout as a Codex project.
2. Create a local environment named `Signal Engine Portfolio V1`.
3. Set its macOS/Linux setup command to:

   ```bash
   scripts/portfolio/setup-worktree.sh
   ```

4. Select that environment when starting Portfolio V1 worktree chats.

The setup script creates an ignored per-worktree virtual environment, installs
only the core and development dependencies, and validates the control-room
contract. It deliberately does not copy `.env`, API keys, AWS credentials, raw
documents, or other ignored data into a worktree.

## Start-of-Task Checks

```bash
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
make portfolio-v1-status
```

Abort if the remote is wrong, the branch is outside the task contract, or
unrelated changes overlap the task.

## Handoff Checks

```bash
make portfolio-v1-check
```

Also run the narrow tests and build checks named in the issue. A release
candidate additionally runs:

```bash
make portfolio-v1-release-check
```

## Approval Boundaries

Codex may make reversible local changes, run tests, prepare commits, and draft
issues or PRs. Keith must explicitly approve:

- cloud credentials, model access, or paid spend;
- third-party data with unresolved rights;
- public deployment or publication of the case study;
- published evaluation or business claims;
- merge to `main`.

## Control-Room Prompt

> Act as the Signal Engine Portfolio Product V1 control room. Read `AGENTS.md`,
> `docs/portfolio_v1/README.md`, and `docs/portfolio_v1/STATUS.md`. Do not
> implement feature code in the control-room checkout. Select the single
> highest-value unblocked outcome, verify its task contract is complete, and
> prepare one focused Codex worktree task. Accept a handoff only after its diff,
> validation, rights, security, and claim boundaries pass. Update `STATUS.md`
> only after integration evidence exists.
