from __future__ import annotations

from pathlib import Path

from signal_engine.corpus.manual_local import build_manual_case_record, validate_manual_case_record


def test_manual_local_parse_does_not_copy_raw_text_when_commit_blocked(tmp_path: Path) -> None:
    transcript = tmp_path / "manual_transcript.txt"
    transcript.write_text(
        "Operator: Prepared remarks begin.\nQuestion-and-Answer Session\nAnalyst: What changed?\nCFO: We are cautious.",
        encoding="utf-8",
    )
    record = build_manual_case_record(
        case_id="manual_demo",
        source_path=transcript,
        rights_tier="manual_supplied",
        commit_allowed=False,
        operator="tester",
    )
    assert record["raw_text_copied"] is False
    assert validate_manual_case_record(record) == []
    assert all("redacted_preview" not in turn for turn in record["speaker_turns"])
    assert {section["section"] for section in record["sections"]} == {"prepared_remarks", "qa"}
