from __future__ import annotations

from scripts.report_manual_local_vs_ir_sec_gap import build_report_text


def test_manual_local_gap_report_names_controlled_provenance_and_ir_sec_additions() -> None:
    text = build_report_text()

    assert "actual transcript body already in local control" in text
    assert "sha256 hash provenance" in text
    assert "explicit operator-supplied path" in text
    assert "source candidates at scale" in text
    assert "8-K/press release/filing context" in text
    assert "500-call universe status" in text
