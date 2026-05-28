#!/usr/bin/env python3
"""Discover metadata-only company IR transcript source candidates."""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.source_adapters import SOURCE_CANDIDATE_FIELDS, candidate_to_csv_row, normalize_candidate, source_domain_for_url

USER_AGENT = "SignalEngineSourceDiscovery/0.1 (+metadata-only; contact=local)"
DEFAULT_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_media_manifest.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_company_ir_source_candidates.csv"
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "company_ir_source_discovery.md"
MEDIA_SUFFIXES = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".mov", ".mkv", ".webm", ".avi")


class LinkExtractor(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self._href: str | None = None
        self._text: list[str] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href:
            return
        source_url = urljoin(self.base_url, self._href)
        link_text = " ".join(" ".join(self._text).split())
        self.links.append({"source_url": source_url, "candidate_kind": classify_candidate_kind(source_url, link_text)})
        self._href = None
        self._text = []


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_CANDIDATE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def classify_candidate_kind(source_url: str, link_text: str = "") -> str:
    parsed = urlparse(source_url)
    combined = f"{source_url} {link_text}".lower()
    if "youtube.com" in parsed.netloc.lower() or "youtu.be" in parsed.netloc.lower():
        return "youtube_or_external_video"
    if parsed.path.lower().endswith(MEDIA_SUFFIXES):
        return "audio_video"
    if "transcript" in combined:
        return "transcript"
    if "webcast" in combined or "conference call" in combined or "replay" in combined:
        return "webcast"
    if "presentation" in combined or "slides" in combined or parsed.path.lower().endswith(".pdf"):
        return "presentation"
    if "earnings release" in combined or "results" in combined:
        return "earnings_release"
    if "investor" in combined or "ir." in parsed.netloc.lower():
        return "company_ir"
    return "unknown"


def extract_candidate_links(base_url: str, html: str) -> list[dict[str, str]]:
    parser = LinkExtractor(base_url)
    parser.feed(html)
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for row in parser.links:
        if row["source_url"] in seen:
            continue
        seen.add(row["source_url"])
        rows.append(row)
    return rows


def robots_allowed(source_url: str) -> bool:
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return False
    return parser.can_fetch(USER_AGENT, source_url)


def fetch_html(source_url: str, *, timeout: int = 20) -> str:
    request = Request(source_url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - guarded optional metadata-only operator path
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            return ""
        return response.read().decode("utf-8", errors="replace")


def manifest_seed_candidates(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        base = {
            "case_id": row.get("case_id", ""),
            "ticker": row.get("ticker_symbol") or row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "fiscal_period": f"FY{row.get('fiscal_year', '')} {row.get('fiscal_quarter', '')}".strip(),
            "event_date": row.get("earnings_call_date", ""),
            "source_type": row.get("source_type") or "company_ir",
            "source_name": "company_ir_manifest",
            "discovery_method": "media_manifest_seed_no_network",
            "rights_status": "metadata_only",
            "download_allowed": False,
            "approval_required": True,
            "raw_text_committed": False,
            "robots_allowed": False,
            "paywall_status": "not_checked",
            "confidence": 0.25,
            "notes": "Metadata-only candidate from existing manifest URL; no page payload fetched.",
        }
        for url_field in ("transcript_source_url", "audio_source_url", "video_source_url"):
            source_url = str(row.get(url_field, "")).strip()
            if not source_url:
                continue
            key = (base["case_id"], source_url, "")
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    **base,
                    "source_url": source_url,
                    "source_domain": row.get("source_domain") or source_domain_for_url(source_url),
                    "discovered_from_url": source_url,
                    "candidate_kind": classify_candidate_kind(source_url),
                }
            )
    return candidates


def fetch_page_candidates(seed_candidates: list[dict[str, Any]], *, rate_limit_seconds: float, timeout: int) -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []
    for seed in seed_candidates:
        source_url = str(seed.get("source_url", ""))
        if not robots_allowed(source_url):
            continue
        time.sleep(max(0.0, rate_limit_seconds))
        html = fetch_html(source_url, timeout=timeout)
        for link in extract_candidate_links(source_url, html):
            discovered.append(
                {
                    **seed,
                    "source_url": link["source_url"],
                    "source_domain": source_domain_for_url(link["source_url"]),
                    "discovered_from_url": source_url,
                    "discovery_method": "company_ir_html_link_metadata_only",
                    "candidate_kind": link["candidate_kind"],
                    "robots_allowed": True,
                    "confidence": 0.5,
                    "notes": "Metadata-only HTML link candidate; page payload was not stored.",
                }
            )
    return discovered


def write_report(path: Path, *, summary: dict[str, Any], skipped_reason: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Company IR Source Discovery",
        "",
        f"- Created at: {datetime.now(UTC).replace(microsecond=0).isoformat()}",
        f"- Status: {'skipped' if skipped_reason else 'completed'}",
        f"- Manifest rows: {summary.get('manifest_rows', 0)}",
        f"- Candidate rows: {summary.get('candidate_rows', 0)}",
        f"- Fetch pages enabled: {str(summary.get('fetch_pages', False)).lower()}",
        "- Source payload storage performed: false",
        "- Downloads allowed by discovery: false",
    ]
    if skipped_reason:
        lines.append(f"- Skipped reason: {skipped_reason}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_discovery(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    out_csv: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
    fetch_pages: bool = False,
    rate_limit_seconds: float = 1.0,
    timeout: int = 20,
) -> dict[str, Any]:
    if not manifest_path.exists():
        summary = {"manifest_rows": 0, "candidate_rows": 0, "fetch_pages": fetch_pages}
        write_csv(out_csv, [])
        write_report(report_path, summary=summary, skipped_reason=f"input manifest missing: {manifest_path}")
        return summary
    manifest_rows = read_csv(manifest_path)
    seed_candidates = manifest_seed_candidates(manifest_rows)
    candidates = seed_candidates
    if fetch_pages:
        candidates = seed_candidates + fetch_page_candidates(seed_candidates, rate_limit_seconds=rate_limit_seconds, timeout=timeout)
    csv_rows = [candidate_to_csv_row(normalize_candidate(candidate)) for candidate in candidates]
    write_csv(out_csv, csv_rows)
    summary = {"manifest_rows": len(manifest_rows), "candidate_rows": len(csv_rows), "fetch_pages": fetch_pages}
    write_report(report_path, summary=summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--fetch-pages", action="store_true")
    parser.add_argument("--rate-limit-seconds", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)
    summary = run_discovery(
        manifest_path=args.manifest,
        out_csv=args.out_csv,
        report_path=args.report_path,
        fetch_pages=args.fetch_pages,
        rate_limit_seconds=args.rate_limit_seconds,
        timeout=args.timeout,
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
