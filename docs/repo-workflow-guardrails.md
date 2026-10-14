# Repo Workflow Guardrails

## Correct Signal Engine repository

Canonical remote:

```text
git@github.com:keithtgrehan/earnings-call-signal-engine.git
```

The repository identity, remote, branch base, and clean state are authoritative;
one historical absolute path is not. For Portfolio Product V1, the clean local
control-room checkout created on 2026-08-24 is:

```text
/Users/keith/GitHub/earnings-call-signal-engine-portfolio
```

Codex-managed worktrees derived from that checkout are also valid. The older
`earnings-call-codex-fix`, `earnings-call-audio-fix`, and long historical
checkout are not Portfolio V1 integration checkouts.

## Wrong workspace to avoid for Signal Engine

Do not run Signal Engine Codex tasks from:

```text
/Users/keith/Documents/New project
```

Reason:

That parent directory is a different git repo / mixed project area and may point to unrelated remotes such as:

```text
https://github.com/keithtgrehan/Rave-For-Good-Site-V1.2-Feb-2026.git
```

The accidental parent worktree was observed on branch `codex/earnings-150-hardening` with dirty local files. It also contains nested projects, backups, local data, generated files, and the nested Signal Engine repo. Do not use it as the working directory for Signal Engine tasks.

## Required preflight for every Codex task

Run before editing:

```bash
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
```

Abort unless:

- `git remote -v` contains `keithtgrehan/earnings-call-signal-engine`
- the task starts from the branch named in its contract
- the worktree is clean or the task contract explicitly identifies the existing
  changes as in scope
- Portfolio V1 tasks read `docs/portfolio_v1/README.md` and
  `docs/portfolio_v1/STATUS.md` before editing

## Future branch workflow

- `main` is the stable source of truth.
- Do not work directly on `main`.
- Portfolio Product V1 is the exception to the generic base rule below: its
  task branches and Codex-managed worktrees derive from
  `codex/portfolio-v1-integration`, or the exact replacement integration branch
  recorded in the issue contract.
- Before new work, update `main` in its existing worktree:

```bash
git checkout main
git pull --ff-only origin main
```

- If `main` is checked out in another worktree, do not force checkout. Either use that existing `main` worktree or create a new task branch directly from `origin/main`.
- Create one feature branch per task:

```bash
git checkout -b codex/<short-task-name>
```

- One task = one branch.
- Do not reuse dirty Codex branches for unrelated work.
- Do not switch branches with uncommitted files.
- Never use `git add .` for preservation or cleanup tasks; stage explicit paths only.

## Preservation rules

- Do not delete files during repo-boundary audits.
- Do not run `git reset`.
- Do not run `git clean`.
- Do not stash unless absolutely necessary and reported.
- Do not commit generated outputs, caches, virtual environments, PDFs, audio/video, local corpus files, raw transcripts, or secrets.
- If a file is ambiguous, leave it uncommitted and report it.
