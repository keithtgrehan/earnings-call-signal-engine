#!/usr/bin/env python3
"""Find official direct audio candidates for registered first30 transcripts."""

from __future__ import annotations

import argparse
import csv
import json
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

from tools.first30_transcript_common import AUDIT_DIR, DESKTOP_WORKSPACE, read_csv, write_csv  # noqa: E402

TRANSCRIPT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
INGESTION_MANIFEST = ROOT / "data" / "acquisition" / "first30_transcript_ingestion_manifest.csv"
AUDIO_REGISTRY = ROOT / "data" / "acquisition" / "audio_registry.csv"
OUT_PATH = ROOT / "data" / "acquisition" / "first30_audio_candidates.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_audio_candidate_status.md"

USER_AGENT = "SignalEngineCorpusAssessment/2.0 (metadata-safe; contact: project owner)"
AUDIO_SUFFIXES = (".mp3", ".m4a", ".wav")
AUDIO_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "source_page_url",
    "audio_url",
    "source_domain",
    "source_relation",
    "direct_audio",
    "download_allowed",
    "review_required",
    "blocked_reason",
    "confidence",
    "already_registered",
    "commit_allowed",
    "training_allowed",
    "raw_audio_committed",
    "notes",
]

KNOWN_AUDIO_PAGES = {
    "vz_2025_q1": "https://www.verizon.com/about/investors/quarterly-reports/1q-2025-earnings-conference-call-webcast",
    "vz_2025_q2": "https://www.verizon.com/about/investors/quarterly-reports/2q-2025-earnings-conference-call-webcast",
    "vz_2025_q3": "https://www.verizon.com/about/investors/quarterly-reports/3q-2025-earnings-conference-call-webcast",
    "vz_2025_q4": "https://www.verizon.com/about/investors/quarterly-reports/4q-2025-earnings-conference-call-webcast",
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
    try:
        request = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Accept": "audio/*,*/*"})
        with urlopen(request, timeout=timeout) as response:
            return 200 <= int(response.status) < 300
    except HTTPError as exc:
        if exc.code not in {403, 405}:
            return False
    except (TimeoutError, URLError, socket.timeout, OSError):
        return False
    try:
        request = Request(url, method="GET", headers={"User-Agent": USER_AGENT, "Accept": "audio/*,*/*"})
        with urlopen(request, timeout=timeout) as response:
            response.read(1)
            return 200 <= int(response.status) < 300
    except Exception:
        return False


def is_direct_audio_url(url: str) -> bool:
    lowered = url.lower()
    if "youtube.com" in lowered or "youtu.be" in lowered or "soundcloud.com" in lowered:
        return False
    return any(urlparse(lowered).path.endswith(suffix) for suffix in AUDIO_SUFFIXES)


def _same_domain(page_url: str, candidate_url: str) -> bool:
    page_host = urlparse(page_url).netloc.lower()
    candidate_host = urlparse(candidate_url).netloc.lower()
    return bool(page_host and candidate_host and (page_host == candidate_host or candidate_host.endswith("." + page_host) or page_host.endswith("." + candidate_host)))


def crawl_audio_urls(page_url: str) -> list[str]:
    if not page_url.startswith(("http://", "https://")):
        return []
    try:
        html = fetch_page(page_url)
    except Exception:
        return []
    parser = LinkExtractor()
    parser.feed(html)
    urls: list[str] = []
    for href in parser.links:
        candidate = urljoin(page_url, href)
        if not _same_domain(page_url, candidate):
            continue
        if is_direct_audio_url(candidate):
            urls.append(candidate)
    return list(dict.fromkeys(urls))


def _source_pages(row: dict[str, str], manifest_by_case: dict[str, dict[str, str]]) -> list[str]:
    pages: list[str] = []
    if row.get("case_id") in KNOWN_AUDIO_PAGES:
        pages.append(KNOWN_AUDIO_PAGES[row["case_id"]])
    for value in (row.get("source_url", ""), manifest_by_case.get(row.get("case_id", ""), {}).get("source_url", "")):
        if value.startswith(("http://", "https://")):
            pages.append(value)
    return list(dict.fromkeys(pages))


def _base_row(transcript: dict[str, str]) -> dict[str, str]:
    return {
        "case_id": transcript.get("case_id", ""),
        "ticker": transcript.get("ticker", ""),
        "company_name": transcript.get("company_name", ""),
        "source_page_url": transcript.get("source_url", ""),
        "audio_url": "",
        "source_domain": "",
        "source_relation": "audio_support_for_transcript",
        "direct_audio": "false",
        "download_allowed": "false",
        "review_required": "false",
        "blocked_reason": "direct_official_audio_not_found",
        "confidence": "0.000",
        "already_registered": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
        "raw_audio_committed": "false",
        "notes": "",
    }


def resolve_audio_candidates(
    *,
    transcript_registry: Path = TRANSCRIPT_REGISTRY,
    ingestion_manifest: Path = INGESTION_MANIFEST,
    audio_registry: Path = AUDIO_REGISTRY,
    out_path: Path = OUT_PATH,
    audit_dir: Path = AUDIT_DIR,
) -> dict[str, Any]:
    transcripts = [row for row in read_csv(transcript_registry) if row.get("asset_type") == "transcript" and row.get("eval_allowed") == "true"]
    manifest_by_case = {row.get("case_id", ""): row for row in read_csv(ingestion_manifest)}
    registered_audio = {row.get("case_id", ""): row for row in read_csv(audio_registry)}
    rows: list[dict[str, str]] = []
    for transcript in transcripts:
        row = _base_row(transcript)
        registered = registered_audio.get(transcript.get("case_id", ""))
        if registered:
            row.update(
                {
                    "audio_url": registered.get("source_url", ""),
                    "source_domain": urlparse(registered.get("source_url", "")).netloc.lower(),
                    "direct_audio": "true" if is_direct_audio_url(registered.get("source_url", "")) else "false",
                    "download_allowed": "false",
                    "blocked_reason": "already_registered",
                    "confidence": "1.000",
                    "already_registered": "true",
                    "notes": "Audio already present in repo-safe registry; raw audio remains Desktop-only.",
                }
            )
            rows.append(row)
            continue
        found = False
        checked_pages = _source_pages(transcript, manifest_by_case)
        for page in checked_pages:
            for audio_url in crawl_audio_urls(page):
                row.update(
                    {
                        "source_page_url": page,
                        "audio_url": audio_url,
                        "source_domain": urlparse(audio_url).netloc.lower(),
                        "direct_audio": "true",
                        "download_allowed": "true" if url_accessible(audio_url) else "false",
                        "blocked_reason": "" if url_accessible(audio_url) else "direct_audio_url_not_accessible",
                        "confidence": "0.900",
                        "notes": "Direct official audio URL discovered from same-domain IR page.",
                    }
                )
                found = True
                break
            if found:
                break
        if not found:
            row["notes"] = "Checked official transcript/source pages; no direct same-domain MP3/M4A/WAV found."
        rows.append(row)
    write_csv(out_path, rows, AUDIO_FIELDS)
    write_csv(audit_dir / "first30_audio_candidates.csv", rows, AUDIO_FIELDS)
    write_report(rows)
    return {
        "registered_transcript_rows": len(transcripts),
        "candidate_rows": len(rows),
        "new_download_allowed_audio": sum(1 for row in rows if row.get("download_allowed") == "true"),
        "already_registered_audio": sum(1 for row in rows if row.get("already_registered") == "true"),
        "out_path": str(out_path),
        "desktop_audit": str(audit_dir / "first30_audio_candidates.csv"),
    }


def write_report(rows: list[dict[str, str]]) -> None:
    allowed = [row for row in rows if row.get("download_allowed") == "true"]
    blocked = [row for row in rows if row.get("blocked_reason") not in {"", "already_registered"}]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Audio Candidate Status",
        "",
        f"- Registered transcript cases checked: {len(rows)}",
        f"- New direct audio download-allowed rows: {len(allowed)}",
        f"- Already registered audio rows: {sum(1 for row in rows if row.get('already_registered') == 'true')}",
        f"- Blocked/no-direct-audio rows: {len(blocked)}",
        "- YouTube media used: false",
        "- Cloud ASR used: false",
        "",
        "## Direct Audio Candidates",
        "",
    ]
    if allowed:
        for row in allowed:
            lines.append(f"- `{row['case_id']}` `{row['ticker']}` {row['audio_url']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Blocked Rows", ""])
    if blocked:
        for row in blocked:
            lines.append(f"- `{row['case_id']}` `{row['ticker']}`: {row['blocked_reason']}")
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve direct official audio candidates for registered first30 transcripts.")
    parser.add_argument("--transcript-registry", type=Path, default=TRANSCRIPT_REGISTRY)
    parser.add_argument("--ingestion-manifest", type=Path, default=INGESTION_MANIFEST)
    parser.add_argument("--audio-registry", type=Path, default=AUDIO_REGISTRY)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    args = parser.parse_args(argv)
    summary = resolve_audio_candidates(
        transcript_registry=args.transcript_registry,
        ingestion_manifest=args.ingestion_manifest,
        audio_registry=args.audio_registry,
        out_path=args.out,
        audit_dir=args.audit_dir,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
