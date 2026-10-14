#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

portfolio_python="${PORTFOLIO_PYTHON:-python3}"

if [[ ! -x .venv/bin/python ]]; then
  "$portfolio_python" -m venv .venv
fi

.venv/bin/python -m pip install --disable-pip-version-check --upgrade pip
.venv/bin/python -m pip install --disable-pip-version-check -e ".[dev]"

.venv/bin/python scripts/portfolio/validate_control_room.py

echo "Portfolio V1 worktree environment is ready. No provider keys or cloud credentials were copied."
