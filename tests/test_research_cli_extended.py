from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "research_paper_map.py"


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


def test_extended_cli_commands_do_not_crash() -> None:
    commands = [
        ("--brief", "attention_is_all_you_need"),
        ("--parsed-status",),
        ("--feature-backlog",),
        ("--reading-plan",),
        ("--source-registry",),
        ("--validate-full-asset",),
    ]
    for command in commands:
        _run(*command)


def test_brief_cli_returns_deep_brief() -> None:
    output = _run("--brief", "attention_is_all_you_need")
    assert "Attention Is All You Need" in output
    assert "Signal Engine 2.0 Relevance" in output
    assert "Direct Feature Ideas" in output


def test_parsed_status_cli_reports_expected_statuses() -> None:
    output = _run("--parsed-status")
    assert "full_text_parsed" in output
    assert "citation_only" in output
    assert "attention_is_all_you_need" in output
