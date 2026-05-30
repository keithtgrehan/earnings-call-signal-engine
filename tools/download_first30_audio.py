#!/usr/bin/env python3
"""Download approved direct first30 audio candidates into Desktop-only storage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.asr_backends import probe_audio  # noqa: E402
from signal_engine.audio.schemas import AUDIO_REGISTRY_FIELDS  # noqa: E402
from tools.first30_transcript_common import (  # noqa: E402
    APPROVAL_REF,
    DESKTOP_WORKSPACE,
    file_sha256,
    now_iso,
    read_csv,
    slugify,
    write_csv,
    write_json,
)
from tools.resolve_first30_audio_candidates import AUDIO_FIELDS, OUT_PATH as AUDIO_CANDIDATES_PATH, is_direct_audio_url  # noqa: E402

ACQUISITION_AUDIO_REGISTRY = ROOT / "data" / "acquisition" / "audio_registry.csv"
MANUAL_AUDIO_REGISTRY = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "first30_audio_download_status.md"
DOWNLOAD_LOG_FIELDS = [
    "case_id",
    "ticker",
    "audio_url",
    "attempted",
    "download_status",
    "blocked_reason",
    "local_path",
    "sha256",
    "bytes",
    "content_type",
    "commit_allowed",
    "training_allowed",
    "raw_audio_committed",
]

MANUAL_AUDIO_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "local_path",
    "sha256",
    "source_url",
    "provenance_path",
    "rights_status",
    "eval_allowed",
    "commit_allowed",
    "training_allowed",
    "approval_ref",
    "registered_timestamp",
    "notes",
]

USER_AGENT = "SignalEngineCorpusAssessment/2.0 (metadata-safe; contact: project owner)"


def _call_audio_path(row: dict[str, str], workspace: Path) -> Path:
    suffix = Path(urlparse(row.get("audio_url", "")).path).suffix.lower() or ".mp3"
    return (
        workspace
        / f"{slugify(row.get('ticker', 'UNKNOWN'))}_{slugify(row.get('company_name', ''))}"
        / slugify(row.get("case_id", "unknown"))
        / "audio"
        / f"{slugify(row.get('case_id', 'unknown'))}_first30_audio{suffix}"
    )


def _fetch_audio(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "audio/*,*/*"})
    with urlopen(request, timeout=90) as response:
        return response.read(), response.headers.get("Content-Type", "")


def _base_log(row: dict[str, str]) -> dict[str, str]:
    return {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "audio_url": row.get("audio_url", ""),
        "attempted": "false",
        "download_status": "not_attempted",
        "blocked_reason": row.get("blocked_reason", ""),
        "local_path": "",
        "sha256": "",
        "bytes": "0",
        "content_type": "",
        "commit_allowed": "false",
        "training_allowed": "false",
        "raw_audio_committed": "false",
    }


def _dedupe(rows: list[dict[str, str]], new_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_case: dict[str, dict[str, str]] = {}
    for row in rows + new_rows:
        case_id = row.get("case_id", "")
        if case_id:
            by_case[case_id] = row
    return [by_case[key] for key in sorted(by_case)]


def download_audio_candidate(row: dict[str, str], workspace: Path) -> tuple[dict[str, str], dict[str, str] | None, dict[str, str] | None]:
    log = _base_log(row)
    if row.get("download_allowed") != "true":
        log["download_status"] = "blocked"
        log["blocked_reason"] = row.get("blocked_reason") or "download_not_allowed"
        return log, None, None
    if not is_direct_audio_url(row.get("audio_url", "")):
        log["download_status"] = "blocked"
        log["blocked_reason"] = "not_direct_audio_url"
        return log, None, None
    log["attempted"] = "true"
    try:
        payload, content_type = _fetch_audio(row["audio_url"])
    except Exception as exc:  # pragma: no cover - network dependent
        log["download_status"] = "failed"
        log["blocked_reason"] = f"download_error:{type(exc).__name__}"
        return log, None, None
    local_path = _call_audio_path(row, workspace)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(payload)
    digest = file_sha256(local_path)
    probe = probe_audio(local_path)
    provenance = local_path.parent / "provenance.json"
    write_json(
        provenance,
        {
            "case_id": row.get("case_id", ""),
            "source_url": row.get("audio_url", ""),
            "local_path": str(local_path),
            "sha256": digest,
            "commit_allowed": False,
            "training_allowed": False,
            "raw_audio_committed": False,
            "approval_ref": APPROVAL_REF,
        },
    )
    log.update(
        {
            "download_status": "downloaded",
            "local_path": str(local_path),
            "sha256": digest,
            "bytes": str(len(payload)),
            "content_type": content_type,
        }
    )
    audio_asset_id = f"{row.get('case_id', '')}_audio"
    acquisition = {
        "audio_asset_id": audio_asset_id,
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "local_path": str(local_path),
        "sha256": digest,
        "source_url": row.get("audio_url", ""),
        "rights_status": "safe_to_download",
        "eval_allowed": "true",
        "commit_allowed": "false",
        "training_allowed": "false",
        "approval_ref": APPROVAL_REF,
        "raw_audio_committed": "false",
        "ffprobe_status": probe.get("ffprobe_status", ""),
        "duration_sec": str(probe.get("duration_sec", "")),
        "sample_rate_hz": str(probe.get("sample_rate_hz", "")),
        "channels": str(probe.get("channels", "")),
        "asr_status": "not_run",
        "asr_text_path": "",
        "raw_asr_committed": "false",
        "notes": "Registered by path and sha256 only; raw audio remains in Desktop workspace.",
    }
    manual = {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "asset_type": "audio",
        "local_path": str(local_path),
        "sha256": digest,
        "source_url": row.get("audio_url", ""),
        "provenance_path": str(provenance),
        "rights_status": "safe_to_download",
        "eval_allowed": "true",
        "commit_allowed": "false",
        "training_allowed": "false",
        "approval_ref": APPROVAL_REF,
        "registered_timestamp": now_iso(),
        "notes": "Registered by path and sha256 only; raw audio remains in Desktop workspace.",
    }
    return log, acquisition, manual


def download_first30_audio(
    *,
    candidates_path: Path = AUDIO_CANDIDATES_PATH,
    workspace: Path = DESKTOP_WORKSPACE,
    acquisition_registry: Path = ACQUISITION_AUDIO_REGISTRY,
    manual_registry: Path = MANUAL_AUDIO_REGISTRY,
) -> dict[str, Any]:
    candidates = read_csv(candidates_path)
    logs: list[dict[str, str]] = []
    acquisition_rows: list[dict[str, str]] = []
    manual_rows: list[dict[str, str]] = []
    for row in candidates:
        log, acquisition, manual = download_audio_candidate(row, workspace)
        logs.append(log)
        if acquisition:
            acquisition_rows.append(acquisition)
        if manual:
            manual_rows.append(manual)
    final_acquisition = _dedupe(read_csv(acquisition_registry), acquisition_rows)
    final_manual = _dedupe(read_csv(manual_registry), manual_rows)
    write_csv(acquisition_registry, final_acquisition, AUDIO_REGISTRY_FIELDS)
    write_csv(manual_registry, final_manual, MANUAL_AUDIO_FIELDS)
    audit = workspace / "_audit" / "first30_audio_download_log.csv"
    write_csv(audit, logs, DOWNLOAD_LOG_FIELDS)
    summary = {
        "candidate_rows": len(candidates),
        "download_attempts": sum(1 for row in logs if row.get("attempted") == "true"),
        "download_succeeded": sum(1 for row in logs if row.get("download_status") == "downloaded"),
        "registered_audio_rows": len(final_acquisition),
        "out_registry": str(acquisition_registry),
        "manual_registry": str(manual_registry),
        "desktop_audit": str(audit),
    }
    write_report(summary, logs)
    return summary


def write_report(summary: dict[str, Any], logs: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First30 Audio Download Status",
        "",
        f"- Candidate rows: {summary['candidate_rows']}",
        f"- Download attempts: {summary['download_attempts']}",
        f"- Download succeeded: {summary['download_succeeded']}",
        f"- Registered audio rows: {summary['registered_audio_rows']}",
        "- Raw audio committed: false",
        "- Cloud ASR used: false",
        "",
        "## Failed/Blocked Rows",
        "",
    ]
    blocked = [row for row in logs if row.get("download_status") != "downloaded"]
    if blocked:
        for row in blocked:
            lines.append(f"- `{row.get('case_id')}` `{row.get('ticker')}`: {row.get('blocked_reason') or row.get('download_status')}")
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download approved first30 direct audio candidates.")
    parser.add_argument("--candidates", type=Path, default=AUDIO_CANDIDATES_PATH)
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    parser.add_argument("--audio-registry", type=Path, default=ACQUISITION_AUDIO_REGISTRY)
    parser.add_argument("--manual-audio-registry", type=Path, default=MANUAL_AUDIO_REGISTRY)
    args = parser.parse_args(argv)
    summary = download_first30_audio(
        candidates_path=args.candidates,
        workspace=args.workspace,
        acquisition_registry=args.audio_registry,
        manual_registry=args.manual_audio_registry,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
