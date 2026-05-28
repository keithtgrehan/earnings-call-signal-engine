from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")

USER_AUTHORIZED_QUEUE_FIELDS = [
    "source_id",
    "case_id",
    "ticker",
    "company_name",
    "fiscal_year",
    "fiscal_quarter",
    "asset_type",
    "source_type",
    "source_url",
    "source_domain",
    "rights_status",
    "blocked_reason",
    "allow_download",
    "allow_eval_use",
    "allow_training_use",
    "commit_allowed",
    "manual_approval_required",
    "approval_ref",
    "approved_by",
    "approved_at",
    "license_config_ref",
    "explicit_training_rights_ref",
    "source_terms_checked",
    "robots_checked",
    "review_priority",
    "next_action",
    "provenance_hash",
]

USER_AUTHORIZED_PERMITTED_FIELDS = [
    "source_id",
    "case_id",
    "ticker",
    "company_name",
    "fiscal_year",
    "fiscal_quarter",
    "asset_type",
    "source_type",
    "source_url",
    "source_domain",
    "rights_status",
    "allow_download",
    "allow_eval_use",
    "allow_training_use",
    "commit_allowed",
    "approval_ref",
    "approved_by",
    "approved_at",
    "license_config_ref",
    "youtube_written_authorization_ref",
    "explicit_training_rights_ref",
    "provenance_hash",
    "blocked_reason",
]

DOWNLOAD_LOG_FIELDS = [
    "source_id",
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "source_type",
    "source_url",
    "download_status",
    "blocked_reason",
    "local_path",
    "sha256",
    "bytes",
    "content_type",
    "commit_allowed",
    "training_allowed",
    "eval_allowed",
    "approval_ref",
    "provenance_path",
]

TRANSCRIPT_REGISTRY_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "local_path",
    "sha256",
    "rights_status",
    "eval_allowed",
    "commit_allowed",
    "training_allowed",
    "approval_ref",
    "registered_timestamp",
    "notes",
]

AUDIO_REGISTRY_FIELDS = TRANSCRIPT_REGISTRY_FIELDS.copy()

TRANSCRIPT_CHUNK_FIELDS = [
    "chunk_id",
    "case_id",
    "ticker",
    "asset_id",
    "asset_type",
    "chunk_type",
    "section",
    "speaker_role",
    "source_sha256",
    "text_sha256",
    "local_chunk_path",
    "start_char",
    "end_char",
    "start_time_sec",
    "end_time_sec",
    "rights_status",
    "rag_eligible",
    "raw_text_committed",
]

AUDIO_RAG_FIELDS = [
    "record_id",
    "case_id",
    "ticker",
    "audio_asset_id",
    "audio_local_path",
    "source_sha256",
    "rights_status",
    "eval_use_allowed",
    "asr_status",
    "asr_text_path",
    "chunk_manifest_path",
    "notes",
    "created_at",
    "raw_text_committed",
]

SIGNED_OR_SESSION_QUERY_KEYS = {
    "x-amz-signature",
    "x-amz-credential",
    "x-amz-security-token",
    "signature",
    "sig",
    "token",
    "session",
    "sessionid",
    "jwt",
    "expires",
    "policy",
    "auth",
}

VENDOR_SOURCE_TYPES = {"vendor", "licensed_vendor", "licensed_vendor_blocked", "transcript_vendor", "earnings_platform"}
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_policy(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    return payload if isinstance(payload, dict) else {}


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def bytes_sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_") or "unknown"


def source_domain(value: str) -> str:
    parsed = urlparse(str(value))
    return parsed.netloc.lower()


def is_youtube_url(value: str) -> bool:
    host = urlparse(str(value)).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def has_signed_or_session_query(value: str) -> bool:
    query = parse_qs(urlparse(str(value)).query)
    return any(key.lower() in SIGNED_OR_SESSION_QUERY_KEYS for key in query)


def url_suffix(value: str) -> str:
    return Path(unquote(urlparse(str(value)).path)).suffix.lower()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def normalize_source_type(row: dict[str, str]) -> str:
    source_type = str(row.get("source_type", "")).strip()
    asset_type = str(row.get("asset_type", "")).strip()
    if source_type == "official_ir" and asset_type == "transcript":
        return "official_ir_transcript"
    if source_type == "official_ir" and asset_type == "audio":
        return "official_ir_webcast"
    if source_type == "webcast_provider":
        return "official_ir_webcast"
    return source_type


def hard_barrier_reason(row: dict[str, str], policy: dict[str, Any]) -> str:
    source_type = normalize_source_type(row)
    source_url = str(row.get("source_url", "")).strip()
    asset_type = str(row.get("asset_type", "")).strip()
    blocked_reason = str(row.get("blocked_reason", "")).strip().lower()
    lower_url = source_url.lower()

    if not source_url:
        return "missing_source_url"
    if as_bool(row.get("commit_allowed")):
        return "commit_allowed_must_be_false"
    if as_bool(row.get("allow_training_use")) and not row.get("explicit_training_rights_ref"):
        return "training_use_requires_explicit_training_rights_ref"
    if source_type in set(policy.get("blocked_source_types") or []):
        if source_type == "youtube_metadata_only":
            return "youtube_audio_video_requires_written_authorization"
        if source_type in VENDOR_SOURCE_TYPES:
            return "vendor_raw_requires_license_config_ref"
        return f"blocked_source_type:{source_type}"
    if any(marker in lower_url for marker in ("login", "signin", "sign-in", "paywall", "subscription")):
        return "paywall_or_login_blocked"
    if any(marker in blocked_reason for marker in ("paywall", "login")):
        return "paywall_or_login_blocked"
    if "drm" in lower_url or "drm" in blocked_reason:
        return "drm_restricted"
    if has_signed_or_session_query(source_url) or any(marker in blocked_reason for marker in ("signed", "session")):
        return "signed_or_session_url_blocked"
    if any(marker in blocked_reason for marker in ("robots_blocked", "terms_blocked", "hard_block")):
        return "robots_or_source_terms_hard_block"
    if (is_youtube_url(source_url) or source_type == "youtube_metadata_only") and asset_type in {"audio", "video", "video_metadata"}:
        if not row.get("youtube_written_authorization_ref"):
            return "youtube_audio_video_requires_written_authorization"
    if source_type in VENDOR_SOURCE_TYPES and not row.get("license_config_ref"):
        return "vendor_raw_requires_license_config_ref"
    return ""


def call_folder_from_audit(workspace: Path, case_id: str) -> Path:
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    for row in read_csv(audit):
        if row.get("case_id") != case_id:
            continue
        transcript_path = row.get("transcript_local_path", "")
        audio_path = row.get("audio_local_path", "")
        for value in (transcript_path, audio_path):
            path = Path(value)
            if path.name in {"transcript", "audio", "video"}:
                return path.parent
    return workspace / slugify(case_id)


def approved_row_errors(row: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if not as_bool(row.get("allow_download")):
        errors.append("allow_download must be true")
    for field in ("approval_ref", "approved_by", "approved_at", "source_url"):
        if not str(row.get(field, "")).strip():
            errors.append(f"{field} is required")
    if as_bool(row.get("commit_allowed")):
        errors.append("commit_allowed must be false")
    if as_bool(row.get("allow_training_use")) and not row.get("explicit_training_rights_ref"):
        errors.append("allow_training_use requires explicit_training_rights_ref")
    return errors
