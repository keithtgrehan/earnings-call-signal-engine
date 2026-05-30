from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
AUDIT_DIR = DESKTOP_WORKSPACE / "_audit"

USER_AGENT = "SignalEngineCorpusAssessment/2.0 (metadata-safe; contact: project owner)"
APPROVAL_REF = "user_authorized_project_assessment"

FIRST30_CANDIDATE_PATH = ROOT / "data" / "acquisition" / "transcript_candidates_first30.csv"
FIRST30_INGESTION_MANIFEST_PATH = ROOT / "data" / "acquisition" / "first30_transcript_ingestion_manifest.csv"
FIRST30_INGESTION_PLAN_PATH = ROOT / "reports" / "acquisition" / "first30_transcript_ingestion_plan.md"
FIRST30_RIGHTS_QUEUE_PATH = ROOT / "reports" / "acquisition" / "first30_source_rights_queue.md"
MANUAL_TRANSCRIPT_REGISTRY_PATH = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
PARSED_TRANSCRIPT_REGISTRY_PATH = ROOT / "data" / "corpus" / "parsed_transcript_text_registry.csv"
DOWNLOAD_STATUS_REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_transcript_download_status.md"

FIRST30_INGESTION_FIELDS = [
    "candidate_id",
    "priority_rank",
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "event_date",
    "source_url",
    "source_domain",
    "source_type",
    "expected_format",
    "source_url_kind",
    "rights_status",
    "approval_required",
    "rights_review_required",
    "download_allowed",
    "blocked_reason",
    "raw_text_committed",
    "commit_allowed",
    "training_allowed",
    "explicit_training_rights_ref",
    "license_config_ref",
    "control_fixture",
    "qna_expected",
    "source_relation",
    "approval_ref",
    "next_action",
    "notes",
]

DOWNLOAD_LOG_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "source_url",
    "attempted",
    "download_status",
    "blocked_reason",
    "raw_local_path",
    "raw_sha256",
    "bytes",
    "content_type",
    "text_parse_status",
    "parsed_text_path",
    "parsed_text_sha256",
    "commit_allowed",
    "training_allowed",
    "eval_allowed",
    "approval_ref",
    "provenance_path",
]

PARSED_TRANSCRIPT_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "source_url",
    "raw_local_path",
    "raw_sha256",
    "parsed_text_path",
    "parsed_text_sha256",
    "text_parse_status",
    "parser",
    "content_type",
    "bytes",
    "rights_status",
    "eval_allowed",
    "commit_allowed",
    "training_allowed",
    "approval_ref",
    "registered_timestamp",
    "notes",
]

MANUAL_TRANSCRIPT_REGISTRY_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "local_path",
    "sha256",
    "source_url",
    "provenance_path",
    "rights_status",
    "eval_allowed",
    "commit_allowed",
    "training_allowed",
    "approval_ref",
    "registered_timestamp",
    "notes",
]

