from __future__ import annotations

import csv
import hashlib
import html.parser
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

RESOLVED_ASSET_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "company_name",
    "fiscal_period",
    "event_date",
    "asset_type",
    "source_type",
    "source_url",
    "resolved_asset_url",
    "asset_url_domain",
    "file_ext",
    "content_type_hint",
    "confidence",
    "confidence_reason",
    "rights_status",
    "download_allowed",
    "approval_ref",
    "license_config_ref",
    "blocked_reason",
    "next_action",
    "provenance_hash",
]

ASSET_RANK = {
    "transcript_text": 1,
    "transcript_html": 1,
    "transcript_pdf": 1,
    "audio_mp3": 2,
    "audio_m4a": 2,
    "audio_wav": 2,
    "webcast_metadata": 4,
    "sec_exhibit": 5,
    "slides_metadata": 6,
    "landing_page": 7,
    "blocked": 8,
}

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

AUDIO_EXTENSIONS = {".mp3": "audio_mp3", ".m4a": "audio_m4a", ".wav": "audio_wav"}
TRANSCRIPT_EXTENSIONS = {".txt": "transcript_text", ".pdf": "transcript_pdf", ".html": "transcript_html", ".htm": "transcript_html"}
MEDIA_DOC_RE = re.compile(r"https?://[^\"'\\\s<>]+?\.(?:pdf|txt|html|htm|mp3|m4a|wav)(?:\?[^\"'\\\s<>]*)?", re.I)
TRANSCRIPT_MARKERS = ("transcript", "earnings call transcript", "conference call transcript")
WEBCAST_MARKERS = ("webcast", "replay", "earnings call")
SLIDES_MARKERS = ("slides", "presentation", "deck")
EVENT_PAGE_MARKERS = (
    "earnings",
    "quarter",
    "quarterly",
    "results",
    "webcast",
    "replay",
    "transcript",
    "event",
    "events",
    "presentation",
    "presentations",
)
QUARTER_TOKENS = {
    "Q1": ("q1", "1q", "1st-quarter", "first-quarter"),
    "Q2": ("q2", "2q", "2nd-quarter", "second-quarter"),
    "Q3": ("q3", "3q", "3rd-quarter", "third-quarter"),
    "Q4": ("q4", "4q", "4th-quarter", "fourth-quarter"),
}


@dataclass(frozen=True)
class FetchResponse:
    status_code: int
    content_type: str
    text: str


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.metadata_links: list[str] = []
        self.jsonld: list[str] = []
        self._in_script = False
        self._script_type = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag == "a" and attrs_dict.get("href"):
            label = attrs_dict.get("title", "") or attrs_dict.get("aria-label", "")
            self.links.append((attrs_dict["href"], label))
        if tag == "link" and attrs_dict.get("href") and attrs_dict.get("rel", "").lower() == "canonical":
            self.metadata_links.append(attrs_dict["href"])
        if tag == "meta" and attrs_dict.get("content") and attrs_dict.get("property", "").lower() in {"og:url", "twitter:url"}:
            self.metadata_links.append(attrs_dict["content"])
        if tag == "script":
            self._in_script = True
            self._script_type = attrs_dict.get("type", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_script = False
            self._script_type = ""

    def handle_data(self, data: str) -> None:
        if self._in_script and self._script_type == "application/ld+json":
            self.jsonld.append(data)
        elif self._in_script:
            for match in MEDIA_DOC_RE.findall(data):
                self.metadata_links.append(match)

    def handle_entityref(self, name: str) -> None:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] = RESOLVED_ASSET_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def domain_for(url: str) -> str:
    return urlparse(str(url)).netloc.lower()


def file_ext_for(url: str) -> str:
    return Path(unquote(urlparse(str(url)).path)).suffix.lower()


def has_signed_or_session_query(url: str) -> bool:
    query = parse_qs(urlparse(str(url)).query)
    return any(key.lower() in SIGNED_OR_SESSION_QUERY_KEYS for key in query)


