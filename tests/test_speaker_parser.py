from __future__ import annotations

from signal_engine.chunking.speaker_parser import speaker_turn_spans


def test_speaker_parser_outputs_spans_without_turn_text() -> None:
    turns = speaker_turn_spans("CEO: welcome\nAnalyst: question\nCFO: answer")

    assert len(turns) == 3
    assert turns[0]["speaker"] == "CEO"
    assert "welcome" not in str(turns)
