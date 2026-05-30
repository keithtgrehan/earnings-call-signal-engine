#!/usr/bin/env python3
"""Normalize registered Desktop transcripts into repo-safe manifests."""

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
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.transcripts import NORMALIZER_VERSION, normalize_transcript_text
from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE, is_relative_to, read_csv, write_csv

DEFAULT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
DEFAULT_OUT = ROOT / "data" / "corpus" / "normalized_transcript_manifest.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "normalization_quality_report.md"
FIRST30_REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_normalization_status.md"

NORMALIZED_MANIFEST_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "call_date",
    "source_url",
    "raw_sha256",
    "normalized_sha256",
    "normalizer_version",
    "section_count",
    "speaker_turn_count",
    "qa_pair_count",
    "quality_flags",
    "normalized_local_path",
    "raw_text_committed",
]


def _metadata_dir_for_raw(path: Path) -> Path:
    if path.parent.name == "transcript":
        return path.parent.parent / "metadata"
    return path.parent / "metadata"


def _display_path(path: str) -> str:
    value = Path(path)
    try:
        return str(value.resolve().relative_to(ROOT.resolve()))
    except (OSError, ValueError):
        return path


def _manifest_row(normalized: dict[str, Any], normalized_path: Path) -> dict[str, str]:
    return {
        "case_id": normalized["case_id"],
        "ticker": normalized.get("ticker", ""),
        "company_name": normalized.get("company_name", ""),
        "exchange": normalized.get("exchange", ""),
        "fiscal_year": normalized.get("fiscal_year", ""),
        "fiscal_quarter": normalized.get("fiscal_quarter", ""),
        "call_date": normalized.get("call_date", ""),
        "source_url": normalized.get("source_url", ""),
        "raw_sha256": normalized.get("raw_sha256", ""),
        "normalized_sha256": normalized.get("normalized_sha256", ""),
        "normalizer_version": normalized.get("normalizer_version", NORMALIZER_VERSION),
        "section_count": str(len(normalized.get("sections", []))),
        "speaker_turn_count": str(len(normalized.get("speaker_turns", []))),
        "qa_pair_count": str(len(normalized.get("qa_pairs", []))),
        "quality_flags": ";".join(normalized.get("quality_flags", [])),
        "normalized_local_path": str(normalized_path),
        "raw_text_committed": "false",
    }


def normalize_registered_transcripts(*, registry_path: Path, workspace: Path, out_path: Path = DEFAULT_OUT) -> dict[str, Any]:
    registry_rows = read_csv(registry_path)
    manifest_rows: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for row in registry_rows:
        if row.get("asset_type") != "transcript" or row.get("eval_allowed") != "true" or row.get("commit_allowed") != "false":
            skipped.append({"case_id": row.get("case_id", ""), "reason": "not_eval_allowed_or_not_transcript"})
            continue
        raw_path = Path(row.get("local_path", ""))
        if not raw_path.exists() or not is_relative_to(raw_path, workspace) or is_relative_to(raw_path, ROOT):
            skipped.append({"case_id": row.get("case_id", ""), "reason": "raw_path_missing_or_not_desktop_only"})
            continue
        text = raw_path.read_text(encoding="utf-8", errors="replace")
        normalized = normalize_transcript_text(
            text,
            case_id=row.get("case_id", ""),
            ticker=row.get("ticker", ""),
            company_name=row.get("company_name", ""),
            exchange="NYSE",
            source_url=row.get("source_url", ""),
            source_asset_id=f"{row.get('case_id', 'unknown')}_transcript",
            rights_status=row.get("rights_status", "safe_to_download"),
            provenance={
                "raw_local_path": str(raw_path),
                "approval_ref": row.get("approval_ref", ""),
                "provenance_path": row.get("provenance_path", ""),
                "commit_allowed": False,
                "training_allowed": False,
            },
        )
        metadata_dir = _metadata_dir_for_raw(raw_path)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        normalized_path = metadata_dir / "normalized_transcript.json"
        normalized_path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest_rows.append(_manifest_row(normalized, normalized_path))
    write_csv(out_path, manifest_rows, NORMALIZED_MANIFEST_FIELDS)
    desktop_index = workspace / "_audit" / "normalized_transcript_manifest.csv"
    write_csv(desktop_index, manifest_rows, NORMALIZED_MANIFEST_FIELDS)
    summary = {
        "registry_rows": len(registry_rows),
        "normalized_transcripts": len(manifest_rows),
        "skipped": len(skipped),
        "out_manifest": str(out_path),
        "desktop_index": str(desktop_index),
        "raw_text_committed": False,
        "normalizer_version": NORMALIZER_VERSION,
    }
    write_report(summary, skipped)
    return summary


def write_report(summary: dict[str, Any], skipped: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Normalization Quality Report",
        "",
        f"- Registry rows: {summary['registry_rows']}",
        f"- Normalized transcripts: {summary['normalized_transcripts']}",
        f"- Skipped rows: {summary['skipped']}",
        f"- Normalizer version: `{summary['normalizer_version']}`",
        f"- Repo manifest: `{_display_path(str(summary['out_manifest']))}`",
        f"- Desktop index: `{summary['desktop_index']}`",
        "- Raw transcript text committed: false",
        "",
        "## Skipped Rows",
        "",
    ]
    lines.extend(f"- {row.get('case_id', '')}: {row.get('reason', '')}" for row in skipped) if skipped else lines.append("- none")
    payload = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(payload, encoding="utf-8")
    FIRST30_REPORT_PATH.write_text(payload.replace("# Normalization Quality Report", "# First30 Normalization Status", 1), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize registered Desktop transcripts.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(normalize_registered_transcripts(registry_path=args.registry, workspace=args.workspace, out_path=args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
