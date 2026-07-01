from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav"}
TRANSCRIPT_EXTENSIONS = {".pdf", ".html", ".htm", ".txt"}
VENDOR_DOMAINS = {"fool.com", "seekingalpha.com", "factset.com", "refinitiv.com", "alpha-sense.com", "quartr.com"}
SIGNED_QUERY_KEYS = {"token", "signature", "sig", "expires", "x-amz-signature", "x-amz-credential", "session"}

MATCHED_PAIR_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "event_date",
    "transcript_url",
    "prepared_transcript_url",
    "audio_url",
    "webcast_url",
    "source_type",
    "status",
    "blocker",
    "source_relation",
    "review_required",
    "prepared_audio_label",
    "asr_ready",
    "license_config_ref",
    "approval_required",
    "transcript_download_allowed",
    "audio_download_allowed",
    "commit_allowed",
    "training_allowed",
    "pair_status",
    "next_action",
    "notes",
]

VALID_BLOCKERS = {
    "none",
    "source terms review needed",
    "webcast player only",
    "vendor license missing",
    "youtube media blocked",
    "rights unknown",
    "metadata only",
}
VALID_SOURCE_TYPES = {"official_ir", "official_ir_hosted_third_party", "webcast_player", "vendor", "youtube", "manual_local", "sec_metadata"}


def url_domain(url: str) -> str:
    return urlparse(str(url)).netloc.lower()


def url_suffix(url: str) -> str:
    return Path(urlparse(str(url)).path).suffix.lower()


def is_youtube_url(url: str) -> bool:
    host = url_domain(url)
    return "youtube.com" in host or "youtu.be" in host


def is_vendor_url(url: str) -> bool:
    host = url_domain(url)
    return any(host == domain or host.endswith("." + domain) for domain in VENDOR_DOMAINS)


def has_signed_or_session_query(url: str) -> bool:
    query = parse_qs(urlparse(str(url)).query)
    return any(key.lower() in SIGNED_QUERY_KEYS for key in query)


def classify_ir_platform_url(url: str) -> str:
    lower = str(url).lower()
    suffix = url_suffix(url)
    if not url:
        return "missing"
    if is_youtube_url(url):
        return "youtube_media_blocked"
    if has_signed_or_session_query(url):
        return "signed_or_session_url_blocked"
    if is_vendor_url(url):
        return "vendor_restricted"
    if suffix in AUDIO_EXTENSIONS:
        return "direct_audio"
    if suffix in TRANSCRIPT_EXTENSIONS and "transcript" in lower:
        return "direct_transcript"
    if "choruscall.com" in lower or "mediaframe/webcast" in lower or "webcast" in lower:
        return "webcast_player_only"
    return "official_ir_page"


def validate_matched_pair_row(row: dict[str, str], *, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    for field in MATCHED_PAIR_FIELDS:
        if field not in row:
            errors.append(f"missing required column {field}")
    if errors:
        return errors
    if row["source_type"] not in VALID_SOURCE_TYPES:
        errors.append("source_type enum invalid")
    if row["blocker"] not in VALID_BLOCKERS:
        errors.append("blocker enum invalid")
    if row["exchange"] != "NYSE":
        errors.append("exchange must be NYSE")
    if row["commit_allowed"] != "false":
        errors.append("commit_allowed must be false")
    if row["training_allowed"] != "false":
        errors.append("training_allowed must be false")
    audio_url = row.get("audio_url", "")
    audio_kind = classify_ir_platform_url(audio_url) if audio_url else ""
    if audio_url and audio_kind == "direct_audio" and url_suffix(audio_url) not in AUDIO_EXTENSIONS:
        errors.append("direct audio URL must end with allowed audio extension")
    if audio_url and audio_kind == "youtube_media_blocked" and row["blocker"] != "youtube media blocked":
        errors.append("YouTube media must be blocked")
    if audio_url and audio_kind == "vendor_restricted" and not row.get("license_config_ref"):
        errors.append("vendor domains require license_config_ref")
    webcast_url = row.get("webcast_url", "")
    if webcast_url and classify_ir_platform_url(webcast_url) == "direct_audio":
        errors.append("webcast player must not be marked direct audio")
    if "choruscall.com" in webcast_url.lower() and classify_ir_platform_url(webcast_url) != "webcast_player_only":
        errors.append("ChorusCall page must classify as webcast_player_only")
    if row.get("case_id") == "vz_2024_q4" and audio_url and classify_ir_platform_url(audio_url) == "direct_audio":
        if row.get("approval_required") != "true" or row.get("audio_download_allowed") == "true":
            errors.append("VZ direct MP3 must be approval-gated")
    for field in ("transcript_url", "prepared_transcript_url", "audio_url", "webcast_url"):
        value = row.get(field, "")
        if repo_root and value:
            path = Path(value)
            if path.is_absolute():
                try:
                    path.resolve().relative_to(repo_root.resolve())
                    errors.append(f"{field} must not point inside the repo")
                except (OSError, ValueError):
                    pass
    return errors


def resolve_matched_pair_status(row: dict[str, str], *, transcript_registered: bool, audio_registered: bool) -> dict[str, str]:
    if row.get("blocker") not in {"", "none"}:
        status = "candidate"
    elif transcript_registered and audio_registered:
        status = "matched"
    elif transcript_registered or audio_registered:
        status = "partial"
    else:
        status = "candidate"
    if row.get("source_relation") == "prepared_audio_vs_full_transcript" and status == "matched":
        status = "matched_review_required"
    return {
        "case_id": row.get("case_id", ""),
        "pair_status": status,
        "review_required": "true" if row.get("review_required") == "true" or status.endswith("review_required") else "false",
        "source_relation": row.get("source_relation", ""),
    }


def summarize_matched_pair_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    blockers: dict[str, int] = {}
    for row in rows:
        statuses[row.get("status", "")] = statuses.get(row.get("status", ""), 0) + 1
        blockers[row.get("blocker", "")] = blockers.get(row.get("blocker", ""), 0) + 1
    return {"rows": len(rows), "statuses": statuses, "blockers": blockers}
