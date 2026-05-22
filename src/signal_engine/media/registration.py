from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_media_registration(
    *,
    media_path_ref: str,
    media_type: str,
    source_type: str,
    rights_tier: str,
    asr_allowed: bool = False,
    diarization_allowed: bool = False,
    video_window_allowed: bool = False,
) -> dict[str, Any]:
    return {
        "media_path_ref": media_path_ref,
        "media_type": media_type,
        "duration_if_known": None,
        "source_type": source_type,
        "rights_tier": rights_tier,
        "raw_media_commit_allowed": False,
        "asr_allowed": asr_allowed,
        "diarization_allowed": diarization_allowed,
        "video_window_allowed": video_window_allowed,
        "transcript_alignment_status": "not_aligned",
        "media_copied_into_repo": False,
        "registered_at": datetime.now(UTC).isoformat(),
        "blocked_reason": "Manual-local media metadata only; raw media is not copied or committed.",
    }


def validate_media_registration(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "media_path_ref",
        "media_type",
        "source_type",
        "rights_tier",
        "raw_media_commit_allowed",
        "asr_allowed",
        "diarization_allowed",
        "video_window_allowed",
        "transcript_alignment_status",
    ):
        if field not in row:
            errors.append(f"missing required field {field}")
    if row.get("source_type") != "manual_local":
        errors.append("media registration is manual_local only")
    if row.get("media_type") not in {"audio", "video"}:
        errors.append("media_type must be audio or video")
    if row.get("raw_media_commit_allowed") is not False:
        errors.append("raw_media_commit_allowed must be false by default")
    if row.get("source_type") == "youtube_metadata" or "youtube.com" in str(row.get("media_path_ref", "")):
        errors.append("YouTube media download/registration as raw media is blocked")
    path = Path(str(row.get("media_path_ref", "")))
    if not path.is_absolute():
        errors.append("media_path_ref should be an absolute manual-local path")
    elif path.is_relative_to(Path.cwd()) and "/local_only/" not in str(path):
        errors.append("media_path_ref should point outside repo or an ignored local_only path")
    return errors
