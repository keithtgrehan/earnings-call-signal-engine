#!/usr/bin/env python3
"""Deterministically discover and verify tiered public transcript source candidates."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import discover_high_signal_transcript_sources as high_signal_discovery  # noqa: E402
import intake_high_signal_transcripts as intake  # noqa: E402

USER_AGENT = "SignalEngineTieredTranscriptDiscovery/1.0 (+deterministic public transcript verification; no LLMs)"
DEFAULT_TARGETS_CSV = ROOT / "data" / "corpus" / "tiered_transcript_targets.csv"
DEFAULT_CONFIG = ROOT / "data" / "corpus" / "transcript_source_discovery.yaml"
DEFAULT_OUTPUT_CSV = ROOT / "data" / "corpus" / "discovered_transcript_sources.csv"
DEFAULT_REPORT = ROOT / "reports" / "transcript_source_discovery.md"

DISCOVERED_FIELDS = (
    "tier",
    "case_id",
    "ticker",
    "company_name",
    "fiscal_year",
    "quarter",
    "priority",
    "source_url",
    "source_domain",
    "source_type",
    "discovery_method",
    "discovered_timestamp",
    "http_status",
    "content_type",
    "estimated_pdf",
    "verification_status",
    "verified_allowed",
    "acquisition_quality_score",
    "acquisition_quality_band",
    "transcript_char_estimate",
    "matched_markers",
    "rejection_reason",
    "notes",
)

PAYWALL_MARKERS = tuple(high_signal_discovery.PAYWALL_MARKERS)
PREPARED_MARKERS = ("prepared remarks", "prepared comment", "prepared statement")
QA_MARKERS = ("question-and-answer", "questions and answers", "q&a", "question and answer")
HARD_FAIL_STATUSES = {"robots_disallowed", "blocked", "paywalled", "unsupported_content_type", "download_failed", "rejected"}


class TieredDiscoveryError(RuntimeError):
    """Raised for deterministic discovery errors."""


@dataclass(frozen=True)
class TieredTarget:
    tier: str
    case_id: str
    ticker: str
    company_name: str
    fiscal_year: str
    quarter: str
    priority: str
    notes: str = ""


@dataclass(frozen=True)
class CandidateURL:
    target: TieredTarget
    source_url: str
    discovery_method: str
    notes: str = ""
    source_type: str = ""


@dataclass(frozen=True)
class FetchMetadata:
    status_code: int
    content_type: str


@dataclass
class QualityResult:
    score: int
    band: str
    signals: list[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    target: TieredTarget
    source_url: str
    source_domain: str
    source_type: str
    discovery_method: str
    discovered_timestamp: str
    http_status: int = 0
    content_type: str = ""
    estimated_pdf: bool = False
    verification_status: str = "candidate"
    verified_allowed: bool = False
    acquisition_quality_score: int = 0
    acquisition_quality_band: str = "unusable"
    transcript_char_estimate: int = 0
    matched_markers: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    notes: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def parse_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets-csv", default=str(DEFAULT_TARGETS_CSV))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--candidate-url-file")
    parser.add_argument("--search-results-file")
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT))
    parser.add_argument("--tiers", nargs="*", default=None)
    parser.add_argument("--min-transcript-chars", type=int, default=5000)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=45)
    return parser.parse_args(argv)


def read_targets(path: Path, tiers: set[str] | None = None) -> list[TieredTarget]:
    if not path.exists():
        raise TieredDiscoveryError(f"tiered target CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    targets: list[TieredTarget] = []
    for row in rows:
        tier = str(row.get("tier") or "").strip()
        if tiers and tier not in tiers:
            continue
        targets.append(
            TieredTarget(
                tier=tier,
                case_id=str(row.get("case_id") or "").strip(),
                ticker=str(row.get("ticker") or "").strip().upper(),
                company_name=str(row.get("company_name") or "").strip(),
                fiscal_year=str(row.get("fiscal_year") or "").strip(),
                quarter=str(row.get("quarter") or "").strip().upper(),
                priority=str(row.get("priority") or "").strip(),
                notes=str(row.get("notes") or "").strip(),
            )
        )
    return [target for target in targets if target.case_id and target.ticker and target.fiscal_year and target.quarter]


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise TieredDiscoveryError(f"source discovery config not found: {path}")
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise TieredDiscoveryError("PyYAML is required for transcript source discovery config") from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def domain_for_url(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def company_domain(target: TieredTarget) -> str:
    return high_signal_discovery.COMPANY_METADATA.get(target.ticker, {}).get("company_domain", "")


def format_pattern(template: str, target: TieredTarget) -> str:
    return template.format(
        ticker=target.ticker,
        ticker_lower=target.ticker.lower(),
        company_name=target.company_name,
        company_slug=slug(target.company_name),
        company_domain=company_domain(target),
        fiscal_year=target.fiscal_year,
        fiscal_year_short=target.fiscal_year[-2:],
        quarter=target.quarter,
        quarter_lower=target.quarter.lower(),
    )


def normalize_url(value: str) -> str:
    value = str(value or "").strip()
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def candidates_from_patterns(targets: list[TieredTarget], config: dict[str, Any]) -> list[CandidateURL]:
    candidates: list[CandidateURL] = []
    for pattern in config.get("source_patterns") or []:
        if not isinstance(pattern, dict) or not pattern.get("enabled", True):
            continue
        template = str(pattern.get("url_template") or "")
        if not template:
            continue
        method = str(pattern.get("discovery_method") or pattern.get("name") or "approved_url_pattern")
        for target in targets:
            url = normalize_url(format_pattern(template, target))
            if url:
                candidates.append(CandidateURL(target=target, source_url=url, discovery_method=method, source_type=str(pattern.get("source_type") or ""), notes=str(pattern.get("notes") or "")))
    return candidates


def flatten_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("results", "organic_results", "items", "candidates", "cases"):
            value = payload.get(key)
            if isinstance(value, list):
                rows: list[dict[str, Any]] = []
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    if key == "cases" and isinstance(item.get("candidates"), list):
                        for candidate in item["candidates"]:
                            if isinstance(candidate, dict):
                                rows.append({"case_id": item.get("case_id", ""), **candidate})
                    else:
                        rows.append(item)
                return rows
    return []


def rows_from_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".json":
        return flatten_json(json.loads(path.read_text(encoding="utf-8")))
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def import_candidate_files(targets_by_id: dict[str, TieredTarget], paths: list[Path], method: str) -> list[CandidateURL]:
    candidates: list[CandidateURL] = []
    for path in paths:
        for row in rows_from_file(path):
            case_id = str(row.get("case_id") or "").strip()
            if not case_id:
                ticker = str(row.get("ticker") or "").strip().upper()
                fiscal_year = str(row.get("fiscal_year") or row.get("year") or "").strip()
                quarter = str(row.get("quarter") or row.get("fiscal_quarter") or "").strip().upper()
                case_id = f"{ticker}_{fiscal_year}_{quarter}" if ticker and fiscal_year and quarter else ""
            target = targets_by_id.get(case_id)
            if not target:
                continue
            url = normalize_url(str(row.get("source_url") or row.get("url") or row.get("link") or row.get("href") or ""))
            if url:
                candidates.append(CandidateURL(target=target, source_url=url, discovery_method=method, source_type=str(row.get("source_type") or ""), notes=str(row.get("notes") or row.get("title") or "")))
    return candidates


def build_candidates(targets: list[TieredTarget], config: dict[str, Any], extra_paths: list[Path] | None = None) -> list[CandidateURL]:
    targets_by_id = {target.case_id: target for target in targets}
    candidates = candidates_from_patterns(targets, config)
    configured_files = [resolve_path(path) for path in config.get("candidate_files") or []]
    if extra_paths:
        configured_files.extend(extra_paths)
    candidates.extend(import_candidate_files(targets_by_id, configured_files, "imported_candidate_file"))
    seen: set[tuple[str, str]] = set()
    unique: list[CandidateURL] = []
    for candidate in candidates:
        key = (candidate.target.case_id, candidate.source_url)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def fetch_metadata(url: str, timeout: int) -> FetchMetadata:
    try:
        import requests
    except Exception as exc:  # pragma: no cover
        raise TieredDiscoveryError("requests is required for transcript source discovery") from exc
    response = requests.head(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,application/pdf,*/*;q=0.8"}, timeout=timeout, allow_redirects=True)
    return FetchMetadata(status_code=response.status_code, content_type=response.headers.get("content-type", "").lower())


def fetch_content(url: str, timeout: int) -> tuple[bytes, str, int]:
    try:
        import requests
    except Exception as exc:  # pragma: no cover
        raise TieredDiscoveryError("requests is required for transcript source discovery") from exc
    response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,*/*;q=0.8"}, timeout=timeout)
    return response.content, response.headers.get("content-type", "").lower(), response.status_code


def estimate_source_type(url: str, content_type: str = "") -> str:
    lowered = url.lower().split("?", 1)[0]
    if lowered.endswith(".pdf") or "pdf" in content_type:
        return "pdf"
    if lowered.endswith(".txt") or "plain" in content_type:
        return "txt"
    if "html" in content_type or url:
        return "html"
    return "unknown"


def is_supported_text_type(source_type: str, content_type: str) -> bool:
    return source_type in {"html", "txt"} or any(token in content_type for token in ("html", "plain", "text"))


def normalize_content_to_text(url: str, content: bytes, content_type: str) -> tuple[str, str]:
    source_type = estimate_source_type(url, content_type)
    if source_type == "pdf":
        raise TieredDiscoveryError("PDF parsing is intentionally disabled for acquisition")
    if source_type == "txt":
        return intake.clean_text(content.decode("utf-8", errors="replace")), "txt"
    return intake.clean_text(intake.extract_html_text(content, url)), "html"


def matched_markers(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in intake.MARKERS if marker in lowered]


def has_prepared_markers(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PREPARED_MARKERS)


def has_qa_markers(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in QA_MARKERS)


def has_speaker_labels(text: str) -> bool:
    return bool(re.search(r"(?m)^[A-Z][A-Za-z .,'-]{2,60}:\s+\S", text))


def encoding_is_clean(text: str) -> bool:
    if not text:
        return False
    return text.count("\ufffd") / max(len(text), 1) <= 0.001


def has_repetition_signal(text: str) -> bool:
    chunks = [text[index : index + 120] for index in range(0, min(len(text), 24000), 120) if len(text[index : index + 120].strip()) > 80]
    if len(chunks) < 10:
        return False
    counts = Counter(chunks)
    return counts.most_common(1)[0][1] >= 4


def contains_paywall_or_block(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PAYWALL_MARKERS)


def target_case_for_quality(target: TieredTarget) -> high_signal_discovery.TargetCase:
    return high_signal_discovery.TargetCase(
        case_id=target.case_id,
        ticker=target.ticker,
        company_name=target.company_name,
        fiscal_year=target.fiscal_year,
        quarter=target.quarter,
        company_domain=company_domain(target),
    )


def band_for_score(score: int, hard_fail: bool = False) -> str:
    if hard_fail or score < 40:
        return "unusable"
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def score_acquisition_quality(
    *,
    target: TieredTarget,
    text: str,
    source_url: str,
    source_type: str,
    content_type: str,
    verification_status: str,
    min_chars: int = 5000,
) -> QualityResult:
    hard_fail = verification_status in HARD_FAIL_STATUSES or source_type not in {"html", "txt", "pdf"}
    if hard_fail:
        return QualityResult(score=0, band="unusable", signals=[f"hard_fail:{verification_status}"])
    if source_type == "pdf":
        return QualityResult(score=60, band="medium", signals=["pdf_metadata_only", "manual_conversion_required"])

    score = 0
    signals: list[str] = []
    if len(text) >= 15000:
        score += 25
        signals.append("long_transcript")
    elif len(text) >= min_chars:
        score += 18
        signals.append("adequate_length")
    elif len(text) >= 1500:
        score += 8
        signals.append("short_but_substantial")
    else:
        score -= 25
        signals.append("too_short")
    if has_prepared_markers(text):
        score += 15
        signals.append("prepared_markers")
    if has_qa_markers(text):
        score += 15
        signals.append("qa_markers")
    if has_speaker_labels(text):
        score += 10
        signals.append("speaker_labels")
    if encoding_is_clean(text):
        score += 10
        signals.append("clean_encoding")
    case = target_case_for_quality(target)
    if high_signal_discovery.ticker_company_match(case, text, source_url):
        score += 10
        signals.append("ticker_company_match")
    else:
        score -= 20
        signals.append("weak_ticker_company_match")
    if high_signal_discovery.fiscal_period_match(case, text, source_url):
        score += 8
        signals.append("fiscal_period_match")
    if not has_repetition_signal(text):
        score += 7
        signals.append("no_repetition_signal")
    else:
        score -= 15
        signals.append("repetition_signal")
    if contains_paywall_or_block(text):
        return QualityResult(score=0, band="unusable", signals=[*signals, "blocked_or_paywalled_marker"])
    score = max(0, min(100, score))
    return QualityResult(score=score, band=band_for_score(score), signals=signals)


def pdf_status_from_metadata(status_code: int, content_type: str) -> str:
    if status_code in {401, 403, 407, 429}:
        return "blocked_pdf"
    if status_code >= 400:
        return "unsupported_pdf"
    if "pdf" in content_type:
        return "verified_manual_pdf"
    return "unsupported_pdf"


def verify_candidate(
    candidate: CandidateURL,
    *,
    min_chars: int,
    timeout: int,
    robots_checker: Any = high_signal_discovery.robots_allowed,
    metadata_fetcher: Any = fetch_metadata,
    content_fetcher: Any = fetch_content,
) -> VerificationResult:
    timestamp = now_iso()
    source_domain = domain_for_url(candidate.source_url)
    source_type = candidate.source_type or estimate_source_type(candidate.source_url)
    result = VerificationResult(
        target=candidate.target,
        source_url=candidate.source_url,
        source_domain=source_domain,
        source_type=source_type,
        discovery_method=candidate.discovery_method,
        discovered_timestamp=timestamp,
        notes=candidate.notes,
    )
    if not normalize_url(candidate.source_url):
        result.verification_status = "rejected"
        result.rejection_reason = "invalid_url"
        return result
    if not robots_checker(candidate.source_url):
        result.verification_status = "robots_disallowed"
        result.rejection_reason = "robots_txt_disallowed"
        return result
    try:
        metadata = metadata_fetcher(candidate.source_url, timeout)
    except Exception as exc:
        result.verification_status = "download_failed"
        result.rejection_reason = f"metadata_failed:{exc}"
        return result
    result.http_status = int(metadata.status_code)
    result.content_type = str(metadata.content_type or "").lower()
    result.source_type = estimate_source_type(candidate.source_url, result.content_type)
    result.estimated_pdf = result.source_type == "pdf"
    if result.estimated_pdf:
        result.verification_status = pdf_status_from_metadata(result.http_status, result.content_type)
        quality = score_acquisition_quality(
            target=candidate.target,
            text="",
            source_url=candidate.source_url,
            source_type="pdf",
            content_type=result.content_type,
            verification_status=result.verification_status,
            min_chars=min_chars,
        )
        result.acquisition_quality_score = quality.score
        result.acquisition_quality_band = quality.band
        result.verified_allowed = False
        result.rejection_reason = "pdf_manual_conversion_required"
        return result
    if result.http_status in {401, 403, 407, 429}:
        result.verification_status = "blocked"
        result.rejection_reason = f"http_blocked:{result.http_status}"
        return result
    if result.http_status >= 400:
        result.verification_status = "download_failed"
        result.rejection_reason = f"http_error:{result.http_status}"
        return result
    if not is_supported_text_type(result.source_type, result.content_type):
        result.verification_status = "unsupported_content_type"
        result.rejection_reason = f"unsupported_content_type:{result.content_type}"
        return result
    try:
        content, content_type, status_code = content_fetcher(candidate.source_url, timeout)
        result.http_status = int(status_code)
        result.content_type = str(content_type or result.content_type).lower()
        text, extracted_type = normalize_content_to_text(candidate.source_url, content, result.content_type)
        result.source_type = extracted_type
    except Exception as exc:
        result.verification_status = "download_failed"
        result.rejection_reason = f"content_failed:{exc}"
        return result
    result.transcript_char_estimate = len(text)
    result.matched_markers = matched_markers(text)
    if contains_paywall_or_block(text):
        result.verification_status = "paywalled"
        result.rejection_reason = "paywall_login_captcha_or_block_marker"
    elif result.transcript_char_estimate < min_chars:
        result.verification_status = "rejected"
        result.rejection_reason = f"short_transcript:{result.transcript_char_estimate}<{min_chars}"
    elif not result.matched_markers:
        result.verification_status = "rejected"
        result.rejection_reason = "missing_transcript_markers"
    else:
        result.verification_status = "candidate"
    quality = score_acquisition_quality(
        target=candidate.target,
        text=text,
        source_url=candidate.source_url,
        source_type=result.source_type,
        content_type=result.content_type,
        verification_status=result.verification_status,
        min_chars=min_chars,
    )
    result.acquisition_quality_score = quality.score
    result.acquisition_quality_band = quality.band
    if result.verification_status == "candidate" and result.acquisition_quality_score >= 60:
        result.verification_status = "verified"
        result.verified_allowed = True
        result.rejection_reason = ""
    else:
        result.verified_allowed = False
    return result


def result_to_row(result: VerificationResult) -> dict[str, Any]:
    return {
        "tier": result.target.tier,
        "case_id": result.target.case_id,
        "ticker": result.target.ticker,
        "company_name": result.target.company_name,
        "fiscal_year": result.target.fiscal_year,
        "quarter": result.target.quarter,
        "priority": result.target.priority,
        "source_url": result.source_url,
        "source_domain": result.source_domain,
        "source_type": result.source_type,
        "discovery_method": result.discovery_method,
        "discovered_timestamp": result.discovered_timestamp,
        "http_status": result.http_status,
        "content_type": result.content_type,
        "estimated_pdf": str(result.estimated_pdf).lower(),
        "verification_status": result.verification_status,
        "verified_allowed": str(result.verified_allowed).lower(),
        "acquisition_quality_score": result.acquisition_quality_score,
        "acquisition_quality_band": result.acquisition_quality_band,
        "transcript_char_estimate": result.transcript_char_estimate,
        "matched_markers": ";".join(result.matched_markers),
        "rejection_reason": result.rejection_reason,
        "notes": result.notes,
    }


def write_discovered_csv(path: Path, results: list[VerificationResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(DISCOVERED_FIELDS))
        writer.writeheader()
        for result in results:
            writer.writerow(result_to_row(result))


def write_report(path: Path, targets: list[TieredTarget], candidates: list[CandidateURL], results: list[VerificationResult]) -> None:
    verified = [result for result in results if result.verified_allowed]
    blocked = [result for result in results if result.verification_status in {"robots_disallowed", "blocked", "paywalled"}]
    pdfs = [result for result in results if result.estimated_pdf or result.verification_status.endswith("_pdf")]
    band_counts = Counter(result.acquisition_quality_band for result in results)
    lines = [
        "# Transcript Source Discovery",
        "",
        f"- generated_at: `{now_iso()}`",
        f"- target_cases: `{len(targets)}`",
        f"- candidate_urls: `{len(candidates)}`",
        f"- verified_allowed: `{len(verified)}`",
        f"- blocked_paywalled_or_robots: `{len(blocked)}`",
        f"- pdf_manual_queue_candidates: `{len(pdfs)}`",
        "",
        "## Quality Bands",
        "",
    ]
    for band in ("high", "medium", "low", "unusable"):
        lines.append(f"- `{band}`: {band_counts.get(band, 0)}")
    lines.extend(["", "## Top High-Quality Candidates", ""])
    top = sorted([result for result in results if result.acquisition_quality_band == "high"], key=lambda item: item.acquisition_quality_score, reverse=True)[:10]
    if top:
        for result in top:
            lines.append(f"- `{result.target.case_id}` score `{result.acquisition_quality_score}`: {result.source_url}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Low-Quality Or Manual-Review Candidates", ""])
    low = [result for result in results if result.acquisition_quality_band in {"low", "medium"} and not result.verified_allowed]
    if low:
        for result in low[:25]:
            lines.append(f"- `{result.target.case_id}` `{result.acquisition_quality_band}` `{result.verification_status}`: {result.source_url}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Unusable Candidates", ""])
    unusable = [result for result in results if result.acquisition_quality_band == "unusable"]
    if unusable:
        for result in unusable[:50]:
            lines.append(f"- `{result.target.case_id}` `{result.verification_status}`: {result.rejection_reason or result.source_url}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Deterministic Policy",
            "",
            "- No LLM summarization, extraction, classification, autonomous agents, hidden AI preprocessing, or AI-assisted verification.",
            "- No robots.txt bypass, blocked scraping, paywalled/private sources, OCR, PDF parsing, embeddings, or retrieval.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    targets = read_targets(resolve_path(args.targets_csv), set(args.tiers) if args.tiers else None)
    config = load_config(resolve_path(args.config))
    extra_paths = [resolve_path(path) for path in (args.candidate_url_file, args.search_results_file) if path]
    candidates = build_candidates(targets, config, extra_paths=extra_paths)
    results: list[VerificationResult] = []
    for index, candidate in enumerate(candidates):
        if index and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)
        results.append(verify_candidate(candidate, min_chars=args.min_transcript_chars, timeout=args.timeout))
    write_discovered_csv(resolve_path(args.output_csv), results)
    write_report(resolve_path(args.report_path), targets, candidates, results)
    return {
        "target_cases": len(targets),
        "candidate_urls": len(candidates),
        "verified_allowed": sum(1 for result in results if result.verified_allowed),
        "manual_fallback_required": sum(1 for result in results if not result.verified_allowed),
        "output_csv": str(resolve_path(args.output_csv)),
        "report_path": str(resolve_path(args.report_path)),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run(args)
    except TieredDiscoveryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
