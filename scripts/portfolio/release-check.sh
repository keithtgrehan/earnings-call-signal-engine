#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

scripts/portfolio/preflight.sh
make capstone-ci
python3 scripts/portfolio/validate_control_room.py --release

echo "Portfolio V1 release checks passed. Human publication and main-merge approval are still required."
