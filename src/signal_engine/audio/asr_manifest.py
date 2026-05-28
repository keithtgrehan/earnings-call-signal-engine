from __future__ import annotations

from typing import Any


def build_asr_manifest_row(*, case_id: str, audio_sha256: str, engine: str = "", status: str = "todo_local_asr_not_run") -> dict[str, Any]:
    return {
        "case_id": case_id,
        "audio_sha256": audio_sha256,
        "engine": engine,
        "status": status,
        "cloud_upload": False,
        "raw_asr_text_committed": False,
    }
