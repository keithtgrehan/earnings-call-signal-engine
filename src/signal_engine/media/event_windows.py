from __future__ import annotations

from typing import Any


def build_event_windows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        span = row.get("span_hints") or {}
        windows.append(
            {
                "event_window_id": f"window-{index + 1}",
                "case_id": row.get("case_id", ""),
                "source_object_id": row.get("object_id", ""),
                "span_hints": span,
                "media_scope": "sparse_transcript_aligned",
                "full_call_processing_allowed": False,
            }
        )
    return windows
