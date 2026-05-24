#!/usr/bin/env python3
"""Rights-gated local acquisition for the NYSE 100 earnings-call workspace."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import UTC, date, datetime
import hashlib
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
REPORT_DIR = ROOT / "reports" / "acquisition"

ALLOWED_DOWNLOAD_RIGHTS = {"safe_to_download", "rights_cleared", "manual_local_review_only"}
EVAL_ALLOWED_RIGHTS = {"safe_to_download", "rights_cleared", "manual_local_review_only"}
TRANSCRIPT_ASSET_TYPES = {"transcript"}
AUDIO_ASSET_TYPES = {"audio"}
VIDEO_ASSET_TYPES = {"video_metadata"}
RAW_AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
SIGNED_OR_SESSION_QUERY_KEYS = {
    "x-amz-signature",
    "x-amz-credential",
    "x-amz-security-token",
    "x-amz-expires",
    "awsaccesskeyid",
    "signature",
    "sig",
    "token",
    "session",
    "sessionid",
    "jwt",
    "expires",
    "policy",
    "key-pair-id",
    "auth",
}

AUDIT_FIELDS = [
    "asset_id",
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "calendar_year",
    "earnings_call_date",
    "asset_type",
    "source_url",
    "source_type",
    "rights_status",
    "availability",
    "download_status",
    "blocked_reason",
    "local_path",
    "transcript_local_path",
    "audio_local_path",
    "sha256",
    "content_type",
    "bytes",
    "created_at",
    "provenance_hash",
    "metadata_path",
    "provenance_path",
    "raw_git_committed",
    "license_config_ref",
    "manual_approval_ref",
    "allow_eval_use",
    "allow_training_use",
    "source_domain",
    "folder_path",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            text = " ".join(data.split())
            if text:
                self._parts.append(text)

    def text(self) -> str:
        return "\n".join(self._parts).strip() + "\n"


def coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def truthy(value: Any) -> bool:
    return coerce_bool(value) is True


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_manual_approvals(path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    approvals: list[dict[str, Any]]
    if path.suffix.lower() == ".csv":
        approvals = read_csv(path)
    else:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            approvals = payload.get("approvals") or []
        elif isinstance(payload, list):
            approvals = payload
        else:
            approvals = []
    mapped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in approvals:
        if not isinstance(row, dict):
            continue
        key = (
            str(row.get("case_id", "")).strip(),
            str(row.get("ticker", "") or row.get("ticker_symbol", "")).strip().upper(),
            str(row.get("asset_type", "")).strip(),
            str(row.get("source_url", "")).strip(),
        )
        mapped[key] = row
    return mapped


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return slug or "unknown"


def cutoff_date(as_of: date, years_back: int) -> date:
    try:
        return as_of.replace(year=as_of.year - years_back)
    except ValueError:
        return as_of.replace(month=2, day=28, year=as_of.year - years_back)


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def select_targets(rows: list[dict[str, str]], *, target_count: int, years_back: int, as_of: date | None = None) -> list[dict[str, str]]:
    as_of_date = as_of or datetime.now(UTC).date()
    min_date = cutoff_date(as_of_date, years_back)
    selected: list[dict[str, str]] = []
    for row in rows:
        if str(row.get("exchange", "")).strip() != "NYSE":
            continue
        call_date = parse_date(str(row.get("earnings_call_date", "")))
        if call_date is None or call_date < min_date or call_date > as_of_date:
            continue
        selected.append(row)
        if len(selected) >= target_count:
            break
    return selected


def call_folder_for(workspace: Path, row: dict[str, str]) -> Path:
    ticker = str(row.get("ticker_symbol") or row.get("ticker") or "UNKNOWN").strip().upper()
    company = str(row.get("company_name") or "Unknown").strip()
    call_date = str(row.get("earnings_call_date") or "unknown-date").strip()
    fiscal_year = str(row.get("fiscal_year") or row.get("calendar_year") or "").strip()
    fiscal_quarter = str(row.get("fiscal_quarter") or "").strip()
    period = f"FY{fiscal_year}" if fiscal_year else f"CY{row.get('calendar_year', 'unknown')}"
    if fiscal_quarter:
        period = f"{period}_{fiscal_quarter}"
    call_date_segment = re.sub(r"[^A-Za-z0-9-]+", "_", call_date).strip("_") or "unknown-date"
    return workspace / f"{slugify(ticker)}_{slugify(company)}" / f"{call_date_segment}_{slugify(period)}"


def create_call_tree(call_folder: Path) -> None:
    for child in ("transcript", "audio", "video", "metadata", "provenance", "chunks"):
        (call_folder / child).mkdir(parents=True, exist_ok=True)


def registry_by_case(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("case_id", "")).strip()].append(row)
    return grouped


def fallback_sources(manifest_row: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    case_id = str(manifest_row.get("case_id", "")).strip()
    base = {
        "case_id": case_id,
        "ticker_symbol": str(manifest_row.get("ticker_symbol", "")),
        "company_name": str(manifest_row.get("company_name", "")),
        "fiscal_year": str(manifest_row.get("fiscal_year", "")),
        "fiscal_quarter": str(manifest_row.get("fiscal_quarter", "")),
        "source_type": str(manifest_row.get("source_type", "company_ir")),
        "source_domain": str(manifest_row.get("source_domain", "")),
        "rights_status": str(manifest_row.get("rights_status", "unknown")),
        "raw_download_allowed": "false",
        "blocked_reason": "",
        "manual_action": "Source registry missing; metadata-only fallback.",
        "license_config_ref": "",
        "allow_eval_use": "false",
        "allow_training_use": "false",
        "acquisition_method": str(manifest_row.get("acquisition_method", "")),
        "discovered_timestamp": str(manifest_row.get("discovered_timestamp", "")),
        "provenance_hash": str(manifest_row.get("provenance_hash", "")),
        "notes": str(manifest_row.get("notes", "")),
    }
    for asset_type, source_field, availability_field in (
        ("transcript", "transcript_source_url", "transcript_availability"),
        ("audio", "audio_source_url", "audio_availability"),
        ("video_metadata", "video_source_url", "video_availability"),
    ):
        source_url = str(manifest_row.get(source_field, "")).strip()
        if not source_url:
            continue
        rows.append(
            {
                **base,
                "registry_id": f"{case_id}_{asset_type}_fallback",
                "asset_type": asset_type,
                "source_url": source_url,
                "availability": str(manifest_row.get(availability_field, "unknown")),
            }
        )
    return rows


def infer_asset_type(source: dict[str, str]) -> str:
    explicit = str(source.get("asset_type", "")).strip()
    if explicit in {"transcript", "audio", "video_metadata", "metadata"}:
        return explicit
    source_type = str(source.get("source_type", "")).strip()
    if source_type in {"webcast_provider", "official_ir_webcast", "official_ir_webcast_metadata"}:
        return "audio"
    if source_type in {"youtube", "youtube_metadata_only"}:
        return "video_metadata"
    if source_type in {"sec_edgar", "sec_edgar_metadata", "sec_edgar_metadata_candidate"}:
        return "metadata"
    return "transcript"


def normalized_source_url(source: dict[str, str], manifest_row: dict[str, str], asset_type: str) -> str:
    url = str(source.get("source_url", "")).strip()
    if url:
        return url
    if asset_type == "audio":
        return str(manifest_row.get("audio_source_url", "")).strip()
    if asset_type == "video_metadata":
        return str(manifest_row.get("video_source_url", "")).strip()
    if asset_type == "transcript":
        return str(manifest_row.get("transcript_source_url", "")).strip()
    return str(manifest_row.get("transcript_source_url", "")).strip()


def is_youtube_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def has_signed_or_session_query(url: str) -> bool:
    query = parse_qs(urlparse(url).query)
    return any(key.lower() in SIGNED_OR_SESSION_QUERY_KEYS for key in query)


def url_path_suffix(url: str) -> str:
    parsed = urlparse(url)
    return Path(unquote(parsed.path)).suffix.lower()


def reject_download_url(url: str, asset_type: str) -> str:
    if not url:
        return "missing_source_url"
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https", "file"}:
        return "unsupported_url_scheme"
    lowered = url.lower()
    if any(marker in lowered for marker in ("login", "signin", "sign-in", "paywall", "subscription")):
        return "paywall_or_login_url_blocked"
    if has_signed_or_session_query(url):
        return "signed_or_session_url_blocked"
    if is_youtube_url(url):
        return "youtube_media_download_blocked_without_authorization"
    suffix = url_path_suffix(url)
    if asset_type == "audio" and suffix in VIDEO_SUFFIXES:
        return "video_url_rejected_for_audio"
    if asset_type == "audio" and suffix and suffix not in RAW_AUDIO_SUFFIXES:
        return "non_audio_url_rejected"
    if asset_type == "transcript" and suffix == ".pdf":
        return "pdf_text_extraction_not_enabled"
    return ""


def manual_approval_for(
    approvals: dict[tuple[str, str, str, str], dict[str, Any]],
    *,
    case_id: str,
    ticker: str,
    asset_type: str,
    source_url: str,
) -> dict[str, Any] | None:
    keys = [
        (case_id, ticker.upper(), asset_type, source_url),
        (case_id, ticker.upper(), asset_type, ""),
        (case_id, "", asset_type, source_url),
    ]
    for key in keys:
        if key in approvals:
            return approvals[key]
    return None


def download_decision(
    *,
    source: dict[str, str],
    asset_type: str,
    source_url: str,
    policy: dict[str, Any],
    approval: dict[str, Any] | None,
    run_mode: str,
) -> tuple[str, str]:
    source_type = str(source.get("source_type", "")).strip()
    rights_status = str(source.get("rights_status", "") or "unknown").strip()
    availability = str(source.get("availability", "") or "unknown").strip()
    manual_download = approval is not None and truthy(approval.get("allow_download"))

    if run_mode == "dry-run":
        return "not_attempted", "dry_run_no_download"
    if run_mode == "metadata-only":
        return "metadata_only", "run_mode_metadata_only"
    if asset_type in VIDEO_ASSET_TYPES or source_type in {"youtube", "youtube_metadata_only"} or is_youtube_url(source_url):
        return "blocked", "youtube_media_download_blocked_without_authorization"
    if source_type in set(policy.get("blocked_source_types") or []):
        return "blocked", f"blocked_source_type:{source_type}"
    if source_type in {"licensed_vendor", "licensed_vendor_blocked", "transcript_vendor"}:
        if not str(source.get("license_config_ref", "")).strip():
            return "blocked", "licensed_vendor_raw_blocked_without_license_config"
        if not truthy(policy.get("allow_vendor_downloads")):
            return "blocked", "vendor_downloads_disabled_by_policy"
    if rights_status in {"unknown", "restricted", "blocked"}:
        return "blocked", f"rights_status_{rights_status}_blocked"
    if not truthy(policy.get("enabled")):
        return "metadata_only", "policy_disabled_metadata_only"
    if rights_status == "metadata_only" and not manual_download:
        return "metadata_only", "metadata_only_rights"
    if availability in {"blocked", "paywalled"}:
        return "blocked", f"availability_{availability}_blocked"
    if asset_type == "metadata":
        return "metadata_only", "metadata_source_only"
    if not manual_download:
        if rights_status not in ALLOWED_DOWNLOAD_RIGHTS:
            return "metadata_only", f"rights_status_{rights_status}_metadata_only"
        if not truthy(source.get("raw_download_allowed")):
            return "blocked", "raw_download_allowed_not_true"
    if asset_type == "transcript":
        allowed_types = set(policy.get("allowed_source_types_for_transcript_download") or [])
        if source_type not in allowed_types and not manual_download:
            return "blocked", f"transcript_source_type_not_allowed:{source_type}"
        if not truthy(policy.get("allow_transcript_downloads")) and not manual_download:
            return "metadata_only", "transcript_downloads_disabled_by_policy"
    if asset_type == "audio":
        allowed_types = set(policy.get("allowed_source_types_for_audio_download") or [])
        if source_type not in allowed_types and not manual_download:
            return "blocked", f"audio_source_type_not_allowed:{source_type}"
        if not truthy(policy.get("allow_audio_downloads")) and not manual_download:
            return "metadata_only", "audio_downloads_disabled_by_policy"
    url_rejection = reject_download_url(source_url, asset_type)
    if url_rejection:
        return "blocked", url_rejection
    return "downloaded", ""


def read_source_bytes(source_url: str, user_agent: str) -> tuple[bytes, str]:
    parsed = urlparse(source_url)
    if parsed.scheme == "file":
        local_path = Path(unquote(parsed.path))
        data = local_path.read_bytes()
        guessed, _ = mimetypes.guess_type(str(local_path))
        return data, guessed or "application/octet-stream"
    request = Request(source_url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=20) as response:
        content_type = response.headers.get_content_type() or "application/octet-stream"
        return response.read(), content_type


def html_to_text(data: bytes) -> bytes:
    parser = TextExtractor()
    parser.feed(data.decode("utf-8", errors="replace"))
    return parser.text().encode("utf-8")


def save_download(
    *,
    asset_type: str,
    case_id: str,
    asset_id: str,
    source_url: str,
    call_folder: Path,
    user_agent: str,
) -> tuple[str, str, str, int]:
    data, content_type = read_source_bytes(source_url, user_agent)
    suffix = url_path_suffix(source_url)
    if asset_type == "transcript":
        if "html" in content_type or suffix in {".html", ".htm"}:
            data = html_to_text(data)
            content_type = "text/plain"
        elif suffix == ".pdf" or "pdf" in content_type:
            raise ValueError("pdf_text_extraction_not_enabled")
        target = call_folder / "transcript" / f"{slugify(case_id)}_transcript.txt"
        if target.exists():
            target = call_folder / "transcript" / f"{slugify(asset_id)}.txt"
        target.write_bytes(data)
        return str(target), file_sha256(target), "text/plain", target.stat().st_size
    if asset_type == "audio":
        extension = suffix if suffix in RAW_AUDIO_SUFFIXES else mimetypes.guess_extension(content_type) or ".audio"
        if extension in VIDEO_SUFFIXES:
            raise ValueError("video_url_rejected_for_audio")
        target = call_folder / "audio" / f"{slugify(asset_id)}{extension}"
        target.write_bytes(data)
        return str(target), file_sha256(target), content_type, target.stat().st_size
    raise ValueError(f"unsupported_download_asset_type:{asset_type}")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_audit_row(
    *,
    manifest_row: dict[str, str],
    source: dict[str, str],
    call_folder: Path,
    asset_id: str,
    asset_type: str,
    source_url: str,
    download_status: str,
    blocked_reason: str,
    local_path: str,
    sha256: str,
    content_type: str,
    byte_count: int | str,
    created_at: str,
    provenance_hash: str,
    metadata_path: Path,
    provenance_path: Path,
    approval: dict[str, Any] | None,
) -> dict[str, Any]:
    allow_eval = approval.get("allow_eval_use") if approval else source.get("allow_eval_use", "false")
    allow_training = approval.get("allow_training_use") if approval else source.get("allow_training_use", "false")
    return {
        "asset_id": asset_id,
        "case_id": str(manifest_row.get("case_id", "")),
        "ticker": str(manifest_row.get("ticker_symbol") or manifest_row.get("ticker") or source.get("ticker_symbol", "")).upper(),
        "company_name": str(manifest_row.get("company_name") or source.get("company_name", "")),
        "exchange": str(manifest_row.get("exchange", "")),
        "fiscal_year": str(manifest_row.get("fiscal_year") or source.get("fiscal_year", "")),
        "fiscal_quarter": str(manifest_row.get("fiscal_quarter") or source.get("fiscal_quarter", "")),
        "calendar_year": str(manifest_row.get("calendar_year", "")),
        "earnings_call_date": str(manifest_row.get("earnings_call_date", "")),
        "asset_type": asset_type,
        "source_url": source_url,
        "source_type": str(source.get("source_type", "")),
        "rights_status": str(source.get("rights_status", "") or "unknown"),
        "availability": str(source.get("availability", "") or "unknown"),
        "download_status": download_status,
        "blocked_reason": blocked_reason,
        "local_path": local_path,
        "transcript_local_path": local_path if asset_type == "transcript" else "",
        "audio_local_path": local_path if asset_type == "audio" else "",
        "sha256": sha256,
        "content_type": content_type,
        "bytes": str(byte_count) if byte_count != "" else "",
        "created_at": created_at,
        "provenance_hash": provenance_hash,
        "metadata_path": str(metadata_path),
        "provenance_path": str(provenance_path),
        "raw_git_committed": "false",
        "license_config_ref": str(source.get("license_config_ref", "")),
        "manual_approval_ref": str(approval.get("approval_ref", "")) if approval else "",
        "allow_eval_use": str(allow_eval).lower() if isinstance(allow_eval, bool) else str(allow_eval or "false").lower(),
        "allow_training_use": str(allow_training).lower() if isinstance(allow_training, bool) else str(allow_training or "false").lower(),
        "source_domain": str(source.get("source_domain", "")),
        "folder_path": str(call_folder),
    }


def summary_from_audit(rows: list[dict[str, Any]], targets: list[dict[str, str]]) -> dict[str, Any]:
    blockers = Counter(str(row.get("blocked_reason", "") or "none") for row in rows if row.get("download_status") == "blocked")
    domains = Counter(str(row.get("source_domain", "") or urlparse(str(row.get("source_url", ""))).netloc or "unknown") for row in rows)
    manual_actions = Counter(
        str(row.get("blocked_reason", "") or "metadata_only") for row in rows if row.get("download_status") in {"blocked", "metadata_only"}
    )
    transcript_downloaded_cases = {row["case_id"] for row in rows if row.get("asset_type") == "transcript" and row.get("download_status") == "downloaded"}
    audio_downloaded_cases = {row["case_id"] for row in rows if row.get("asset_type") == "audio" and row.get("download_status") == "downloaded"}
    return {
        "total_companies": len({str(row.get("ticker_symbol") or row.get("ticker")) for row in targets}),
        "total_calls": len({str(row.get("case_id")) for row in targets}),
        "audit_rows": len(rows),
        "transcripts_downloaded": sum(1 for row in rows if row.get("asset_type") == "transcript" and row.get("download_status") == "downloaded"),
        "audio_downloaded": sum(1 for row in rows if row.get("asset_type") == "audio" and row.get("download_status") == "downloaded"),
        "metadata_only_count": sum(1 for row in rows if row.get("download_status") == "metadata_only"),
        "blocked_count": sum(1 for row in rows if row.get("download_status") == "blocked"),
        "safe_to_download_count": sum(1 for row in rows if row.get("rights_status") == "safe_to_download"),
        "chunks_created": 0,
        "rag_ready_calls": len(transcript_downloaded_cases),
        "audio_rag_ready_calls": len(audio_downloaded_cases),
        "top_blockers": blockers.most_common(10),
        "top_domains": domains.most_common(10),
        "manual_actions": manual_actions.most_common(10),
    }


def write_summary_reports(summary: dict[str, Any], rows: list[dict[str, Any]], workspace: Path) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    audit_dir = workspace / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "nyse_100_asset_acquisition_summary.json", summary)
    write_json(audit_dir / "acquisition_summary.json", summary)

    lines = [
        "# NYSE 100 Asset Acquisition Summary",
        "",
        f"- Total companies: {summary['total_companies']}",
        f"- Total calls: {summary['total_calls']}",
        f"- Audit rows: {summary['audit_rows']}",
        f"- Transcript downloads: {summary['transcripts_downloaded']}",
        f"- Audio downloads: {summary['audio_downloaded']}",
        f"- Metadata-only rows: {summary['metadata_only_count']}",
        f"- Blocked rows: {summary['blocked_count']}",
        f"- Safe-to-download rows: {summary['safe_to_download_count']}",
        f"- RAG-ready calls: {summary['rag_ready_calls']}",
        f"- Audio RAG-ready calls: {summary['audio_rag_ready_calls']}",
        "",
        "## Top Blockers",
        "",
        *[f"- `{reason}`: {count}" for reason, count in summary["top_blockers"]],
        "",
        "## Top Domains",
        "",
        *[f"- `{domain}`: {count}" for domain, count in summary["top_domains"]],
    ]
    summary_md = "\n".join(lines) + "\n"
    (REPORT_DIR / "nyse_100_asset_acquisition_summary.md").write_text(summary_md, encoding="utf-8")
    (audit_dir / "acquisition_summary.md").write_text(summary_md, encoding="utf-8")

    blocked = [row for row in rows if row.get("download_status") == "blocked"]
    blocked_lines = [
        "# Blocked Asset Sources",
        "",
        f"Blocked source rows: {len(blocked)}",
        "",
        "| case_id | ticker | asset_type | source_type | source_domain | blocked_reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    blocked_lines.extend(
        f"| {row.get('case_id')} | {row.get('ticker')} | {row.get('asset_type')} | {row.get('source_type')} | "
        f"{row.get('source_domain')} | {row.get('blocked_reason')} |"
        for row in blocked
    )
    (REPORT_DIR / "blocked_asset_sources.md").write_text("\n".join(blocked_lines) + "\n", encoding="utf-8")

    permitted = [row for row in rows if row.get("download_status") == "downloaded"]
    permitted_lines = [
        "# Permitted Download Summary",
        "",
        f"Downloaded source rows: {len(permitted)}",
        "",
        "| case_id | ticker | asset_type | local_path | sha256 |",
        "| --- | --- | --- | --- | --- |",
    ]
    permitted_lines.extend(
        f"| {row.get('case_id')} | {row.get('ticker')} | {row.get('asset_type')} | {row.get('local_path')} | {row.get('sha256')} |"
        for row in permitted
    )
    (REPORT_DIR / "permitted_download_summary.md").write_text("\n".join(permitted_lines) + "\n", encoding="utf-8")


def acquire_assets(
    *,
    manifest_path: Path,
    source_registry_path: Path,
    policy_path: Path,
    manual_approvals_path: Path,
    workspace: Path,
    target_count: int,
    years_back: int,
    run_mode: str,
) -> dict[str, Any]:
    manifest_rows = read_csv(manifest_path)
    registry_rows = read_csv(source_registry_path) if source_registry_path.exists() else []
    policy = read_yaml(policy_path)
    approvals = read_manual_approvals(manual_approvals_path)
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "_audit").mkdir(parents=True, exist_ok=True)

    selected = select_targets(manifest_rows, target_count=target_count, years_back=years_back)
    grouped = registry_by_case(registry_rows)
    audit_rows: list[dict[str, Any]] = []
    request_delay = 1.0 / float(policy.get("max_requests_per_second") or 1)
    user_agent = str(policy.get("user_agent") or "SignalEngine/NYSE100 rights-gated acquisition")
    last_request_at = 0.0

    for manifest_row in selected:
        call_folder = call_folder_for(workspace, manifest_row)
        create_call_tree(call_folder)
        case_id = str(manifest_row.get("case_id", "")).strip()
        ticker = str(manifest_row.get("ticker_symbol") or manifest_row.get("ticker") or "").strip().upper()
        sources = grouped.get(case_id) or fallback_sources(manifest_row)
        for index, source in enumerate(sources, start=1):
            asset_type = infer_asset_type(source)
            source_url = normalized_source_url(source, manifest_row, asset_type)
            registry_id = str(source.get("registry_id", "")).strip() or f"{case_id}_{asset_type}_{index}"
            asset_id = slugify(registry_id)
            approval = manual_approval_for(approvals, case_id=case_id, ticker=ticker, asset_type=asset_type, source_url=source_url)
            created_at = now_iso()
            decision_status, blocked_reason = download_decision(
                source=source,
                asset_type=asset_type,
                source_url=source_url,
                policy=policy,
                approval=approval,
                run_mode=run_mode,
            )
            local_path = ""
            sha256 = ""
            content_type = ""
            byte_count: int | str = ""
            if decision_status == "downloaded":
                elapsed = time.monotonic() - last_request_at
                if elapsed < request_delay:
                    time.sleep(request_delay - elapsed)
                try:
                    local_path, sha256, content_type, byte_count = save_download(
                        asset_type=asset_type,
                        case_id=case_id,
                        asset_id=asset_id,
                        source_url=source_url,
                        call_folder=call_folder,
                        user_agent=user_agent,
                    )
                    last_request_at = time.monotonic()
                except Exception as exc:  # noqa: BLE001 - failure is recorded in provenance/audit.
                    decision_status = "failed"
                    blocked_reason = str(exc)
                    local_path = ""
                    sha256 = ""
                    content_type = ""
                    byte_count = ""

            provenance_payload = {
                "asset_id": asset_id,
                "case_id": case_id,
                "ticker": ticker,
                "asset_type": asset_type,
                "source_url": source_url,
                "source_type": source.get("source_type", ""),
                "rights_status": source.get("rights_status", "unknown"),
                "download_status": decision_status,
                "blocked_reason": blocked_reason,
                "local_path": local_path,
                "source_registry_row": source,
                "manifest_row": manifest_row,
                "manual_approval_ref": approval.get("approval_ref", "") if approval else "",
                "raw_git_committed": False,
            }
            provenance_hash = stable_hash(provenance_payload)
            metadata_path = call_folder / "metadata" / f"{asset_id}.metadata.json"
            provenance_path = call_folder / "provenance" / f"{asset_id}.provenance.json"
            write_json(
                metadata_path,
                {
                    "asset_id": asset_id,
                    "case_id": case_id,
                    "asset_type": asset_type,
                    "source_url": source_url,
                    "source_type": source.get("source_type", ""),
                    "rights_status": source.get("rights_status", "unknown"),
                    "download_status": decision_status,
                    "blocked_reason": blocked_reason,
                    "local_path": local_path,
                    "sha256": sha256,
                    "content_type": content_type,
                    "bytes": byte_count,
                    "created_at": created_at,
                    "provenance_hash": provenance_hash,
                    "raw_git_committed": False,
                },
            )
            write_json(provenance_path, {**provenance_payload, "created_at": created_at, "provenance_hash": provenance_hash})
            audit_rows.append(
                build_audit_row(
                    manifest_row=manifest_row,
                    source=source,
                    call_folder=call_folder,
                    asset_id=asset_id,
                    asset_type=asset_type,
                    source_url=source_url,
                    download_status=decision_status,
                    blocked_reason=blocked_reason,
                    local_path=local_path,
                    sha256=sha256,
                    content_type=content_type,
                    byte_count=byte_count,
                    created_at=created_at,
                    provenance_hash=provenance_hash,
                    metadata_path=metadata_path,
                    provenance_path=provenance_path,
                    approval=approval,
                )
            )

    audit_path = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)
    summary = summary_from_audit(audit_rows, selected)
    write_summary_reports(summary, audit_rows, workspace)
    return {"audit_path": str(audit_path), "summary": summary, "rows": audit_rows}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Populate a rights-gated local NYSE 100 earnings-call asset workspace.")
    parser.add_argument("--manifest", default=str(ROOT / "data" / "acquisition" / "nyse_100_media_manifest.csv"))
    parser.add_argument("--source-registry", default=str(ROOT / "data" / "acquisition" / "nyse_100_media_source_registry.csv"))
    parser.add_argument("--policy", default=str(ROOT / "configs" / "nyse_100_asset_acquisition_policy.example.yml"))
    parser.add_argument("--manual-approvals", default=str(ROOT / "configs" / "nyse_100_manual_approval.example.yml"))
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--target-count", type=int, default=100)
    parser.add_argument("--start-year", type=int, default=2025, help="Accepted for run metadata compatibility; date filtering uses --years-back.")
    parser.add_argument("--years-back", type=int, default=5)
    parser.add_argument("--run-mode", choices=["metadata-only", "permitted-only", "dry-run"], default="permitted-only")
    parser.add_argument("--max-workers", type=int, default=4, help="Accepted for compatibility; downloads remain rate-limited and rights-gated.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_mode = "metadata-only" if args.run_mode == "metadata-only" else args.run_mode
    result = acquire_assets(
        manifest_path=Path(args.manifest),
        source_registry_path=Path(args.source_registry),
        policy_path=Path(args.policy),
        manual_approvals_path=Path(args.manual_approvals),
        workspace=Path(args.workspace),
        target_count=args.target_count,
        years_back=args.years_back,
        run_mode=run_mode,
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    print(f"Audit CSV: {result['audit_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
