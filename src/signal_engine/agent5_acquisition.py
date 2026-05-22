from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

PILOT_BLOCKED_REASON = "Metadata-only target until rights are cleared."
PILOT_TARGET_PERIOD = "latest_annual_or_q4_2023_plus"
PILOT_FALLBACK_PERIODS = ["previous_annual_or_q4_2023_plus", "next_available_quarter_2023_plus"]

PILOT_COMPANIES = [
    ("JPM", "JPMorgan Chase & Co.", "Financials"),
    ("WMT", "Walmart Inc.", "Consumer Staples"),
    ("HD", "The Home Depot, Inc.", "Consumer Discretionary"),
    ("JNJ", "Johnson & Johnson", "Health Care"),
    ("XOM", "Exxon Mobil Corporation", "Energy"),
    ("BAC", "Bank of America Corporation", "Financials"),
    ("GS", "The Goldman Sachs Group, Inc.", "Financials"),
    ("MS", "Morgan Stanley", "Financials"),
    ("BLK", "BlackRock, Inc.", "Financials"),
    ("AXP", "American Express Company", "Financials"),
    ("CRM", "Salesforce, Inc.", "Information Technology"),
    ("ORCL", "Oracle Corporation", "Information Technology"),
    ("IBM", "International Business Machines Corporation", "Information Technology"),
    ("NOW", "ServiceNow, Inc.", "Information Technology"),
    ("NET", "Cloudflare, Inc.", "Information Technology"),
    ("LLY", "Eli Lilly and Company", "Health Care"),
    ("MRK", "Merck & Co., Inc.", "Health Care"),
    ("PFE", "Pfizer Inc.", "Health Care"),
    ("UNH", "UnitedHealth Group Incorporated", "Health Care"),
    ("CVS", "CVS Health Corporation", "Health Care"),
    ("BA", "The Boeing Company", "Industrials"),
    ("CAT", "Caterpillar Inc.", "Industrials"),
    ("DE", "Deere & Company", "Industrials"),
    ("GE", "GE Aerospace", "Industrials"),
    ("HON", "Honeywell International Inc.", "Industrials"),
    ("KO", "The Coca-Cola Company", "Consumer Staples"),
    ("MCD", "McDonald's Corporation", "Consumer Discretionary"),
    ("NKE", "NIKE, Inc.", "Consumer Discretionary"),
    ("DIS", "The Walt Disney Company", "Communication Services"),
    ("T", "AT&T Inc.", "Communication Services"),
]

SOURCE_CANDIDATE_TYPES = [
    "official_ir_candidate",
    "sec_edgar_metadata_candidate",
    "manual_local_pending",
    "youtube_metadata_only",
    "licensed_vendor_blocked",
]


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def build_nyse_30_targets() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ticker, company_name, sector in PILOT_COMPANIES:
        rows.append(
            {
                "case_id": f"nyse30_{ticker.lower()}_2023_plus",
                "ticker": ticker,
                "company_name": company_name,
                "exchange": "NYSE",
                "sector": sector,
                "primary_target_period": PILOT_TARGET_PERIOD,
                "fallback_periods": list(PILOT_FALLBACK_PERIODS),
                "source_candidates": SOURCE_CANDIDATE_TYPES.copy(),
                "rights_status": "unknown",
                "raw_transcript_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "commit_allowed": False,
                "training_allowed": False,
                "eval_allowed": False,
                "blocked_reason": PILOT_BLOCKED_REASON,
                "provenance_complete": False,
            }
        )
    return rows


