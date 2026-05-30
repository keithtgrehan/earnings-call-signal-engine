from __future__ import annotations

from typing import Any


def alignment_row(*, case_id: str, audio_sha256: str, transcript_sha256: str) -> dict[str, Any]:
    return {
        "alignment_id": f"{case_id}_audio_transcript_alignment",
        "case_id": case_id,
        "audio_asset_id": f"{case_id}_audio",
        "transcript_asset_id": f"{case_id}_transcript",
        "audio_sha256": audio_sha256,
        "transcript_sha256": transcript_sha256,
        "alignment_status": "not_run",
        "matched_span_count": 0,
        "raw_text_committed": False,
        "notes": "Alignment requires local ASR segments and registered transcript spans.",
    }
