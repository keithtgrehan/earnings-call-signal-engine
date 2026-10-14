#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

branch="$(git branch --show-current)"
if [[ "$branch" == "main" ]]; then
  echo "Portfolio V1 checks refuse direct work on main." >&2
  exit 1
fi

if ! git remote get-url origin | grep -q 'keithtgrehan/earnings-call-signal-engine'; then
  echo "Unexpected origin remote; aborting Portfolio V1 checks." >&2
  exit 1
fi

git diff --check

if git grep -n -E '^(<<<<<<<|>>>>>>>)' -- . >/dev/null; then
  echo "Merge-conflict markers found." >&2
  exit 1
fi

python3 scripts/portfolio/validate_control_room.py
python3 scripts/check_markdown_links.py docs/portfolio_v1/*.md

changed_paths_file="$(mktemp)"
trap 'rm -f "$changed_paths_file"' EXIT
{
  git diff --name-only --diff-filter=ACMR
  git diff --cached --name-only --diff-filter=ACMR
  git ls-files --others --exclude-standard
  if [[ -n "${GITHUB_BASE_REF:-}" ]] && git rev-parse --verify --quiet "origin/${GITHUB_BASE_REF}" >/dev/null; then
    git diff --name-only --diff-filter=ACMR "origin/${GITHUB_BASE_REF}...HEAD"
  fi
} | sort -u > "$changed_paths_file"

changed_paths=()
while IFS= read -r path; do
  [[ -n "$path" ]] && changed_paths+=("$path")
done < "$changed_paths_file"

if (( ${#changed_paths[@]} > 0 )); then
  python3 scripts/check_restricted_artifacts.py "${changed_paths[@]}"
else
  python3 scripts/check_restricted_artifacts.py --dry-run
fi

python3 -m py_compile scripts/portfolio/validate_control_room.py
python3 -m pytest -q tests/test_portfolio_control_room.py

if command -v ruff >/dev/null 2>&1; then
  ruff check scripts/portfolio/validate_control_room.py tests/test_portfolio_control_room.py
elif [[ -x .venv/bin/ruff ]]; then
  .venv/bin/ruff check scripts/portfolio/validate_control_room.py tests/test_portfolio_control_room.py
else
  echo "ruff unavailable; targeted lint skipped"
fi

echo "Portfolio V1 preflight passed. Include these exact results in the task handoff."
