from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

REQUIRED_NYSE_CASE_FIELDS = {
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_period",
    "call_date",
    "call_datetime",
    "source_candidates",
    "transcript_availability",
    "audio_availability",
    "video_availability",
    "source_rights_status",
    "raw_transcript_allowed",
    "raw_audio_allowed",
    "raw_video_allowed",
    "commit_allowed",
    "training_allowed",
    "eval_allowed",
    "robots_checked",
    "source_terms_checked",
    "paywall_or_login_required",
    "blocked_reason",
    "quality_flags",
    "provenance_complete",
}

RIGHTS_CLEAR_FOR_RAW = {"rights_cleared", "manual_local_rights_cleared", "official_terms_checked"}


def build_case_from_metadata(
    *,
    case_id: str,
    ticker: str,
    company_name: str,
    fiscal_period: str,
    call_date: str,
    call_datetime: str,
    source_candidates: list[dict[str, Any]] | None = None,
    source_rights_status: str = "unknown",
) -> dict[str, Any]:
    """Build metadata-only target-universe rows; this never discovers or downloads raw content."""
    return {
        "case_id": case_id,
        "ticker": ticker,
        "company_name": company_name,
        "exchange": "NYSE",
        "fiscal_period": fiscal_period,
        "call_date": call_date,
        "call_datetime": call_datetime,
        "source_candidates": source_candidates or [],
        "transcript_availability": "candidate_unknown",
        "audio_availability": "candidate_unknown",
        "video_availability": "candidate_unknown",
        "source_rights_status": source_rights_status,
        "raw_transcript_allowed": False,
        "raw_audio_allowed": False,
        "raw_video_allowed": False,
        "commit_allowed": False,
        "training_allowed": False,
        "eval_allowed": False,
        "robots_checked": False,
        "source_terms_checked": False,
        "paywall_or_login_required": "unknown",
        "blocked_reason": "Rights not cleared; target-universe metadata only.",
        "quality_flags": ["target_universe_only"],
        "provenance_complete": False,
        "created_at": datetime.now(UTC).isoformat(),
    }


def validate_nyse_case(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(REQUIRED_NYSE_CASE_FIELDS - set(row)):
        errors.append(f"missing required field {field}")
    if row.get("exchange") != "NYSE":
        errors.append("exchange must be NYSE")
    if str(row.get("call_date", "")) < "2023-01-01":
        errors.append("call_date must be 2023-01-01 or later")
    if not str(row.get("ticker", "")).strip():
        errors.append("ticker is required")
    if not isinstance(row.get("source_candidates"), list):
        errors.append("source_candidates must be a list")
    if not isinstance(row.get("quality_flags"), list):
        errors.append("quality_flags must be a list")
    raw_requested = any(row.get(field) is True for field in ("raw_transcript_allowed", "raw_audio_allowed", "raw_video_allowed"))
    if str(row.get("source_rights_status", "")).lower() in {"unknown", "", "restricted"} and raw_requested:
        errors.append("unknown or restricted rights cannot request raw ingest")
    if row.get("source_rights_status") == "unknown" and row.get("blocked_reason") in {"", None}:
        errors.append("unknown rights require blocked_reason")
    if raw_requested and row.get("source_rights_status") not in RIGHTS_CLEAR_FOR_RAW:
        errors.append("raw ingest requires explicit rights-cleared source_rights_status")
    if row.get("commit_allowed") is True and row.get("raw_transcript_allowed") is not True:
        errors.append("commit_allowed cannot be true unless raw transcript storage is explicitly allowed")
    if row.get("training_allowed") is True and row.get("source_rights_status") not in {"rights_cleared", "manual_local_rights_cleared"}:
        errors.append("training_allowed requires explicit rights-cleared status")
    if row.get("provenance_complete") is True and not row.get("source_candidates"):
        errors.append("provenance_complete cannot be true without source_candidates")
    if row.get("eval_allowed") not in {True, False}:
        errors.append("eval_allowed must be explicit")
    return errors


def validate_nyse_universe(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        case_id = str(row.get("case_id", "")).strip()
        if case_id in seen:
            errors.append(f"row {index}: duplicate case_id {case_id}")
        seen.add(case_id)
        for error in validate_nyse_case(row):
            errors.append(f"row {index}: {error}")
    return errors
