#!/usr/bin/env python3
"""Validate rights-gated NYSE 100 local asset acquisition outputs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
DEFAULT_AUDIT = DEFAULT_WORKSPACE / "_audit" / "nyse_earnings_call_audit.csv"
DEFAULT_CHUNK_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
DEFAULT_AUDIO_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_audio_rag_manifest.csv"
REPORT_DIR = ROOT / "reports" / "acquisition"

VALID_AVAILABILITY = {"available", "unavailable", "blocked", "paywalled", "unknown", ""}
VALID_RIGHTS = {
    "safe_to_link",
    "safe_to_download",
    "metadata_only",
    "blocked",
    "unknown",
    "restricted",
    "rights_cleared",
    "manual_local_review_only",
}
VALID_DOWNLOAD_STATUS = {"downloaded", "metadata_only", "blocked", "failed", "not_attempted"}
DOWNLOAD_ALLOWED_RIGHTS = {"safe_to_download", "rights_cleared", "manual_local_review_only"}
CHUNK_ALLOWED_RIGHTS = {"safe_to_download", "rights_cleared", "manual_local_review_only"}
RAW_SUFFIXES = {".txt", ".html", ".htm", ".pdf", ".mp3", ".mp4", ".wav", ".m4a", ".mov", ".aac", ".flac", ".mkv", ".webm"}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def cutoff_date(as_of: date, years_back: int) -> date:
    try:
        return as_of.replace(year=as_of.year - years_back)
    except ValueError:
        return as_of.replace(month=2, day=28, year=as_of.year - years_back)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def is_youtube(value: str) -> bool:
    host = urlparse(value).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def raw_path_looks_restricted(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    suffix = Path(normalized).suffix
    if suffix not in RAW_SUFFIXES:
        return False
    return any(marker in normalized for marker in ("transcript", "/audio/", "/video/", "webcast", "raw/", "vendor", "paywall", "login"))


def staged_paths(repo_root: Path) -> list[str]:
    if not (repo_root / ".git").exists():
        return []
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def validate_audit_rows(
    rows: list[dict[str, str]],
    *,
    workspace: Path,
    repo_root: Path,
    years_back: int,
    target_count: int,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    as_of = datetime.now(UTC).date()
    cutoff = cutoff_date(as_of, years_back)
    cases = {row.get("case_id", "") for row in rows if row.get("case_id")}
    if len(cases) < target_count:
        warnings.append(f"target shortfall: {len(cases)} call(s) present; expected {target_count}")

    for index, row in enumerate(rows, start=1):
        prefix = f"audit row {index}"
        if row.get("exchange") != "NYSE":
            errors.append(f"{prefix}: exchange must equal NYSE")
        call_date = parse_date(row.get("earnings_call_date", ""))
        if call_date is None:
            errors.append(f"{prefix}: earnings_call_date must be YYYY-MM-DD")
        elif call_date < cutoff or call_date > as_of:
            errors.append(f"{prefix}: earnings_call_date outside {years_back}-year lookback")
        if row.get("availability", "") not in VALID_AVAILABILITY:
            errors.append(f"{prefix}: invalid availability {row.get('availability')!r}")
        if row.get("rights_status", "") not in VALID_RIGHTS:
            errors.append(f"{prefix}: invalid rights_status {row.get('rights_status')!r}")
        download_status = row.get("download_status") or ("metadata_only" if row.get("rights_status") == "metadata_only" else "")
        if download_status not in VALID_DOWNLOAD_STATUS:
            errors.append(f"{prefix}: invalid download_status {row.get('download_status')!r}")
        if download_status == "blocked" and not row.get("blocked_reason"):
            errors.append(f"{prefix}: blocked sources require blocked_reason")
        if not str(row.get("provenance_hash", "")).startswith("sha256:"):
            errors.append(f"{prefix}: provenance_hash is required")
        asset_type = row.get("asset_type", "")
        if asset_type == "transcript" and download_status == "downloaded" and row.get("rights_status") not in DOWNLOAD_ALLOWED_RIGHTS:
            errors.append(f"{prefix}: downloaded transcript has disallowed rights_status")
        if asset_type == "audio" and download_status == "downloaded" and row.get("rights_status") not in DOWNLOAD_ALLOWED_RIGHTS:
            errors.append(f"{prefix}: downloaded audio has disallowed rights_status")
        if download_status == "downloaded" and (is_youtube(row.get("source_url", "")) or row.get("source_type") == "youtube_metadata_only"):
            errors.append(f"{prefix}: YouTube media was downloaded")
        if (
            download_status == "downloaded"
            and row.get("source_type") in {"licensed_vendor", "licensed_vendor_blocked", "transcript_vendor"}
            and not row.get("license_config_ref")
        ):
            errors.append(f"{prefix}: vendor raw ingest requires license_config_ref")
        local_path = str(row.get("local_path", "")).strip()
        if local_path and asset_type in {"transcript", "audio", "video"} and is_relative_to(Path(local_path), repo_root):
            errors.append(f"{prefix}: raw asset local_path is inside repo: {local_path}")
        if local_path and download_status == "downloaded" and not Path(local_path).exists():
            errors.append(f"{prefix}: downloaded local_path missing: {local_path}")

    staged = staged_paths(repo_root)
    restricted_staged = [path for path in staged if raw_path_looks_restricted(path)]
    for path in restricted_staged:
        errors.append(f"staged raw transcript/audio/video artifact is not allowed: {path}")

    summary = {
        "audit_rows": len(rows),
        "unique_calls": len(cases),
        "transcripts_downloaded": sum(1 for row in rows if row.get("asset_type") == "transcript" and (row.get("download_status") or "") == "downloaded"),
        "audio_downloaded": sum(1 for row in rows if row.get("asset_type") == "audio" and (row.get("download_status") or "") == "downloaded"),
        "metadata_only_count": sum(
            1 for row in rows if (row.get("download_status") or ("metadata_only" if row.get("rights_status") == "metadata_only" else "")) == "metadata_only"
        ),
        "blocked_count": sum(1 for row in rows if (row.get("download_status") or "") == "blocked"),
        "workspace": str(workspace),
    }
    return errors, warnings, summary


def validate_chunk_manifest(path: Path, repo_root: Path) -> list[str]:
    if not path.exists():
        return []
    errors: list[str] = []
    for index, row in enumerate(read_csv(path), start=1):
        prefix = f"chunk row {index}"
        if row.get("rights_status") not in CHUNK_ALLOWED_RIGHTS:
            errors.append(f"{prefix}: disallowed rights_status {row.get('rights_status')!r}")
        if parse_bool(row.get("raw_text_committed")):
            errors.append(f"{prefix}: raw_text_committed must be false")
        chunk_path = row.get("local_chunk_path", "")
        if chunk_path and is_relative_to(Path(chunk_path), repo_root):
            errors.append(f"{prefix}: local_chunk_path points inside repo")
        for field_name in ("source_sha256", "text_sha256"):
            if not str(row.get(field_name, "")).startswith("sha256:"):
                errors.append(f"{prefix}: {field_name} must start with sha256:")
    return errors


def validate_audio_manifest(path: Path) -> list[str]:
    if not path.exists():
        return []
    errors: list[str] = []
    for index, row in enumerate(read_csv(path), start=1):
        if parse_bool(row.get("raw_text_committed")):
            errors.append(f"audio RAG row {index}: raw_text_committed must be false")
        if is_youtube(row.get("audio_local_path", "")):
            errors.append(f"audio RAG row {index}: YouTube audio path is not allowed")
    return errors


def validate_acquisition(
    *,
    workspace: Path = DEFAULT_WORKSPACE,
    audit_path: Path = DEFAULT_AUDIT,
    repo_root: Path = ROOT,
    target_count: int = 100,
    years_back: int = 5,
    chunk_manifest: Path = DEFAULT_CHUNK_MANIFEST,
    audio_manifest: Path = DEFAULT_AUDIO_MANIFEST,
) -> ValidationResult:
    result = ValidationResult()
    if not workspace.exists():
        result.errors.append(f"workspace missing: {workspace}")
    if not audit_path.exists():
        result.errors.append(f"audit CSV missing: {audit_path}")
        return result
    rows = read_csv(audit_path)
    errors, warnings, summary = validate_audit_rows(rows, workspace=workspace, repo_root=repo_root, years_back=years_back, target_count=target_count)
    result.errors.extend(errors)
    result.warnings.extend(warnings)
    result.summary.update(summary)
    result.errors.extend(validate_chunk_manifest(chunk_manifest, repo_root))
    result.errors.extend(validate_audio_manifest(audio_manifest))
    return result


def write_validation_report(result: ValidationResult) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "valid": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "summary": result.summary,
    }
    (REPORT_DIR / "nyse_100_asset_acquisition_validation.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# NYSE 100 Asset Acquisition Validation", "", f"- Valid: {str(result.ok).lower()}"]
    lines.extend(f"- {key}: {value}" for key, value in result.summary.items())
    if result.errors:
        lines.extend(["", "## Errors", *[f"- {error}" for error in result.errors]])
    if result.warnings:
        lines.extend(["", "## Warnings", *[f"- {warning}" for warning in result.warnings]])
    (REPORT_DIR / "nyse_100_asset_acquisition_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate NYSE 100 rights-gated asset acquisition outputs.")
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--audit", default=str(DEFAULT_AUDIT))
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--target-count", type=int, default=100)
    parser.add_argument("--years-back", type=int, default=5)
    parser.add_argument("--chunk-manifest", default=str(DEFAULT_CHUNK_MANIFEST))
    parser.add_argument("--audio-manifest", default=str(DEFAULT_AUDIO_MANIFEST))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_acquisition(
        workspace=Path(args.workspace),
        audit_path=Path(args.audit),
        repo_root=Path(args.repo_root),
        target_count=args.target_count,
        years_back=args.years_back,
        chunk_manifest=Path(args.chunk_manifest),
        audio_manifest=Path(args.audio_manifest),
    )
    write_validation_report(result)
    print(json.dumps({"valid": result.ok, "errors": result.errors, "warnings": result.warnings, "summary": result.summary}, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
