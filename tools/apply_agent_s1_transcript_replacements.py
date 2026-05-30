#!/usr/bin/env python3
"""Apply Agent S1 first30 transcript replacement URLs with guardrail probes."""

from __future__ import annotations

import argparse
from io import BytesIO
import json
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
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

REPORT_PATH = ROOT / "reports" / "acquisition" / "agent_s1_replacement_application.md"

S1_REPLACEMENTS: dict[str, dict[str, str]] = {
    "jpm_2025_q4": {
        "url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/4th-quarter/jpm-4q25-earnings-call-transcript.pdf",
        "source_type": "official_ir",
        "policy": "download_if_clean",
    },
    "jpm_2025_q3": {
        "url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/3rd-quarter/jpm-3q25-earnings-call-transcript.pdf",
        "source_type": "official_ir",
        "policy": "download_if_clean",
    },
    "jpm_2025_q2": {
        "url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/2nd-quarter/jpm-2q25-earnings-call-transcript.pdf",
        "source_type": "official_ir",
        "policy": "download_if_clean",
    },
    "jpm_2025_q1": {
        "url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/1st-quarter/1q25-earnings-transcript.pdf",
        "source_type": "official_ir",
        "policy": "download_if_clean",
    },
    "cat_2025_q3": {
        "url": "https://s25.q4cdn.com/358376879/files/doc_financials/2025/q3/3Q-2025-Caterpillar-Inc-Earnings-Call-Transcript_-10-29-2025.pdf",
        "source_type": "official_ir_hosted_third_party",
        "policy": "official_ir_cdn_pdf_review_required",
    },
    "cat_2025_q2": {
        "url": "https://s25.q4cdn.com/358376879/files/doc_financials/2025/q2/2Q-2025-Caterpillar-Inc-Earnings-Call-Transcript_8-5-2025.pdf",
        "source_type": "official_ir_hosted_third_party",
        "policy": "official_ir_cdn_pdf_review_required",
    },
    "cat_2025_q1": {
        "url": "https://s25.q4cdn.com/358376879/files/doc_financials/2025/q1/1Q-2025-Caterpillar-Inc-Earnings-Call-Transcript_4-30-2025_vF.pdf",
        "source_type": "official_ir_hosted_third_party",
        "policy": "official_ir_cdn_pdf_review_required",
    },
    "cat_2024_q4": {
        "url": "https://s25.q4cdn.com/358376879/files/doc_financials/2024/q4/4Q-2024-Caterpillar-Inc-Earnings-Call-Transcript_1-30-2025_vF.pdf",
        "source_type": "official_ir_hosted_third_party",
        "policy": "official_ir_cdn_pdf_review_required",
    },
}