def is_youtube_url(url: str) -> bool:
    host = domain_for(url)
    return "youtube.com" in host or "youtu.be" in host


def is_http_url(url: str) -> bool:
    return urlparse(str(url)).scheme in {"http", "https"}


def same_domain(url: str, root_url: str) -> bool:
    return domain_for(url) == domain_for(root_url)


def rank_asset_type(asset_type: str) -> int:
    return ASSET_RANK.get(asset_type, 99)


def fiscal_period_for(row: dict[str, str]) -> str:
    if row.get("fiscal_period"):
        return row.get("fiscal_period", "")
    fiscal_year = row.get("fiscal_year") or row.get("target_year") or ""
    fiscal_quarter = row.get("fiscal_quarter") or ""
    return " ".join(part for part in [fiscal_year, fiscal_quarter] if part).strip()


def link_matches_case(row: dict[str, str], url: str, label: str = "") -> bool:
    """Keep generic IR pages from assigning unrelated transcripts to a target call."""
    parsed = urlparse(str(url))
    label_parsed = urlparse(str(label)) if str(label).startswith(("http://", "https://")) else None
    label_context = f"{label_parsed.path} {label_parsed.query}" if label_parsed else str(label)
    lower = f"{parsed.path} {parsed.query} {label_context}".lower().replace("_", "-")
    if any(marker in lower for marker in ("investor-day", "company-update", "firm-overview")) and "earnings" not in lower:
        return False
    if not any(marker in lower for marker in ("earnings", "quarter", "transcript", "webcast", "replay", "call")):
        return False
    fiscal_period = str(row.get("fiscal_period") or "")
    fiscal_quarter = str(row.get("fiscal_quarter") or "").upper()
    if not fiscal_quarter:
        match = re.search(r"\bQ([1-4])\b", fiscal_period.upper())
        fiscal_quarter = f"Q{match.group(1)}" if match else ""
    if fiscal_quarter in QUARTER_TOKENS:
        target_tokens = QUARTER_TOKENS[fiscal_quarter]
        all_quarter_tokens = {token for tokens in QUARTER_TOKENS.values() for token in tokens}
        present_tokens = {token for token in all_quarter_tokens if token in lower}
        if not any(token in lower for token in target_tokens):
            return False
        if present_tokens and not any(token in present_tokens for token in target_tokens):
            return False
        if "quarterly-earnings" in lower and not any(token in lower for token in target_tokens):
            return False
    fiscal_year = str(row.get("fiscal_year") or row.get("target_year") or "")
    if not fiscal_year:
        match = re.search(r"\b(20\d{2})\b", fiscal_period)
        fiscal_year = match.group(1) if match else ""
    if fiscal_year:
        years = set(re.findall(r"(?<!\d)(20\d{2})(?!\d)", lower))
        if years and fiscal_year not in years:
            return False
        quarter_years = set(re.findall(r"\b[1-4]q(\d{2})\b", lower))
        if quarter_years and fiscal_year[-2:] not in quarter_years:
            return False
    return True


def event_link_score(row: dict[str, str], url: str, label: str = "") -> int:
    """Score public IR links for event/archive traversal without assigning rights."""
    lower = f"{url} {label}".lower().replace("_", "-")
    score = 0
    score += sum(2 for marker in EVENT_PAGE_MARKERS if marker in lower)
    fiscal_quarter = str(row.get("fiscal_quarter") or "").upper()
    if fiscal_quarter in QUARTER_TOKENS and any(token in lower for token in QUARTER_TOKENS[fiscal_quarter]):
        score += 6
    fiscal_year = str(row.get("fiscal_year") or row.get("target_year") or "")
    if fiscal_year and fiscal_year in lower:
        score += 4
    if fiscal_year and fiscal_year[-2:] and re.search(rf"\b[1-4]q{re.escape(fiscal_year[-2:])}\b", lower):
        score += 4
    if "investor-day" in lower and "earnings" not in lower:
        score -= 8
    if any(marker in lower for marker in ("rss", "email-alert", "privacy", "careers", "governance")):
        score -= 4
    return score


