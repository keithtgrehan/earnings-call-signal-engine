#!/usr/bin/env python3
"""Discover lawfully provided Desktop transcript/audio files without copying raw assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import (  # noqa: E402
    DEFAULT_WORKSPACE,
    DOWNLOAD_LOG_FIELDS,
    file_sha256,
    is_relative_to,
    read_csv,
    write_csv,
)

REPORT_PATH = ROOT / "reports" / "acquisition" / "manual_local_desktop_asset_discovery.md"
TRANSCRIPT_SUFFIXES = {".txt", ".html", ".htm", ".pdf"}
AUDIO_SUFFIXES = {".mp3", ".m4a", ".wav"}


def _audit_rows(workspace: Path) -> list[dict[str, str]]:
    return read_csv(workspace / "_audit" / "nyse_earnings_call_audit.csv")


def _asset_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TRANSCRIPT_SUFFIXES:
        return "transcript"
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    return ""


def _matching_audit_row(path: Path, rows: list[dict[str, str]], asset_type: str) -> dict[str, str]:
    path_resolved = path.resolve()
    for row in rows:
        local_field = "transcript_local_path" if asset_type == "transcript" else "audio_local_path"
        local_root = Path(row.get(local_field, ""))
        if local_root and local_root.exists() and is_relative_to(path_resolved, local_root):
            return row
    lower_parts = " ".join(part.lower() for part in path.parts)
    for row in rows:
        case_id = row.get("case_id", "").lower()
        ticker = (row.get("ticker") or row.get("ticker_symbol") or "").lower()
        fiscal_year = row.get("fiscal_year", "")
        fiscal_quarter = row.get("fiscal_quarter", "").lower()
        if case_id and case_id in lower_parts:
            return row
        if ticker and ticker in lower_parts and fiscal_year and fiscal_year in lower_parts and fiscal_quarter and fiscal_quarter in lower_parts:
            return row
    return {}


def _row_for_path(path: Path, audit_row: dict[str, str], asset_type: str) -> dict[str, str]:
    source_url = audit_row.get("transcript_source_url" if asset_type == "transcript" else "audio_source_url", "")
    sha256 = file_sha256(path)
    return {
        "source_id": f"manual_local:{sha256[7:23]}",
        "case_id": audit_row.get("case_id", path.parent.parent.name if path.parent.name in {"transcript", "audio"} else path.stem),
        "ticker": audit_row.get("ticker") or audit_row.get("ticker_symbol", ""),
        "company_name": audit_row.get("company_name", ""),
        "asset_type": asset_type,
        "source_type": "manual_local",
        "source_url": source_url or str(path),
        "download_status": "downloaded",
        "blocked_reason": "",
        "local_path": str(path),
        "sha256": sha256,
        "bytes": str(path.stat().st_size),
        "content_type": "manual-local",
        "commit_allowed": "false",
        "training_allowed": "false",
        "eval_allowed": "true",
        "approval_ref": "user_authorized_manual_local_desktop_workspace",
        "provenance_path": str(Path(audit_row.get("provenance_path", ""))) if audit_row.get("provenance_path") else str(path),
    }


def _candidate_paths(workspace: Path) -> list[Path]:
    paths: list[Path] = []
    for suffix in sorted(TRANSCRIPT_SUFFIXES | AUDIO_SUFFIXES):
        paths.extend(workspace.rglob(f"*{suffix}"))
    generated_dirs = {"_audit", "chunks", "metadata"}
    return sorted(
        path
        for path in paths
        if path.is_file()
        and not generated_dirs.intersection(path.parts)
        and not (path.parent / "provenance.json").exists()
    )


def discover_desktop_assets(*, workspace: Path = DEFAULT_WORKSPACE, out_path: Path | None = None) -> dict[str, Any]:
    out_path = out_path or workspace / "_audit" / "manual_local_desktop_asset_discovery.csv"
    audit_rows = _audit_rows(workspace)
    log_rows: list[dict[str, str]] = []
    unmatched = 0
    for path in _candidate_paths(workspace):
        if not is_relative_to(path, workspace) or is_relative_to(path, ROOT):
            continue
        asset_type = _asset_kind(path)
        if not asset_type:
            continue
        audit_row = _matching_audit_row(path, audit_rows, asset_type)
        if not audit_row:
            unmatched += 1
        log_rows.append(_row_for_path(path, audit_row, asset_type))
    write_csv(out_path, log_rows, DOWNLOAD_LOG_FIELDS)
    summary = {
        "workspace": str(workspace),
        "files_found": len(log_rows),
        "transcript_files": sum(1 for row in log_rows if row["asset_type"] == "transcript"),
        "audio_files": sum(1 for row in log_rows if row["asset_type"] == "audio"),
        "unmatched_files": unmatched,
        "out_path": str(out_path),
        "raw_files_copied": False,
        "raw_files_committed": False,
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Manual-Local Desktop Asset Discovery\n\n"
        f"- Workspace: `{summary['workspace']}`\n"
        f"- Files found: {summary['files_found']}\n"
        f"- Transcript files: {summary['transcript_files']}\n"
        f"- Audio files: {summary['audio_files']}\n"
        f"- Unmatched files: {summary['unmatched_files']}\n"
        f"- Audit log: `{summary['out_path']}`\n"
        "- Raw files copied: false\n"
        "- Raw files committed: false\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover Desktop transcript/audio files and write path/hash audit rows.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(discover_desktop_assets(workspace=args.workspace, out_path=args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
