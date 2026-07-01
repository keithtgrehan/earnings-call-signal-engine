#!/usr/bin/env python3
"""Write an operational baseline for the Desktop-backed NYSE 100 ingest workspace."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE, read_csv, write_json

REPORT_PATH = ROOT / "reports" / "acquisition" / "operational_ingest_baseline.md"
SUMMARY_PATH = ROOT / "reports" / "acquisition" / "operational_ingest_baseline.json"


def _row_count(path: Path) -> int:
    return len(read_csv(path))


def _count_files(root: Path, suffixes: set[str]) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes)


def _csv_count_if(path: Path, field: str, value: str) -> int:
    return sum(1 for row in read_csv(path) if row.get(field) == value)


def build_baseline(*, workspace: Path = DEFAULT_WORKSPACE) -> dict[str, Any]:
    audit_dir = workspace / "_audit"
    permitted = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_permitted_downloads.csv"
    download_log = audit_dir / "user_authorized_download_log.csv"
    transcript_registry = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
    audio_registry = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"
    chunk_manifest = ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv"
    retrieval_manifest = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
    audio_rag_manifest = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_audio_rag_manifest.csv"
    normalized_manifest = ROOT / "data" / "corpus" / "normalized_transcript_manifest.csv"

    summary = {
        "workspace": str(workspace),
        "desktop_workspace_exists": workspace.exists(),
        "desktop_audit_exists": audit_dir.exists(),
        "available_manifests": {
            "source_rights_queue": _row_count(ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"),
            "user_authorized_permitted_downloads": _row_count(permitted),
            "download_log": _row_count(download_log),
            "manual_local_transcript_registry": _row_count(transcript_registry),
            "manual_local_audio_registry": _row_count(audio_registry),
            "normalized_transcript_manifest": _row_count(normalized_manifest),
            "chunk_manifest": _row_count(chunk_manifest),
            "retrieval_objects_manifest": _row_count(retrieval_manifest),
            "audio_rag_manifest": _row_count(audio_rag_manifest),
        },
        "desktop_file_counts": {
            "transcript_like_files": _count_files(workspace, {".txt", ".html", ".htm", ".pdf"}),
            "audio_files": _count_files(workspace, {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}),
            "video_files": _count_files(workspace, {".mp4", ".mov", ".mkv", ".webm", ".avi"}),
        },
        "operational_counts": {
            "approved_download_rows": _row_count(permitted),
            "transcript_downloads_succeeded": _csv_count_if(download_log, "download_status", "downloaded"),
            "registered_transcripts": _row_count(transcript_registry),
            "registered_audio": _row_count(audio_registry),
            "normalized_transcripts": _row_count(normalized_manifest),
            "transcript_chunks": _row_count(chunk_manifest),
            "retrieval_objects": _row_count(retrieval_manifest),
            "audio_rag_records": _row_count(audio_rag_manifest),
        },
    }
    blockers: list[str] = []
    if not workspace.exists():
        blockers.append("Desktop workspace does not exist.")
    if summary["operational_counts"]["approved_download_rows"] == 0:
        blockers.append("No user-authorized permitted-download rows exist.")
    if summary["operational_counts"]["registered_transcripts"] == 0:
        blockers.append("No registered transcript files are available for normalization/chunking.")
    if summary["operational_counts"]["registered_audio"] == 0:
        blockers.append("No registered audio files are available for audio readiness.")
    summary["remaining_blockers"] = blockers
    write_report(summary)
    write_json(SUMMARY_PATH, summary)
    return summary


def write_report(summary: dict[str, Any], path: Path = REPORT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Operational Ingest Baseline",
        "",
        f"- Desktop workspace: `{summary['workspace']}`",
        f"- Desktop workspace exists: {str(summary['desktop_workspace_exists']).lower()}",
        f"- Desktop audit folder exists: {str(summary['desktop_audit_exists']).lower()}",
        "",
        "## Available Manifests",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in summary["available_manifests"].items())
    lines.extend(["", "## Desktop Workspace Status", ""])
    lines.extend(f"- {key}: {value}" for key, value in summary["desktop_file_counts"].items())
    lines.extend(["", "## Operational Counts", ""])
    lines.extend(f"- {key}: {value}" for key, value in summary["operational_counts"].items())
    lines.extend(["", "## Remaining Blockers", ""])
    blockers = summary.get("remaining_blockers") or []
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    lines.extend(["", "Raw files committed: false"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the operational ingest baseline report.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args(argv)
    print(json.dumps(build_baseline(workspace=args.workspace), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
