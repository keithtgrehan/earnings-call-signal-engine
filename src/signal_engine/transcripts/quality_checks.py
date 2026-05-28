from __future__ import annotations


def transcript_quality_flags(text: str, *, section_count: int, speaker_turn_count: int, qa_pair_count: int) -> list[str]:
    flags: list[str] = []
    if not text.strip():
        flags.append("empty_transcript")
    if len(text) < 500:
        flags.append("short_transcript")
    if section_count == 0:
        flags.append("no_sections_detected")
    if speaker_turn_count == 0:
        flags.append("no_speaker_turns_detected")
    if qa_pair_count == 0:
        flags.append("no_qa_pairs_detected")
    return flags
