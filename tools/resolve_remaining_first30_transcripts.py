#!/usr/bin/env python3
"""Resolve remaining first30 transcript gaps from official/public company feeds."""

from __future__ import annotations

import argparse
import json
import socket
import sys
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import (  # noqa: E402
    APPROVAL_REF,
    AUDIT_DIR,
    FIRST30_INGESTION_FIELDS,
    FIRST30_INGESTION_MANIFEST_PATH,
    USER_AGENT,
    domain_for_url,
    fetch_url,
    hard_blocker_for_source,
    html_to_text,
    is_direct_text_url,
    is_official_cdn_domain,
    looks_like_vendor_raw,
    normalize_text,
    read_csv,
    write_csv,
)
from tools.resolve_first30_missing_transcript_urls import OUT_PATH as REPLACEMENTS_PATH  # noqa: E402
from tools.resolve_first30_missing_transcript_urls import REPLACEMENT_FIELDS  # noqa: E402

OUT_PATH = ROOT / "data" / "acquisition" / "remaining_first30_transcript_url_replacements.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "remaining_first30_transcript_gap_status.md"

REPORT_TYPE_BY_QUARTER = {
    "Q1": "First Quarter",
    "Q2": "Second Quarter",
    "Q3": "Third Quarter",
    "Q4": "Fourth Quarter",
}

