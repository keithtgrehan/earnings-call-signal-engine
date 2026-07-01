from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


QUEUE_FIELDS = [
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

PERMITTED_DOWNLOAD_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "source_type",
    "source_url",
    "rights_status",
    "license_config_ref",
    "authorization_ref",
    "approval_ref",
    "approved_by",
    "approved_at",
    "allow_eval_use",
    "allow_training_use",
    "provenance_hash",
]

PERMITTED_SOURCE_TYPES = {
    "company_ir",
    "official_ir",
    "official_ir_transcript",
    "official_ir_webcast",
    "sec_allowed_exhibit",
    "sec_edgar_allowed_exhibit",
    "manually_approved_source",
}

VENDOR_SOURCE_TYPES = {"vendor", "licensed_vendor", "licensed_vendor_blocked", "transcript_vendor", "earnings_platform"}


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


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def is_youtube_url(value: str) -> bool:
    host = urlparse(str(value)).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def source_domain(value: str) -> str:
    parsed = urlparse(str(value))
    return parsed.netloc.lower()
