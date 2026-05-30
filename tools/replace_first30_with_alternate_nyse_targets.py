#!/usr/bin/env python3
"""Add clean NYSE alternate transcript-ready cases when original first30 gaps remain."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import (  # noqa: E402
    APPROVAL_REF,
    AUDIT_DIR,
    FIRST30_INGESTION_FIELDS,
    FIRST30_INGESTION_MANIFEST_PATH,
    domain_for_url,
    is_direct_text_url,
    is_official_cdn_domain,
    read_csv,
    write_csv,
)
from tools.resolve_remaining_first30_transcripts import probe_transcript_url  # noqa: E402

OUT_PATH = ROOT / "data" / "acquisition" / "first30_alternate_replacement_candidates.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_alternate_replacement_status.md"

ALTERNATE_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "event_date",
    "source_url",
    "source_domain",
    "source_type",
    "expected_format",
    "download_allowed",
    "blocked_reason",
    "rights_review_required",
    "commit_allowed",
    "training_allowed",
    "raw_text_committed",
    "replacement_for_blocked_case",
    "replacement_reason",
]

ALTERNATES: list[dict[str, str]] = [
    {
        "case_id": "f_2025_q1",
        "ticker": "F",
        "company_name": "Ford Motor Company",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "event_date": "2025-05-05",
        "source_url": "https://s205.q4cdn.com/882619693/files/doc_financials/2025/q1/Ford-Q1-2025-Earnings-Call-Transcript-5-5-25.pdf",
        "replacement_for_blocked_case": "dow_2025_q4",
    },
    {
        "case_id": "f_2025_q2",
        "ticker": "F",
        "company_name": "Ford Motor Company",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q2",
        "event_date": "2025-07-30",
        "source_url": "https://s205.q4cdn.com/882619693/files/doc_financials/2025/q2/Ford-Q2-2025-Earnings-Call-Transcript.pdf",
        "replacement_for_blocked_case": "eqt_2025_q4",
    },
    {
        "case_id": "f_2025_q3",
        "ticker": "F",
        "company_name": "Ford Motor Company",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q3",
        "event_date": "2025-10-23",
        "source_url": "https://s205.q4cdn.com/882619693/files/doc_financials/2025/q3/Ford-Q3-2025-Earnings-Call-Transcript.pdf",
        "replacement_for_blocked_case": "hig_2025_q4",
    },
    {
        "case_id": "lyb_2025_q1",
        "ticker": "LYB",
        "company_name": "LyondellBasell Industries N.V.",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "event_date": "2025-04-25",
        "source_url": "https://s204.q4cdn.com/455115734/files/doc_financials/2025/q1/LYB-1Q25-Earnings-Transcript-1.pdf",
        "replacement_for_blocked_case": "oc_2025_q4",
    },
    {
        "case_id": "lyb_2025_q2",
        "ticker": "LYB",
        "company_name": "LyondellBasell Industries N.V.",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q2",
        "event_date": "2025-08-01",
        "source_url": "https://s204.q4cdn.com/455115734/files/doc_financials/2025/q2/250804-2Q25-Earnings-Transcript.pdf",
        "replacement_for_blocked_case": "omc_2025_q4",
    },
    {
        "case_id": "lyb_2025_q3",
        "ticker": "LYB",
        "company_name": "LyondellBasell Industries N.V.",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q3",
        "event_date": "2025-10-31",
        "source_url": "https://s204.q4cdn.com/455115734/files/doc_financials/2025/q3/251004-3Q25-Earnings-Transcript.pdf",
        "replacement_for_blocked_case": "rf_2025_q4",
    },
    {
        "case_id": "rddt_2025_q1",
        "ticker": "RDDT",
        "company_name": "Reddit Inc.",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "event_date": "2025-05-01",
        "source_url": "https://s203.q4cdn.com/380862485/files/doc_financials/2025/q1/Reddit-Q1-25-Earnings-Call-Transcript.pdf",
        "replacement_for_blocked_case": "uber_2025_q4",
    },
    {
        "case_id": "rddt_2025_q2",
        "ticker": "RDDT",
        "company_name": "Reddit Inc.",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q2",
        "event_date": "2025-07-31",
        "source_url": "https://s203.q4cdn.com/380862485/files/doc_financials/2025/q2/Reddit-Q2-25-Earnings-Call_Transcript.pdf",
        "replacement_for_blocked_case": "vz_2025_q1",
    },
    {
        "case_id": "rddt_2025_q3",
        "ticker": "RDDT",
        "company_name": "Reddit Inc.",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q3",
        "event_date": "2025-10-30",
        "source_url": "https://s203.q4cdn.com/380862485/files/doc_financials/2025/q3/Reddit-Q3-25-Earnings-Call_Transcript.pdf",
        "replacement_for_blocked_case": "vz_2025_q2",
    },
    {
        "case_id": "jpm_2024_q1",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "fiscal_year": "2024",
        "fiscal_quarter": "Q1",
        "event_date": "2024-04-12",
        "source_url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2024/1st-quarter/jpm-1q24-earnings-call-transcript.pdf",
        "replacement_for_blocked_case": "vz_2025_q3",
    },
    {
        "case_id": "jpm_2024_q2",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "fiscal_year": "2024",
        "fiscal_quarter": "Q2",
        "event_date": "2024-07-12",
        "source_url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2024/2nd-quarter/jpm-2q24-earnings-call-transcript-final.pdf",
        "replacement_for_blocked_case": "vz_2025_q4",
    },
    {
        "case_id": "jpm_2024_q3",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "fiscal_year": "2024",
        "fiscal_quarter": "Q3",
        "event_date": "2024-10-11",
        "source_url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2024/3rd-quarter/jpm-3q24-earnings-call-transcript-final.pdf",
        "replacement_for_blocked_case": "vz_2024_q4",
    },
    {
        "case_id": "jpm_2024_q4",
        "ticker": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "fiscal_year": "2024",
        "fiscal_quarter": "Q4",
        "event_date": "2025-01-15",
        "source_url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2024/4th-quarter/4q24-earnings-transcript.pdf",
        "replacement_for_blocked_case": "crm_2025_q4",
    },
]


def _ingestion_row(row: dict[str, str], priority_rank: int, *, download_allowed: bool, blocked_reason: str, reason: str) -> dict[str, str]:
    url = row["source_url"]
    domain = domain_for_url(url)
    rights_review = "true" if is_official_cdn_domain(domain) else "false"
    return {
        "candidate_id": f"alternate_{row['case_id']}",
        "priority_rank": str(priority_rank),
        "case_id": row["case_id"],
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "exchange": "NYSE",
        "fiscal_year": row["fiscal_year"],
        "fiscal_quarter": row["fiscal_quarter"],
        "event_date": row["event_date"],
        "source_url": url,
        "source_domain": domain,
        "source_type": "official_ir_hosted_third_party" if rights_review == "true" else "official_ir",
        "expected_format": Path(urlparse(url).path).suffix.lower().lstrip(".") or "pdf",
        "source_url_kind": "official_ir_cdn_direct" if rights_review == "true" else "official_direct",
        "rights_status": "official_ir_public_linked",
        "approval_required": "true",
        "rights_review_required": rights_review,
        "download_allowed": str(download_allowed).lower(),
        "blocked_reason": "" if download_allowed else blocked_reason,
        "raw_text_committed": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
        "explicit_training_rights_ref": "",
        "license_config_ref": "",
        "control_fixture": "false",
        "qna_expected": "true",
        "source_relation": "transcript_canonical_alternate_replacement",
        "approval_ref": APPROVAL_REF if download_allowed else "",
        "next_action": "download_desktop_only" if download_allowed else "blocked_pending_clean_source",
        "notes": f"Alternate NYSE transcript-ready replacement for {row['replacement_for_blocked_case']}; {reason}",
    }


def _alternate_candidate_row(row: dict[str, str], *, download_allowed: bool, blocked_reason: str, reason: str) -> dict[str, str]:
    url = row["source_url"]
    domain = domain_for_url(url)
    return {
        "candidate_id": f"alternate_{row['case_id']}",
        "case_id": row["case_id"],
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "exchange": "NYSE",
        "fiscal_year": row["fiscal_year"],
        "fiscal_quarter": row["fiscal_quarter"],
        "event_date": row["event_date"],
        "source_url": url,
        "source_domain": domain,
        "source_type": "official_ir_hosted_third_party" if is_official_cdn_domain(domain) else "official_ir",
        "expected_format": Path(urlparse(url).path).suffix.lower().lstrip(".") or "pdf",
        "download_allowed": str(download_allowed).lower(),
        "blocked_reason": "" if download_allowed else blocked_reason,
        "rights_review_required": str(is_official_cdn_domain(domain)).lower(),
        "commit_allowed": "false",
        "training_allowed": "false",
        "raw_text_committed": "false",
        "replacement_for_blocked_case": row["replacement_for_blocked_case"],
        "replacement_reason": reason,
    }


def _next_priority(rows: list[dict[str, str]]) -> int:
    priorities = []
    for row in rows:
        try:
            priorities.append(int(row.get("priority_rank", "0")))
        except ValueError:
            continue
    return (max(priorities) if priorities else 100) + 1


def replace_first30_with_alternate_nyse_targets(
    *,
    manifest_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    out_path: Path = OUT_PATH,
    audit_dir: Path = AUDIT_DIR,
    probe_content: bool = True,
) -> dict[str, Any]:
    manifest_rows = read_csv(manifest_path)
    existing_cases = {row.get("case_id", "") for row in manifest_rows}
    blocked_cases = {
        row.get("case_id", "")
        for row in manifest_rows
        if row.get("control_fixture") != "true" and row.get("download_allowed") != "true"
    }
    priority = _next_priority(manifest_rows)
    candidate_rows: list[dict[str, str]] = []
    new_manifest_rows: list[dict[str, str]] = []
    for alternate in ALTERNATES:
        if alternate["case_id"] in existing_cases:
            continue
        if alternate["replacement_for_blocked_case"] not in blocked_cases:
            continue
        clean, reason, _parser = probe_transcript_url(
            {
                **alternate,
                "exchange": "NYSE",
                "source_type": "official_ir_hosted_third_party" if is_official_cdn_domain(domain_for_url(alternate["source_url"])) else "official_ir",
                "expected_format": "pdf",
                "commit_allowed": "false",
                "training_allowed": "false",
            },
            alternate["source_url"],
            probe_content=probe_content,
        )
        direct = is_direct_text_url(alternate["source_url"], "pdf")
        download_allowed = clean and direct
        blocked_reason = "" if download_allowed else reason or "alternate_not_clean_for_download"
        candidate_rows.append(_alternate_candidate_row(alternate, download_allowed=download_allowed, blocked_reason=blocked_reason, reason=reason))
        if download_allowed:
            new_manifest_rows.append(_ingestion_row(alternate, priority, download_allowed=True, blocked_reason="", reason=reason))
            priority += 1
    final_manifest = manifest_rows + new_manifest_rows
    write_csv(out_path, candidate_rows, ALTERNATE_FIELDS)
    write_csv(audit_dir / "first30_alternate_replacement_candidates.csv", candidate_rows, ALTERNATE_FIELDS)
    write_csv(manifest_path, final_manifest, FIRST30_INGESTION_FIELDS)
    write_csv(audit_dir / "first30_transcript_ingestion_manifest.csv", final_manifest, FIRST30_INGESTION_FIELDS)
    summary = {
        "blocked_cases_before_alternates": len(blocked_cases),
        "alternate_candidates_checked": len(candidate_rows),
        "download_allowed_alternates": sum(1 for row in candidate_rows if row.get("download_allowed") == "true"),
        "alternates_added_to_manifest": len(new_manifest_rows),
        "manifest_rows": len(final_manifest),
        "out_path": str(out_path),
        "desktop_audit": str(audit_dir / "first30_alternate_replacement_candidates.csv"),
    }
    write_report(summary, candidate_rows)
    return summary


def write_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Alternate Replacement Status",
        "",
        f"- Blocked cases before alternates: {summary['blocked_cases_before_alternates']}",
        f"- Alternate candidates checked: {summary['alternate_candidates_checked']}",
        f"- Download-allowed alternates: {summary['download_allowed_alternates']}",
        f"- Alternates added to ingestion manifest: {summary['alternates_added_to_manifest']}",
        "- Exchange: NYSE only",
        "- Past five years only: true",
        "- Raw files downloaded by this script: false",
        "",
        "## Alternates",
        "",
    ]
    if rows:
        for row in rows:
            status = "download_allowed" if row.get("download_allowed") == "true" else f"blocked:{row.get('blocked_reason')}"
            lines.append(f"- `{row['case_id']}` replaces `{row['replacement_for_blocked_case']}`: {status}; {row['source_url']}")
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append clean NYSE alternate transcript-ready cases to the first30 ingestion manifest.")
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    parser.add_argument("--skip-content-probe", action="store_true")
    args = parser.parse_args(argv)
    summary = replace_first30_with_alternate_nyse_targets(
        manifest_path=args.manifest,
        out_path=args.out,
        audit_dir=args.audit_dir,
        probe_content=not args.skip_content_probe,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
