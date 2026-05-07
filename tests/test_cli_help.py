from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def test_cli_help_mentions_download_only() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"

    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
    )

    proc = subprocess.run(
        [sys.executable, "-m", "earnings_call_sentiment", "--help"],
        cwd=str(repo_root),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, output
    assert "--download-only" in output
    assert "--question-shifts" in output
    assert "question-related sentiment shifts" in output
    assert "--prior-guidance" in output
    assert "--tone-change-threshold" in output
    assert "--vad" in output
    assert "--force" in output
    assert "--resume" in output
    assert "--strict" in output
    assert "--sentiment-model" in output
    assert "--sentiment-revision" in output
    assert "--symbol" in output
    assert "--event-dt" in output
    assert "--llm-summary" in output
    assert "--summary-provider" in output
    assert "--summary-model" in output
    assert "--summary-base-url" in output
    assert "--summary-api-key-env" in output
    assert "--summary-timeout-s" in output
