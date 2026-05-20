#!/usr/bin/env python3
"""Discover and verify public high-signal earnings-call transcript source URLs."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import intake_high_signal_transcripts as intake  # noqa: E402

USER_AGENT = "SignalEngineSourceDiscovery/1.0 (+public transcript source verification; no paywalled sources)"
TARGET_CALLS = 100
DEFAULT_OUTPUT_CSV = ROOT / "data" / "corpus" / "high_signal_source_urls.csv"
DEFAULT_CANDIDATES_JSON = ROOT / "data" / "corpus" / "high_signal_source_candidates.json"
DEFAULT_QUERIES_CSV = ROOT / "data" / "corpus" / "high_signal_source_queries.csv"
DEFAULT_REPORT = ROOT / "reports" / "high_signal_source_discovery.md"
SOURCE_CSV_FIELDS = (
    "case_id",
    "ticker",
    "company_name",
    "fiscal_year",
    "quarter",
    "source_url",
    "source_type",
    "source_domain",
    "confidence",
    "verification_status",
    "transcript_char_estimate",
    "matched_markers",
    "notes",
)
QUERY_CSV_FIELDS = ("case_id", "ticker", "company_name", "fiscal_year", "quarter", "query")
VERIFICATION_STATUSES = {
    "verified",
    "candidate",
    "rejected",
    "blocked",
    "paywalled",
    "robots_disallowed",
    "download_failed",
}
PAYWALL_MARKERS = tuple(intake.BLOCK_PHRASES) + (
    "enable javascript",
    "sign up to continue",
    "create an account",
    "membership required",
    "verify you are human",
)
TRANSCRIPT_MARKERS = tuple(intake.MARKERS)
SOURCE_URL_COLUMNS = ("source_url", "url", "link", "href")

COMPANY_METADATA: dict[str, dict[str, str]] = {
    "NVDA": {"company_name": "NVIDIA Corporation", "company_domain": "nvidia.com"},
    "MSFT": {"company_name": "Microsoft Corporation", "company_domain": "microsoft.com"},
    "GOOGL": {"company_name": "Alphabet Inc.", "company_domain": "abc.xyz"},
    "AMZN": {"company_name": "Amazon.com, Inc.", "company_domain": "amazon.com"},
    "META": {"company_name": "Meta Platforms, Inc.", "company_domain": "meta.com"},
    "AAPL": {"company_name": "Apple Inc.", "company_domain": "apple.com"},
    "AMD": {"company_name": "Advanced Micro Devices, Inc.", "company_domain": "amd.com"},
    "ASML": {"company_name": "ASML Holding N.V.", "company_domain": "asml.com"},
    "TSM": {"company_name": "Taiwan Semiconductor Manufacturing Company Limited", "company_domain": "tsmc.com"},
    "AVGO": {"company_name": "Broadcom Inc.", "company_domain": "broadcom.com"},
    "CRM": {"company_name": "Salesforce, Inc.", "company_domain": "salesforce.com"},
    "SNOW": {"company_name": "Snowflake Inc.", "company_domain": "snowflake.com"},
    "HUBS": {"company_name": "HubSpot, Inc.", "company_domain": "hubspot.com"},
    "NOW": {"company_name": "ServiceNow, Inc.", "company_domain": "servicenow.com"},
    "DDOG": {"company_name": "Datadog, Inc.", "company_domain": "datadoghq.com"},
    "NET": {"company_name": "Cloudflare, Inc.", "company_domain": "cloudflare.com"},
    "MDB": {"company_name": "MongoDB, Inc.", "company_domain": "mongodb.com"},
    "PANW": {"company_name": "Palo Alto Networks, Inc.", "company_domain": "paloaltonetworks.com"},
    "CRWD": {"company_name": "CrowdStrike Holdings, Inc.", "company_domain": "crowdstrike.com"},
    "TSLA": {"company_name": "Tesla, Inc.", "company_domain": "tesla.com"},
    "SHOP": {"company_name": "Shopify Inc.", "company_domain": "shopify.com"},
    "UBER": {"company_name": "Uber Technologies, Inc.", "company_domain": "uber.com"},
    "RBLX": {"company_name": "Roblox Corporation", "company_domain": "roblox.com"},
    "COIN": {"company_name": "Coinbase Global, Inc.", "company_domain": "coinbase.com"},
    "PLTR": {"company_name": "Palantir Technologies Inc.", "company_domain": "palantir.com"},
}


class DiscoveryError(RuntimeError):
    """Raised for explicit source discovery failures."""


@dataclass(frozen=True)
class TargetCase:
    case_id: str
    ticker: str
    company_name: str
    fiscal_year: str
    quarter: str
    company_domain: str


@dataclass
class CandidateSource:
    source_url: str
    source_type: str = "html"
    source_domain: str = ""
    confidence: float = 0.0
    verification_status: str = "candidate"
    transcript_char_estimate: int = 0
    matched_markers: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    notes: str = ""


@dataclass
class CaseDiscovery:
    case: TargetCase
    candidates: list[CandidateSource] = field(default_factory=list)
    selected_source_url: str = ""
    selected_reason: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="*", default=list(intake.TARGET_TICKERS))
    parser.add_argument("--years", nargs="+", default=None, help="Optional discovery years. Defaults to intake's latest-call periods.")
    parser.add_argument("--quarters", nargs="+", default=None, help="Optional discovery quarters. Defaults to intake's latest-call periods.")
    parser.add_argument("--max-cases-per-ticker", type=int, default=4)
    parser.add_argument("--full-refresh", action="store_true", help="Verify all target cases instead of only missing cases.")
    parser.add_argument("--query-only", action="store_true", help="Write search queries only; perform no downloads or source writes.")
    parser.add_argument("--search-results-file", help="CSV/JSON exported from a search provider or manual research.")
    parser.add_argument("--source-url-file", help="CSV/JSON containing manually supplied candidate URLs to verify.")
    parser.add_argument("--verify-only", action="store_true", help="Verify candidate URLs from --source-url-file or --search-results-file.")
    parser.add_argument("--live-search", action="store_true", help="Use an optional configured live search adapter when available.")
    parser.add_argument("--cache-sources", action="store_true", help="Cache downloaded source HTML/PDF/text for audit. Off by default.")
    parser.add_argument("--cache-dir", default="data/corpus/source_cache")
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--candidates-json", default=str(DEFAULT_CANDIDATES_JSON))
    parser.add_argument("--queries-csv", default=str(DEFAULT_QUERIES_CSV))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT))
    parser.add_argument("--min-transcript-chars", type=int, default=5000)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=45)
    return parser.parse_args(argv)


def company_name_for_ticker(ticker: str) -> str:
    return COMPANY_METADATA.get(ticker, {}).get("company_name", ticker)


def company_domain_for_ticker(ticker: str) -> str:
    return COMPANY_METADATA.get(ticker, {}).get("company_domain", "")


def build_target_cases(
    *,
    tickers: list[str],
    years: list[str] | None,
    quarters: list[str] | None,
    max_cases_per_ticker: int,
) -> list[TargetCase]:
    if years is None and quarters is None:
        periods = list(intake.DEFAULT_DISCOVERY_PERIODS)
    else:
        period_years = [str(year) for year in (years or [year for year, _quarter in intake.DEFAULT_DISCOVERY_PERIODS])]
        period_quarters = [quarter.upper() for quarter in (quarters or intake.DEFAULT_DISCOVERY_QUARTERS_FROM_PERIODS)]
        periods = sorted(
            [(year, quarter) for year in period_years for quarter in period_quarters],
            key=lambda item: (int(item[0]) if item[0].isdigit() else 0, intake.quarter_sort_key(item[1])),
            reverse=True,
        )
    planned = intake.plan_cases(
        tickers=[ticker.upper() for ticker in tickers],
        periods=periods,
        configured_sources={},
        latest_calls=max_cases_per_ticker,
        source_mode="manual_placeholder",
    )
    return [
        TargetCase(
            case_id=case.case_id,
            ticker=case.ticker,
            company_name=company_name_for_ticker(case.ticker),
            fiscal_year=case.fiscal_year,
            quarter=case.quarter,
            company_domain=company_domain_for_ticker(case.ticker),
        )
        for case in planned
    ]


def generate_queries(case: TargetCase) -> list[str]:
    queries = [
        f"{case.company_name} {case.fiscal_year} {case.quarter} earnings call transcript",
        f"{case.ticker} {case.fiscal_year} {case.quarter} earnings call transcript",
        f"{case.company_name} fiscal {case.quarter} {case.fiscal_year} results conference call transcript",
        f"site:sec.gov {case.ticker} 8-K earnings call transcript",
    ]
    if case.company_domain:
        queries.insert(3, f"site:investor.{case.company_domain} {case.ticker} earnings call transcript")
    return queries


def write_queries(path: Path, cases: list[TargetCase]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(QUERY_CSV_FIELDS))
        writer.writeheader()
        for case in cases:
            for query in generate_queries(case):
                writer.writerow(
                    {
                        "case_id": case.case_id,
                        "ticker": case.ticker,
                        "company_name": case.company_name,
                        "fiscal_year": case.fiscal_year,
                        "quarter": case.quarter,
                        "query": query,
                    }
                )


def domain_for_url(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def guess_source_type(url: str, content_type: str = "") -> str:
    lowered = url.lower().split("?", 1)[0]
    if lowered.endswith(".pdf") or "application/pdf" in content_type:
        return "pdf"
    if lowered.endswith(".txt") or "text/plain" in content_type:
        return "txt"
    return "html"


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return ""
    return value


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def flatten_search_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("cases"), list):
            rows: list[dict[str, Any]] = []
            for case in payload["cases"]:
                if not isinstance(case, dict):
                    continue
                case_id = str(case.get("case_id") or "")
                for candidate in case.get("candidates") or []:
                    if isinstance(candidate, dict):
                        rows.append({"case_id": case_id, **candidate})
            return rows
        for key in ("results", "organic_results", "items", "candidates"):
            if isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
    return []


def read_json_rows(path: Path) -> list[dict[str, Any]]:
    return flatten_search_json(json.loads(path.read_text(encoding="utf-8")))


def rows_from_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise DiscoveryError(f"candidate/search results file does not exist: {path}")
    if path.suffix.lower() == ".json":
        return read_json_rows(path)
    if path.suffix.lower() in {".csv", ".tsv"}:
        return read_csv_rows(path)
    raise DiscoveryError(f"unsupported file type for candidate/search results file: {path.suffix}")


def case_lookup_key(row: dict[str, Any]) -> str:
    case_id = str(row.get("case_id") or "").strip()
    if case_id:
        return case_id
    ticker = str(row.get("ticker") or "").strip().upper()
    fiscal_year = str(row.get("fiscal_year") or row.get("year") or "").strip()
    quarter = str(row.get("quarter") or row.get("fiscal_quarter") or "").strip().upper()
    return f"{ticker}_{fiscal_year}_{quarter}" if ticker and fiscal_year and quarter else ""


def source_url_from_row(row: dict[str, Any]) -> str:
    for column in SOURCE_URL_COLUMNS:
        url = normalize_url(str(row.get(column) or ""))
        if url:
            return url
    return ""


def candidate_notes_from_row(row: dict[str, Any]) -> str:
    parts = []
    for column in ("title", "snippet", "notes"):
        value = str(row.get(column) or "").strip()
        if value:
            parts.append(f"{column}: {value}")
    return " | ".join(parts)


def candidates_from_rows(rows: list[dict[str, Any]], cases_by_id: dict[str, TargetCase]) -> dict[str, list[CandidateSource]]:
    result: dict[str, list[CandidateSource]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        case_id = case_lookup_key(row)
        if case_id not in cases_by_id:
            continue
        url = source_url_from_row(row)
        if not url:
            continue
        key = (case_id, url)
        if key in seen:
            continue
        seen.add(key)
        result[case_id].append(
            CandidateSource(
                source_url=url,
                source_type=str(row.get("source_type") or guess_source_type(url)).strip() or guess_source_type(url),
                source_domain=str(row.get("source_domain") or domain_for_url(url)).strip(),
                confidence=float(row.get("confidence") or 0.0),
                verification_status=str(row.get("verification_status") or "candidate").strip() or "candidate",
                transcript_char_estimate=int(float(row.get("transcript_char_estimate") or 0)),
                matched_markers=parse_marker_list(row.get("matched_markers")),
                notes=candidate_notes_from_row(row),
            )
        )
    return result


def parse_marker_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in re.split(r"[;|,]", text) if item.strip()]


def load_existing_configured_sources() -> dict[str, CandidateSource]:
    sources: dict[str, CandidateSource] = {}
    for source in intake.load_configured_sources().values():
        if source.source_url:
            sources[source.case_id] = CandidateSource(
                source_url=source.source_url,
                source_type=guess_source_type(source.source_url),
                source_domain=domain_for_url(source.source_url),
                confidence=0.0,
                verification_status="candidate",
                notes=source.notes or "Existing configured source from tools/transcript_downloader/sources.yaml.",
            )
    for case_id, candidate in load_existing_manifest_sources(ROOT / "data" / "corpus" / "corpus_manifest.csv").items():
        sources.setdefault(case_id, candidate)
    for case_id, candidate in load_existing_manifest_sources(ROOT / "data" / "corpus" / "high_signal_cases" / "high_signal_manifest.csv").items():
        sources.setdefault(case_id, candidate)
    return sources


def load_existing_manifest_sources(path: Path) -> dict[str, CandidateSource]:
    if not path.exists():
        return {}
    result: dict[str, CandidateSource] = {}
    for row in read_csv_rows(path):
        case_id = str(row.get("case_id") or "").strip()
        source_url = normalize_url(str(row.get("source_url") or ""))
        if not case_id or not source_url:
            continue
        result[case_id] = CandidateSource(
            source_url=source_url,
            source_type=guess_source_type(source_url),
            source_domain=domain_for_url(source_url),
            verification_status="candidate",
            notes=f"Existing source from {path.relative_to(ROOT)}.",
        )
    return result


def robots_allowed(url: str, user_agent: str = USER_AGENT) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return False
    return parser.can_fetch(user_agent, url)


def fetch_url(url: str, timeout: int) -> tuple[bytes, str, int]:
    try:
        import requests
    except Exception as exc:
        raise DiscoveryError("requests is required to verify live candidate URLs") from exc
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,text/plain,*/*;q=0.8"},
        timeout=timeout,
    )
    return response.content, response.headers.get("content-type", "").lower(), response.status_code


def is_supported_content_type(url: str, content_type: str) -> bool:
    guessed = guess_source_type(url, content_type)
    return guessed in {"html", "pdf", "txt"} or any(token in content_type for token in ("html", "pdf", "plain", "text"))


def extract_candidate_text(url: str, content: bytes, content_type: str) -> tuple[str, str]:
    source_type = guess_source_type(url, content_type)
    if source_type == "pdf" or intake.is_pdf_bytes(url, content, content_type):
        return intake.clean_text(intake.extract_pdf_text(content)), "pdf"
    if source_type == "txt":
        return intake.clean_text(content.decode("utf-8", errors="replace")), "txt"
    return intake.clean_text(intake.extract_html_text(content, url)), "html"


def detect_matched_markers(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in TRANSCRIPT_MARKERS if marker in lowered]


def contains_paywall_or_block(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PAYWALL_MARKERS)


def official_domain_match(case: TargetCase, domain: str) -> bool:
    if not case.company_domain:
        return False
    company_domain = case.company_domain.lower()
    return domain == company_domain or domain.endswith(f".{company_domain}") or domain.startswith(f"investor.{company_domain}")


def is_sec_source(domain: str, url: str) -> bool:
    lowered = url.lower()
    return domain.endswith("sec.gov") and ("8-k" in lowered or "ex-" in lowered or "exhibit" in lowered or "/ixviewer/" in lowered)


def ticker_company_match(case: TargetCase, text: str, url: str) -> bool:
    lowered = f"{text[:20000]} {url}".lower()
    company_tokens = [token for token in re.split(r"[^a-z0-9]+", case.company_name.lower()) if len(token) >= 4]
    return case.ticker.lower() in lowered or any(token in lowered for token in company_tokens[:3])


def fiscal_period_match(case: TargetCase, text: str, url: str) -> bool:
    lowered = f"{text[:20000]} {url}".lower()
    quarter_forms = {case.quarter.lower(), case.quarter.lower().replace("q", "q "), case.quarter.lower().replace("q", "quarter ")}
    year_hit = case.fiscal_year.lower() in lowered or f"fy{case.fiscal_year[-2:]}" in lowered or f"fy {case.fiscal_year[-2:]}" in lowered
    quarter_hit = any(form in lowered for form in quarter_forms)
    return year_hit and quarter_hit


def score_candidate(
    *,
    case: TargetCase,
    candidate: CandidateSource,
    text: str,
    min_chars: int,
    paywall_or_block: bool,
) -> float:
    score = 0.0
    domain = candidate.source_domain or domain_for_url(candidate.source_url)
    if official_domain_match(case, domain) or domain.endswith("q4cdn.com"):
        score += 0.30
    if is_sec_source(domain, candidate.source_url) or (candidate.source_type == "pdf" and (official_domain_match(case, domain) or domain.endswith("q4cdn.com"))):
        score += 0.20
    if candidate.matched_markers:
        score += 0.20
    if ticker_company_match(case, text, candidate.source_url):
        score += 0.15
    if fiscal_period_match(case, text, candidate.source_url):
        score += 0.10
    if candidate.transcript_char_estimate >= min_chars:
        score += 0.05
    if paywall_or_block:
        score -= 0.50
    if not fiscal_period_match(case, text, candidate.source_url):
        score -= 0.30
    if candidate.transcript_char_estimate < min_chars and candidate.source_type == "html":
        score -= 0.30
    return max(0.0, min(1.0, round(score, 2)))


def verify_candidate(
    case: TargetCase,
    candidate: CandidateSource,
    *,
    min_chars: int,
    timeout: int,
    cache_sources: bool = False,
    cache_dir: Path | None = None,
    robots_checker: Any = robots_allowed,
    downloader: Any = fetch_url,
) -> CandidateSource:
    candidate.source_domain = candidate.source_domain or domain_for_url(candidate.source_url)
    if not normalize_url(candidate.source_url):
        candidate.verification_status = "rejected"
        candidate.rejection_reason = "invalid_url"
        return candidate
    if not robots_checker(candidate.source_url):
        candidate.verification_status = "robots_disallowed"
        candidate.rejection_reason = "robots_txt_disallowed"
        candidate.confidence = 0.0
        return candidate
    try:
        content, content_type, status_code = downloader(candidate.source_url, timeout)
    except Exception as exc:
        candidate.verification_status = "download_failed"
        candidate.rejection_reason = f"download_failed:{exc}"
        candidate.confidence = 0.0
        return candidate
    if status_code in {401, 403, 407, 429}:
        candidate.verification_status = "blocked"
        candidate.rejection_reason = f"http_blocked:{status_code}"
        return candidate
    if status_code >= 400:
        candidate.verification_status = "download_failed"
        candidate.rejection_reason = f"http_error:{status_code}"
        return candidate
    if not is_supported_content_type(candidate.source_url, content_type):
        candidate.verification_status = "rejected"
        candidate.rejection_reason = f"unsupported_content_type:{content_type}"
        return candidate
    try:
        text, source_type = extract_candidate_text(candidate.source_url, content, content_type)
    except Exception as exc:
        candidate.verification_status = "download_failed"
        candidate.rejection_reason = f"extract_failed:{exc}"
        return candidate
    candidate.source_type = source_type
    candidate.transcript_char_estimate = len(text)
    candidate.matched_markers = detect_matched_markers(text)
    paywall_or_block = contains_paywall_or_block(text)
    candidate.confidence = score_candidate(case=case, candidate=candidate, text=text, min_chars=min_chars, paywall_or_block=paywall_or_block)
    if cache_sources and cache_dir:
        cache_path = cache_dir / f"{case.case_id}_{safe_domain(candidate.source_domain)}.{candidate.source_type}"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if candidate.source_type == "txt":
            cache_path.write_text(text, encoding="utf-8")
        else:
            cache_path.write_bytes(content)
        candidate.notes = f"{candidate.notes} | cached_source: {cache_path.relative_to(ROOT)}".strip(" |")
    if paywall_or_block:
        candidate.verification_status = "paywalled"
        candidate.rejection_reason = "paywall_login_captcha_or_block_marker"
    elif candidate.transcript_char_estimate < min_chars:
        candidate.verification_status = "rejected"
        candidate.rejection_reason = f"short_transcript:{candidate.transcript_char_estimate}<{min_chars}"
    elif not candidate.matched_markers:
        candidate.verification_status = "rejected"
        candidate.rejection_reason = "missing_transcript_markers"
    elif candidate.confidence >= 0.70:
        candidate.verification_status = "verified"
        candidate.rejection_reason = ""
    else:
        candidate.verification_status = "candidate"
        candidate.rejection_reason = "below_selection_threshold"
    return candidate


def safe_domain(domain: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", domain or "source")


def selectable(candidate: CandidateSource) -> bool:
    return (
        candidate.verification_status == "verified"
        and candidate.confidence >= 0.70
        and candidate.transcript_char_estimate >= 5000
        and candidate.rejection_reason == ""
    )


def select_source(candidates: list[CandidateSource]) -> CandidateSource | None:
    verified = [candidate for candidate in candidates if selectable(candidate)]
    if not verified:
        return None
    return sorted(verified, key=lambda item: (item.confidence, item.transcript_char_estimate), reverse=True)[0]


def candidate_to_json(candidate: CandidateSource) -> dict[str, Any]:
    return {
        "source_url": candidate.source_url,
        "source_type": candidate.source_type,
        "source_domain": candidate.source_domain,
        "confidence": candidate.confidence,
        "verification_status": candidate.verification_status,
        "transcript_char_estimate": candidate.transcript_char_estimate,
        "matched_markers": candidate.matched_markers,
        "rejection_reason": candidate.rejection_reason,
        "notes": candidate.notes,
    }


def write_candidates_json(path: Path, discoveries: list[CaseDiscovery]) -> None:
    resolved = sum(1 for discovery in discoveries if discovery.selected_source_url)
    payload = {
        "generated_at": now_iso(),
        "target_calls": len(discoveries),
        "resolved_sources": resolved,
        "missing_sources": len(discoveries) - resolved,
        "cases": [
            {
                "case_id": discovery.case.case_id,
                "ticker": discovery.case.ticker,
                "company_name": discovery.case.company_name,
                "fiscal_year": discovery.case.fiscal_year,
                "quarter": discovery.case.quarter,
                "candidates": [candidate_to_json(candidate) for candidate in discovery.candidates],
                "selected_source_url": discovery.selected_source_url,
                "selected_reason": discovery.selected_reason,
            }
            for discovery in discoveries
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_csv_row(discovery: CaseDiscovery, candidate: CandidateSource) -> dict[str, Any]:
    return {
        "case_id": discovery.case.case_id,
        "ticker": discovery.case.ticker,
        "company_name": discovery.case.company_name,
        "fiscal_year": discovery.case.fiscal_year,
        "quarter": discovery.case.quarter,
        "source_url": candidate.source_url,
        "source_type": candidate.source_type,
        "source_domain": candidate.source_domain,
        "confidence": f"{candidate.confidence:.2f}",
        "verification_status": candidate.verification_status,
        "transcript_char_estimate": candidate.transcript_char_estimate,
        "matched_markers": ";".join(candidate.matched_markers),
        "notes": candidate.notes,
    }


def write_source_csv(path: Path, discoveries: list[CaseDiscovery]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SOURCE_CSV_FIELDS))
        writer.writeheader()
        for discovery in discoveries:
            selected = select_source(discovery.candidates)
            if selected:
                writer.writerow(source_csv_row(discovery, selected))


def write_report(path: Path, discoveries: list[CaseDiscovery], *, already_resolved: int, newly_verified: int) -> None:
    selected = [discovery for discovery in discoveries if discovery.selected_source_url]
    missing = [discovery for discovery in discoveries if not discovery.selected_source_url]
    all_candidates = [candidate for discovery in discoveries for candidate in discovery.candidates]
    blocked = [candidate for candidate in all_candidates if candidate.verification_status in {"blocked", "paywalled", "robots_disallowed"}]
    domain_counts = Counter(candidate.source_domain for candidate in all_candidates if candidate.verification_status == "verified")
    lines = [
        "# High-Signal Source Discovery",
        "",
        f"- generated_at: `{now_iso()}`",
        f"- target_calls: `{len(discoveries)}`",
        f"- already_resolved: `{already_resolved}`",
        f"- newly_verified: `{newly_verified}`",
        f"- resolved_sources: `{len(selected)}`",
        f"- still_missing: `{len(missing)}`",
        f"- blocked_or_paywalled: `{len(blocked)}`",
        "",
        "## Top Domains Used",
        "",
    ]
    if domain_counts:
        for domain, count in domain_counts.most_common(10):
            lines.append(f"- `{domain}`: {count}")
    else:
        lines.append("- None yet.")
    lines.extend(["", "## Manual Review Required", ""])
    if missing:
        for discovery in missing:
            lines.append(f"- `{discovery.case.case_id}`: no verified public source selected")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Constraints",
            "",
            "- Public HTML/PDF/text sources only.",
            "- Paywall, login, captcha, blocked, and robots-disallowed pages are not silently accepted.",
            "- No transcripts or gold labels are auto-promoted by this discovery tool.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def existing_verified_for_targets(targets: list[TargetCase]) -> dict[str, CandidateSource]:
    targets_by_id = {case.case_id for case in targets}
    existing = load_existing_configured_sources()
    return {case_id: candidate for case_id, candidate in existing.items() if case_id in targets_by_id and candidate.source_url}


def enforce_live_search_config() -> None:
    if os.getenv("TAVILY_API_KEY") or os.getenv("SERPAPI_API_KEY") or os.getenv("BING_SEARCH_API_KEY"):
        raise DiscoveryError("live search adapter hooks are not implemented yet; use --query-only or --search-results-file.")
    raise DiscoveryError("no live search API key configured; use --query-only or --search-results-file.")


def run_discovery(args: argparse.Namespace) -> dict[str, Any]:
    targets = build_target_cases(
        tickers=[ticker.upper() for ticker in args.tickers],
        years=[str(year) for year in args.years] if args.years else None,
        quarters=[quarter.upper() for quarter in args.quarters] if args.quarters else None,
        max_cases_per_ticker=args.max_cases_per_ticker,
    )
    queries_path = resolve_path(args.queries_csv)
    write_queries(queries_path, targets)
    if args.query_only:
        return {"mode": "query_only", "target_calls": len(targets), "queries_path": str(queries_path), "queries_written": len(targets) * 5}

    if args.live_search:
        enforce_live_search_config()
    if not args.search_results_file and not args.source_url_file:
        raise DiscoveryError("no candidate URLs supplied; use --query-only, --search-results-file, or --source-url-file.")

    cases_by_id = {case.case_id: case for case in targets}
    existing = existing_verified_for_targets(targets)
    target_ids = set(cases_by_id)
    rows: list[dict[str, Any]] = []
    if args.search_results_file:
        rows.extend(rows_from_file(resolve_path(args.search_results_file)))
    if args.source_url_file:
        rows.extend(rows_from_file(resolve_path(args.source_url_file)))
    candidates_by_case = candidates_from_rows(rows, cases_by_id)

    already_resolved = 0
    if not args.full_refresh:
        for case_id, candidate in existing.items():
            candidates_by_case.setdefault(case_id, []).insert(0, candidate)
            already_resolved += 1
    discoveries: list[CaseDiscovery] = []
    cache_dir = resolve_path(args.cache_dir)
    cases_to_verify = targets if args.full_refresh else [case for case in targets if case.case_id in target_ids]
    for case_index, case in enumerate(cases_to_verify):
        if case_index and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)
        discovery = CaseDiscovery(case=case)
        case_candidates = candidates_by_case.get(case.case_id, [])
        verified_candidates: list[CandidateSource] = []
        for candidate in case_candidates:
            verified_candidates.append(
                verify_candidate(
                    case,
                    candidate,
                    min_chars=args.min_transcript_chars,
                    timeout=args.timeout,
                    cache_sources=args.cache_sources,
                    cache_dir=cache_dir,
                )
            )
        discovery.candidates = verified_candidates
        selected = select_source(discovery.candidates)
        if selected:
            discovery.selected_source_url = selected.source_url
            discovery.selected_reason = f"verified confidence {selected.confidence:.2f}"
        discoveries.append(discovery)
    newly_verified = sum(1 for discovery in discoveries if discovery.selected_source_url and discovery.case.case_id not in existing)
    write_source_csv(resolve_path(args.output_csv), discoveries)
    write_candidates_json(resolve_path(args.candidates_json), discoveries)
    write_report(resolve_path(args.report_path), discoveries, already_resolved=already_resolved, newly_verified=newly_verified)
    resolved = sum(1 for discovery in discoveries if discovery.selected_source_url)
    return {
        "mode": "verify",
        "target_calls": len(discoveries),
        "resolved_sources": resolved,
        "missing_sources": len(discoveries) - resolved,
        "already_resolved": already_resolved,
        "newly_verified": newly_verified,
        "source_url_file": str(resolve_path(args.output_csv)),
        "candidates_json": str(resolve_path(args.candidates_json)),
        "report_path": str(resolve_path(args.report_path)),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_discovery(args)
    except DiscoveryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
