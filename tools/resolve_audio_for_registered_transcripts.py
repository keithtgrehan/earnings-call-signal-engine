#!/usr/bin/env python3
"""Resolve audio coverage status for every registered transcript case."""

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

from tools.first30_transcript_common import AUDIT_DIR, read_csv, write_csv  # noqa: E402
from tools.resolve_first30_audio_candidates import (  # noqa: E402
    AUDIO_FIELDS,
    OUT_PATH,
    is_direct_audio_url,
    resolve_audio_candidates,
)

TRANSCRIPT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
INGESTION_MANIFEST = ROOT / "data" / "acquisition" / "first30_transcript_ingestion_manifest.csv"
AUDIO_REGISTRY = ROOT / "data" / "acquisition" / "audio_registry.csv"
SOURCE_GAP_MANIFEST = ROOT / "data" / "acquisition" / "first30_audio_source_gap_manifest.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_audio_coverage_status.md"


def _gap_rows_by_case(path: Path) -> dict[str, dict[str, str]]:
    return {row.get("case_id", ""): row for row in read_csv(path)}


def _apply_gap_context(rows: list[dict[str, str]], gap_by_case: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    updated: list[dict[str, str]] = []
    for row in rows:
        merged = dict(row)
        gap = gap_by_case.get(row.get("case_id", ""))
        if gap and row.get("already_registered") != "true" and row.get("download_allowed") != "true":
            source_type = gap.get("source_type", "")
            relation = gap.get("source_relation", "")
            if source_type == "webcast_player_only":
                merged["blocked_reason"] = "webcast_player_metadata_only"
                merged["source_relation"] = relation or "webcast_player_metadata_only"
                merged["review_required"] = "true"
                merged["notes"] = "Webcast player exists, but no clean direct MP3/M4A/WAV was exposed; metadata-only."
            elif source_type == "official_ir_direct_audio" and gap.get("source_relation") == "prepared_only":
                merged["source_relation"] = "prepared_audio_support_only"
                merged["review_required"] = "true"
                merged["notes"] = "Prepared audio is support-only and not full-call transcript evidence."
        if merged.get("audio_url") and not is_direct_audio_url(merged.get("audio_url", "")):
            merged["download_allowed"] = "false"
            merged["blocked_reason"] = "not_direct_audio_url"
        updated.append(merged)
    return updated


def resolve_audio_for_registered_transcripts(
    *,
    transcript_registry: Path = TRANSCRIPT_REGISTRY,
    ingestion_manifest: Path = INGESTION_MANIFEST,
    audio_registry: Path = AUDIO_REGISTRY,
    source_gap_manifest: Path = SOURCE_GAP_MANIFEST,
    out_path: Path = OUT_PATH,
    audit_dir: Path = AUDIT_DIR,
) -> dict[str, Any]:
    base_summary = resolve_audio_candidates(
        transcript_registry=transcript_registry,
        ingestion_manifest=ingestion_manifest,
        audio_registry=audio_registry,
        out_path=out_path,
        audit_dir=audit_dir,
    )
    rows = _apply_gap_context(read_csv(out_path), _gap_rows_by_case(source_gap_manifest))
    write_csv(out_path, rows, AUDIO_FIELDS)
    write_csv(audit_dir / "first30_audio_candidates.csv", rows, AUDIO_FIELDS)
    summary = {
        **base_summary,
        "candidate_rows": len(rows),
        "direct_audio_download_allowed": sum(1 for row in rows if row.get("download_allowed") == "true"),
        "already_registered_audio": sum(1 for row in rows if row.get("already_registered") == "true"),
        "webcast_metadata_only": sum(1 for row in rows if row.get("blocked_reason") == "webcast_player_metadata_only"),
        "youtube_blocked": sum(1 for row in rows if "youtube" in row.get("audio_url", "").lower() or "youtu.be" in row.get("audio_url", "").lower()),
        "signed_session_blocked": sum(1 for row in rows if urlparse(row.get("audio_url", "")).query.lower().find("token=") >= 0),
        "out_path": str(out_path),
        "desktop_audit": str(audit_dir / "first30_audio_candidates.csv"),
    }
    write_report(summary, rows)
    return summary


def write_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Audio Coverage Status",
        "",
        f"- Registered transcript cases checked: {summary['candidate_rows']}",
        f"- Already registered audio rows: {summary['already_registered_audio']}",
        f"- New direct audio download-allowed rows: {summary['direct_audio_download_allowed']}",
        f"- Webcast-player metadata-only rows: {summary['webcast_metadata_only']}",
        "- YouTube media downloaded: false",
        "- Signed/session audio URLs downloaded: false",
        "- Cloud ASR used: false",
        "",
        "## Rows",
        "",
    ]
    if rows:
        for row in rows:
            status = "already_registered" if row.get("already_registered") == "true" else ("download_allowed" if row.get("download_allowed") == "true" else row.get("blocked_reason"))
            lines.append(f"- `{row.get('case_id')}` `{row.get('ticker')}`: {status}")
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve audio coverage for every registered transcript case.")
    parser.add_argument("--transcript-registry", type=Path, default=TRANSCRIPT_REGISTRY)
    parser.add_argument("--ingestion-manifest", type=Path, default=INGESTION_MANIFEST)
    parser.add_argument("--audio-registry", type=Path, default=AUDIO_REGISTRY)
    parser.add_argument("--source-gap-manifest", type=Path, default=SOURCE_GAP_MANIFEST)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    args = parser.parse_args(argv)
    summary = resolve_audio_for_registered_transcripts(
        transcript_registry=args.transcript_registry,
        ingestion_manifest=args.ingestion_manifest,
        audio_registry=args.audio_registry,
        source_gap_manifest=args.source_gap_manifest,
        out_path=args.out,
        audit_dir=args.audit_dir,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
