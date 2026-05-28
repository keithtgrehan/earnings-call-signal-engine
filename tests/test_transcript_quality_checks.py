from __future__ import annotations

from signal_engine.transcripts.quality_checks import transcript_quality_flags


def test_quality_checks_flag_empty_and_missing_structure() -> None:
    flags = transcript_quality_flags("", section_count=0, speaker_turn_count=0, qa_pair_count=0)

    assert "empty_transcript" in flags
    assert "no_sections_detected" in flags
    assert "no_speaker_turns_detected" in flags
    assert "no_qa_pairs_detected" in flags


def test_quality_checks_accept_structured_transcript() -> None:
    flags = transcript_quality_flags("x" * 600, section_count=2, speaker_turn_count=4, qa_pair_count=1)

    assert "empty_transcript" not in flags
    assert "short_transcript" not in flags
