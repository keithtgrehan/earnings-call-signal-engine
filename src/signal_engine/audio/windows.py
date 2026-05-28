from __future__ import annotations

from typing import Any


def flagged_window_row(*, case_id: str, audio_sha256: str, start_time_sec: float, end_time_sec: float, reason: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "audio_sha256": audio_sha256,
        "start_time_sec": start_time_sec,
        "end_time_sec": end_time_sec,
        "reason": reason,
        "label_type": "review_window",
        "emotion_label": False,
        "stress_label": False,
        "deception_label": False,
    }