def infer_asset_type(url: str, label: str = "", content_type: str = "") -> tuple[str, str, float]:
    ext = file_ext_for(url)
    lower = f"{url} {label} {content_type}".lower()
    if ext in AUDIO_EXTENSIONS:
        return AUDIO_EXTENSIONS[ext], "direct audio extension/content type", 0.92
    if "audio/mpeg" in lower:
        return "audio_mp3", "direct audio content type", 0.9
    if "audio/mp4" in lower:
        return "audio_m4a", "direct audio content type", 0.9
    if "audio/wav" in lower or "audio/x-wav" in lower:
        return "audio_wav", "direct audio content type", 0.9
    if ext in TRANSCRIPT_EXTENSIONS and any(marker in lower for marker in TRANSCRIPT_MARKERS):
        return TRANSCRIPT_EXTENSIONS[ext], "direct transcript extension and label", 0.95
    if ext in TRANSCRIPT_EXTENSIONS and ext == ".txt":
        return "transcript_text", "direct text asset", 0.8
    if ext in {".html", ".htm"} and any(marker in lower for marker in TRANSCRIPT_MARKERS):
        return "transcript_html", "transcript-like html page", 0.86
    if ext == ".pdf" and any(marker in lower for marker in TRANSCRIPT_MARKERS):
        return "transcript_pdf", "transcript-like pdf", 0.9
    if ext == ".pdf" and any(marker in lower for marker in SLIDES_MARKERS):
        return "slides_metadata", "presentation/slides metadata", 0.72
    if "sec.gov" in lower or "ixviewer" in lower:
        return "sec_exhibit", "SEC filing or exhibit link", 0.74
    if any(marker in lower for marker in WEBCAST_MARKERS) and any(marker in lower for marker in ("webcast", "replay")):
        return "webcast_metadata", "webcast/replay metadata", 0.7
    return "landing_page", "landing page or unresolved event metadata", 0.35


def block_reason_for_url(url: str, source_type: str = "") -> str:
    lower = url.lower()
    if not url:
        return "missing_source_url"
    if is_youtube_url(url):
        return "youtube_media_blocked"
    if has_signed_or_session_query(url):
        return "signed_or_session_url_blocked"
    if any(marker in lower for marker in ("login", "signin", "sign-in", "paywall", "subscription", "drm")):
        return "paywall_or_login_or_drm_blocked"
    if source_type in {"vendor", "licensed_vendor", "transcript_vendor", "earnings_platform"}:
        return "vendor_raw_requires_license_config_ref"
    return ""


def make_candidate(
    row: dict[str, str],
    *,
    asset_type: str,
    source_type: str,
    source_url: str,
    resolved_asset_url: str,
    confidence: float,
    confidence_reason: str,
    rights_status: str = "user_authorized_public_direct",
    download_allowed: bool = False,
    blocked_reason: str = "",
    next_action: str = "",
    content_type_hint: str = "",
    approval_ref: str = "",
    license_config_ref: str = "",
) -> dict[str, str]:
    payload = {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker") or row.get("ticker_symbol", ""),
        "company_name": row.get("company_name", ""),
        "fiscal_period": fiscal_period_for(row),
        "event_date": row.get("event_date") or row.get("earnings_call_date", ""),
        "asset_type": asset_type,
        "source_type": source_type,
        "source_url": source_url,
        "resolved_asset_url": resolved_asset_url,
        "asset_url_domain": domain_for(resolved_asset_url),
        "file_ext": file_ext_for(resolved_asset_url),
        "content_type_hint": content_type_hint,
        "confidence": f"{confidence:.2f}",
        "confidence_reason": confidence_reason,
        "rights_status": rights_status,
        "download_allowed": "true" if download_allowed and not blocked_reason else "false",
        "approval_ref": approval_ref or row.get("approval_ref", "user_authorized_project_assessment_public_direct"),
        "license_config_ref": license_config_ref or row.get("license_config_ref", ""),
        "blocked_reason": blocked_reason,
        "next_action": next_action or ("download" if download_allowed and not blocked_reason else "review_or_skip"),
    }
    payload["provenance_hash"] = stable_hash(payload)
    payload["candidate_id"] = stable_hash(
        {
            "case_id": payload["case_id"],
            "asset_type": asset_type,
            "resolved_asset_url": resolved_asset_url,
            "source_type": source_type,
        }
    )[7:23]
    return {field: payload.get(field, "") for field in RESOLVED_ASSET_FIELDS}


