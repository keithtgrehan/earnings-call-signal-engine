#!/usr/bin/env python3
"""Validate user-authorized NYSE 100 ingest outputs and Desktop audit summary."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import (
    AUDIO_RAG_FIELDS,
    DEFAULT_WORKSPACE,
    DOWNLOAD_LOG_FIELDS,
    TRANSCRIPT_CHUNK_FIELDS,
    is_relative_to,
    is_youtube_url,
    read_csv,
    read_policy,
)

DEFAULT_POLICY = ROOT / "configs" / "nyse_100_user_authorized_ingest_policy.yml"
DEFAULT_PERMITTED = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_permitted_downloads.csv"
DEFAULT_TRANSCRIPT_REGISTRY = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
DEFAULT_AUDIO_REGISTRY = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"
DEFAULT_TRANSCRIPT_CHUNKS = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_transcript_chunks.csv"
DEFAULT_AUDIO_RAG = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_audio_rag_manifest.csv"


def staged_paths() -> list[str]:
    result = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def raw_path_looks_forbidden(path: str) -> bool:
    normalized = path.lower().replace("\\", "/")
    suffix = Path(normalized).suffix
    return suffix in {".txt", ".mp3", ".mp4", ".wav", ".m4a", ".mov", ".aac", ".flac"} and any(
        marker in normalized for marker in ("transcript", "/audio/", "/video/", "/chunks/", "/raw/")
    )


def validate_outputs(
    *,
    workspace: Path,
    policy_path: Path = DEFAULT_POLICY,
    permitted_path: Path = DEFAULT_PERMITTED,
    transcript_registry_path: Path = DEFAULT_TRANSCRIPT_REGISTRY,
    audio_registry_path: Path = DEFAULT_AUDIO_REGISTRY,
    transcript_chunks_path: Path = DEFAULT_TRANSCRIPT_CHUNKS,
    audio_rag_path: Path = DEFAULT_AUDIO_RAG,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not workspace.exists():
        errors.append(f"workspace missing: {workspace}")
    if not policy_path.exists():
        errors.append(f"policy missing: {policy_path}")
    policy = read_policy(policy_path)
    if not policy.get("enabled"):
        errors.append("user authorization policy must be enabled")

    audit_dir = workspace / "_audit"
    download_log_path = audit_dir / "user_authorized_download_log.csv"
    if not download_log_path.exists():
        errors.append(f"download log missing: {download_log_path}")
    permitted = read_csv(permitted_path)
    approved_keys = {(row.get("source_id"), row.get("case_id"), row.get("asset_type")) for row in permitted}
    download_rows = read_csv(download_log_path)
    transcript_registry = read_csv(transcript_registry_path)
    audio_registry = read_csv(audio_registry_path)
    transcript_chunks = read_csv(transcript_chunks_path)
    audio_rag = read_csv(audio_rag_path)

    for index, row in enumerate(download_rows, start=1):
        prefix = f"download row {index}"
        if row.get("download_status") == "downloaded":
            if (row.get("source_id"), row.get("case_id"), row.get("asset_type")) not in approved_keys:
                errors.append(f"{prefix}: downloaded row is not in approved manifest")
            local_path = Path(row.get("local_path", ""))
            if not local_path.exists():
                errors.append(f"{prefix}: downloaded local_path missing")
            if is_relative_to(local_path, ROOT):
                errors.append(f"{prefix}: raw local_path points inside repo")
            if not is_relative_to(local_path, workspace):
                errors.append(f"{prefix}: raw local_path must be under Desktop workspace")
            if is_youtube_url(row.get("source_url", "")):
                errors.append(f"{prefix}: YouTube media was downloaded")
            if "vendor" in row.get("source_type", "") and not row.get("license_config_ref"):
                errors.append(f"{prefix}: vendor raw requires license_config_ref")
        if row.get("commit_allowed") != "false":
            errors.append(f"{prefix}: commit_allowed must be false")
        if row.get("training_allowed") != "false":
            errors.append(f"{prefix}: training_allowed must be false without explicit training rights")

    registered_paths = {row.get("local_path", "") for row in transcript_registry + audio_registry}
    for index, row in enumerate(transcript_chunks, start=1):
        prefix = f"chunk row {index}"
        chunk_path = Path(row.get("local_chunk_path", ""))
        if chunk_path and is_relative_to(chunk_path, ROOT):
            errors.append(f"{prefix}: chunk text path points inside repo")
        if row.get("raw_text_committed") != "false":
            errors.append(f"{prefix}: raw_text_committed must be false")
        if row.get("source_sha256") not in {item.get("sha256", "") for item in transcript_registry}:
            errors.append(f"{prefix}: chunk source_sha256 not registered")
    for index, row in enumerate(audio_rag, start=1):
        prefix = f"audio RAG row {index}"
        if row.get("raw_text_committed") != "false":
            errors.append(f"{prefix}: raw_text_committed must be false")
        if row.get("audio_local_path") and row.get("audio_local_path") not in registered_paths:
            errors.append(f"{prefix}: audio path not registered")

    for path in staged_paths():
        if raw_path_looks_forbidden(path):
            errors.append(f"staged raw artifact forbidden: {path}")

    audit_rows = read_csv(workspace / "_audit" / "nyse_earnings_call_audit.csv")
    summary = {
        "companies_processed": len({row.get("ticker_symbol") or row.get("ticker") for row in audit_rows if row.get("ticker_symbol") or row.get("ticker")}),
        "calls_processed": len({row.get("case_id") for row in audit_rows if row.get("case_id")}),
        "permitted_download_rows": len(permitted),
        "transcript_downloads_attempted": sum(1 for row in download_rows if row.get("asset_type") == "transcript"),
        "transcript_downloads_succeeded": sum(1 for row in download_rows if row.get("asset_type") == "transcript" and row.get("download_status") == "downloaded"),
        "audio_downloads_attempted": sum(1 for row in download_rows if row.get("asset_type") == "audio"),
        "audio_downloads_succeeded": sum(1 for row in download_rows if row.get("asset_type") == "audio" and row.get("download_status") == "downloaded"),
        "registered_transcripts": len(transcript_registry),
        "registered_audio": len(audio_registry),
        "transcript_chunks": len(transcript_chunks),
        "audio_rag_records": len(audio_rag),
        "agent1_status": _read_status(ROOT / "reports" / "acquisition" / "user_authorized_agent1_assessment_status.md"),
        "training_readiness": _read_status(ROOT / "reports" / "acquisition" / "user_authorized_training_gate.md"),
        "blocked_reasons": _blocked_reasons(download_rows),
        "next_manual_actions": [
            "Replace IR landing-page placeholders with exact transcript or direct audio URLs for approved sources.",
            "Keep raw transcript/audio files under the Desktop workspace only.",
            "Add license_config_ref before any vendor raw use.",
            "Add youtube_written_authorization_ref before any YouTube media use.",
        ],
        "valid": not errors,
    }
    write_summary(workspace, summary)
    return errors, summary


def _blocked_reasons(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if row.get("download_status") == "downloaded":
            continue
        reason = row.get("blocked_reason", "") or "unknown"
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _read_status(path: Path) -> str:
    if not path.exists():
        return "NOT_RECORDED"
    for line in path.read_text(encoding="utf-8").splitlines():
        if "NOT_READY" in line:
            return "NOT_READY"
        if "READY" in line:
            return "READY"
    return "RECORDED"


def write_summary(workspace: Path, summary: dict[str, Any]) -> None:
    audit_dir = workspace / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "user_authorized_ingest_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# User-Authorized Ingest Summary",
        "",
        f"- Companies processed: {summary['companies_processed']}",
        f"- Calls processed: {summary['calls_processed']}",
        f"- Permitted download rows: {summary['permitted_download_rows']}",
        f"- Transcript downloads attempted: {summary['transcript_downloads_attempted']}",
        f"- Transcript downloads succeeded: {summary['transcript_downloads_succeeded']}",
        f"- Audio downloads attempted: {summary['audio_downloads_attempted']}",
        f"- Audio downloads succeeded: {summary['audio_downloads_succeeded']}",
        f"- Registered transcripts: {summary['registered_transcripts']}",
        f"- Registered audio: {summary['registered_audio']}",
        f"- Transcript chunks: {summary['transcript_chunks']}",
        f"- Audio RAG records: {summary['audio_rag_records']}",
        f"- Agent 1 status: {summary['agent1_status']}",
        f"- Training readiness: {summary['training_readiness']}",
        "",
        "## Blocked Reasons",
        "",
    ]
    if summary["blocked_reasons"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in summary["blocked_reasons"].items())
    else:
        lines.append("- none")
    lines.extend(["", "## Next Manual Actions", ""])
    lines.extend(f"- {item}" for item in summary["next_manual_actions"])
    (audit_dir / "user_authorized_ingest_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    report_dir = ROOT / "reports" / "acquisition"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "user_authorized_ingest_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate user-authorized ingest guardrails.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)
    errors, summary = validate_outputs(workspace=args.workspace, policy_path=args.policy)
    print(json.dumps({"valid": not errors, "errors": errors, "summary": summary}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
