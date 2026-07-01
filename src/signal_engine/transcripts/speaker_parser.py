from __future__ import annotations

import re

SPEAKER_LINE = re.compile(r"(?m)^(?P<speaker>[A-Z][A-Za-z0-9 .,&'/-]{1,80}):\s+")
ANALYST_HINT = re.compile(r"\b(analyst|questioner|research|securities|capital markets|bank|j\.?p\.? morgan|goldman|morgan stanley)\b", re.I)
MANAGEMENT_HINT = re.compile(r"\b(ceo|cfo|president|chief|management|officer|chair|treasurer|controller|executive)\b", re.I)
OPERATOR_HINT = re.compile(r"\b(operator|conference coordinator)\b", re.I)
IR_HINT = re.compile(r"\b(investor relations|ir)\b", re.I)


def speaker_role_for_name(name: str) -> str:
    if OPERATOR_HINT.search(name):
        return "operator"
    if IR_HINT.search(name):
        return "investor_relations"
    if ANALYST_HINT.search(name):
        return "analyst"
    if MANAGEMENT_HINT.search(name):
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
