#!/usr/bin/env python3
"""Collect official webcast replay metadata without downloading media."""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import AUDIT_DIR, USER_AGENT, read_csv, write_csv  # noqa: E402

TRANSCRIPT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
OUT_PATH = ROOT / "data" / "acquisition" / "first30_webcast_replay_metadata.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_webcast_replay_metadata_status.md"

FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "webcast_url",
    "source_domain",
    "source_type",
    "download_allowed",
    "blocked_reason",
    "metadata_only",
    "notes",
]

REPORT_TYPE_BY_QUARTER = {
    "Q1": "First Quarter",
    "Q2": "Second Quarter",
    "Q3": "Third Quarter",
    "Q4": "Fourth Quarter",
}

Q4_EVENT_HOSTS = {
    "DOW": "https://investors.dow.com",
    "EQT": "https://ir.eqt.com",
    "F": "https://shareholder.ford.com",
    "HIG": "https://ir.thehartford.com",
    "LYB": "https://investors.lyondellbasell.com",
    "OC": "https://investor.owenscorning.com",
    "OMC": "https://investor.omnicomgroup.com",
    "RDDT": "https://investor.redditinc.com",
    "RF": "https://ir.regions.com",
    "UBER": "https://investor.uber.com",
}


def _event_feed_url(host: str) -> str:
    params = {
        "apiKey": "",
        "LanguageId": "1",
        "eventSelection": "3",
        "eventDateFilter": "3",
        "includeFinancialReports": "true",
        "includePresentations": "true",
        "includePressReleases": "true",
        "sortOperator": "1",
        "pageSize": "-1",
        "pageNumber": "0",
        "tagList": "financials",
        "includeTags": "true",
        "excludeSelection": "1",
        "year": "-1",
    }
    return f"{host.rstrip('/')}/feed/Event.svc/GetEventList?{urlencode(params)}"


def _events(host: str) -> list[dict[str, Any]]:
    request = Request(_event_feed_url(host), headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    events = payload.get("GetEventListResult", [])
    return events if isinstance(events, list) else []


def _event_matches_case(event: dict[str, Any], row: dict[str, str]) -> bool:
    title = str(event.get("Title", "")).lower()
    tags = " ".join(str(tag).lower() for tag in event.get("TagsList", []) or [])
    year, quarter = _period_from_row(row)
    quarter = quarter.lower()
    qnum = quarter.replace("q", "")
    tokens = [f"{qnum}q{year[-2:]}", f"{quarter} {year}", f"{year} {quarter}", REPORT_TYPE_BY_QUARTER.get(row.get("fiscal_quarter", ""), "").lower()]
    haystack = f"{title} {tags}"
    return any(token and token in haystack for token in tokens)


def _period_from_row(row: dict[str, str]) -> tuple[str, str]:
    year = row.get("fiscal_year", "")
    quarter = row.get("fiscal_quarter", "")
    if year and quarter:
        return year, quarter
    match = re.search(r"_(20\d{2})_q([1-4])$", row.get("case_id", ""))
    if match:
        return match.group(1), f"Q{match.group(2)}"
    return year, quarter


def _row_for_metadata(transcript: dict[str, str], webcast_url: str, source_type: str, blocked_reason: str, notes: str) -> dict[str, str]:
    return {
        "case_id": transcript.get("case_id", ""),
        "ticker": transcript.get("ticker", ""),
        "company_name": transcript.get("company_name", ""),
        "webcast_url": webcast_url,
        "source_domain": urlparse(webcast_url).netloc.lower() if webcast_url else "",
        "source_type": source_type,
        "download_allowed": "false",
        "blocked_reason": blocked_reason,
        "metadata_only": "true",
        "notes": notes,
    }


def search_official_webcast_replay_metadata(
    *,
    transcript_registry: Path = TRANSCRIPT_REGISTRY,
    out_path: Path = OUT_PATH,
    audit_dir: Path = AUDIT_DIR,
) -> dict[str, Any]:
    transcripts = [row for row in read_csv(transcript_registry) if row.get("asset_type") == "transcript"]
    rows: list[dict[str, str]] = []
    cache: dict[str, list[dict[str, Any]]] = {}
    for transcript in transcripts:
        ticker = transcript.get("ticker", "")
        host = Q4_EVENT_HOSTS.get(ticker)
        if not host:
            rows.append(_row_for_metadata(transcript, "", "unknown", "official_webcast_metadata_not_found", "No official event feed mapping configured."))
            continue
        try:
            events = cache.setdefault(host, _events(host))
        except (HTTPError, URLError, TimeoutError, socket.timeout, OSError, json.JSONDecodeError):
            rows.append(_row_for_metadata(transcript, "", "official_event_feed", "official_event_feed_unavailable", "Could not read official event feed."))
            continue
        matched = [event for event in events if _event_matches_case(event, transcript)]
        event = matched[0] if matched else {}
        webcast_url = str(event.get("WebCastLink", "") or "")
        if webcast_url:
            rows.append(
                _row_for_metadata(
                    transcript,
                    webcast_url,
                    "webcast_player_only",
                    "metadata_only_no_direct_audio_download",
                    "Official event feed exposes webcast/player metadata only; no direct MP3/M4A/WAV download attempted.",
                )
            )
        else:
            rows.append(_row_for_metadata(transcript, "", "official_event_feed", "direct_official_audio_not_found", "No webcast URL found in official event feed for this case."))
    write_csv(out_path, rows, FIELDS)
    write_csv(audit_dir / "first30_webcast_replay_metadata.csv", rows, FIELDS)
    summary = {
        "registered_transcript_rows": len(transcripts),
        "metadata_rows": len(rows),
        "webcast_player_only": sum(1 for row in rows if row.get("source_type") == "webcast_player_only"),
        "direct_audio_download_allowed": 0,
        "out_path": str(out_path),
        "desktop_audit": str(audit_dir / "first30_webcast_replay_metadata.csv"),
    }
    write_report(summary, rows)
    return summary


def write_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Webcast Replay Metadata Status",
        "",
        f"- Registered transcript rows checked: {summary['registered_transcript_rows']}",
        f"- Metadata rows: {summary['metadata_rows']}",
        f"- Webcast-player-only rows: {summary['webcast_player_only']}",
        "- Direct audio downloads: 0",
        "- YouTube media used: false",
        "- Signed/session media extracted: false",
        "",
        "## Rows",
        "",
    ]
    if rows:
        for row in rows:
            lines.append(f"- `{row.get('case_id')}` `{row.get('ticker')}`: {row.get('blocked_reason')}")
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search official webcast replay metadata without media downloads.")
    parser.add_argument("--transcript-registry", type=Path, default=TRANSCRIPT_REGISTRY)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    args = parser.parse_args(argv)
    summary = search_official_webcast_replay_metadata(
        transcript_registry=args.transcript_registry,
        out_path=args.out,
        audit_dir=args.audit_dir,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
