from __future__ import annotations

from typing import Any

from .asr_backends import detect_local_asr_backend


def build_asr_manifest_row(
    *,
    case_id: str,
    audio_sha256: str,
    audio_asset_id: str = "",
    engine: str = "",
    status: str = "todo_local_asr_not_run",
) -> dict[str, Any]:
    backend = detect_local_asr_backend(engine)
    dependency_status = backend["dependency_status"]
    if dependency_status == "dependency_missing" and status == "todo_local_asr_not_run":
        status = "dependency_missing"
    return {
        "asr_record_id": f"{case_id}_{audio_asset_id or 'audio'}_asr",
        "case_id": case_id,
        "audio_asset_id": audio_asset_id,
        "audio_sha256": audio_sha256,
        "backend": backend["backend"],
        "status": status,
        "dependency_status": dependency_status,
        "asr_text_path": "",
        "segments_path": "",
        "cloud_upload": False,
        "raw_asr_committed": False,
        "raw_asr_text_committed": False,
    }
