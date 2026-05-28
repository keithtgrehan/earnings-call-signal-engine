from __future__ import annotations

from typing import Any


def alignment_row(*, case_id: str, audio_sha256: str, transcript_sha256: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "audio_sha256": audio_sha256,
        "transcript_sha256": transcript_sha256,
        "alignment_status": "not_run",
        "raw_text_committed": False,
    }
