#!/usr/bin/env python3
"""Download public earnings-call transcripts listed in sources.yaml."""

from __future__ import annotations

import argparse
import csv
import io
import logging
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_common import (  # noqa: E402
    APPROVED_CORPUS_ROOT,
    BLOCK_PHRASES,
    MARKERS,
    CaseInfo,
    clean_transcript,
    enforce_exact_root,
    load_sources,
    write_csv,
)

logging.getLogger("pypdf").setLevel(logging.ERROR)

USER_AGENT = "SignalEngineTranscriptDownloader/1.0 (+local research; public sources only)"
MIN_TRANSCRIPT_CHARS = 5000
REMOVE_SELECTORS = (
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "iframe",
    "svg",
    "[class*='advert']",
    "[id*='advert']",
)


class DownloadError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default=str(Path(__file__).with_name("sources.yaml")))
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=int, default=45)
    return parser.parse_args()


def robots_allowed(url: str) -> bool:
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
    return parser.can_fetch(USER_AGENT, url)


def fetch(url: str, timeout: int) -> requests.Response:
    if not robots_allowed(url):
        raise DownloadError("blocked: robots.txt does not allow this URL")
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*;q=0.8"},
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise DownloadError(f"HTTP error: {response.status_code}")
    return response


def is_pdf(url: str, response: requests.Response) -> bool:
    content_type = response.headers.get("content-type", "").lower()
    return url.lower().split("?", 1)[0].endswith(".pdf") or "application/pdf" in content_type or response.content.startswith(b"%PDF")


def extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_html_text(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for selector in REMOVE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()
    for link in soup.find_all("a", href=True):
        href = str(link.get("href"))
        if href.lower().endswith(".pdf") and "transcript" in link.get_text(" ", strip=True).lower():
            absolute = urljoin(url, href)
            linked = fetch(absolute, timeout=45)
            if is_pdf(absolute, linked):
                return extract_pdf_text(linked.content)
    candidates = soup.select("article, main, [class*='transcript'], [id*='transcript']")
    text_blocks = [node.get_text("\n", strip=True) for node in candidates]
    text = max(text_blocks, key=len) if text_blocks else soup.get_text("\n", strip=True)
    return text


def validate_text(text: str) -> None:
    lowered = text.lower()
    if len(text) <= MIN_TRANSCRIPT_CHARS:
        raise DownloadError(f"short file: transcript text is {len(text)} characters")
    if any(phrase in lowered for phrase in BLOCK_PHRASES):
        raise DownloadError("blocked: login/paywall/blocked page marker detected")
    if not any(marker in lowered for marker in MARKERS):
        raise DownloadError("validation failed: earnings-call markers not found")


def download_case(case: CaseInfo, root: Path, timeout: int) -> dict[str, str]:
    raw_dir = root / case.case_id / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    response = fetch(case.source_url, timeout)
    if is_pdf(case.source_url, response):
        pdf_path = raw_dir / "transcript.pdf"
        pdf_path.write_bytes(response.content)
        text = extract_pdf_text(response.content)
        note = "PDF saved and extracted to transcript.txt"
        file_path = str(pdf_path)
    else:
        text = extract_html_text(response.text, case.source_url)
        note = "HTML transcript saved"
        file_path = str(raw_dir / "transcript.txt")
    text, _ = clean_transcript(text)
    validate_text(text)
    (raw_dir / "transcript.txt").write_text(text, encoding="utf-8")
    return {
        "case_id": case.case_id,
        "ticker": case.ticker,
        "fiscal_year": str(case.fiscal_year),
        "quarter": case.quarter,
        "source_url": case.source_url,
        "file_path": file_path,
        "status": "success",
        "notes": note,
    }


def main() -> int:
    args = parse_args()
    root = enforce_exact_root(Path(args.out))
    cases = load_sources(Path(args.sources))
    rows: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []
    for case in cases.values():
        try:
            rows.append(download_case(case, root, args.timeout))
        except Exception as exc:
            reason = str(exc)
            rows.append(
                {
                    "case_id": case.case_id,
                    "ticker": case.ticker,
                    "fiscal_year": str(case.fiscal_year),
                    "quarter": case.quarter,
                    "source_url": case.source_url,
                    "file_path": "",
                    "status": "failed",
                    "notes": reason,
                }
            )
            failed.append({"case_id": case.case_id, "ticker": case.ticker, "reason": reason, "source_url": case.source_url})
            print(f"FAILED {case.case_id}: {reason}", file=sys.stderr)
    write_csv(root / "manifest.csv", rows, ["case_id", "ticker", "fiscal_year", "quarter", "source_url", "file_path", "status", "notes"])
    write_csv(root / "failed_downloads.csv", failed, ["case_id", "ticker", "reason", "source_url"])
    successes = sum(1 for row in rows if row["status"] == "success")
    print(f"Download complete: {successes} succeeded, {len(failed)} failed, root={APPROVED_CORPUS_ROOT}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
