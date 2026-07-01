from __future__ import annotations

from pathlib import Path

from scripts.validate_transcript_candidates_first30 import validate_file


def test_first30_manifest_has_30_targets_plus_control() -> None:
    summary = validate_file(Path("data/acquisition/transcript_candidates_first30.csv"))
    assert summary["errors"] == []
    assert summary["target_rows"] == 30
    assert summary["control_rows"] == 1


def test_hd_2025_q4_is_control_fixture_only() -> None:
    text = Path("data/acquisition/transcript_candidates_first30.csv").read_text(encoding="utf-8")
    assert "control_hd_2025_q4,hd_2025_q4" in text
    assert "Existing registered control fixture; not counted as a first-30 target." in text