def _url_accessible(url: str, *, timeout: int = 20) -> tuple[bool, str]:
    for method in ("HEAD", "GET"):
        try:
            request = Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,text/html,text/plain,*/*"})
            with urlopen(request, timeout=timeout) as response:
                if 200 <= int(response.status) < 300:
                    return True, f"{response.status}:{response.headers.get('Content-Type', '')}"
                return False, f"http_status_{response.status}"
        except HTTPError as exc:
            if exc.code in {403, 405} and method == "HEAD":
                continue
            return False, f"http_error_{exc.code}"
        except (TimeoutError, URLError, socket.timeout, OSError) as exc:
            if method == "HEAD":
                continue
            return False, f"{type(exc).__name__}"
    return False, "not_accessible"


def _pdf_payload_to_text(payload: bytes) -> tuple[str, str]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(payload))
        return normalize_text("\n\n".join(page.extract_text() or "" for page in reader.pages)), "pypdf_memory"
    except Exception as exc:  # pragma: no cover - parser/runtime dependent
        return "", f"memory_parse_failed:{type(exc).__name__}"


def _text_from_payload(url: str, payload: bytes, content_type: str) -> tuple[str, str]:
    lowered = content_type.lower()
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix == ".pdf" or "pdf" in lowered:
        return _pdf_payload_to_text(payload)
    if suffix in {".html", ".htm"} or "html" in lowered:
        return html_to_text(payload), "html_parser_memory"
    return normalize_text(payload.decode("utf-8", errors="replace")), "text_memory"


def _content_clean(url: str, *, probe_content: bool = True) -> tuple[bool, str, str]:
    if not probe_content:
        return True, "content_probe_skipped", ""
    try:
        payload, content_type = fetch_url(url, timeout=45)
    except Exception as exc:  # pragma: no cover - network-dependent
        return False, f"content_fetch_failed:{type(exc).__name__}", ""
    text, parser = _text_from_payload(url, payload, content_type)
    if text and looks_like_vendor_raw(text):
        return False, "vendor_copyright_marker_detected", parser
    return True, f"content_clean:{parser}", parser


def _source_url_kind(url: str) -> str:
    domain = domain_for_url(url)
    if is_official_cdn_domain(domain) and is_direct_text_url(url):
        return "official_ir_cdn_direct"
    if is_direct_text_url(url):
        return "official_direct"
    return "landing_or_metadata"


def _replacement_row(
    row: dict[str, str],
    url: str,
    *,
    clean: bool,
    blocked_reason: str,
    reason: str,
    content_probe: str,
    official_ir_cdn_assessment: bool,
) -> dict[str, str]:
    domain = domain_for_url(url)
    spec = S1_REPLACEMENTS[row["case_id"]]
    is_cdn = is_official_cdn_domain(domain)
    direct = is_direct_text_url(url, row.get("expected_format", ""))
    candidate = {
        **row,
        "source_url": url,
        "source_domain": domain,
        "source_type": spec["source_type"],
        "commit_allowed": "false",
        "training_allowed": "false",
    }
    hard_blocker = hard_blocker_for_source(candidate)
    if hard_blocker:
        clean = False
        blocked_reason = hard_blocker
    if not direct:
        clean = False
        blocked_reason = blocked_reason or "not_direct_transcript_url"
    if is_cdn and not official_ir_cdn_assessment:
        clean = False
        blocked_reason = blocked_reason or "official_ir_cdn_review_queue_only"
    allowed = clean and not blocked_reason
    rights_review_required = "true" if is_cdn else "false"
    return {
        "candidate_id": row.get("candidate_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "fiscal_year": row.get("fiscal_year", ""),
        "fiscal_quarter": row.get("fiscal_quarter", ""),
        "original_source_url": row.get("source_url", ""),
        "replacement_source_url": url,
        "source_domain": domain,
        "source_type": spec["source_type"],
        "expected_format": Path(urlparse(url).path).suffix.lower().lstrip(".") or row.get("expected_format", ""),
        "replacement_confidence": "1.000" if allowed else "0.500",
        "replacement_reason": f"agent_s1_{spec['policy']};{reason};{content_probe}",
        "download_allowed": str(allowed).lower(),
        "blocked_reason": "" if allowed else blocked_reason or "not_clean_for_download",
        "rights_review_required": rights_review_required,
        "commit_allowed": "false",
        "training_allowed": "false",
        "raw_text_committed": "false",
        "approval_ref": APPROVAL_REF if allowed else "",
        "checked_urls": url,
    }


def _updated_manifest_row(row: dict[str, str], replacement: dict[str, str]) -> dict[str, str]:
    if replacement.get("download_allowed") != "true":
        return row
    url = replacement["replacement_source_url"]
    updated = dict(row)
    updated["source_url"] = url
    updated["source_domain"] = replacement["source_domain"]
    updated["source_type"] = replacement["source_type"]
    updated["expected_format"] = replacement["expected_format"]
    updated["source_url_kind"] = _source_url_kind(url)
    updated["rights_review_required"] = replacement["rights_review_required"]
    updated["download_allowed"] = "true"
    updated["blocked_reason"] = ""
    updated["raw_text_committed"] = "false"
    updated["commit_allowed"] = "false"
    updated["training_allowed"] = "false"
    updated["approval_ref"] = APPROVAL_REF
    updated["next_action"] = "download_desktop_only"
    note = f"Agent S1 replacement applied; {replacement.get('replacement_reason', '')}"
    updated["notes"] = (row.get("notes", "") + " " + note).strip()
    return updated


def apply_agent_s1_transcript_replacements(
    *,
    manifest_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    replacements_path: Path = REPLACEMENTS_PATH,
    audit_dir: Path = AUDIT_DIR,
    probe_network: bool = True,
    probe_content: bool = True,
    official_ir_cdn_assessment: bool = True,
) -> dict[str, Any]:
    manifest_rows = read_csv(manifest_path)
    manifest_by_case = {row.get("case_id", ""): row for row in manifest_rows}
    existing_replacements = {row.get("case_id", ""): row for row in read_csv(replacements_path)}
    applied: list[str] = []
    blocked: list[str] = []
    s1_rows: dict[str, dict[str, str]] = {}
    for case_id, spec in S1_REPLACEMENTS.items():
        row = manifest_by_case.get(case_id)
        if not row:
            continue
        url = spec["url"]
        accessible, access_reason = _url_accessible(url) if probe_network else (True, "network_probe_skipped")
        clean = accessible
        blocked_reason = "" if accessible else f"direct_url_not_accessible:{access_reason}"
        content_ok, content_reason, _parser = _content_clean(url, probe_content=probe_content) if accessible else (False, "content_probe_skipped_not_accessible", "")
        clean = clean and content_ok
        if not content_ok:
            blocked_reason = content_reason
        replacement = _replacement_row(
            row,
            url,
            clean=clean,
            blocked_reason=blocked_reason,
            reason=access_reason,
            content_probe=content_reason,
            official_ir_cdn_assessment=official_ir_cdn_assessment,
        )
        s1_rows[case_id] = replacement
        existing_replacements[case_id] = replacement
    final_manifest: list[dict[str, str]] = []
    for row in manifest_rows:
        replacement = s1_rows.get(row.get("case_id", ""))
        updated = _updated_manifest_row(row, replacement) if replacement else row
        if replacement and updated != row:
            applied.append(row.get("case_id", ""))
        if replacement and replacement.get("download_allowed") != "true":
            blocked.append(row.get("case_id", ""))
        final_manifest.append(updated)
    ordered_replacements: list[dict[str, str]] = []
    for row in manifest_rows:
        case_id = row.get("case_id", "")
        if case_id in existing_replacements:
            ordered_replacements.append(existing_replacements[case_id])
    for case_id, row in sorted(existing_replacements.items()):
        if case_id and case_id not in manifest_by_case:
            ordered_replacements.append(row)
    write_csv(replacements_path, ordered_replacements, REPLACEMENT_FIELDS)
    write_csv(audit_dir / "first30_transcript_url_replacements.csv", ordered_replacements, REPLACEMENT_FIELDS)
    write_csv(manifest_path, final_manifest, FIRST30_INGESTION_FIELDS)
    write_csv(audit_dir / "first30_transcript_ingestion_manifest.csv", final_manifest, FIRST30_INGESTION_FIELDS)
    summary = {
        "s1_rows": len(S1_REPLACEMENTS),
        "applied_replacements": len(applied),
        "applied_case_ids": applied,
        "blocked_case_ids": blocked,
        "download_allowed_rows": sum(1 for row in final_manifest if row.get("download_allowed") == "true"),
        "cat_review_required_rows": sum(1 for row in final_manifest if row.get("ticker") == "CAT" and row.get("rights_review_required") == "true"),
        "official_ir_cdn_assessment": official_ir_cdn_assessment,
        "manifest_path": str(manifest_path),
        "replacements_path": str(replacements_path),
        "desktop_audit": str(audit_dir / "first30_transcript_url_replacements.csv"),
    }
    write_report(summary, s1_rows)
    return summary


def write_report(summary: dict[str, Any], rows: dict[str, dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Agent S1 Replacement Application",
        "",
        f"- Agent S1 rows: {summary['s1_rows']}",
        f"- Applied replacements: {summary['applied_replacements']}",
        f"- Download-allowed rows after apply: {summary['download_allowed_rows']}",
        f"- CAT review-required rows in manifest: {summary['cat_review_required_rows']}",
        f"- Official IR CDN assessment policy enabled: {str(summary['official_ir_cdn_assessment']).lower()}",
        "- Commit allowed for raw assets: false",
        "- Training allowed: false",
        "",
        "## S1 Rows",
        "",
    ]
    for case_id in S1_REPLACEMENTS:
        row = rows.get(case_id)
        if not row:
            lines.append(f"- `{case_id}`: not present in manifest")
            continue
        status = "download_allowed" if row.get("download_allowed") == "true" else f"blocked:{row.get('blocked_reason')}"
        lines.append(f"- `{case_id}` `{row.get('ticker')}`: {status}; rights_review_required={row.get('rights_review_required')}; {row.get('replacement_source_url')}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply Agent S1 first30 transcript replacement rows.")
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--replacements", type=Path, default=REPLACEMENTS_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--skip-content-probe", action="store_true")
    parser.add_argument("--disable-official-ir-cdn-assessment", action="store_true")
    args = parser.parse_args(argv)
    summary = apply_agent_s1_transcript_replacements(
        manifest_path=args.manifest,
        replacements_path=args.replacements,
        audit_dir=args.audit_dir,
        probe_network=not args.no_network,
        probe_content=not args.skip_content_probe,
        official_ir_cdn_assessment=not args.disable_official_ir_cdn_assessment,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
