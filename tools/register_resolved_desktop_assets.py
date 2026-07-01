#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

from tools.user_authorized_ingest_common import (
    AUDIO_REGISTRY_FIELDS,
    DEFAULT_WORKSPACE,
    TRANSCRIPT_REGISTRY_FIELDS,
    file_sha256,
    is_relative_to,
    now_iso,
    read_csv,
    write_csv,
)

DEFAULT_LOG = DEFAULT_WORKSPACE / "_audit" / "resolved_download_log.csv"
DEFAULT_TRANSCRIPT_OUT = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
DEFAULT_AUDIO_OUT = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "resolved_registration_status.md"


def _registry_row(row: dict[str, str], *, sha256: str) -> dict[str, str]:
    return {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "asset_type": row.get("asset_type", ""),
        "local_path": row.get("local_path", ""),
        "sha256": sha256,
        "source_url": row.get("source_url", ""),
        "provenance_path": row.get("provenance_path", ""),
        "rights_status": "safe_to_download",
        "eval_allowed": row.get("eval_allowed", "true"),
        "commit_allowed": "false",
        "training_allowed": "false",
        "approval_ref": row.get("approval_ref", ""),
        "registered_timestamp": now_iso(),
        "notes": "Registered by path and sha256 only; raw file remains in Desktop workspace.",
    }


def register_resolved_assets(*, workspace: Path, download_log: Path, transcript_out: Path = DEFAULT_TRANSCRIPT_OUT, audio_out: Path = DEFAULT_AUDIO_OUT) -> dict[str, Any]:
    rows = read_csv(download_log)
    transcripts: list[dict[str, str]] = []
    audio: list[dict[str, str]] = []
    skipped = 0
    for row in rows:
        if row.get("download_status") != "downloaded":
            continue
        local_path = Path(row.get("local_path", ""))
        if not local_path.exists() or not is_relative_to(local_path, workspace) or is_relative_to(local_path, ROOT):
            skipped += 1
            continue
        if row.get("commit_allowed") != "false" or row.get("training_allowed") != "false":
            skipped += 1
            continue
        registry_row = _registry_row(row, sha256=file_sha256(local_path))
        if row.get("asset_type") == "transcript":
            transcripts.append(registry_row)
        elif row.get("asset_type") == "audio":
            audio.append(registry_row)
        else:
            skipped += 1
    write_csv(transcript_out, transcripts, TRANSCRIPT_REGISTRY_FIELDS)
    write_csv(audio_out, audio, AUDIO_REGISTRY_FIELDS)
    summary = {
        "download_log_rows": len(rows),
        "registered_transcripts": len(transcripts),
        "registered_audio": len(audio),
        "skipped": skipped,
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Resolved Registration Status\n\n"
        f"- Download log rows: {summary['download_log_rows']}\n"
        f"- Registered transcripts: {summary['registered_transcripts']}\n"
        f"- Registered audio: {summary['registered_audio']}\n"
        f"- Skipped rows: {summary['skipped']}\n"
        "- Raw files copied into repo: false\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register resolved Desktop assets by path and sha256.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--download-log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--transcript-out", type=Path, default=DEFAULT_TRANSCRIPT_OUT)
    parser.add_argument("--audio-out", type=Path, default=DEFAULT_AUDIO_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(register_resolved_assets(workspace=args.workspace, download_log=args.download_log, transcript_out=args.transcript_out, audio_out=args.audio_out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
