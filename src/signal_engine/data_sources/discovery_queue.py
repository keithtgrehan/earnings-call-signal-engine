from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from typing import Any

SOURCE_TYPES = {
    "official_ir",
    "sec_edgar",
    "press_release_8k",
    "licensed_vendor",
    "manual_local",
    "youtube_metadata",
    "restricted_paywalled_login",
    "restricted",
    "paywalled_login",
}


def provenance_hash(row: dict[str, Any]) -> str:
    payload = {
        "source_url": row.get("source_url", ""),
        "source_type": row.get("source_type", ""),
        "content_type_claimed": row.get("content_type_claimed", ""),
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def build_candidate(**kwargs: Any) -> dict[str, Any]:
    row = {
        "source_url": kwargs["source_url"],
        "source_type": kwargs["source_type"],
        "content_type_claimed": kwargs.get("content_type_claimed", "metadata"),
        "rights_tier": kwargs.get("rights_tier", "unknown"),
        "terms_checked": kwargs.get("terms_checked", False),
        "robots_checked": kwargs.get("robots_checked", False),
        "paywall_or_login_status": kwargs.get("paywall_or_login_status", "unknown"),
        "raw_body_allowed": kwargs.get("raw_body_allowed", False),
        "raw_audio_allowed": kwargs.get("raw_audio_allowed", False),
        "raw_video_allowed": kwargs.get("raw_video_allowed", False),
        "stores_body": False,
        "stores_transcript_text": False,
        "stores_media": False,
        "blocked_reason": kwargs.get("blocked_reason", "Rights not cleared; metadata only."),
        "discovered_at": kwargs.get("discovered_at", datetime.now(UTC).isoformat()),
        "fair_access_rate_limit_per_second": kwargs.get("fair_access_rate_limit_per_second"),
        "fair_access_note": kwargs.get("fair_access_note", ""),
    }
    row["provenance_hash"] = provenance_hash(row)
    return row


def validate_candidate(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "source_url",
        "source_type",
        "content_type_claimed",
        "rights_tier",
        "terms_checked",
        "robots_checked",
        "paywall_or_login_status",
        "raw_body_allowed",
        "raw_audio_allowed",
        "raw_video_allowed",
        "blocked_reason",
        "discovered_at",
        "provenance_hash",
    ):
        if field not in row:
            errors.append(f"missing required field {field}")
    source_type = row.get("source_type")
    if source_type not in SOURCE_TYPES:
        errors.append(f"invalid source_type {source_type!r}")
    if source_type == "youtube_metadata" and (row.get("raw_audio_allowed") is True or row.get("raw_video_allowed") is True):
        errors.append("YouTube candidates must be metadata-only by default")
    if source_type == "youtube_metadata" and row.get("raw_body_allowed") is True:
        errors.append("YouTube raw body is blocked by default")
    if source_type == "licensed_vendor" and row.get("raw_body_allowed") is True:
        errors.append("licensed vendor raw body is blocked by default")
    if source_type in {"licensed_vendor", "restricted", "restricted_paywalled_login", "paywalled_login"}:
        if row.get("blocked_reason") in {"", None}:
            errors.append("restricted/paywalled/vendor candidates require blocked_reason")
        if row.get("raw_body_allowed") is True:
            errors.append("restricted/paywalled/vendor raw body is blocked by default")
    if source_type == "sec_edgar":
        if row.get("fair_access_rate_limit_per_second") not in {None, 10}:
            errors.append("SEC/EDGAR fair access rate limit must be at or below 10 requests/second")
        if not str(row.get("fair_access_note", "")).strip():
            errors.append("SEC/EDGAR candidates require fair_access_note")
    if row.get("raw_body_allowed") is True and not (row.get("terms_checked") and row.get("robots_checked")):
        errors.append("raw body requires terms and robots checks")
    for field in ("stores_body", "stores_transcript_text", "stores_media"):
        if row.get(field, False) is True:
            errors.append(f"{field} must remain false for discovery-queue records")
    return errors
