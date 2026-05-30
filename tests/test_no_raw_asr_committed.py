from __future__ import annotations

from pathlib import Path


def test_no_repo_asr_text_payloads_committed() -> None:
    offenders = [path for path in Path("data").rglob("*asr*.txt")]
    assert offenders == []
