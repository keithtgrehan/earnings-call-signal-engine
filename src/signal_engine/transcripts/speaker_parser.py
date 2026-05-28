from __future__ import annotations

import re

SPEAKER_LINE = re.compile(r"(?m)^(?P<speaker>[A-Z][A-Za-z0-9 .,&'/-]{1,80}):\s+")
QUESTION_HINT = re.compile(r"\b(analyst|question|operator)\b", re.I)
ANSWER_HINT = re.compile(r"\b(ceo|cfo|president|chief|management|officer)\b", re.I)


def speaker_role_for_name(name: str) -> str:
    if QUESTION_HINT.search(name):
        return "questioner"
    if ANSWER_HINT.search(name):
        return "management"
    return "unknown"


def speaker_turn_spans(text: str) -> list[dict[str, int | str]]:
    """Return speaker span metadata only; turn text is intentionally omitted."""
    matches = list(SPEAKER_LINE.finditer(text))
    turns: list[dict[str, int | str]] = []
    for index, match in enumerate(matches, start=1):
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(text)
        speaker = " ".join(match.group("speaker").split())
        turns.append(
            {
                "turn_id": f"turn_{index:04d}",
                "speaker": speaker,
                "speaker_role": speaker_role_for_name(speaker),
                "start_char": start,
                "end_char": end,
            }
        )
    return turns
