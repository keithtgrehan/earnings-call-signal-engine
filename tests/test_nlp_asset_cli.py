from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "nlp_asset_map.py"


def _run(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip()
    return result.stdout


def test_nlp_asset_cli_commands_do_not_crash() -> None:
    commands = [
        ("--list",),
        ("--category", "finance"),
        ("--downloaded",),
        ("--manual-required",),
        ("--signal-engine-area", "weak_labeling"),
        ("--priority", "high"),
        ("--validate",),
    ]
    for command in commands:
        _run(*command)


def test_nlp_asset_cli_outputs_expected_assets() -> None:
    assert "sec_company_tickers" in _run("--downloaded")
    assert "loughran_mcdonald_lexicon" in _run("--manual-required")
    assert "rank_bm25" in _run("--signal-engine-area", "retrieval")
