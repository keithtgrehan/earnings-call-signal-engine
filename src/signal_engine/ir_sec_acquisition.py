from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SOURCE_TYPES = {
    "official_ir_metadata",
    "official_ir_permitted_raw",
    "sec_edgar_metadata",
    "sec_exhibit_metadata",
    "manual_local",
    "blocked_restricted",
}

OFFICIAL_IR_SECTIONS = [
    "investor_relations_home",
    "quarterly_results",
    "earnings",
    "events_presentations",
    "webcast_archive",
    "sec_filings",
    "press_releases",
    "presentations_slides",
]

REQUIRED_CANDIDATE_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_period",
    "source_type",
    "source_url_or_ref",
    "source_domain",
    "source_terms_url",
    "robots_url",
    "rights_status",
    "rights_tier",
    "source_terms_checked",
    "robots_checked",
    "paywall_or_login_required",
    "raw_transcript_allowed",
    "raw_audio_allowed",
    "raw_video_allowed",
    "raw_slides_allowed",
    "commit_allowed",
    "eval_allowed",
    "training_allowed",
    "metadata_only",
    "blocked_reason_code",
    "manual_action",
    "last_checked_at",
    "provenance_hash",
]

NO_RAW_CONTENT_FIELDS = {
    "raw_text",
    "raw_body",
    "raw_transcript",
    "transcript_body",
    "transcript_text",
    "audio_bytes",
    "video_bytes",
    "slide_bytes",
    "slides_pdf",
    "filing_body",
}


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _domain(value: str) -> str:
    if "://" not in value:
        return "local" if value.startswith("/") else ""
    parsed = urlparse(value)
    return parsed.netloc.lower()