def default_fetcher(url: str) -> tuple[int, str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "SignalEngine/2.0 asset resolver (project assessment; contact: keithtgrehan)",
            "Accept": "text/html,text/plain,application/xhtml+xml,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=8) as response:  # noqa: S310 - public HTTP fetch with guardrails.
        raw = response.read(2_000_000)
        content_type = response.headers.get("content-type", "")
        return int(getattr(response, "status", 200)), content_type, raw.decode("utf-8", errors="replace")


def extract_links(base_url: str, html_text: str) -> list[tuple[str, str]]:
    parser = LinkExtractor()
    parser.feed(html_text)
    extracted: list[tuple[str, str]] = []
    for href, label in parser.links:
        extracted.append((urljoin(base_url, href), label))
    for href in parser.metadata_links:
        extracted.append((urljoin(base_url, href), "metadata url"))
    for raw_json in parser.jsonld:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            payload = raw_json
        for value in _json_urls(payload):
            extracted.append((urljoin(base_url, value), "json-ld url"))
    for match in MEDIA_DOC_RE.findall(html_text):
        extracted.append((urljoin(base_url, match), "script embedded public asset url"))
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for href, label in extracted:
        if href not in seen and is_http_url(href):
            seen.add(href)
            deduped.append((href, label))
    return deduped


def _json_urls(payload: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in {"url", "contenturl", "embedurl", "associatedmedia"}:
                urls.extend(_json_urls(value) if not isinstance(value, str) else [value])
            else:
                urls.extend(_json_urls(value))
    elif isinstance(payload, list):
        for item in payload:
            urls.extend(_json_urls(item))
    elif isinstance(payload, str) and (payload.startswith("http://") or payload.startswith("https://")):
        urls.append(payload)
    return urls


def resolve_official_ir_rows(
    rows: list[dict[str, str]],
    *,
    fetcher: Callable[[str], tuple[int, str, str]] = default_fetcher,
    robots_allowed: Callable[[str], bool] | None = None,
    max_depth: int = 2,
    per_domain_delay_sec: float = 0.0,
    max_pages: int | None = None,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    last_fetch_by_domain: dict[str, float] = {}
    pages_seen = 0
    for row in rows:
        source_url = row.get("source_url") or row.get("official_ir_url") or ""
        if not source_url:
            continue
        if robots_allowed is not None and not robots_allowed(source_url):
            candidates.append(
                make_candidate(
                    row,
                    asset_type="blocked",
                    source_type=row.get("source_type", "official_ir"),
                    source_url=source_url,
                    resolved_asset_url=source_url,
                    confidence=0.0,
                    confidence_reason="robots or source terms blocked fetch",
                    rights_status="blocked",
                    blocked_reason="robots_or_source_terms_hard_block",
                    next_action="manual_review",
                )
            )
            continue
        queue: list[tuple[str, int]] = [(source_url, 0)]
        seen: set[str] = set()
        while queue:
            url, depth = queue.pop(0)
            if url in seen or (max_pages is not None and pages_seen >= max_pages):
                continue
            seen.add(url)
            block_reason = block_reason_for_url(url, row.get("source_type", "official_ir"))
            if block_reason:
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="blocked",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=0.0,
                        confidence_reason="blocked URL class",
                        rights_status="blocked",
                        blocked_reason=block_reason,
                        next_action="skip",
                    )
                )
                continue
            domain = domain_for(url)
            delay_remaining = per_domain_delay_sec - (time.time() - last_fetch_by_domain.get(domain, 0.0))
            if delay_remaining > 0:
                time.sleep(delay_remaining)
            last_fetch_by_domain[domain] = time.time()
            try:
                status_code, content_type, body = fetcher(url)
            except Exception as exc:  # pragma: no cover - exercised against live web.
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="blocked",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=0.0,
                        confidence_reason=f"fetch failed: {type(exc).__name__}",
                        rights_status="metadata_only",
                        blocked_reason="fetch_failed",
                        next_action="manual_review",
                    )
                )
                continue
            pages_seen += 1
            if status_code >= 400:
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="blocked",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=0.0,
                        confidence_reason=f"HTTP {status_code}",
                        rights_status="metadata_only",
                        blocked_reason=f"http_{status_code}",
                        next_action="manual_review",
                        content_type_hint=content_type,
                    )
                )
                continue
            landing_asset, reason, confidence = infer_asset_type(url, content_type=content_type)
            if landing_asset == "landing_page":
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="landing_page",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=confidence,
                        confidence_reason=reason,
                        rights_status="metadata_only",
                        download_allowed=False,
                        next_action="inspect_links",
                        content_type_hint=content_type,
                    )
                )
            else:
                candidates.append(candidate_from_url(row, source_url=source_url, url=url, label="", content_type=content_type))
            if "html" not in content_type.lower():
                continue
            for href, label in extract_links(url, body):
                href_block = block_reason_for_url(href, row.get("source_type", "official_ir"))
                if href_block:
                    candidates.append(
                        make_candidate(
                            row,
                            asset_type="blocked",
                            source_type=row.get("source_type", "official_ir"),
                            source_url=source_url,
                            resolved_asset_url=href,
                            confidence=0.0,
                            confidence_reason="blocked linked URL class",
                            rights_status="blocked",
                            blocked_reason=href_block,
                            next_action="skip",
                        )
                    )
                    continue
                asset_type, _, _ = infer_asset_type(href, label)
                if asset_type != "landing_page":
                    if asset_type in {"transcript_text", "transcript_pdf", "transcript_html", "audio_mp3", "audio_m4a", "audio_wav"} and not link_matches_case(row, href, label):
                        candidates.append(
                            make_candidate(
                                row,
                                asset_type="blocked",
                                source_type=row.get("source_type", "official_ir"),
                                source_url=source_url,
                                resolved_asset_url=href,
                                confidence=0.0,
                                confidence_reason="linked direct asset did not match target fiscal period or earnings-call context",
                                rights_status="metadata_only",
                                blocked_reason="mismatched_event_period_or_non_earnings",
                                next_action="manual_review",
                            )
                        )
                    else:
                        candidates.append(candidate_from_url(row, source_url=source_url, url=href, label=label))
                elif same_domain(href, source_url) and depth + 1 <= max_depth:
                    queue.append((href, depth + 1))
    return sorted(dedupe_candidates(candidates), key=lambda row: (rank_asset_type(row["asset_type"]), row.get("case_id", ""), row.get("resolved_asset_url", "")))


