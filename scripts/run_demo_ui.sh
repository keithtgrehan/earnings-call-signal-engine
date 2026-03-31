#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-7872}"
URL="http://127.0.0.1:${PORT}"

echo "Starting demo UI from: $ROOT_DIR"
echo "Demo URL: $URL"
echo "Press Ctrl-C to stop."

PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}" PORT="$PORT" exec python3 app/site_server.py
