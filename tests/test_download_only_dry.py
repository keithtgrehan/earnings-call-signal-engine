from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def test_dry_run_wins_over_download_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    cache_dir = tmp_path / "cache"
    out_dir = tmp_path / "out"

    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "earnings_call_sentiment",
            "--youtube-url",
            "https://example.com",
            "--cache-dir",
            str(cache_dir),
            "--out-dir",
            str(out_dir),
            "--download-only",
            "--dry-run",
        ],
        cwd=str(repo_root),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")
    assert not list(cache_dir.glob("audio.*"))
