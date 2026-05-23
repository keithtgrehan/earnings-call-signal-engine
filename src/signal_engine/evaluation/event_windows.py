from __future__ import annotations

EVENT_WINDOWS = [(-1, 1), (0, 1), (0, 2)]


def supported_event_windows() -> list[dict[str, int]]:
    return [{"start_day": start, "end_day": end} for start, end in EVENT_WINDOWS]
