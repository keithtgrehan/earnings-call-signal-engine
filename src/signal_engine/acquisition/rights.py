from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

RIGHTS_STATUSES = {
    "safe_to_link",
    "safe_to_download",
    "metadata_only",
    "manual_local_review_only",
    "license_required",
    "blocked",
    "unknown_fail_closed",
}

BLOCKED_REASONS = {
    "non_nyse",
    "outside_lookback",
    "paywall_login",
    "robots_blocked",
    "terms_blocked",
    "vendor_license_missing",
    "youtube_media_blocked",
    "source_unavailable",
    "transcript_not_found",
    "rights_unknown",
    "raw_git_risk",
    "sec_metadata_only",
    "metadata_only_no_raw_download",
    "signed_or_session_url",
    "source_url_required",
    "source_type_not_permitted",
}

PERMITTED_DOWNLOAD_SOURCE_TYPES = {"official_ir", "sec_allowed_exhibit", "manually_approved_source"}


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def is_youtube_url(value: str) -> bool:
    lowered = str(value).lower()
    return "youtube.com" in lowered or "youtu.be" in lowered


def is_vendor_source(row: dict[str, Any]) -> bool:
    source_type = str(row.get("source_type", "")).lower()
    url = str(row.get("source_url") or row.get("source_url_or_ref") or "").lower()
    return source_type in {"vendor", "licensed_vendor", "earnings_platform"} or url.startswith(("licensed-vendor://", "vendor://"))


def is_signed_or_session_url(value: str) -> bool:
    lowered = str(value).lower()
    return any(marker in lowered for marker in ("x-amz-signature=", "signature=", "session=", "token=", "expires="))


def decide_rights(row: dict[str, Any]) -> dict[str, Any]:
    source_type = str(row.get("source_type", "")).strip().lower()
    source_url = str(row.get("source_url") or row.get("source_url_or_ref") or "")
    rights_status = str(row.get("rights_status", "unknown")).strip().lower() or "unknown"
    asset_type = str(row.get("asset_type", "transcript")).strip().lower()
    raw_requested = as_bool(row.get("raw_requested", False))

    if str(row.get("exchange", "NYSE")).strip() and str(row.get("exchange", "NYSE")).strip() != "NYSE":
        return _decision("blocked", "non_nyse", row, asset_type)
    if as_bool(row.get("outside_lookback", False)):
        return _decision("blocked", "outside_lookback", row, asset_type)
    if as_bool(row.get("paywall_or_login_required", False)):
        return _decision("blocked", "paywall_login", row, asset_type)
    if is_signed_or_session_url(source_url):
        return _decision("blocked", "signed_or_session_url", row, asset_type)

    if is_youtube_url(source_url) or source_type == "youtube":
        if raw_requested or asset_type in {"audio", "video"}:
            if not str(row.get("authorization_ref", "")).strip():
                return _decision("metadata_only", "youtube_media_blocked", row, asset_type)
        return _decision("metadata_only", "metadata_only_no_raw_download", row, asset_type)

    if is_vendor_source(row):
        if not str(row.get("license_config_ref", "")).strip():
            return _decision("license_required", "vendor_license_missing", row, asset_type)
        if raw_requested and rights_status == "safe_to_download":
            return _decision("safe_to_download", "", row, asset_type, download_allowed=True)
        return _decision("metadata_only", "metadata_only_no_raw_download", row, asset_type)

    if source_type in {"sec_edgar", "sec_exhibit", "sec_metadata"}:
        if source_type == "sec_allowed_exhibit" and raw_requested and rights_status == "safe_to_download":
            return _decision("safe_to_download", "", row, asset_type, download_allowed=True)
        return _decision("metadata_only", "sec_metadata_only", row, asset_type)

    if source_type in {"manual_local", "manual-local"}:
        if str(row.get("sha256") or row.get("source_sha256") or "").startswith("sha256:"):
            return _decision("manual_local_review_only", "", row, asset_type)
        return _decision("blocked", "rights_unknown", row, asset_type)

    if not raw_requested:
        return _decision("metadata_only", "metadata_only_no_raw_download", row, asset_type)

    if rights_status not in {"safe_to_download", "approved"}:
        return _decision("unknown_fail_closed", "rights_unknown", row, asset_type)
    if not as_bool(row.get("terms_checked", False)):
        return _decision("blocked", "terms_blocked", row, asset_type)
    if not as_bool(row.get("robots_checked", False)):
        return _decision("blocked", "robots_blocked", row, asset_type)
    if not as_bool(row.get("allowed_storage", False)):
        return _decision("blocked", "terms_blocked", row, asset_type)
    return _decision("safe_to_download", "", row, asset_type, download_allowed=True)


def _decision(
    rights_status: str,
    blocked_reason: str,
    row: dict[str, Any],
    asset_type: str,
    *,
    download_allowed: bool = False,
) -> dict[str, Any]:
    return {
        "source_type": row.get("source_type", ""),
        "source_url": row.get("source_url") or row.get("source_url_or_ref") or "",
        "asset_type": asset_type,
        "rights_status": rights_status,
        "blocked_reason": blocked_reason,
        "download_allowed": download_allowed,
        "commit_allowed": False,
        "training_allowed": False,
        "eval_allowed": bool(download_allowed or rights_status == "manual_local_review_only"),
        "notes": row.get("notes", ""),
    }


def validate_permitted_download_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_url = str(row.get("source_url", "")).strip()
    source_type = str(row.get("source_type", "")).strip()
    rights_status = str(row.get("rights_status", "")).strip()

    if rights_status != "safe_to_download":
        errors.append("rights_status must be safe_to_download")
    if not source_url:
        errors.append("source_url is required")
    if source_type not in PERMITTED_DOWNLOAD_SOURCE_TYPES:
        errors.append(f"source_type must be one of {sorted(PERMITTED_DOWNLOAD_SOURCE_TYPES)}")
    if is_youtube_url(source_url) or source_type == "youtube":
        errors.append("YouTube audio/video download is blocked without explicit written authorization")
    if is_vendor_source(row) and not str(row.get("license_config_ref", "")).strip():
        errors.append("vendor raw content requires license_config_ref")
    if is_signed_or_session_url(source_url):
        errors.append("signed, session, token, or expiring URLs are not permitted")
    parsed = urlparse(source_url)
    if parsed.scheme == "file" and Path(parsed.path).suffix.lower() in {".mp3", ".mp4", ".wav", ".m4a", ".mov"}:
        if str(row.get("asset_type", "")).strip() not in {"audio", "video"}:
            errors.append("media file extension requires matching audio/video asset_type")
    return errors