def resolve_official_ir_event_rows(
    rows: list[dict[str, str]],
    *,
    fetcher: Callable[[str], tuple[int, str, str]] = default_fetcher,
    robots_allowed: Callable[[str], bool] | None = None,
    max_depth: int = 2,
    per_domain_delay_sec: float = 0.0,
    max_pages_per_row: int = 3,
) -> list[dict[str, str]]:
    """Resolve official IR pages with event/archive priority and per-call page limits."""
    candidates: list[dict[str, str]] = []
    last_fetch_by_domain: dict[str, float] = {}
    fetch_cache: dict[str, tuple[int, str, str]] = {}
    fetch_errors: dict[str, str] = {}
    for row in rows:
        source_url = row.get("source_url") or row.get("official_ir_url") or ""
        if not source_url:
            continue
        queue: list[tuple[str, int, int]] = [(source_url, 0, event_link_score(row, source_url))]
        seen: set[str] = set()
        pages_seen = 0
        while queue and pages_seen < max_pages_per_row:
            queue.sort(key=lambda item: (-item[2], item[1], item[0]))
            url, depth, _score = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            if robots_allowed is not None and not robots_allowed(url):
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="blocked",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=0.0,
                        confidence_reason="robots or source terms blocked fetch",
                        rights_status="blocked",
                        blocked_reason="robots_or_source_terms_hard_block",
                        next_action="manual_review",
                    )
                )
                continue
            block_reason = block_reason_for_url(url, row.get("source_type", "official_ir"))
            if block_reason:
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="blocked",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=0.0,
                        confidence_reason="blocked URL class",
                        rights_status="blocked",
                        blocked_reason=block_reason,
                        next_action="skip",
                    )
                )
                continue
            try:
                if url in fetch_cache:
                    status_code, content_type, body = fetch_cache[url]
                elif url in fetch_errors:
                    raise RuntimeError(fetch_errors[url])
                else:
                    domain = domain_for(url)
                    delay_remaining = per_domain_delay_sec - (time.time() - last_fetch_by_domain.get(domain, 0.0))
                    if delay_remaining > 0:
                        time.sleep(delay_remaining)
                    last_fetch_by_domain[domain] = time.time()
                    status_code, content_type, body = fetcher(url)
                    fetch_cache[url] = (status_code, content_type, body)
            except Exception as exc:  # pragma: no cover - live network defensive path.
                fetch_errors.setdefault(url, type(exc).__name__)
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="blocked",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=0.0,
                        confidence_reason=f"fetch failed: {type(exc).__name__}",
                        rights_status="metadata_only",
                        blocked_reason="fetch_failed",
                        next_action="manual_review",
                    )
                )
                continue
            pages_seen += 1
            if status_code >= 400:
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="blocked",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=0.0,
                        confidence_reason=f"HTTP {status_code}",
                        rights_status="metadata_only",
                        blocked_reason=f"http_{status_code}",
                        next_action="manual_review",
                        content_type_hint=content_type,
                    )
                )
                continue
            landing_asset, reason, confidence = infer_asset_type(url, content_type=content_type)
            if landing_asset == "landing_page":
                candidates.append(
                    make_candidate(
                        row,
                        asset_type="landing_page",
                        source_type=row.get("source_type", "official_ir"),
                        source_url=source_url,
                        resolved_asset_url=url,
                        confidence=max(confidence, min(0.75, 0.35 + event_link_score(row, url) * 0.03)),
                        confidence_reason="event/archive landing page candidate" if event_link_score(row, url) > 0 else reason,
                        rights_status="metadata_only",
                        download_allowed=False,
                        next_action="inspect_links",
                        content_type_hint=content_type,
                    )
                )
            else:
                if landing_asset in {"transcript_text", "transcript_pdf", "transcript_html", "audio_mp3", "audio_m4a", "audio_wav"} and not link_matches_case(row, url):
                    candidates.append(
                        make_candidate(
                            row,
                            asset_type="blocked",
                            source_type=row.get("source_type", "official_ir"),
                            source_url=source_url,
                            resolved_asset_url=url,
                            confidence=0.0,
                            confidence_reason="direct page did not match target fiscal period or earnings-call context",
                            rights_status="metadata_only",
                            blocked_reason="mismatched_event_period_or_non_earnings",
                            next_action="manual_review",
                            content_type_hint=content_type,
                        )
                    )
                else:
                    candidates.append(candidate_from_url(row, source_url=source_url, url=url, label="", content_type=content_type))
            if "html" not in content_type.lower():
                continue
            for href, label in extract_links(url, body):
                href_block = block_reason_for_url(href, row.get("source_type", "official_ir"))
                if href_block:
                    candidates.append(
                        make_candidate(
                            row,
                            asset_type="blocked",
                            source_type=row.get("source_type", "official_ir"),
                            source_url=source_url,
                            resolved_asset_url=href,
                            confidence=0.0,
                            confidence_reason="blocked linked URL class",
                            rights_status="blocked",
                            blocked_reason=href_block,
                            next_action="skip",
                        )
                    )
                    continue
                asset_type, _, _ = infer_asset_type(href, label)
                if asset_type != "landing_page":
                    if asset_type in {"transcript_text", "transcript_pdf", "transcript_html", "audio_mp3", "audio_m4a", "audio_wav"} and not link_matches_case(row, href, label):
                        candidates.append(
                            make_candidate(
                                row,
                                asset_type="blocked",
                                source_type=row.get("source_type", "official_ir"),
                                source_url=source_url,
                                resolved_asset_url=href,
                                confidence=0.0,
                                confidence_reason="linked direct asset did not match target fiscal period or earnings-call context",
                                rights_status="metadata_only",
                                blocked_reason="mismatched_event_period_or_non_earnings",
                                next_action="manual_review",
                            )
                        )
                    else:
                        candidates.append(candidate_from_url(row, source_url=source_url, url=href, label=label))
                    continue
                score = event_link_score(row, href, label)
                if same_domain(href, source_url) and depth + 1 <= max_depth and score > 0:
                    queue.append((href, depth + 1, score))
    return sorted(dedupe_candidates(candidates), key=lambda row: (rank_asset_type(row["asset_type"]), row.get("case_id", ""), -float(row.get("confidence") or 0), row.get("resolved_asset_url", "")))