def make_provenance_hash(row: dict[str, Any]) -> str:
    payload = {
        "candidate_id": row.get("candidate_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "fiscal_period": row.get("fiscal_period", ""),
        "source_type": row.get("source_type", ""),
        "source_url_or_ref": row.get("source_url_or_ref", ""),
        "source_sha256": row.get("source_sha256", ""),
        "approval_ref": row.get("approval_ref", ""),
        "license_config_ref": row.get("license_config_ref", ""),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def case_id_for(ticker: str, fiscal_period: str) -> str:
    return f"irsec_{ticker.strip().lower()}_{fiscal_period.strip().lower()}"


def candidate_id_for(case_id: str, source_type: str, suffix: str) -> str:
    normalized = suffix.strip().lower().replace(" ", "_").replace("/", "_")
    return f"{case_id}_{source_type}_{normalized}"


def current_fiscal_periods(*, lookback_years: int = 5, anchor: datetime | None = None) -> list[str]:
    anchor_dt = anchor or datetime.now(UTC)
    start_year = anchor_dt.year - lookback_years + 1
    current_quarter = ((anchor_dt.month - 1) // 3) + 1
    periods: list[str] = []
    for year in range(start_year, anchor_dt.year + 1):
        max_quarter = current_quarter if year == anchor_dt.year else 4
        for quarter in range(1, max_quarter + 1):
            periods.append(f"{year}_Q{quarter}")
    return periods


def expand_target_periods(targets: Iterable[dict[str, Any]], *, lookback_years: int = 5) -> list[dict[str, Any]]:
    default_periods = current_fiscal_periods(lookback_years=lookback_years)
    expanded: list[dict[str, Any]] = []
    for target in targets:
        periods = target.get("fiscal_periods") or default_periods
        expanded.append({**target, "fiscal_periods": list(periods)})
    return expanded


def target_rows_from_payload(payload: Any, *, lookback_years: int = 5) -> list[dict[str, Any]]:
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("target config must be a list or an object with a targets list")
    configured_lookback = lookback_years
    if isinstance(payload, dict):
        configured_lookback = int(payload.get("lookback_years", payload.get("year_range", {}).get("lookback_years", lookback_years)))
    return expand_target_periods(rows, lookback_years=configured_lookback)


def classify_source_type(url_or_ref: str) -> str:
    lowered = str(url_or_ref).strip().lower()
    if lowered.startswith(("manual-local://", "manual_local://")) or lowered.startswith("/"):
        return "manual_local"
    if lowered.startswith("sec-edgar://") or "sec.gov" in lowered or "edgar" in lowered:
        if "exhibit" in lowered or "/ex-" in lowered or "_ex" in lowered:
            return "sec_exhibit_metadata"
        return "sec_edgar_metadata"
    if lowered.startswith("official-ir://") or "investor" in lowered or "/ir" in lowered:
        return "official_ir_metadata"
    if "youtube.com" in lowered or "youtu.be" in lowered or "licensed-vendor://" in lowered or lowered.startswith("vendor://"):
        return "blocked_restricted"
    return "blocked_restricted"


def normalize_candidate(row: dict[str, Any]) -> dict[str, Any]:
    candidate = dict(row)
    source_ref = str(candidate.get("source_url_or_ref") or candidate.get("source_url") or "")
    source_type = str(candidate.get("source_type") or classify_source_type(source_ref))
    if source_type not in SOURCE_TYPES:
        source_type = classify_source_type(source_ref)
    candidate["source_url_or_ref"] = source_ref
    candidate["source_type"] = source_type
    candidate.setdefault("source_domain", _domain(source_ref))
    candidate.setdefault("source_terms_url", "")
    candidate.setdefault("robots_url", "")
    candidate.setdefault("rights_status", "unknown")
    candidate.setdefault("rights_tier", "unknown")
    candidate.setdefault("source_terms_checked", False)
    candidate.setdefault("robots_checked", False)
    candidate.setdefault("paywall_or_login_required", False)
    candidate.setdefault("raw_transcript_allowed", False)
    candidate.setdefault("raw_audio_allowed", False)
    candidate.setdefault("raw_video_allowed", False)
    candidate.setdefault("raw_slides_allowed", False)
    candidate.setdefault("commit_allowed", False)
    candidate.setdefault("eval_allowed", False)
    candidate.setdefault("training_allowed", False)
    candidate.setdefault("metadata_only", True)
    candidate.setdefault("blocked_reason_code", "")
    candidate.setdefault("manual_action", "")
    candidate.setdefault("last_checked_at", _utc_now())
    candidate.setdefault("candidate_id", candidate_id_for(str(candidate.get("case_id", "")), source_type, source_ref or "candidate"))
    for field in (
        "source_terms_checked",
        "robots_checked",
        "paywall_or_login_required",
        "raw_transcript_allowed",
        "raw_audio_allowed",
        "raw_video_allowed",
        "raw_slides_allowed",
        "commit_allowed",
        "eval_allowed",
        "training_allowed",
        "metadata_only",
    ):
        candidate[field] = _bool(candidate.get(field))
    if "provenance_hash" not in candidate or not str(candidate.get("provenance_hash", "")).startswith("sha256:"):
        candidate["provenance_hash"] = make_provenance_hash(candidate)
    return candidate


def _raw_asset_fields(candidate: dict[str, Any]) -> list[str]:
    return [
        field
        for field in ("raw_transcript_allowed", "raw_audio_allowed", "raw_video_allowed", "raw_slides_allowed")
        if candidate.get(field) is True
    ]


def _has_raw_permission(candidate: dict[str, Any], policy: dict[str, Any], field: str) -> bool:
    policy_field = {
        "raw_transcript_allowed": "allow_raw_transcript_ingest",
        "raw_audio_allowed": "allow_raw_audio_ingest",
        "raw_video_allowed": "allow_raw_video_ingest",
        "raw_slides_allowed": "allow_raw_slides_ingest",
    }[field]
    return _bool(policy.get(policy_field, False))


def _decision(decision: str, reason: str = "", *, metadata_only: bool = False) -> dict[str, Any]:
    return {"decision": decision, "blocked_reason_code": reason, "metadata_only": metadata_only}


def decide_source_use(candidate: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    row = normalize_candidate(candidate)
    source_ref = str(row.get("source_url_or_ref", "")).lower()
    source_type = str(row.get("source_type", ""))
    raw_fields = _raw_asset_fields(row)

    if row.get("paywall_or_login_required") is True:
        return _decision("blocked", "paywall_or_login_required")

    if raw_fields and ("youtube.com" in source_ref or "youtu.be" in source_ref):
        return _decision("blocked", "youtube_raw_media_blocked_without_authorization")

    if raw_fields and ("licensed-vendor://" in source_ref or source_ref.startswith("vendor://")) and not row.get("license_config_ref"):
        return _decision("blocked", "licensed_vendor_without_license_config")

    if source_type in {"sec_edgar_metadata", "sec_exhibit_metadata"}:
        if raw_fields or row.get("raw_body_allowed") is True:
            return _decision("blocked", "sec_metadata_only")
        return _decision("metadata_only", row.get("blocked_reason_code", "sec_metadata_only"), metadata_only=True)

    if not raw_fields and row.get("metadata_only") is True:
        return _decision("metadata_only", str(row.get("blocked_reason_code", "")), metadata_only=True)

    if raw_fields and str(row.get("rights_status", "unknown")).lower() in {"", "unknown", "restricted", "blocked"}:
        return _decision("blocked", "unknown_rights")

    require_terms = _bool(policy.get("require_source_terms_check", True))
    require_robots = _bool(policy.get("require_robots_check", True))
    if raw_fields and require_terms and row.get("source_terms_checked") is not True and not row.get("approval_ref"):
        return _decision("blocked", "source_terms_not_checked")
    if raw_fields and require_robots and row.get("robots_checked") is not True and not row.get("approval_ref"):
        return _decision("blocked", "robots_not_checked")

    for field in raw_fields:
        if not _has_raw_permission(row, policy, field):
            return _decision("blocked", "raw_ingest_disabled_by_policy")

    if raw_fields and source_type == "official_ir_permitted_raw":
        official_policy = policy.get("official_ir", {})
        source_config_allows_raw = isinstance(official_policy, dict) and _bool(official_policy.get("raw_body_allowed", False))
        if not row.get("approval_ref") and not source_config_allows_raw:
            return _decision("blocked", "official_ir_raw_not_approved")

    if raw_fields and _bool(policy.get("require_manual_approval_for_raw", True)):
        if not row.get("approval_ref") and not row.get("license_config_ref"):
            return _decision("blocked", "official_ir_raw_not_approved")

    if row.get("commit_allowed") is True and _bool(policy.get("commit_raw_assets", False)) is not True:
        return _decision("blocked", "raw_commit_forbidden")

    if row.get("training_allowed") is True and not row.get("training_approval_ref"):
        return _decision("blocked", "training_use_forbidden")

    if not str(row.get("provenance_hash", "")).startswith("sha256:"):
        return _decision("blocked", "provenance_incomplete")

    return _decision("allowed", "", metadata_only=False)


def build_asset_availability(candidate_rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    availability: dict[str, dict[str, Any]] = {}
    for raw_row in candidate_rows:
        row = normalize_candidate(raw_row)
        case_id = str(row.get("case_id", ""))
        if not case_id:
            continue
        record = availability.setdefault(
            case_id,
            {
                "case_id": case_id,
                "ticker": row.get("ticker", ""),
                "fiscal_period": row.get("fiscal_period", ""),
                "event_identity_status": "target_only",
                "transcript_status": "not_collected_metadata_only",
                "audio_status": "not_collected_metadata_only",
                "video_status": "not_collected_metadata_only",
                "slides_status": "not_collected_metadata_only",
                "official_ir_candidate": False,
                "sec_candidate": False,
                "exhibit_candidate": False,
                "manual_local_registered": False,
                "permitted_ingest_available": False,
                "rights_status": row.get("rights_status", "unknown"),
                "blocked_reason_code": "",
                "manual_action": "",
                "provenance_complete": False,
            },
        )
        record["ticker"] = record.get("ticker") or row.get("ticker", "")
        record["fiscal_period"] = record.get("fiscal_period") or row.get("fiscal_period", "")
        if row.get("source_type") in {"official_ir_metadata", "official_ir_permitted_raw"}:
            record["official_ir_candidate"] = True
            record["event_identity_status"] = "source_candidate_found"
            if record["transcript_status"] == "not_collected_metadata_only":
                record["transcript_status"] = "official_ir_candidate_rights_pending"
            if record["slides_status"] == "not_collected_metadata_only":
                record["slides_status"] = "official_ir_candidate_rights_pending"
        if row.get("source_type") in {"sec_edgar_metadata", "sec_exhibit_metadata"}:
            record["sec_candidate"] = True
            record["event_identity_status"] = "source_candidate_found"
            if row.get("source_type") == "sec_exhibit_metadata" or row.get("exhibit_metadata_candidate") is True:
                record["exhibit_candidate"] = True
        if row.get("source_type") == "manual_local" or row.get("manual_local_registered") is True:
            record["manual_local_registered"] = True
            record["event_identity_status"] = "manual_verified" if row.get("source_sha256") else record["event_identity_status"]
            record["transcript_status"] = "manual_local_registered_by_path_hash"
            record["provenance_complete"] = bool(row.get("source_sha256"))
        if any(row.get(field) is True for field in ("raw_transcript_allowed", "raw_audio_allowed", "raw_video_allowed", "raw_slides_allowed")):
            record["permitted_ingest_available"] = bool(row.get("approval_ref") or row.get("license_config_ref"))
        if row.get("blocked_reason_code") and not record.get("blocked_reason_code"):
            record["blocked_reason_code"] = row["blocked_reason_code"]
        if row.get("manual_action") and not record.get("manual_action"):
            record["manual_action"] = row["manual_action"]
        if row.get("rights_status"):
            record["rights_status"] = row["rights_status"]
    return availability


def _asset_type_from_field(field: str) -> str:
    return {
        "raw_transcript_allowed": "transcript",
        "raw_audio_allowed": "audio",
        "raw_video_allowed": "video",
        "raw_slides_allowed": "slides",
    }[field]


def build_permitted_ingest_queue(candidate_rows: Iterable[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for raw_row in candidate_rows:
        row = normalize_candidate(raw_row)
        decision = decide_source_use(row, policy)
        if decision["decision"] != "allowed":
            continue
        for raw_field in _raw_asset_fields(row):
            queue.append(
                {
                    "candidate_id": row["candidate_id"],
                    "case_id": row["case_id"],
                    "source_type": row["source_type"],
                    "source_url_or_ref": row["source_url_or_ref"],
                    "asset_type": _asset_type_from_field(raw_field),
                    "allowed_storage": row.get("allowed_storage", "controlled_local_store_only"),
                    "allowed_commit": bool(row.get("commit_allowed", False)),
                    "allowed_eval_use": bool(row.get("eval_allowed", False)),
                    "allowed_training_use": bool(row.get("training_allowed", False)),
                    "source_terms_checked": bool(row.get("source_terms_checked", False)),
                    "robots_checked": bool(row.get("robots_checked", False)),
                    "approval_ref": row.get("approval_ref") or row.get("license_config_ref") or "",
                    "output_path_policy": row.get("output_path_policy", "no_raw_assets_committed"),
                    "blocked_if_missing": True,
                    "provenance_hash": row["provenance_hash"],
                }
            )
    return queue


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("exchange") != "NYSE":
        errors.append("exchange must be NYSE")
    if int(policy.get("lookback_years", 0) or 0) != 5:
        errors.append("lookback_years must be 5")
    if policy.get("default_mode") != "metadata_only":
        errors.append("default_mode must be metadata_only")
    if policy.get("unknown_rights_default") != "blocked":
        errors.append("unknown_rights_default must be blocked")
    if _bool(policy.get("commit_raw_assets", False)):
        errors.append("commit_raw_assets must be false unless a separate explicit commit policy is approved")
    output = policy.get("output", {})
    if isinstance(output, dict) and _bool(output.get("write_raw_assets", False)):
        errors.append("output.write_raw_assets must be false for this metadata-first tool")
    for field in ("allow_raw_transcript_ingest", "allow_raw_audio_ingest", "allow_raw_video_ingest", "allow_raw_slides_ingest"):
        if _bool(policy.get(field, False)):
            errors.append(f"{field} must remain false in the example fail-closed policy")

    sec = policy.get("sec", {})
    if not isinstance(sec, dict):
        errors.append("sec must be an object")
    else:
        max_rps = sec.get("max_requests_per_second", 0)
        try:
            if float(max_rps) > 10:
                errors.append("sec.max_requests_per_second must be <= 10")
        except (TypeError, ValueError):
            errors.append("sec.max_requests_per_second must be numeric")
        if _bool(sec.get("raw_filing_body_downloads", False)):
            errors.append("sec.raw_filing_body_downloads must remain false for this metadata-first tool")
        if _bool(sec.get("enabled", False)) and not str(sec.get("user_agent", "")).strip():
            errors.append("sec.user_agent is required when SEC metadata discovery is enabled")
    official_ir = policy.get("official_ir", {})
    if not isinstance(official_ir, dict):
        errors.append("official_ir must be an object")
    elif _bool(official_ir.get("raw_body_allowed", False)):
        if not (_bool(official_ir.get("source_terms_checked", False)) and _bool(official_ir.get("robots_checked", False))):
            errors.append("official_ir.raw_body_allowed requires source_terms_checked and robots_checked")
    return errors


def validate_source_candidates(rows: Iterable[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, raw_row in enumerate(rows, start=1):
        row = normalize_candidate(raw_row)
        for field in REQUIRED_CANDIDATE_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        for field in NO_RAW_CONTENT_FIELDS:
            if field in raw_row:
                errors.append(f"row {index}: raw content field {field} is not allowed")
        if not str(row.get("provenance_hash", "")).startswith("sha256:"):
            errors.append(f"row {index}: provenance_hash required")
        raw_fields = _raw_asset_fields(row)
        if raw_fields:
            if str(row.get("rights_status", "unknown")).lower() in {"", "unknown", "restricted", "blocked"}:
                errors.append(f"row {index}: unknown rights fail closed for raw use")
            if not row.get("approval_ref") and (row.get("source_terms_checked") is not True or row.get("robots_checked") is not True):
                errors.append(f"row {index}: raw use requires checked source terms and robots or approval_ref")
            if row.get("source_type") in {"sec_edgar_metadata", "sec_exhibit_metadata"}:
                errors.append(f"row {index}: SEC raw body use is disabled by default")
            source_ref = str(row.get("source_url_or_ref", "")).lower()
            if ("licensed-vendor://" in source_ref or source_ref.startswith("vendor://")) and not row.get("license_config_ref"):
                errors.append(f"row {index}: vendor raw use requires license_config_ref")
            if ("youtube.com" in source_ref or "youtu.be" in source_ref) and (row.get("raw_audio_allowed") or row.get("raw_video_allowed")):
                errors.append(f"row {index}: YouTube raw media requires explicit authorization")
        if row.get("commit_allowed") is True and not (row.get("approval_ref") or row.get("license_config_ref")):
            errors.append(f"row {index}: commit_allowed requires explicit approval_ref or license_config_ref")
        if row.get("training_allowed") is True and not row.get("training_approval_ref"):
            errors.append(f"row {index}: training_allowed requires explicit training_approval_ref")
        if row.get("source_type") == "manual_local" and row.get("manual_local_registered") is True:
            if not row.get("source_url_or_ref") or not row.get("source_sha256"):
                errors.append(f"row {index}: manual-local registration requires path/ref and sha256 hash")
        if row.get("metadata_only") is True or row.get("blocked_reason_code") or row.get("source_type") == "blocked_restricted":
            if not row.get("blocked_reason_code"):
                errors.append(f"row {index}: blocked/metadata-only candidates require blocked_reason_code")
            if not str(row.get("manual_action", "")).strip():
                errors.append(f"row {index}: blocked/metadata-only candidates require manual_action")
    return errors


def validate_availability_rows(rows: Iterable[dict[str, Any]]) -> list[str]:
    required = {
        "case_id",
        "ticker",
        "fiscal_period",
        "event_identity_status",
        "transcript_status",
        "audio_status",
        "video_status",
        "slides_status",
        "official_ir_candidate",
        "sec_candidate",
        "manual_local_registered",
        "permitted_ingest_available",
        "rights_status",
        "blocked_reason_code",
        "manual_action",
        "provenance_complete",
    }
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        missing = required.difference(row)
        for field in sorted(missing):
            errors.append(f"row {index}: missing required field {field}")
        for field in NO_RAW_CONTENT_FIELDS:
            if field in row:
                errors.append(f"row {index}: raw content field {field} is not allowed")
        if row.get("permitted_ingest_available") is False and not row.get("blocked_reason_code"):
            errors.append(f"row {index}: unavailable ingest rows require blocked_reason_code")
    return errors


def validate_permitted_ingest_rows(rows: Iterable[dict[str, Any]]) -> list[str]:
    required = {
        "candidate_id",
        "case_id",
        "source_type",
        "source_url_or_ref",
        "asset_type",
        "allowed_storage",
        "allowed_commit",
        "allowed_eval_use",
        "allowed_training_use",
        "source_terms_checked",
        "robots_checked",
        "approval_ref",
        "output_path_policy",
        "blocked_if_missing",
        "provenance_hash",
    }
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        missing = required.difference(row)
        for field in sorted(missing):
            errors.append(f"row {index}: missing required field {field}")
        if not row.get("approval_ref"):
            errors.append(f"row {index}: permitted ingest requires approval_ref or license config reference")
        if row.get("source_terms_checked") is not True:
            errors.append(f"row {index}: permitted ingest requires source_terms_checked=true")
        if row.get("robots_checked") is not True:
            errors.append(f"row {index}: permitted ingest requires robots_checked=true")
        if not str(row.get("provenance_hash", "")).startswith("sha256:"):
            errors.append(f"row {index}: provenance_hash required")
        for field in NO_RAW_CONTENT_FIELDS:
            if field in row:
                errors.append(f"row {index}: raw content field {field} is not allowed")
    return errors


def read_yaml(path: Path) -> Any:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, payload: Any) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
