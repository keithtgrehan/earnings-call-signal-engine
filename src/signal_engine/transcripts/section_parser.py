from __future__ import annotations

import re

SECTION_MARKERS = [
    ("prepared_remarks", re.compile(r"\b(prepared remarks|presentation|management remarks)\b", re.I)),
    ("qa", re.compile(r"\b(question[- ]and[- ]answer|questions and answers|q&a)\b", re.I)),
]


def section_spans(text: str) -> list[dict[str, int | str]]:
    """Return deterministic section labels and character spans without body text."""
    markers: list[tuple[str, int]] = []
    for label, pattern in SECTION_MARKERS:
        match = pattern.search(text)
        if match:
            markers.append((label, match.start()))
    markers = sorted(set(markers), key=lambda item: item[1])
    if not markers:
        return [{"section_id": "section_0001", "section_type": "unknown", "start_char": 0, "end_char": len(text)}]
    spans: list[dict[str, int | str]] = []
    for index, (label, start) in enumerate(markers, start=1):
        end = markers[index][1] if index < len(markers) else len(text)
        spans.append({"section_id": f"section_{index:04d}", "section_type": label, "start_char": start, "end_char": end})
    if spans and spans[0]["start_char"] != 0:
        spans.insert(0, {"section_id": "section_0000", "section_type": "opening", "start_char": 0, "end_char": int(spans[0]["start_char"])})
    return spans
