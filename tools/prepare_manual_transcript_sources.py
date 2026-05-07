#!/usr/bin/env python3
"""Validate manual public transcript sources for high-signal intake."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import discover_high_signal_transcript_sources as discovery  # noqa: E402
import intake_high_signal_transcripts as intake  # noqa: E402

DEFAULT_TEMPLATE = ROOT / "data" / "corpus" / "manual_source_template.csv"
DEFAULT_URL_OUTPUT = ROOT / "data" / "corpus" / "high_signal_source_urls.csv"
DEFAULT_FILE_MANIFEST = ROOT / "data" / "corpus" / "manual_transcript_file_manifest.csv"
DEFAULT_REPORT = ROOT / "reports" / "manual_source_validation.md"

MANUAL_SOURCE_FIELDS = (
    "case_id",
    "ticker",
    "company_name",
    "fiscal_year",
    "quarter",
    "source_url",
    "local_file_path",
    "source_type",
    "source_license_notes",
    "public_source_confirmed",
    "notes",
)
MANUAL_FILE_FIELDS = (
    "case_id",
    "ticker",
    "company_name",
    "fiscal_year",
    "quarter",
    "source_url",
    "local_file_path",
    "source_type",
    "source_license_notes",
    "public_source_confirmed",
    "transcript_char_estimate",
    "matched_markers",
    "notes",
)


class ManualSourceError(RuntimeError):
    """Raised for malformed manual source input."""


@dataclass(frozen=True)
class ManualSourceRow:
    case_id: str
    ticker: str
    company_name: str
    fiscal_year: str
    quarter: str
    source_url: str
    local_file_path: str
    source_type: str
    source_license_notes: str
    public_source_confirmed: bool
    notes: str


@dataclass
class ManualValidationResult:
    row: ManualSourceRow
    status: str
    rejection_reason: str = ""
    transcript_char_estimate: int = 0
    matched_markers: list[str] = field(default_factory=list)
    verified_candidate: discovery.CandidateSource | None = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def parse_bool(value: Any) -> bool:
    lowered = str(value or "").strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off", ""}:
        return False
    raise ManualSourceError(f"public_source_confirmed must be true or false, got {value!r}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--output-csv", default=str(DEFAULT_URL_OUTPUT))
    parser.add_argument("--file-manifest", default=str(DEFAULT_FILE_MANIFEST))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT))
    parser.add_argument("--min-transcript-chars", type=int, default=5000)
    parser.add_argument("--require-markers", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=45)
    return parser.parse_args(argv)


def read_manual_rows(path: Path) -> list[ManualSourceRow]:
    if not path.exists():
        raise ManualSourceError(f"manual source CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in MANUAL_SOURCE_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ManualSourceError(f"manual source CSV missing columns: {', '.join(missing)}")
        rows: list[ManualSourceRow] = []
        for raw in reader:
            if not any(str(value or "").strip() for value in raw.values()):
                continue
            ticker = str(raw.get("ticker") or "").strip().upper()
            fiscal_year = str(raw.get("fiscal_year") or "").strip()
            quarter = str(raw.get("quarter") or "").strip().upper()
            case_id = str(raw.get("case_id") or f"{ticker}_{fiscal_year}_{quarter}").strip()
            rows.append(
                ManualSourceRow(
                    case_id=case_id,
                    ticker=ticker,
                    company_name=str(raw.get("company_name") or intake.COMPANY_NAMES.get(ticker, "")).strip(),
                    fiscal_year=fiscal_year,
                    quarter=quarter,
                    source_url=str(raw.get("source_url") or "").strip(),
                    local_file_path=str(raw.get("local_file_path") or "").strip(),
                    source_type=str(raw.get("source_type") or "").strip().lower(),
                    source_license_notes=str(raw.get("source_license_notes") or "").strip(),
                    public_source_confirmed=parse_bool(raw.get("public_source_confirmed")),
                    notes=str(raw.get("notes") or "").strip(),
                )
            )
    return rows


def target_case_from_manual(row: ManualSourceRow) -> discovery.TargetCase:
    metadata = discovery.COMPANY_METADATA.get(row.ticker, {})
    return discovery.TargetCase(
        case_id=row.case_id,
        ticker=row.ticker,
        company_name=row.company_name or metadata.get("company_name", row.ticker),
        fiscal_year=row.fiscal_year,
        quarter=row.quarter,
        company_domain=metadata.get("company_domain", ""),
    )


def basic_rejection(row: ManualSourceRow) -> str:
    if not row.case_id or not row.ticker or not row.fiscal_year or not row.quarter:
        return "missing_case_metadata"
    if not row.public_source_confirmed:
        return "public_source_not_confirmed"
    if not row.source_license_notes:
        return "missing_source_license_notes"
    if not (row.source_url or row.local_file_path):
        return "missing_source_url_or_local_file_path"
    return ""


def markers_in_text(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in intake.MARKERS if marker in lowered]


def validate_local_file(row: ManualSourceRow, *, min_chars: int, require_markers: bool) -> ManualValidationResult:
    rejection = basic_rejection(row)
    if rejection:
        return ManualValidationResult(row=row, status="rejected", rejection_reason=rejection)
    path = resolve_path(row.local_file_path)
    if path.suffix.lower() not in {".txt", ".md"}:
        return ManualValidationResult(row=row, status="rejected", rejection_reason="local_file_must_be_plaintext_txt_or_md")
    if not path.exists():
        return ManualValidationResult(row=row, status="rejected", rejection_reason="local_file_not_found")
    text = intake.clean_text(path.read_text(encoding="utf-8", errors="replace"))
    validation_status, flags = intake.validate_transcript(text, min_chars=min_chars, require_markers=require_markers)
    if validation_status == "failed":
        return ManualValidationResult(
            row=row,
            status="rejected",
            rejection_reason=";".join(flags) or "transcript_validation_failed",
            transcript_char_estimate=len(text),
            matched_markers=markers_in_text(text),
        )
    return ManualValidationResult(
        row=row,
        status="verified",
        transcript_char_estimate=len(text),
        matched_markers=markers_in_text(text),
    )


def validate_url(row: ManualSourceRow, *, min_chars: int, timeout: int) -> ManualValidationResult:
    rejection = basic_rejection(row)
    if rejection:
        return ManualValidationResult(row=row, status="rejected", rejection_reason=rejection)
    case = target_case_from_manual(row)
    candidate = discovery.CandidateSource(
        source_url=row.source_url,
        source_type=discovery.guess_source_type(row.source_url),
        source_domain=urlparse(row.source_url).netloc.lower().removeprefix("www."),
        notes=f"{row.notes} License/provenance: {row.source_license_notes}".strip(),
    )
    verified = discovery.verify_candidate(case, candidate, min_chars=min_chars, timeout=timeout)
    status = "verified" if discovery.selectable(verified) else verified.verification_status
    return ManualValidationResult(
        row=row,
        status=status,
        rejection_reason=verified.rejection_reason,
        transcript_char_estimate=verified.transcript_char_estimate,
        matched_markers=verified.matched_markers,
        verified_candidate=verified,
    )


def validate_rows(rows: list[ManualSourceRow], args: argparse.Namespace) -> list[ManualValidationResult]:
    results: list[ManualValidationResult] = []
    for index, row in enumerate(rows):
        if index and args.sleep_seconds > 0 and row.source_url and not row.local_file_path:
            time.sleep(args.sleep_seconds)
        if row.local_file_path:
            results.append(validate_local_file(row, min_chars=args.min_transcript_chars, require_markers=args.require_markers))
        else:
            results.append(validate_url(row, min_chars=args.min_transcript_chars, timeout=args.timeout))
    return results


def write_url_sources(path: Path, results: list[ManualValidationResult]) -> None:
    discoveries: list[discovery.CaseDiscovery] = []
    for result in results:
        if not result.verified_candidate or result.status != "verified":
            continue
        case = target_case_from_manual(result.row)
        discoveries.append(
            discovery.CaseDiscovery(
                case=case,
                candidates=[result.verified_candidate],
                selected_source_url=result.verified_candidate.source_url,
                selected_reason=f"manual verified confidence {result.verified_candidate.confidence:.2f}",
            )
        )
    discovery.write_source_csv(path, discoveries)


def manual_file_row(result: ManualValidationResult) -> dict[str, Any]:
    row = result.row
    return {
        "case_id": row.case_id,
        "ticker": row.ticker,
        "company_name": row.company_name,
        "fiscal_year": row.fiscal_year,
        "quarter": row.quarter,
        "source_url": row.source_url,
        "local_file_path": row.local_file_path,
        "source_type": "manual_file",
        "source_license_notes": row.source_license_notes,
        "public_source_confirmed": "true",
        "transcript_char_estimate": result.transcript_char_estimate,
        "matched_markers": ";".join(result.matched_markers),
        "notes": row.notes,
    }


def write_file_manifest(path: Path, results: list[ManualValidationResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MANUAL_FILE_FIELDS))
        writer.writeheader()
        for result in results:
            if result.row.local_file_path and result.status == "verified":
                writer.writerow(manual_file_row(result))


def write_report(path: Path, results: list[ManualValidationResult]) -> None:
    accepted_urls = [result for result in results if result.status == "verified" and result.verified_candidate]
    accepted_files = [result for result in results if result.status == "verified" and result.row.local_file_path]
    rejected = [result for result in results if result.status != "verified"]
    lines = [
        "# Manual Source Validation",
        "",
        f"- generated_at: `{now_iso()}`",
        f"- rows_read: `{len(results)}`",
        f"- url_sources_verified: `{len(accepted_urls)}`",
        f"- local_files_verified: `{len(accepted_files)}`",
        f"- rejected_rows: `{len(rejected)}`",
        "",
        "## Rejected Rows",
        "",
    ]
    if rejected:
        for result in rejected:
            lines.append(f"- `{result.row.case_id or 'unknown'}`: {result.status} ({result.rejection_reason or 'no reason recorded'})")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Guarantees",
            "",
            "- URL rows are verified through the public-source verifier and robots checks.",
            "- Local files must be manually saved plaintext transcripts from public/legal sources.",
            "- No transcript or gold label is auto-promoted by this preparation step.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        rows = read_manual_rows(resolve_path(args.input_csv))
        results = validate_rows(rows, args)
        write_url_sources(resolve_path(args.output_csv), results)
        write_file_manifest(resolve_path(args.file_manifest), results)
        write_report(resolve_path(args.report_path), results)
    except ManualSourceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    summary = {
        "rows_read": len(results),
        "url_sources_verified": sum(1 for result in results if result.status == "verified" and result.verified_candidate),
        "local_files_verified": sum(1 for result in results if result.status == "verified" and result.row.local_file_path),
        "rejected_rows": sum(1 for result in results if result.status != "verified"),
        "source_url_file": str(resolve_path(args.output_csv)),
        "file_manifest": str(resolve_path(args.file_manifest)),
        "report_path": str(resolve_path(args.report_path)),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
