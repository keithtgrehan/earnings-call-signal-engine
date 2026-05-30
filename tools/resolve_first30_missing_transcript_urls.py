#!/usr/bin/env python3
"""Resolve direct official transcript URLs for blocked first30 rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
import socket
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import (  # noqa: E402
    APPROVAL_REF,
    AUDIT_DIR,
    FIRST30_INGESTION_MANIFEST_PATH,
    hard_blocker_for_source,
    is_direct_text_url,
    is_official_cdn_domain,
    read_csv,
    write_csv,
)

OUT_PATH = ROOT / "data" / "acquisition" / "first30_transcript_url_replacements.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_url_replacement_status.md"

REPLACEMENT_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "fiscal_year",
    "fiscal_quarter",
    "original_source_url",
    "replacement_source_url",
    "source_domain",
    "source_type",
    "expected_format",
    "replacement_confidence",
    "replacement_reason",
    "download_allowed",
    "blocked_reason",
    "rights_review_required",
    "commit_allowed",
    "training_allowed",
    "raw_text_committed",
    "approval_ref",
    "checked_urls",
]

USER_AGENT = "SignalEngineCorpusAssessment/2.0 (metadata-safe; contact: project owner)"
DIRECT_SUFFIXES = (".pdf", ".html", ".htm", ".txt")
MAX_CRAWL_LINKS = 80

JPM_BASE = (
    "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/"
    "investor-relations/documents/quarterly-earnings/{year}/{quarter_dir}/{qnum}q{yy}-earnings-transcript.pdf"
)

QUARTER_DIR = {
    "Q1": "1st-quarter",
    "Q2": "2nd-quarter",
    "Q3": "3rd-quarter",
    "Q4": "4th-quarter",
}

KNOWN_TRANSCRIPT_REPLACEMENTS = {
    # Verified direct official JPMC PDF. Other 2025 JPMC quarter patterns were probed
    # and returned 404 as of this run, so they remain blocked.
    "jpm_2025_q1": JPM_BASE.format(year="2025", quarter_dir="1st-quarter", qnum="1", yy="25"),
}


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key.lower() in {"href", "src"} and value:
                self.links.append(value)


def fetch_page(url: str, *, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*"})
    with urlopen(request, timeout=timeout) as response:
        return response.read(2_000_000).decode("utf-8", errors="replace")


def url_accessible(url: str, *, timeout: int = 12) -> bool:
    for method in ("HEAD", "GET"):
        try:
            request = Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,text/html,text/plain,*/*"})
            with urlopen(request, timeout=timeout) as response:
                if 200 <= int(response.status) < 300:
                    return True
        except HTTPError as exc:
            if exc.code in {403, 405} and method == "HEAD":
                continue
            return False
        except (TimeoutError, URLError, socket.timeout, OSError):
            return False
    return False


def _quarter_number(row: dict[str, str]) -> str:
    return re.sub(r"[^1-4]", "", row.get("fiscal_quarter", "")) or ""


def _period_tokens(row: dict[str, str]) -> set[str]:
    q = _quarter_number(row)
    year = row.get("fiscal_year", "")
    yy = year[-2:] if len(year) == 4 else ""
    tokens = {year, yy}
    if q:
        tokens.update({f"q{q}", f"{q}q", f"{q}q{yy}", f"{q}q-{year}", f"{q}q-{yy}"})
    return {token.lower() for token in tokens if token}


def _period_verified(row: dict[str, str], value: str) -> bool:
    lowered = value.lower()
    q = _quarter_number(row)
    year = row.get("fiscal_year", "")
    yy = year[-2:] if len(year) == 4 else ""
    if not q or not (year or yy):
        return False
    quarter_match = any(token in lowered for token in (f"q{q}", f"{q}q", f"quarter-{q}", f"q-{q}"))
    year_match = any(token and token in lowered for token in (year, yy))
    compact_match = any(token and token in lowered for token in (f"{q}q{yy}", f"{q}q-{year}", f"{q}q-{yy}", f"q{q}{yy}", f"q{q}-{year}", f"q{q}-{yy}"))
    return compact_match or (quarter_match and year_match)


def _same_company_domain(original: str, candidate: str) -> bool:
    original_host = urlparse(original).netloc.lower()
    candidate_host = urlparse(candidate).netloc.lower()
    if not original_host or not candidate_host:
        return False
    if candidate_host == original_host or candidate_host.endswith("." + original_host) or original_host.endswith("." + candidate_host):
        return True
    return is_official_cdn_domain(candidate_host)


def _looks_like_transcript_url(url: str) -> bool:
    lowered = url.lower()
    return any(suffix in lowered for suffix in DIRECT_SUFFIXES) and any(marker in lowered for marker in ("transcript", "earnings", "conference-call", "webcast"))


def generated_candidate_urls(row: dict[str, str]) -> list[str]:
    case_id = row.get("case_id", "")
    if case_id in KNOWN_TRANSCRIPT_REPLACEMENTS:
        return [KNOWN_TRANSCRIPT_REPLACEMENTS[case_id]]
    ticker = row.get("ticker", "")
    q = _quarter_number(row)
    year = row.get("fiscal_year", "")
    if ticker == "JPM" and q and year and row.get("fiscal_quarter") in QUARTER_DIR:
        return [JPM_BASE.format(year=year, quarter_dir=QUARTER_DIR[row["fiscal_quarter"]], qnum=q, yy=year[-2:])]
    if ticker == "CAT" and q and year:
        return [
            f"https://s25.q4cdn.com/358376879/files/doc_financials/{year}/q{q}/{q}Q-{year}-Caterpillar-Inc-Earnings-Conference-Call_Transcript.pdf",
            f"https://s25.q4cdn.com/358376879/files/doc_financials/{year}/q{q}/{q}Q-{year}-Caterpillar-Inc-Earnings-Conference-Call-Transcript.pdf",
        ]
    return []


def crawl_candidate_urls(row: dict[str, str]) -> list[str]:
    source_url = row.get("source_url", "")
    if not source_url.startswith(("http://", "https://")):
        return []
    try:
        html = fetch_page(source_url)
    except Exception:
        return []
    parser = LinkExtractor()
    parser.feed(html)
    urls: list[str] = []
    for href in parser.links:
        candidate = urljoin(source_url, href)
        if not _same_company_domain(source_url, candidate):
            continue
        if not _looks_like_transcript_url(candidate):
            continue
        urls.append(candidate)
        if len(urls) >= MAX_CRAWL_LINKS:
            break
    return urls


def score_transcript_replacement(row: dict[str, str], url: str, *, accessible: bool = True) -> tuple[float, str, str]:
    candidate = {**row, "source_url": url, "source_domain": urlparse(url).netloc.lower(), "commit_allowed": "false", "training_allowed": "false"}
    blocker = hard_blocker_for_source(candidate)
    if blocker:
        return 0.0, "", blocker
    if not is_direct_text_url(url, row.get("expected_format", "")):
        return 0.0, "", "not_direct_transcript_url"
    if not accessible:
        return 0.0, "", "direct_url_not_accessible"
    lowered = url.lower()
    period_match = _period_verified(row, lowered)
    transcript_match = "transcript" in lowered
    official_match = _same_company_domain(row.get("source_url", ""), url)
    confidence = 0.0
    reasons: list[str] = []
    if official_match:
        confidence += 0.35
        reasons.append("official_same_domain_or_ir_cdn")
    if transcript_match:
        confidence += 0.25
        reasons.append("transcript_url_marker")
    if period_match:
        confidence += 0.35
        reasons.append("fiscal_period_url_match")
    if row.get("ticker", "").lower() in lowered:
        confidence += 0.05
        reasons.append("ticker_url_match")
    if not period_match:
        return min(confidence, 0.55), ";".join(reasons), "fiscal_period_not_verified"
    return min(confidence, 1.0), ";".join(reasons), ""


def resolve_row(row: dict[str, str], *, probe_network: bool = True) -> dict[str, str]:
    checked: list[str] = []
    if row.get("download_allowed") == "true":
        return _replacement_row(row, "", 0.0, "already_download_allowed", False, "already_download_allowed", checked)
    candidates = list(dict.fromkeys(generated_candidate_urls(row) + crawl_candidate_urls(row)))
    best: tuple[float, str, str, str] = (0.0, "", "", "direct_official_transcript_not_found")
    for candidate in candidates:
        checked.append(candidate)
        accessible = url_accessible(candidate) if probe_network else True
        confidence, reason, blocker = score_transcript_replacement(row, candidate, accessible=accessible)
        if confidence > best[0]:
            best = (confidence, candidate, reason, blocker)
    confidence, url, reason, blocker = best
    allowed = bool(url and confidence >= 0.75 and not blocker)
    if allowed:
        blocker = ""
    elif not blocker:
        blocker = "direct_official_transcript_not_found"
    return _replacement_row(row, url, confidence, reason or "no_verified_replacement", allowed, blocker, checked)


def _replacement_row(
    row: dict[str, str],
    replacement_url: str,
    confidence: float,
    reason: str,
    download_allowed: bool,
    blocked_reason: str,
    checked_urls: list[str],
) -> dict[str, str]:
    domain = urlparse(replacement_url).netloc.lower() if replacement_url else ""
    rights_review = "true" if domain and is_official_cdn_domain(domain) else "false"
    return {
        "candidate_id": row.get("candidate_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "fiscal_year": row.get("fiscal_year", ""),
        "fiscal_quarter": row.get("fiscal_quarter", ""),
        "original_source_url": row.get("source_url", ""),
        "replacement_source_url": replacement_url,
        "source_domain": domain,
        "source_type": "official_ir_hosted_third_party" if rights_review == "true" else row.get("source_type", "official_ir"),
        "expected_format": Path(urlparse(replacement_url).path).suffix.lower().lstrip(".") or row.get("expected_format", ""),
        "replacement_confidence": f"{confidence:.3f}",
        "replacement_reason": reason,
        "download_allowed": str(download_allowed).lower(),
        "blocked_reason": blocked_reason,
        "rights_review_required": rights_review,
        "commit_allowed": "false",
        "training_allowed": "false",
        "raw_text_committed": "false",
        "approval_ref": APPROVAL_REF if download_allowed else "",
        "checked_urls": " | ".join(checked_urls[:20]),
    }


def write_report(rows: list[dict[str, str]], out_path: Path = REPORT_PATH) -> None:
    allowed = [row for row in rows if row.get("download_allowed") == "true"]
    blocked = [row for row in rows if row.get("download_allowed") != "true" and row.get("blocked_reason") != "already_download_allowed"]
    lines = [
        "# First30 URL Replacement Status",
        "",
        f"- Replacement rows checked: {len(rows)}",
        f"- New download-allowed replacements: {len(allowed)}",
        f"- Still blocked rows: {len(blocked)}",
        "- Raw files downloaded in this phase: false",
        "- Commit allowed for raw assets: false",
        "- Training allowed: false",
        "",
        "## New Replacements",
        "",
    ]
    if allowed:
        for row in allowed:
            lines.append(f"- `{row['case_id']}` `{row['ticker']}` confidence={row['replacement_confidence']} {row['replacement_source_url']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Remaining Blockers", ""])
    if blocked:
        for row in blocked:
            lines.append(f"- `{row['case_id']}` `{row['ticker']}`: {row.get('blocked_reason')}; checked={row.get('checked_urls') or 'none'}")
    else:
        lines.append("- none")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_missing_transcript_urls(
    *,
    manifest_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    out_path: Path = OUT_PATH,
    audit_dir: Path = AUDIT_DIR,
    probe_network: bool = True,
) -> dict[str, Any]:
    rows = read_csv(manifest_path)
    target_rows = [row for row in rows if row.get("control_fixture") != "true"]
    replacements = [resolve_row(row, probe_network=probe_network) for row in target_rows]
    write_csv(out_path, replacements, REPLACEMENT_FIELDS)
    write_csv(audit_dir / "first30_transcript_url_replacements.csv", replacements, REPLACEMENT_FIELDS)
    write_report(replacements)
    return {
        "manifest_rows": len(rows),
        "checked_rows": len(replacements),
        "new_replacements": sum(1 for row in replacements if row.get("download_allowed") == "true"),
        "still_blocked": sum(1 for row in replacements if row.get("download_allowed") != "true" and row.get("blocked_reason") != "already_download_allowed"),
        "out_path": str(out_path),
        "desktop_audit": str(audit_dir / "first30_transcript_url_replacements.csv"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve missing first30 transcript direct URLs from official sources.")
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args(argv)
    summary = resolve_missing_transcript_urls(manifest_path=args.manifest, out_path=args.out, audit_dir=args.audit_dir, probe_network=not args.no_network)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
