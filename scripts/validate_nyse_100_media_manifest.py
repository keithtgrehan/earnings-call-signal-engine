#!/usr/bin/env python3
"""Validate the NYSE 100 earnings-call media candidate manifest."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_media_manifest.csv"
DEFAULT_SUMMARY = ROOT / "reports" / "nyse_100_media_validation_summary.json"
DEFAULT_STATUS_JSON = ROOT / "reports" / "nyse_100_media_corpus_status.json"
DEFAULT_STATUS_MD = ROOT / "reports" / "nyse_100_media_corpus_status.md"

MANIFEST_FIELDS = [
    "case_id",
    "ticker_symbol",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "calendar_year",
    "earnings_call_date",
    "transcript_source_url",
    "audio_source_url",
    "video_source_url",
    "transcript_availability",
    "audio_availability",
    "video_availability",
    "source_type",
    "rights_status",
    "priority_tier",
    "local_paths_created",
    "notes",
    "source_domain",
    "discovered_timestamp",
    "acquisition_method",
    "provenance_hash",
    "call_folder",
]

AVAILABILITY_VALUES = {"available", "unavailable", "blocked", "paywalled", "unknown"}
SOURCE_TYPE_VALUES = {
    "company_ir",
    "sec_edgar",
    "webcast_provider",
    "earnings_platform",
    "youtube_metadata_only",
    "investor_platform",
    "other",
}
RIGHTS_STATUS_VALUES = {"safe_to_link", "safe_to_download", "metadata_only", "blocked", "unknown"}
PRIORITY_TIERS = {"1", "2", "3", "4"}
RAW_MEDIA_SUFFIXES = {".mp3", ".mp4", ".wav", ".m4a", ".mov", ".aac", ".flac", ".mkv", ".webm", ".vtt", ".srt"}
RAW_TEXT_SUFFIXES = {".txt", ".html", ".htm"}


def parse_date(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return datetime.now(timezone.utc).date()


def cutoff_date(as_of_date: date, years_back: int) -> date:
    try:
        return as_of_date.replace(year=as_of_date.year - years_back)
    except ValueError:
        return as_of_date.replace(month=2, day=28, year=as_of_date.year - years_back)


def read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def bool_value(value: str) -> bool | None:
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def repo_tracked_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    commands = (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    for command in commands:
        try:
            result = subprocess.run(
                command,
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError:
            continue
        if result.returncode != 0:
            continue
        paths.extend(repo_root / line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(set(paths))


def path_is_raw_media(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    suffix = path.suffix.lower()
    if suffix in RAW_MEDIA_SUFFIXES:
        return True
    if suffix in RAW_TEXT_SUFFIXES and ("transcript" in normalized or "/raw/" in normalized):
        return True
    return False


def validate_manifest_rows(
    rows: list[dict[str, str]],
    *,
    years_back: int = 5,
    as_of_date: date | None = None,
    repo_root: Path = ROOT,
    tracked_paths: Iterable[Path] | None = None,
) -> list[str]:
    errors: list[str] = []
    as_of = as_of_date or datetime.now(timezone.utc).date()
    cutoff = cutoff_date(as_of, years_back)
    seen: set[tuple[str, str, str, str]] = set()

    if not rows:
        errors.append("manifest must contain at least one row")

    for index, row in enumerate(rows, start=1):
        for field in MANIFEST_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")

        ticker = str(row.get("ticker_symbol", "")).strip()
        company = str(row.get("company_name", "")).strip()
        fiscal_year = str(row.get("fiscal_year", "")).strip()
        fiscal_quarter = str(row.get("fiscal_quarter", "")).strip()
        call_date_text = str(row.get("earnings_call_date", "")).strip()
        if not ticker:
            errors.append(f"row {index}: ticker_symbol is required")
        if not company:
            errors.append(f"row {index}: company_name is required")
        if not fiscal_year:
            errors.append(f"row {index}: fiscal_year is required")
        if not fiscal_quarter:
            errors.append(f"row {index}: fiscal_quarter is required")
        if not call_date_text:
            errors.append(f"row {index}: earnings_call_date is required")

        if row.get("exchange") != "NYSE":
            errors.append(f"row {index}: exchange must equal NYSE")

        identity = (ticker, fiscal_year, fiscal_quarter, call_date_text)
        if identity in seen:
            errors.append(f"row {index}: duplicate manifest identity {identity}")
        seen.add(identity)

        try:
            call_date = date.fromisoformat(call_date_text)
        except ValueError:
            errors.append(f"row {index}: earnings_call_date must be YYYY-MM-DD")
        else:
            if call_date < cutoff or call_date > as_of:
                errors.append(f"row {index}: earnings_call_date outside the {years_back}-year lookback")

        for media_type in ("transcript", "audio", "video"):
            availability_field = f"{media_type}_availability"
            source_field = f"{media_type}_source_url"
            availability = str(row.get(availability_field, "")).strip()
            if availability not in AVAILABILITY_VALUES:
                errors.append(f"row {index}: invalid {availability_field} {availability!r}")
            if availability == "available" and not str(row.get(source_field, "")).strip():
                errors.append(f"row {index}: {source_field} is required when {availability_field}=available")

        if str(row.get("source_type", "")).strip() not in SOURCE_TYPE_VALUES:
            errors.append(f"row {index}: invalid source_type {row.get('source_type')!r}")
        if str(row.get("rights_status", "")).strip() not in RIGHTS_STATUS_VALUES:
            errors.append(f"row {index}: invalid rights_status {row.get('rights_status')!r}")
        if str(row.get("priority_tier", "")).strip() not in PRIORITY_TIERS:
            errors.append(f"row {index}: invalid priority_tier {row.get('priority_tier')!r}")

        if not str(row.get("source_domain", "")).strip():
            errors.append(f"row {index}: source_domain is required")
        if not str(row.get("discovered_timestamp", "")).strip():
            errors.append(f"row {index}: discovered_timestamp is required")
        if not str(row.get("acquisition_method", "")).strip():
            errors.append(f"row {index}: acquisition_method is required")
        if not str(row.get("provenance_hash", "")).startswith("sha256:"):
            errors.append(f"row {index}: provenance_hash is required and must start with sha256:")

        availability_values = {
            str(row.get("transcript_availability", "")).strip(),
            str(row.get("audio_availability", "")).strip(),
            str(row.get("video_availability", "")).strip(),
        }
        if availability_values & {"blocked", "paywalled"} and not str(row.get("notes", "")).strip():
            errors.append(f"row {index}: blocked or paywalled availability requires notes")

        local_paths_created = bool_value(str(row.get("local_paths_created", "")))
        if local_paths_created is None:
            errors.append(f"row {index}: local_paths_created must be true or false")
        if local_paths_created is True:
            call_folder = Path(str(row.get("call_folder", "")))
            if not call_folder.exists():
                errors.append(f"row {index}: local folder missing: {call_folder}")
            else:
                for child in ("transcript", "audio", "video", "metadata", "provenance"):
                    if not (call_folder / child).is_dir():
                        errors.append(f"row {index}: missing local child folder {child}: {call_folder}")

    paths = list(tracked_paths) if tracked_paths is not None else repo_tracked_paths(repo_root)
    for path in paths:
        if path_is_raw_media(path):
            errors.append(f"repo-tracked raw media path is not allowed: {path}")

    return errors


def build_summary(rows: list[dict[str, str]], errors: list[str]) -> dict[str, object]:
    tier_counts = {tier: 0 for tier in ("1", "2", "3", "4")}
    for row in rows:
        tier = str(row.get("priority_tier", "")).strip()
        if tier in tier_counts:
            tier_counts[tier] += 1
    blocked_or_paywalled = sum(
        1
        for row in rows
        if {row.get("transcript_availability", ""), row.get("audio_availability", ""), row.get("video_availability", "")}
        & {"blocked", "paywalled"}
    )
    return {
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "total_rows": len(rows),
        "tier_counts": tier_counts,
        "rights_status_counts": dict(Counter(row.get("rights_status", "") for row in rows)),
        "blocked_or_paywalled_cases": blocked_or_paywalled,
    }


def git_status_summary(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return "git status unavailable"
    return result.stdout.strip()


def update_status_reports(summary: dict[str, object], *, repo_root: Path) -> None:
    validation_status = "passed" if summary["valid"] else "failed"
    if DEFAULT_STATUS_JSON.exists():
        status_payload = json.loads(DEFAULT_STATUS_JSON.read_text(encoding="utf-8"))
        status_payload["validation_status"] = validation_status
        status_payload["validation_summary"] = summary
        status_payload["git_status_summary"] = git_status_summary(repo_root)
        DEFAULT_STATUS_JSON.write_text(json.dumps(status_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if DEFAULT_STATUS_MD.exists():
        text = DEFAULT_STATUS_MD.read_text(encoding="utf-8")
        text = re.sub(r"^- Validation status: .*$", f"- Validation status: {validation_status}", text, flags=re.MULTILINE)
        DEFAULT_STATUS_MD.write_text(text, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--years-back", type=int, default=5)
    parser.add_argument("--as-of-date")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        rows = read_manifest(args.manifest)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    errors = validate_manifest_rows(
        rows,
        years_back=args.years_back,
        as_of_date=parse_date(args.as_of_date),
        repo_root=args.repo_root,
    )
    summary = build_summary(rows, errors)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_status_reports(summary, repo_root=args.repo_root)
    if errors:
        print(f"NYSE 100 media manifest validation failed with {len(errors)} error(s).", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"NYSE 100 media manifest validation passed: {len(rows)} row(s).")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
