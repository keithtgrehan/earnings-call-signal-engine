#!/usr/bin/env python3
"""Acquire verified non-PDF transcript sources into ignored local manual-source files."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import discover_high_signal_transcript_sources as high_signal_discovery  # noqa: E402
import discover_transcript_sources as tiered_discovery  # noqa: E402
import intake_high_signal_transcripts as intake  # noqa: E402
import prepare_manual_transcript_sources as manual_sources  # noqa: E402

DEFAULT_DISCOVERED_CSV = ROOT / "data" / "corpus" / "discovered_transcript_sources.csv"
DEFAULT_MANUAL_TEMPLATE = ROOT / "data" / "corpus" / "manual_source_template.csv"
DEFAULT_FILE_MANIFEST = ROOT / "data" / "corpus" / "manual_transcript_file_manifest.csv"
DEFAULT_PDF_QUEUE = ROOT / "data" / "corpus" / "pdf_manual_conversion_queue.csv"
DEFAULT_MANUAL_SOURCE_ROOT = ROOT / "data" / "corpus" / "manual_sources"
DEFAULT_REPORT = ROOT / "reports" / "transcript_acquisition_report.md"
DEFAULT_FALLBACK_REPORT = ROOT / "reports" / "manual_transcript_fallback_required.md"

PDF_QUEUE_FIELDS = (
    "case_id",
    "source_url",
    "source_domain",
    "discovered_timestamp",
    "content_type",
    "estimated_pdf",
    "verification_status",
    "verified_allowed",
    "acquisition_quality_band",
    "manual_conversion_status",
    "notes",
)


class AcquisitionError(RuntimeError):
    """Raised for deterministic acquisition errors."""


@dataclass(frozen=True)
class AcquisitionResult:
    row: dict[str, str]
    status: str
    local_file_path: str = ""
    transcript_char_estimate: int = 0
    rejection_reason: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovered-csv", default=str(DEFAULT_DISCOVERED_CSV))
    parser.add_argument("--manual-template", default=str(DEFAULT_MANUAL_TEMPLATE))
    parser.add_argument("--file-manifest", default=str(DEFAULT_FILE_MANIFEST))
    parser.add_argument("--pdf-queue", default=str(DEFAULT_PDF_QUEUE))
    parser.add_argument("--manual-source-root", default=str(DEFAULT_MANUAL_SOURCE_ROOT))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT))
    parser.add_argument("--fallback-report-path", default=str(DEFAULT_FALLBACK_REPORT))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout", type=int, default=45)
    return parser.parse_args(argv)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def is_pdf_row(row: dict[str, str]) -> bool:
    return parse_bool(row.get("estimated_pdf")) or str(row.get("source_type") or "").lower() == "pdf" or str(row.get("verification_status") or "").endswith("_pdf")


def pdf_manual_status(row: dict[str, str]) -> str:
    status = str(row.get("verification_status") or "")
    if status in {"robots_disallowed", "blocked", "blocked_pdf", "paywalled"}:
        return "blocked_pdf"
    if status == "verified_manual_pdf":
        return "verified_manual_pdf"
    return "unsupported_pdf"


def pdf_queue_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "case_id": row.get("case_id", ""),
        "source_url": row.get("source_url", ""),
        "source_domain": row.get("source_domain", ""),
        "discovered_timestamp": row.get("discovered_timestamp", ""),
        "content_type": row.get("content_type", ""),
        "estimated_pdf": "true",
        "verification_status": pdf_manual_status(row),
        "verified_allowed": "false",
        "acquisition_quality_band": row.get("acquisition_quality_band", "medium"),
        "manual_conversion_status": "pending_manual_conversion" if pdf_manual_status(row) == "verified_manual_pdf" else "blocked_or_unsupported",
        "notes": row.get("notes") or row.get("rejection_reason") or "PDF queued for manual review; automatic parsing/OCR is disabled.",
    }


def fetch_text_source(url: str, timeout: int) -> tuple[str, str]:
    content, content_type, status_code = tiered_discovery.fetch_content(url, timeout)
    if status_code >= 400:
        raise AcquisitionError(f"http_error:{status_code}")
    text, source_type = tiered_discovery.normalize_content_to_text(url, content, content_type)
    return text, source_type


def acquire_row(
    row: dict[str, str],
    *,
    manual_source_root: Path,
    timeout: int,
    overwrite: bool,
    robots_checker: Any = high_signal_discovery.robots_allowed,
    text_fetcher: Any = fetch_text_source,
) -> AcquisitionResult:
    if is_pdf_row(row):
        return AcquisitionResult(row=row, status="pdf_manual_conversion_required", rejection_reason="pdf_auto_acquisition_disabled")
    if not parse_bool(row.get("verified_allowed")):
        return AcquisitionResult(row=row, status="fallback_required", rejection_reason=row.get("rejection_reason", "not_verified_allowed"))
    source_url = str(row.get("source_url") or "")
    if not robots_checker(source_url):
        return AcquisitionResult(row=row, status="fallback_required", rejection_reason="robots_txt_disallowed_on_recheck")
    case_id = str(row.get("case_id") or "").strip()
    if not case_id:
        return AcquisitionResult(row=row, status="fallback_required", rejection_reason="missing_case_id")
    raw_path = manual_source_root / case_id / "raw" / "transcript.txt"
    if raw_path.exists() and not overwrite:
        return AcquisitionResult(row=row, status="skipped_existing_raw", local_file_path=str(raw_path), rejection_reason="raw_transcript_exists")
    text, _source_type = text_fetcher(source_url, timeout)
    normalized = intake.clean_text(text)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(normalized, encoding="utf-8")
    return AcquisitionResult(row=row, status="acquired", local_file_path=display_path(raw_path), transcript_char_estimate=len(normalized))


def manual_template_row(result: AcquisitionResult) -> dict[str, Any]:
    row = result.row
    return {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "fiscal_year": row.get("fiscal_year", ""),
        "quarter": row.get("quarter", ""),
        "source_url": row.get("source_url", ""),
        "local_file_path": result.local_file_path,
        "source_type": "txt",
        "source_license_notes": "Automatically acquired from a verified public, robots-allowed HTML/plaintext transcript source.",
        "public_source_confirmed": "true",
        "notes": f"Automated deterministic acquisition; quality={row.get('acquisition_quality_band', '')}; method={row.get('discovery_method', '')}",
    }


def manifest_row(result: AcquisitionResult) -> dict[str, Any]:
    template = manual_template_row(result)
    return {
        **template,
        "source_type": "manual_file",
        "transcript_char_estimate": result.transcript_char_estimate or result.row.get("transcript_char_estimate", ""),
        "matched_markers": result.row.get("matched_markers", ""),
    }


def merge_rows(path: Path, fieldnames: tuple[str, ...], new_rows: list[dict[str, Any]], key_fields: tuple[str, ...] = ("case_id",)) -> None:
    existing = read_csv(path)
    merged: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in existing:
        key = tuple(str(row.get(field) or "") for field in key_fields)
        if any(key):
            merged[key] = row
    for row in new_rows:
        key = tuple(str(row.get(field) or "") for field in key_fields)
        if any(key):
            merged[key] = row
    write_csv(path, fieldnames, list(merged.values()))


def write_reports(report_path: Path, fallback_path: Path, results: list[AcquisitionResult], pdf_rows: list[dict[str, Any]]) -> None:
    acquired = [result for result in results if result.status == "acquired"]
    fallback = [result for result in results if result.status != "acquired"]
    band_counts = Counter(result.row.get("acquisition_quality_band", "unknown") for result in results)
    report_lines = [
        "# Transcript Acquisition Report",
        "",
        f"- generated_at: `{now_iso()}`",
        f"- rows_read: `{len(results)}`",
        f"- acquired: `{len(acquired)}`",
        f"- manual_fallback_required: `{len(fallback)}`",
        f"- pdf_queue_rows: `{len(pdf_rows)}`",
        "",
        "## Quality Bands",
        "",
    ]
    for band in ("high", "medium", "low", "unusable", "unknown"):
        if band_counts.get(band):
            report_lines.append(f"- `{band}`: {band_counts[band]}")
    report_lines.extend(["", "## Acquired Sources", ""])
    if acquired:
        for result in acquired:
            report_lines.append(f"- `{result.row.get('case_id')}` -> `{result.local_file_path}`")
    else:
        report_lines.append("- None.")
    report_lines.extend(["", "No gold labels were created or promoted."])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    fallback_lines = [
        "# Manual Transcript Fallback Required",
        "",
        f"- generated_at: `{now_iso()}`",
        f"- fallback_rows: `{len(fallback)}`",
        f"- pdf_manual_conversion_rows: `{len(pdf_rows)}`",
        "",
        "## PDF Manual Conversion Queue",
        "",
    ]
    if pdf_rows:
        for row in pdf_rows:
            fallback_lines.append(f"- `{row.get('case_id')}` `{row.get('verification_status')}`: {row.get('source_url')}")
    else:
        fallback_lines.append("- None.")
    fallback_lines.extend(["", "## Blocked Or Unusable Candidates", ""])
    blocked = [result for result in fallback if not is_pdf_row(result.row)]
    if blocked:
        for result in blocked:
            fallback_lines.append(f"- `{result.row.get('case_id')}` `{result.status}`: {result.rejection_reason or result.row.get('rejection_reason') or result.row.get('source_url')}")
    else:
        fallback_lines.append("- None.")
    fallback_lines.extend(
        [
            "",
            "## Policy",
            "",
            "- PDFs are metadata-only queue items. No automatic conversion, OCR, parsing, or external AI service is used.",
            "- Blocked, paywalled, robots-disallowed, and unsupported sources are not scraped.",
        ]
    )
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_path.write_text("\n".join(fallback_lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    rows = read_csv(resolve_path(args.discovered_csv))
    results = [
        acquire_row(row, manual_source_root=resolve_path(args.manual_source_root), timeout=args.timeout, overwrite=args.overwrite)
        for row in rows
    ]
    acquired = [result for result in results if result.status == "acquired"]
    pdf_rows = [pdf_queue_row(row) for row in rows if is_pdf_row(row)]
    merge_rows(resolve_path(args.manual_template), manual_sources.MANUAL_SOURCE_FIELDS, [manual_template_row(result) for result in acquired])
    merge_rows(resolve_path(args.file_manifest), manual_sources.MANUAL_FILE_FIELDS, [manifest_row(result) for result in acquired])
    write_csv(resolve_path(args.pdf_queue), PDF_QUEUE_FIELDS, pdf_rows)
    write_reports(resolve_path(args.report_path), resolve_path(args.fallback_report_path), results, pdf_rows)
    return {
        "rows_read": len(rows),
        "acquired": len(acquired),
        "manual_fallback_required": len([result for result in results if result.status != "acquired"]),
        "pdf_queue_rows": len(pdf_rows),
        "report_path": str(resolve_path(args.report_path)),
        "fallback_report_path": str(resolve_path(args.fallback_report_path)),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run(args)
    except AcquisitionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