def candidate_from_url(row: dict[str, str], *, source_url: str, url: str, label: str = "", content_type: str = "") -> dict[str, str]:
    asset_type, reason, confidence = infer_asset_type(url, label, content_type)
    downloadable = asset_type in {"transcript_text", "transcript_pdf", "transcript_html", "audio_mp3", "audio_m4a", "audio_wav"}
    rights_status = "user_authorized_public_direct" if downloadable else "metadata_only"
    return make_candidate(
        row,
        asset_type=asset_type,
        source_type=row.get("source_type", "official_ir"),
        source_url=source_url,
        resolved_asset_url=url,
        confidence=confidence,
        confidence_reason=reason,
        rights_status=rights_status,
        download_allowed=downloadable,
        next_action="download" if downloadable else "metadata_review",
        content_type_hint=content_type,
    )


def dedupe_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for candidate in candidates:
        key = (candidate.get("case_id", ""), candidate.get("asset_type", ""), candidate.get("resolved_asset_url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def write_resolution_report(path: Path, rows: list[dict[str, str]], *, title: str = "Official IR Asset Resolution") -> None:
    from collections import Counter

    path.parent.mkdir(parents=True, exist_ok=True)
    by_type = Counter(row.get("asset_type", "") for row in rows)
    blockers = Counter(row.get("blocked_reason", "") for row in rows if row.get("blocked_reason"))
    lines = [
        f"# {title}",
        "",
        f"- Candidate rows: {len(rows)}",
        f"- Direct transcript candidates: {sum(by_type[k] for k in ('transcript_text', 'transcript_pdf', 'transcript_html'))}",
        f"- Direct audio candidates: {sum(by_type[k] for k in ('audio_mp3', 'audio_m4a', 'audio_wav'))}",
        f"- Landing pages: {by_type['landing_page']}",
        f"- Blocked candidates: {by_type['blocked']}",
        "",
        "## Asset Types",
    ]
    lines.extend(f"- {key}: {value}" for key, value in sorted(by_type.items()))
    lines.append("")
    lines.append("## Top Blockers")
    lines.extend(f"- {key}: {value}" for key, value in blockers.most_common(10))
    if not blockers:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