Q4_FEED_HOSTS = {
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

KNOWN_VERIZON_WEBCAST_TRANSCRIPTS = {
    "vz_2025_q1": "https://www.verizon.com/about/file/75373/download?token=zTlud4Fy",
    "vz_2025_q4": "https://www.verizon.com/about/file/77405/download?token=XTRzK52Y",
}


def _quarter_type(row: dict[str, str]) -> str:
    return REPORT_TYPE_BY_QUARTER.get(row.get("fiscal_quarter", ""), "")


def _q4_feed_url(host: str) -> str:
    params = {
        "apiKey": "",
        "LanguageId": "1",
        "reportTypes": "|".join(REPORT_TYPE_BY_QUARTER.values()),
        "reportSubType": "|".join(REPORT_TYPE_BY_QUARTER.values()),
        "reportSubTypeList": "|".join(REPORT_TYPE_BY_QUARTER.values()),
        "pageSize": "-1",
        "pageNumber": "0",
        "tagList": "",
        "includeTags": "true",
        "excludeSelection": "1",
        "year": "-1",
    }
    return f"{host.rstrip('/')}/feed/FinancialReport.svc/GetFinancialReportList?{urlencode(params)}"


def _q4_financial_reports(host: str, *, timeout: int = 30) -> list[dict[str, Any]]:
    request = Request(_q4_feed_url(host), headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    reports = payload.get("GetFinancialReportListResult", [])
    return reports if isinstance(reports, list) else []


def _candidate_urls_from_q4_feed(row: dict[str, str]) -> list[str]:
    host = Q4_FEED_HOSTS.get(row.get("ticker", ""))
    if not host:
        return []
    try:
        reports = _q4_financial_reports(host)
    except (HTTPError, URLError, TimeoutError, socket.timeout, OSError, json.JSONDecodeError):
        return []
    target_year = row.get("fiscal_year", "")
    target_quarter = _quarter_type(row)
    urls: list[str] = []
    for report in reports:
        if str(report.get("ReportYear", "")) != target_year:
            continue
        if str(report.get("ReportSubType", "")) != target_quarter:
            continue
        for document in report.get("Documents") or []:
            title = str(document.get("DocumentTitle", ""))
            category = str(document.get("DocumentCategory", ""))
            url = str(document.get("DocumentPath", ""))
            if not url:
                continue
            if "transcript" not in f"{title} {category} {url}".lower():
                continue
            urls.append(url)
    return list(dict.fromkeys(urls))


def candidate_urls_for_row(row: dict[str, str]) -> list[str]:
    urls = _candidate_urls_from_q4_feed(row)
    if row.get("case_id", "") in KNOWN_VERIZON_WEBCAST_TRANSCRIPTS:
        urls.append(KNOWN_VERIZON_WEBCAST_TRANSCRIPTS[row["case_id"]])
    return list(dict.fromkeys(urls))


def _payload_to_text(url: str, payload: bytes, content_type: str) -> tuple[str, str]:
    lowered = content_type.lower()
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix == ".pdf" or "pdf" in lowered:
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(payload))
            return normalize_text("\n\n".join(page.extract_text() or "" for page in reader.pages)), "pypdf_memory"
        except Exception as exc:  # pragma: no cover - parser/runtime dependent
            return "", f"pdf_parse_failed:{type(exc).__name__}"
    if suffix in {".html", ".htm"} or "html" in lowered:
        return html_to_text(payload), "html_parser_memory"
    return normalize_text(payload.decode("utf-8", errors="replace")), "text_memory"


def probe_transcript_url(row: dict[str, str], url: str, *, probe_content: bool = True) -> tuple[bool, str, str]:
    candidate = {
        **row,
        "source_url": url,
        "source_domain": domain_for_url(url),
        "commit_allowed": "false",
        "training_allowed": "false",
    }
    blocker = hard_blocker_for_source(candidate)
    if blocker:
        return False, blocker, ""
    if not is_direct_text_url(url, row.get("expected_format", "")):
        return False, "not_direct_transcript_url", ""
    if not probe_content:
        return True, "content_probe_skipped", ""
    try:
        payload, content_type = fetch_url(url, timeout=45)
    except Exception as exc:  # pragma: no cover - network-dependent
        return False, f"direct_url_not_accessible:{type(exc).__name__}", ""
    text, parser = _payload_to_text(url, payload, content_type)
    if text and looks_like_vendor_raw(text):
        return False, "vendor_copyright_marker_detected", parser
    if not text:
        return False, parser or "text_parse_empty", parser
    return True, f"content_clean:{parser}", parser


def _replacement_row(
    row: dict[str, str],
    *,
    replacement_url: str,
    download_allowed: bool,
    blocked_reason: str,
    reason: str,
    checked_urls: list[str],
) -> dict[str, str]:
    domain = domain_for_url(replacement_url) if replacement_url else ""
    rights_review_required = "true" if domain and is_official_cdn_domain(domain) else "false"
    return {
        "candidate_id": row.get("candidate_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "fiscal_year": row.get("fiscal_year", ""),
        "fiscal_quarter": row.get("fiscal_quarter", ""),
        "original_source_url": row.get("source_url", ""),
        "replacement_source_url": replacement_url,
        "source_domain": domain,
        "source_type": "official_ir_hosted_third_party" if rights_review_required == "true" else row.get("source_type", "official_ir"),
        "expected_format": Path(urlparse(replacement_url).path).suffix.lower().lstrip(".") or row.get("expected_format", ""),
        "replacement_confidence": "1.000" if download_allowed else ("0.700" if replacement_url else "0.000"),
        "replacement_reason": reason,
        "download_allowed": str(download_allowed).lower(),
        "blocked_reason": "" if download_allowed else blocked_reason,
        "rights_review_required": rights_review_required,
        "commit_allowed": "false",
        "training_allowed": "false",
        "raw_text_committed": "false",
        "approval_ref": APPROVAL_REF if download_allowed else "",
        "checked_urls": " | ".join(checked_urls),
    }


def resolve_remaining_row(row: dict[str, str], *, probe_content: bool = True) -> dict[str, str]:
    checked = candidate_urls_for_row(row)
    if not checked:
        return _replacement_row(
            row,
            replacement_url="",
            download_allowed=False,
            blocked_reason=row.get("blocked_reason") or "direct_official_transcript_not_found",
            reason="official_feed_no_transcript_url",
            checked_urls=[],
        )
    best_blocker = "direct_official_transcript_not_found"
    best_reason = "no_clean_candidate"
    best_url = ""
    for url in checked:
        clean, reason, _parser = probe_transcript_url(row, url, probe_content=probe_content)
        if clean:
            return _replacement_row(
                row,
                replacement_url=url,
                download_allowed=True,
                blocked_reason="",
                reason=f"official_public_financial_feed;{reason}",
                checked_urls=checked,
            )
        best_url = best_url or url
        best_blocker = reason or best_blocker
        best_reason = f"official_public_financial_feed;{reason}"
    return _replacement_row(
        row,
        replacement_url=best_url,
        download_allowed=False,
        blocked_reason=best_blocker,
        reason=best_reason,
        checked_urls=checked,
    )


def _source_url_kind(url: str) -> str:
    domain = domain_for_url(url)
    if is_official_cdn_domain(domain) and is_direct_text_url(url):
        return "official_ir_cdn_direct"
    if is_direct_text_url(url):
        return "official_direct"
    return "landing_or_metadata"


def _is_prepared_only_transcript_url(url: str) -> bool:
    lowered = url.lower()
    return "prepared-remarks" in lowered or "prepared_remarks" in lowered or "preparedremarks" in lowered


def _apply_replacement_to_manifest(row: dict[str, str], replacement: dict[str, str]) -> dict[str, str]:
    if replacement.get("download_allowed") != "true":
        return row
    url = replacement["replacement_source_url"]
    updated = dict(row)
    updated["source_url"] = url
    updated["source_domain"] = replacement["source_domain"]
    updated["source_type"] = replacement["source_type"]
    updated["expected_format"] = replacement["expected_format"] or "pdf"
    updated["source_url_kind"] = _source_url_kind(url)
    updated["rights_review_required"] = replacement["rights_review_required"]
    updated["download_allowed"] = "true"
    updated["blocked_reason"] = ""
    updated["raw_text_committed"] = "false"
    updated["commit_allowed"] = "false"
    updated["training_allowed"] = "false"
    updated["approval_ref"] = APPROVAL_REF
    updated["next_action"] = "download_desktop_only"
    updated["notes"] = (row.get("notes", "") + " Remaining-gap resolver found clean official transcript URL.").strip()
    if _is_prepared_only_transcript_url(url):
        updated["qna_expected"] = "false"
        updated["source_relation"] = "prepared_transcript_only"
        updated["notes"] = (updated.get("notes", "") + " Source is prepared remarks only; do not treat as full-call Q&A transcript.").strip()
    return updated


def _merge_replacements(existing: list[dict[str, str]], new_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_case = {row.get("case_id", ""): row for row in existing if row.get("case_id")}
    for row in new_rows:
        case_id = row.get("case_id", "")
        if case_id:
            by_case[case_id] = row
    return [by_case[key] for key in sorted(by_case)]


def write_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    blockers = Counter(row.get("blocked_reason", "") for row in rows if row.get("download_allowed") != "true")
    lines = [
        "# Remaining First30 Transcript Gap Status",
        "",
        f"- Remaining rows checked: {summary['checked_rows']}",
        f"- Clean replacements applied: {summary['applied_replacements']}",
        f"- Vendor-marker blocked candidates: {summary['vendor_marker_blocked']}",
        f"- Still unresolved or blocked: {summary['still_blocked']}",
        "- Raw files downloaded by resolver: false",
        "- Commit allowed for raw assets: false",
        "- Training allowed: false",
        "",
        "## Applied Replacements",
        "",
    ]
    applied = [row for row in rows if row.get("download_allowed") == "true"]
    if applied:
        for row in applied:
            lines.append(f"- `{row['case_id']}` `{row['ticker']}`: {row['replacement_source_url']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Blockers By Reason", ""])
    if blockers:
        for reason, count in sorted(blockers.items()):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Remaining Blocked Rows", ""])
    blocked = [row for row in rows if row.get("download_allowed") != "true"]
    if blocked:
        for row in blocked:
            lines.append(f"- `{row['case_id']}` `{row['ticker']}`: {row.get('blocked_reason')}; checked={row.get('checked_urls') or 'none'}")
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_remaining_first30_transcripts(
    *,
    manifest_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    replacements_path: Path = REPLACEMENTS_PATH,
    out_path: Path = OUT_PATH,
    audit_dir: Path = AUDIT_DIR,
    probe_content: bool = True,
) -> dict[str, Any]:
    manifest_rows = read_csv(manifest_path)
    target_rows = [
        row
        for row in manifest_rows
        if row.get("control_fixture") != "true" and row.get("download_allowed") != "true"
    ]
    replacement_rows = [resolve_remaining_row(row, probe_content=probe_content) for row in target_rows]
    replacement_by_case = {row.get("case_id", ""): row for row in replacement_rows}
    updated_manifest = [_apply_replacement_to_manifest(row, replacement_by_case[row.get("case_id", "")]) if row.get("case_id", "") in replacement_by_case else row for row in manifest_rows]
    merged_replacements = _merge_replacements(read_csv(replacements_path), replacement_rows)
    write_csv(out_path, replacement_rows, REPLACEMENT_FIELDS)
    write_csv(audit_dir / "remaining_first30_transcript_url_replacements.csv", replacement_rows, REPLACEMENT_FIELDS)
    write_csv(replacements_path, merged_replacements, REPLACEMENT_FIELDS)
    write_csv(audit_dir / "first30_transcript_url_replacements.csv", merged_replacements, REPLACEMENT_FIELDS)
    write_csv(manifest_path, updated_manifest, FIRST30_INGESTION_FIELDS)
    write_csv(audit_dir / "first30_transcript_ingestion_manifest.csv", updated_manifest, FIRST30_INGESTION_FIELDS)
    summary = {
        "checked_rows": len(target_rows),
        "applied_replacements": sum(1 for row in replacement_rows if row.get("download_allowed") == "true"),
        "vendor_marker_blocked": sum(1 for row in replacement_rows if row.get("blocked_reason") == "vendor_copyright_marker_detected"),
        "still_blocked": sum(1 for row in replacement_rows if row.get("download_allowed") != "true"),
        "download_allowed_rows": sum(1 for row in updated_manifest if row.get("download_allowed") == "true"),
        "out_path": str(out_path),
        "replacements_path": str(replacements_path),
        "desktop_audit": str(audit_dir / "remaining_first30_transcript_url_replacements.csv"),
    }
    write_report(summary, replacement_rows)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve remaining first30 transcript direct URLs from official public feeds.")
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--replacements", type=Path, default=REPLACEMENTS_PATH)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    parser.add_argument("--skip-content-probe", action="store_true")
    args = parser.parse_args(argv)
    summary = resolve_remaining_first30_transcripts(
        manifest_path=args.manifest,
        replacements_path=args.replacements,
        out_path=args.out,
        audit_dir=args.audit_dir,
        probe_content=not args.skip_content_probe,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