def validate_nyse_30_targets(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    expected = [ticker for ticker, _, _ in PILOT_COMPANIES]
    seen = [str(row.get("ticker", "")).strip() for row in rows]
    if seen != expected:
        errors.append("pilot target tickers must match the approved 30-ticker order")
    for index, row in enumerate(rows, start=1):
        for field in (
            "case_id",
            "ticker",
            "company_name",
            "exchange",
            "sector",
            "primary_target_period",
            "fallback_periods",
            "source_candidates",
            "rights_status",
            "raw_transcript_allowed",
            "raw_audio_allowed",
            "raw_video_allowed",
            "commit_allowed",
            "training_allowed",
            "eval_allowed",
            "blocked_reason",
            "provenance_complete",
        ):
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        if row.get("exchange") != "NYSE":
            errors.append(f"row {index}: exchange must be NYSE")
        if row.get("primary_target_period") != PILOT_TARGET_PERIOD:
            errors.append(f"row {index}: primary_target_period must be {PILOT_TARGET_PERIOD}")
        if row.get("fallback_periods") != PILOT_FALLBACK_PERIODS:
            errors.append(f"row {index}: fallback_periods must match the approved 2023+ fallback policy")
        if row.get("source_candidates") != SOURCE_CANDIDATE_TYPES:
            errors.append(f"row {index}: source_candidates must include only approved metadata candidate types")
        if row.get("rights_status") in {"unknown", "restricted", None, ""}:
            if any(row.get(field) is True for field in ("raw_transcript_allowed", "raw_audio_allowed", "raw_video_allowed")):
                errors.append(f"row {index}: unknown/restricted rights cannot allow raw ingest")
        for field in ("raw_transcript_allowed", "raw_audio_allowed", "raw_video_allowed", "commit_allowed", "training_allowed", "eval_allowed"):
            if row.get(field) is not False:
                errors.append(f"row {index}: {field} must be false for metadata-only pilot targets")
        if row.get("blocked_reason") != PILOT_BLOCKED_REASON:
            errors.append(f"row {index}: blocked_reason must explain metadata-only target status")
        if row.get("provenance_complete") is not False:
            errors.append(f"row {index}: provenance_complete must be false until a rights-cleared source is registered")
    return errors


def build_500_call_metadata_universe(seed_targets: list[dict[str, Any]] | None = None, *, count: int = 500) -> list[dict[str, Any]]:
    targets = seed_targets or build_nyse_30_targets()
    periods = ["2023_Q4", "2024_Q1", "2024_Q2", "2024_Q3", "2024_Q4", "2025_Q1"]
    rows: list[dict[str, Any]] = []
    for index in range(count):
        target = targets[index % len(targets)]
        period = periods[(index // len(targets)) % len(periods)]
        rows.append(
            {
                "case_id": f"metadata_universe_{target['ticker'].lower()}_{period.lower()}_{index + 1:03d}",
                "ticker": target["ticker"],
                "company_name": target["company_name"],
                "exchange": target["exchange"],
                "sector": target["sector"],
                "target_period": period,
                "source_candidates": target["source_candidates"],
                "rights_status": "unknown",
                "raw_transcript_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "commit_allowed": False,
                "training_allowed": False,
                "eval_allowed": False,
                "blocked_reason": PILOT_BLOCKED_REASON,
                "quality_flags": ["target_universe_only", "metadata_only", "not_ingested"],
                "provenance_complete": False,
            }
        )
    return rows


def build_source_queue(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    now = datetime.now(UTC).isoformat()
    for target in targets:
        ticker = target["ticker"]
        base = {
            "case_id": target["case_id"],
            "ticker": ticker,
            "company_name": target["company_name"],
            "discovered_at": now,
            "stores_body": False,
            "stores_transcript_text": False,
            "stores_media": False,
        }
        candidates = [
            {
                **base,
                "source_url": f"https://investors.example.com/{ticker.lower()}/events",
                "source_type": "official_ir_candidate",
                "content_type_claimed": "earnings_call_metadata_or_transcript_candidate",
                "rights_tier": "unknown",
                "terms_checked": False,
                "robots_checked": False,
                "paywall_or_login_status": "unknown",
                "raw_body_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "blocked_reason": "Official IR candidate requires source terms and robots review before raw use.",
            },
            {
                **base,
                "source_url": f"sec-edgar://CIK_LOOKUP_REQUIRED/{ticker}",
                "source_type": "sec_edgar_metadata_candidate",
                "content_type_claimed": "8k_or_exhibit_metadata_candidate",
                "rights_tier": "public_domain",
                "terms_checked": True,
                "robots_checked": True,
                "paywall_or_login_status": "not_required",
                "raw_body_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "fair_access_rate_limit_per_second": 10,
                "fair_access_note": "SEC automated access must remain at or below 10 requests/second and identify the user agent.",
                "blocked_reason": "Metadata-only SEC candidate until filing/exhibit rights and relevance are reviewed.",
            },
            {
                **base,
                "source_url": f"manual-local://pending/{ticker}",
                "source_type": "manual_local_pending",
                "content_type_claimed": "operator_supplied_transcript_audio_or_video_path_pending",
                "rights_tier": "manual_supplied",
                "terms_checked": False,
                "robots_checked": False,
                "paywall_or_login_status": "operator_attestation_required",
                "raw_body_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "blocked_reason": "Awaiting operator-supplied local path and rights attestation; raw files are not copied.",
            },
            {
                **base,
                "source_url": f"https://www.youtube.com/results?search_query={ticker}+earnings+call",
                "source_type": "youtube_metadata_only",
                "content_type_claimed": "youtube_video_metadata_candidate",
                "rights_tier": "restricted",
                "terms_checked": False,
                "robots_checked": False,
                "paywall_or_login_status": "platform_terms_apply",
                "raw_body_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "blocked_reason": "YouTube remains metadata-only unless explicit authorization allows media storage.",
            },
            {
                **base,
                "source_url": f"licensed-vendor://blocked/{ticker}",
                "source_type": "licensed_vendor_blocked",
                "content_type_claimed": "vendor_transcript_candidate",
                "rights_tier": "restricted",
                "terms_checked": False,
                "robots_checked": False,
                "paywall_or_login_status": "license_required",
                "raw_body_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "license_config_ref": "",
                "blocked_reason": "Licensed vendor raw ingest is blocked unless license config explicitly permits it.",
            },
        ]
        for candidate in candidates:
            candidate["provenance_hash"] = stable_hash(
                {
                    "case_id": candidate["case_id"],
                    "source_url": candidate["source_url"],
                    "source_type": candidate["source_type"],
                    "content_type_claimed": candidate["content_type_claimed"],
                }
            )
            rows.append(candidate)
    return rows


def validate_source_queue(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in (
            "case_id",
            "ticker",
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
                errors.append(f"row {index}: missing required field {field}")
        if row.get("source_type") not in SOURCE_CANDIDATE_TYPES:
            errors.append(f"row {index}: invalid source_type {row.get('source_type')!r}")
        if row.get("source_type") in {"youtube_metadata_only", "licensed_vendor_blocked"}:
            for field in ("raw_body_allowed", "raw_audio_allowed", "raw_video_allowed"):
                if row.get(field) is not False:
                    errors.append(f"row {index}: {row.get('source_type')} must keep {field}=false")
        if row.get("source_type") == "licensed_vendor_blocked" and row.get("license_config_ref"):
            errors.append(f"row {index}: license_config_ref handling is scaffolded; default vendor rows remain blocked")
        if row.get("source_type") == "sec_edgar_metadata_candidate":
            if row.get("fair_access_rate_limit_per_second") not in {10, "10"}:
                errors.append(f"row {index}: SEC metadata candidates require fair access limit metadata at 10 requests/second")
            if not str(row.get("fair_access_note", "")).strip():
                errors.append(f"row {index}: SEC metadata candidates require fair_access_note")
        for field in ("stores_body", "stores_transcript_text", "stores_media"):
            if row.get(field) is not False:
                errors.append(f"row {index}: {field} must be false")
        if row.get("blocked_reason") in {"", None}:
            errors.append(f"row {index}: blocked cases require blocked_reason")
        if not str(row.get("provenance_hash", "")).startswith("sha256:"):
            errors.append(f"row {index}: provenance_hash must be sha256-prefixed")
    return errors


def build_manual_local_registry(rows: list[dict[str, Any]], *, operator: str = "manual_operator") -> list[dict[str, Any]]:
    registered: list[dict[str, Any]] = []
    now = datetime.now(UTC).isoformat()
    for row in rows:
        source_path = Path(str(row["source_path_ref"]))
        record = {
            "case_id": row["case_id"],
            "ticker": row.get("ticker", ""),
            "source_path_ref": str(source_path),
            "source_sha256": file_sha256(source_path) if source_path.exists() else "missing",
            "media_type": row.get("media_type", "transcript"),
            "source_type": "manual_local",
            "rights_tier": row.get("rights_tier", "manual_supplied"),
            "operator_supplied": True,
            "registered_at": now,
            "operator": row.get("operator", operator),
            "raw_body_allowed": bool(row.get("raw_body_allowed", False)),
            "raw_file_copied_into_repo": False,
            "commit_allowed": bool(row.get("commit_allowed", False)),
            "training_allowed": bool(row.get("training_allowed", False)),
            "eval_allowed": bool(row.get("eval_allowed", False)),
            "blocked_reason": row.get("blocked_reason", "Manual local raw use requires rights review; file registered by path and hash only."),
        }
        record["provenance_hash"] = stable_hash(
            {"case_id": record["case_id"], "source_path_ref": record["source_path_ref"], "source_sha256": record["source_sha256"]}
        )
        registered.append(record)
    return registered


def validate_manual_local_registry(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in (
            "case_id",
            "source_path_ref",
            "source_sha256",
            "media_type",
            "source_type",
            "rights_tier",
            "operator_supplied",
            "registered_at",
            "raw_file_copied_into_repo",
            "commit_allowed",
            "training_allowed",
            "eval_allowed",
            "blocked_reason",
            "provenance_hash",
        ):
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        if row.get("source_type") != "manual_local":
            errors.append(f"row {index}: source_type must be manual_local")
        if row.get("media_type") not in {"transcript", "audio", "video"}:
            errors.append(f"row {index}: media_type must be transcript/audio/video")
        if row.get("raw_file_copied_into_repo") is not False:
            errors.append(f"row {index}: raw file must not be copied into repo")
        if row.get("source_sha256") != "missing" and not str(row.get("source_sha256", "")).startswith("sha256:"):
            errors.append(f"row {index}: source_sha256 must be sha256-prefixed")
        if row.get("rights_tier") in {"unknown", "restricted", ""} and (
            row.get("commit_allowed") or row.get("training_allowed") or row.get("eval_allowed")
        ):
            errors.append(f"row {index}: unknown/restricted manual-local rights cannot allow commit/training/eval")
    return errors
