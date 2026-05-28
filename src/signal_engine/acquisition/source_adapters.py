from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any
from urllib.parse import urlparse


SOURCE_CANDIDATE_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "company_name",
    "fiscal_period",
    "event_date",
    "source_type",
    "source_name",
    "source_domain",
    "source_url",
    "discovered_from_url",
    "discovery_method",
    "candidate_kind",
    "rights_status",
    "download_allowed",
    "approval_required",
    "raw_text_committed",
    "license_config_ref",
    "robots_allowed",
    "paywall_status",
    "confidence",
    "notes",
]

RIGHTS_STATUSES = {
    "metadata_only",
    "unknown_fail_closed",
    "approved_manual_local",
    "licensed_vendor_blocked",
    "licensed_vendor_metadata_only",
    "rights_cleared",
    "safe_to_download",
}
FAIL_CLOSED_RIGHTS = {"metadata_only", "unknown_fail_closed", "licensed_vendor_blocked", "licensed_vendor_metadata_only"}
PAID_SOURCE_TYPES = {"paid_transcript_api", "transcript_api", "vendor", "licensed_vendor", "earnings_platform"}
MEDIA_KINDS = {"audio_video", "youtube_or_external_video"}


@dataclass(frozen=True)
class SourceCandidate:
    candidate_id: str
    case_id: str
    ticker: str
    company_name: str
    fiscal_period: str
    event_date: str
    source_type: str
    source_name: str
    source_domain: str
    source_url: str
    discovered_from_url: str
    discovery_method: str
    candidate_kind: str
    rights_status: str
    download_allowed: bool
    approval_required: bool
    raw_text_committed: bool
    license_config_ref: str
    robots_allowed: bool
    paywall_status: str
    confidence: float
    notes: str


def source_domain_for_url(value: str) -> str:
    parsed = urlparse(str(value or ""))
    return parsed.netloc.lower()


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _confidence(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    return max(0.0, min(1.0, score))


def _rights_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    if status in {"", "unknown", "unknown_rights", "rights_unknown"}:
        return "unknown_fail_closed"
    return status if status in RIGHTS_STATUSES else "unknown_fail_closed"


def _stable_id(payload: dict[str, Any]) -> str:
    key = {field: str(payload.get(field, "")) for field in ("case_id", "ticker", "source_type", "source_url", "candidate_kind")}
    digest = hashlib.sha256(json.dumps(key, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return "cand_" + digest[:20]


def _download_allowed(payload: dict[str, Any], rights_status: str) -> bool:
    requested = _as_bool(payload.get("download_allowed"))
    source_type = str(payload.get("source_type", "")).strip().lower()
    candidate_kind = str(payload.get("candidate_kind", "")).strip().lower()
    if rights_status in FAIL_CLOSED_RIGHTS:
        return False
    if candidate_kind in MEDIA_KINDS:
        return False
    if source_type in PAID_SOURCE_TYPES and not str(payload.get("license_config_ref", "")).strip():
        return False
    return requested


def normalize_candidate(candidate: SourceCandidate | dict[str, Any]) -> SourceCandidate:
    payload = asdict(candidate) if isinstance(candidate, SourceCandidate) else dict(candidate)
    rights_status = _rights_status(payload.get("rights_status"))
    source_url = str(payload.get("source_url", "")).strip()
    source_domain = str(payload.get("source_domain") or source_domain_for_url(source_url)).strip().lower()
    normalized = {
        "candidate_id": str(payload.get("candidate_id") or _stable_id({**payload, "source_url": source_url})),
        "case_id": str(payload.get("case_id", "")).strip(),
        "ticker": str(payload.get("ticker", "")).strip().upper(),
        "company_name": str(payload.get("company_name", "")).strip(),
        "fiscal_period": str(payload.get("fiscal_period", "")).strip(),
        "event_date": str(payload.get("event_date", "")).strip(),
        "source_type": str(payload.get("source_type", "company_ir")).strip() or "company_ir",
        "source_name": str(payload.get("source_name", "")).strip(),
        "source_domain": source_domain,
        "source_url": source_url,
        "discovered_from_url": str(payload.get("discovered_from_url", "")).strip(),
        "discovery_method": str(payload.get("discovery_method", "metadata_only_discovery")).strip() or "metadata_only_discovery",
        "candidate_kind": str(payload.get("candidate_kind", "unknown")).strip() or "unknown",
        "rights_status": rights_status,
        "download_allowed": False,
        "approval_required": True,
        "raw_text_committed": False,
        "license_config_ref": str(payload.get("license_config_ref", "")).strip(),
        "robots_allowed": _as_bool(payload.get("robots_allowed")),
        "paywall_status": str(payload.get("paywall_status", "unknown")).strip() or "unknown",
        "confidence": _confidence(payload.get("confidence")),
        "notes": str(payload.get("notes", "")).strip(),
    }
    normalized["download_allowed"] = _download_allowed(normalized, rights_status)
    return SourceCandidate(**normalized)


def validate_candidate(candidate: SourceCandidate | dict[str, Any]) -> list[str]:
    row = normalize_candidate(candidate) if not isinstance(candidate, SourceCandidate) else candidate
    errors: list[str] = []
    if not row.source_url:
        errors.append("source_url is required")
    if row.rights_status not in RIGHTS_STATUSES:
        errors.append("rights_status is invalid")
    if row.download_allowed and row.rights_status in FAIL_CLOSED_RIGHTS:
        errors.append("fail-closed rights_status cannot enable download")
    if row.download_allowed and row.source_type.lower() in PAID_SOURCE_TYPES and not row.license_config_ref:
        errors.append("paid/vendor/API candidates require license_config_ref before raw access")
    if row.download_allowed and row.candidate_kind.lower() in MEDIA_KINDS:
        errors.append("media candidates cannot enable download from discovery output")
    if row.raw_text_committed is not False:
        errors.append("raw_text_committed must be false")
    if not 0.0 <= row.confidence <= 1.0:
        errors.append("confidence must be between 0 and 1")
    return errors


def candidate_to_csv_row(candidate: SourceCandidate | dict[str, Any]) -> dict[str, str]:
    row = normalize_candidate(candidate)
    payload = asdict(row)
    csv_row: dict[str, str] = {}
    for field in SOURCE_CANDIDATE_FIELDS:
        value = payload[field]
        if isinstance(value, bool):
            csv_row[field] = str(value).lower()
        elif isinstance(value, float):
            csv_row[field] = f"{value:.3f}".rstrip("0").rstrip(".") if value else "0"
        else:
            csv_row[field] = str(value)
    return csv_row