DIRECT_TEXT_SUFFIXES = {".pdf", ".txt", ".html", ".htm"}
OFFICIAL_CDN_DOMAINS = {"q4cdn.com", "cloudfront.net"}
OFFICIAL_REPLACEMENT_URLS = {
    "hd_2024_q1": "https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/documents/hd-1q24-transcript.pdf",
    "hd_2024_q2": "https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/documents/hd-2q24-transcript.pdf",
    "hd_2024_q3": "https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/documents/hd-3q-24-transcript-vf.pdf?os=__",
    "hd_2024_q4": "https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/documents/hd-4q24-transcript.pdf",
}
VENDOR_MARKERS = [
    "factset",
    "callstreet",
    "refinitiv",
    "s&p global market intelligence",
    "standard & poor",
    "bloomberg",
    "seeking alpha",
    "motley fool",
    "thomson reuters",
]
PAYWALL_MARKERS = ("login", "signin", "sign-in", "paywall", "subscription", "drm")
SIGNED_QUERY_KEYS = {
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


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def text_sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_") or "unknown"


def domain_for_url(url: str) -> str:
    return urlparse(url).netloc.lower()


def suffix_for_url(url: str) -> str:
    return Path(unquote(urlparse(url).path)).suffix.lower()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def is_official_cdn_domain(domain: str) -> bool:
    host = domain.lower()
    return any(host == known or host.endswith("." + known) for known in OFFICIAL_CDN_DOMAINS)


def is_direct_text_url(url: str, expected_format: str = "") -> bool:
    suffix = suffix_for_url(url)
    if suffix in DIRECT_TEXT_SUFFIXES:
        return True
    return expected_format.lower() in {"txt", "html"} and suffix in {".txt", ".html", ".htm"}


def has_signed_query(url: str) -> bool:
    query = urlparse(url).query.lower()
    if not query:
        return False
    return any((key + "=") in query for key in SIGNED_QUERY_KEYS)


def hard_blocker_for_source(row: dict[str, str]) -> str:
    url = row.get("source_url", "").strip()
    source_type = row.get("source_type", "").strip().lower()
    lower_url = url.lower()
    rights_status = row.get("rights_status", "").strip().lower()
    notes = " ".join([row.get("blocked_reason", ""), row.get("notes", ""), row.get("next_action", "")]).lower()
    if not url:
        return "missing_source_url"
    if row.get("exchange") and row.get("exchange") != "NYSE":
        return "non_nyse"
    if row.get("commit_allowed", "false").strip().lower() == "true":
        return "commit_allowed_must_be_false"
    if row.get("training_allowed", "false").strip().lower() == "true" and not row.get("explicit_training_rights_ref"):
        return "training_requires_explicit_training_rights_ref"
    if "youtube.com" in lower_url or "youtu.be" in lower_url:
        return "youtube_media_requires_written_authorization"
    if source_type in {"vendor", "licensed_vendor", "transcript_vendor", "earnings_platform"} and not row.get("license_config_ref"):
        return "vendor_raw_requires_license_config_ref"
    if any(marker in lower_url for marker in PAYWALL_MARKERS):
        return "paywall_login_or_drm_url"
    if any(marker in notes for marker in ("paywall", "login", "drm", "robots_blocked", "terms_blocked", "hard_block")):
        return "explicit_source_blocker"
    if has_signed_query(url):
        return "signed_or_session_url_blocked"
    if rights_status in {"blocked", "restricted"}:
        return f"rights_status_{rights_status}"
    return ""


def priority_key(row: dict[str, str]) -> tuple[int, str]:
    case_id = row.get("case_id", "")
    ticker = row.get("ticker", "")
    fiscal_quarter = row.get("fiscal_quarter", "")
    fiscal_year = row.get("fiscal_year", "")
    if case_id == "vz_2024_q4":
        return (0, case_id)
    if ticker == "HD" and case_id != "hd_2025_q4":
        order = {"Q3": 1, "Q2": 2, "Q1": 3, "Q4": 4}.get(fiscal_quarter, 9)
        return (10 + order, case_id)
    if ticker == "JPM":
        order = {"Q4": 1, "Q3": 2, "Q2": 3, "Q1": 4}.get(fiscal_quarter, 9)
        return (20 + order, case_id)
    if ticker == "CAT":
        order = {"Q4": 1, "Q3": 2, "Q2": 3, "Q1": 4}.get(fiscal_quarter, 9)
        if fiscal_year == "2024" and fiscal_quarter == "Q4":
            order = 5
        return (30 + order, case_id)
    return (100, case_id)


def call_folder(row: dict[str, str], workspace: Path = DESKTOP_WORKSPACE) -> Path:
    ticker = row.get("ticker", "UNKNOWN")
    company = row.get("company_name", "")
    case_id = row.get("case_id", row.get("candidate_id", "unknown"))
    return workspace / f"{slugify(ticker)}_{slugify(company)}" / slugify(case_id)


def promotion_row(candidate: dict[str, str], priority_rank: int) -> dict[str, str]:
    candidate = dict(candidate)
    replacement_url = OFFICIAL_REPLACEMENT_URLS.get(candidate.get("case_id", ""))
    if replacement_url:
        candidate["source_url"] = replacement_url
        candidate["source_domain"] = domain_for_url(replacement_url)
        candidate["next_action"] = "download_desktop_only"
        candidate["notes"] = (candidate.get("notes", "") + " Official replacement URL resolved from Home Depot IR quarterly earnings listing.").strip()
    domain = candidate.get("source_domain") or domain_for_url(candidate.get("source_url", ""))
    source_url = candidate.get("source_url", "")
    source_type = candidate.get("source_type", "")
    expected_format = candidate.get("expected_format", "")
    blocker = hard_blocker_for_source(candidate)
    official_cdn = is_official_cdn_domain(domain)
    direct_text = is_direct_text_url(source_url, expected_format)
    control = candidate.get("control_fixture", "false").lower() == "true" or candidate.get("candidate_id", "").startswith("control_")
    rights_review_required = candidate.get("approval_required", "false").lower() == "true" or official_cdn
    source_url_kind = "official_ir_cdn_direct" if official_cdn and direct_text else "official_direct" if direct_text else "landing_or_metadata"
    download_allowed = False
    blocked_reason = blocker
    if not blocker and direct_text:
        if source_type in {"official_ir", "official_ir_hosted_third_party"} or official_cdn:
            download_allowed = True
            blocked_reason = ""
    elif not blocker:
        blocked_reason = "direct_transcript_url_required"
    if control:
        download_allowed = False
        blocked_reason = "control_fixture_already_registered"
    notes = candidate.get("notes", "")
    if official_cdn:
        notes = (notes + " Desktop-only assessment download allowed if vendor marker scan remains clean.").strip()
    return {
        "candidate_id": candidate.get("candidate_id", ""),
        "priority_rank": str(priority_rank),
        "case_id": candidate.get("case_id", ""),
        "ticker": candidate.get("ticker", ""),
        "company_name": candidate.get("company_name", ""),
        "exchange": candidate.get("exchange", ""),
        "fiscal_year": candidate.get("fiscal_year", ""),
        "fiscal_quarter": candidate.get("fiscal_quarter", ""),
        "event_date": candidate.get("event_date", ""),
        "source_url": source_url,
        "source_domain": domain,
        "source_type": source_type,
        "expected_format": expected_format,
        "source_url_kind": source_url_kind,
        "rights_status": candidate.get("rights_status", ""),
        "approval_required": candidate.get("approval_required", "true"),
        "rights_review_required": str(rights_review_required).lower(),
        "download_allowed": str(download_allowed).lower(),
        "blocked_reason": blocked_reason,
        "raw_text_committed": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
        "explicit_training_rights_ref": "",
        "license_config_ref": candidate.get("license_config_ref", ""),
        "control_fixture": str(control).lower(),
        "qna_expected": candidate.get("qna_expected", ""),
        "source_relation": "transcript_canonical",
        "approval_ref": APPROVAL_REF if download_allowed else "",
        "next_action": "download_desktop_only" if download_allowed else candidate.get("next_action", "resolve_direct_transcript_url"),
        "notes": notes,
    }


def build_promotion_rows(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    sorted_rows = sorted(candidates, key=priority_key)
    rows: list[dict[str, str]] = []
    for index, candidate in enumerate(sorted_rows, start=1):
        rows.append(promotion_row(candidate, index))
    return rows


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag.lower() in {"p", "div", "br", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag.lower() in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return normalize_text(" ".join(self.parts))


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + ("\n" if text.strip() else "")


def html_to_text(payload: bytes) -> str:
    parser = _TextExtractor()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return parser.text()


def pdf_parser_name() -> str:
    try:
        import pypdf  # noqa: F401

        return "pypdf"
    except Exception:
        return "pdftotext" if shutil.which("pdftotext") else ""


def pdf_to_text(path: Path) -> tuple[str, str]:
    parser = pdf_parser_name()
    if parser == "pypdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return normalize_text("\n\n".join(pages)), parser
    if parser == "pdftotext":
        with tempfile.TemporaryDirectory(prefix="signal_engine_pdf_") as tmp:
            out = Path(tmp) / "out.txt"
            subprocess.run(["pdftotext", "-layout", str(path), str(out)], check=True, capture_output=True)
            return normalize_text(out.read_text(encoding="utf-8", errors="replace")), parser
    return "", ""


def looks_like_vendor_raw(text: str) -> bool:
    lowered = text.lower()
    if not any(marker in lowered for marker in VENDOR_MARKERS):
        return False
    return "copyright" in lowered or "all rights reserved" in lowered or "callstreet" in lowered


def looks_like_transcript(text: str) -> bool:
    lowered = text.lower()
    markers = ["operator", "question-and-answer", "question and answer", "prepared remarks", "conference call"]
    return len(text) >= 1000 and sum(1 for marker in markers if marker in lowered) >= 1


def fetch_url(url: str, timeout: int = 45) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,text/html,text/plain,*/*"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        payload = response.read()
    return payload, content_type


def raw_file_path(row: dict[str, str], content_type: str, workspace: Path = DESKTOP_WORKSPACE) -> Path:
    suffix = suffix_for_url(row.get("source_url", ""))
    if not suffix:
        lowered = content_type.lower()
        suffix = ".pdf" if "pdf" in lowered else ".html" if "html" in lowered else ".txt"
    return call_folder(row, workspace) / "transcript" / f"{slugify(row.get('case_id', 'unknown'))}_{slugify(row.get('candidate_id', 'source'))}{suffix}"


def parsed_text_path(row: dict[str, str], workspace: Path = DESKTOP_WORKSPACE) -> Path:
    return call_folder(row, workspace) / "transcript" / f"{slugify(row.get('case_id', 'unknown'))}_parsed.txt"


def provenance_path(row: dict[str, str], workspace: Path = DESKTOP_WORKSPACE) -> Path:
    return call_folder(row, workspace) / "transcript" / "provenance.json"


def parse_downloaded_transcript(path: Path, payload: bytes, content_type: str) -> tuple[str, str, str]:
    suffix = path.suffix.lower()
    lowered_content_type = content_type.lower()
    if suffix == ".pdf" or "pdf" in lowered_content_type:
        text, parser = pdf_to_text(path)
        if not parser:
            return "", "blocked_parser_missing", ""
        return text, "parsed" if text.strip() else "parsed_empty", parser
    if suffix in {".html", ".htm"} or "html" in lowered_content_type:
        text = html_to_text(payload)
        return text, "parsed" if text.strip() else "parsed_empty", "html_parser"
    text = normalize_text(payload.decode("utf-8", errors="replace"))
    return text, "parsed" if text.strip() else "parsed_empty", "text_decode"


def registry_row_from_parsed(row: dict[str, str], text_path: Path, text_digest: str, provenance: Path) -> dict[str, str]:
    return {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "asset_type": "transcript",
        "local_path": str(text_path),
        "sha256": text_digest,
        "source_url": row.get("source_url", ""),
        "provenance_path": str(provenance),
        "rights_status": "safe_to_download" if row.get("rights_status") else "safe_to_download",
        "eval_allowed": "true",
        "commit_allowed": "false",
        "training_allowed": "false",
        "approval_ref": row.get("approval_ref", APPROVAL_REF),
        "registered_timestamp": now_iso(),
        "notes": "Registered by path and sha256 only; raw transcript file remains in Desktop workspace.",
    }


def dedupe_registry_rows(existing: list[dict[str, str]], new_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_case: dict[str, dict[str, str]] = {}
    for row in existing:
        key = row.get("case_id", "")
        if key:
            by_case[key] = row
    for row in new_rows:
        key = row.get("case_id", "")
        if key:
            by_case[key] = row
    return [by_case[key] for key in sorted(by_case)]
