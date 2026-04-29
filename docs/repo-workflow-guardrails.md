# Repo Workflow Guardrails

## Correct Signal Engine repo

Local path:

```text
/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa
```

Remote:

```text
git@github.com:keithtgrehan/earnings-call-signal-engine.git
```

This is the only repo/worktree to use for Signal Engine Codex tasks.

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

- `git rev-parse --show-toplevel` is `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa`
- `git remote -v` contains `keithtgrehan/earnings-call-signal-engine`
- the worktree is clean or the user has explicitly identified the existing changes as in scope

## Future branch workflow

- `main` is the stable source of truth.
- Do not work directly on `main`.
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
