#!/usr/bin/env python3
"""Build user-authorized audio RAG readiness manifests without cloud ASR."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import AUDIO_RAG_FIELDS, DEFAULT_WORKSPACE, is_relative_to, now_iso, read_csv, slugify, write_csv

REPORT_DIR = ROOT / "reports" / "acquisition"
DEFAULT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_audio_rag_manifest.csv"


def local_asr_available() -> bool:
    return bool(shutil.which("whisper") or shutil.which("whisper-cpp") or shutil.which("whisper.cpp"))


def build_user_authorized_audio_rag(*, registry_path: Path, workspace: Path, out_path: Path = DEFAULT_OUT) -> dict[str, Any]:
    registry_rows = read_csv(registry_path)
    rows: list[dict[str, str]] = []
    asr_available = local_asr_available()
    for row in registry_rows:
        if row.get("asset_type") != "audio" or row.get("eval_allowed") != "true" or row.get("commit_allowed") != "false":
            continue
        audio_path = Path(row.get("local_path", ""))
        if not audio_path.exists() or not is_relative_to(audio_path, workspace) or is_relative_to(audio_path, ROOT):
            continue
        asr_status = "todo_local_asr_not_available"
        notes = "Local ASR tool not available; no cloud ASR called."
        if asr_available:
            asr_status = "todo_local_asr_available_not_run"
            notes = "Local ASR appears available, but automatic ASR execution is not wired in this metadata-safe manifest builder."
        rows.append(
            {
                "record_id": f"{slugify(row.get('case_id', 'unknown'))}_audio_rag",
                "case_id": row.get("case_id", ""),
                "ticker": row.get("ticker", ""),
                "audio_asset_id": f"{row.get('case_id', 'unknown')}_audio",
                "audio_local_path": str(audio_path),
                "source_sha256": row.get("sha256", ""),
                "rights_status": row.get("rights_status", "safe_to_download"),
                "eval_use_allowed": "true",
                "asr_status": asr_status,
                "asr_text_path": "",
                "chunk_manifest_path": "",
                "notes": notes,
                "created_at": now_iso(),
                "raw_text_committed": "false",
            }
        )
    write_csv(out_path, rows, AUDIO_RAG_FIELDS)
    desktop_index = workspace / "_audit" / "audio_rag_index.csv"
    write_csv(desktop_index, rows, AUDIO_RAG_FIELDS)
    summary = {
        "registry_rows": len(registry_rows),
        "audio_rag_records": len(rows),
        "audio_rag_ready_calls": len({row["case_id"] for row in rows if row.get("case_id")}),
        "local_asr_available": asr_available,
        "local_asr_used": False,
        "cloud_asr_used": False,
        "out_manifest": str(out_path),
        "desktop_index": str(desktop_index),
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = (
        "# User-Authorized Audio RAG Readiness\n\n"
        f"- Registry rows: {summary['registry_rows']}\n"
        f"- Audio RAG records: {summary['audio_rag_records']}\n"
        f"- Audio RAG-ready calls: {summary['audio_rag_ready_calls']}\n"
        f"- Local ASR available: {str(summary['local_asr_available']).lower()}\n"
        "- Local ASR used: false\n"
        "- Cloud ASR used: false\n"
        "- Raw ASR text committed: false\n"
    )
    (REPORT_DIR / "audio_rag_readiness.md").write_text(payload, encoding="utf-8")
    (REPORT_DIR / "user_authorized_audio_rag_readiness.md").write_text(payload, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build user-authorized audio RAG readiness metadata.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    print(build_user_authorized_audio_rag(registry_path=args.registry, workspace=args.workspace, out_path=args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
