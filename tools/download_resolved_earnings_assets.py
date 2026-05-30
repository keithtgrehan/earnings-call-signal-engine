#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Callable
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import block_reason_for_url, file_ext_for, read_csv
from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE, DOWNLOAD_LOG_FIELDS, bytes_sha256, slugify, write_csv, write_json

DEFAULT_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_permitted_downloads.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "resolved_download_summary.md"


def default_fetcher(url: str) -> tuple[int, str, bytes]:
    request = Request(url, headers={"User-Agent": "SignalEngine/2.0 resolved asset downloader (project assessment; contact: keithtgrehan)"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - guarded public HTTP fetch.
        return int(getattr(response, "status", 200)), response.headers.get("content-type", ""), response.read(50_000_000)


def _asset_folder(workspace: Path, row: dict[str, str]) -> Path:
    ticker = slugify(row.get("ticker", "UNKNOWN"))
    company = slugify(row.get("company_name", "company"))
    case_id = slugify(row.get("case_id", "case"))
    return workspace / f"{ticker}_{company}" / case_id


def _target_path(workspace: Path, row: dict[str, str]) -> Path:
    root = _asset_folder(workspace, row)
    asset_type = row.get("asset_type", "")
    ext = file_ext_for(row.get("resolved_asset_url", "")) or ".bin"
    if asset_type.startswith("transcript_"):
        return root / "transcript" / f"{slugify(row.get('case_id', 'call'))}{'.txt' if asset_type in {'transcript_text', 'transcript_html'} else ext}"
    return root / "audio" / f"{slugify(row.get('case_id', 'call'))}{ext}"


def _safe_text_from_html(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip() + "\n"


def _log_row(row: dict[str, str], *, status: str, blocked_reason: str = "", local_path: str = "", sha256: str = "", byte_count: int = 0, content_type: str = "", provenance_path: str = "") -> dict[str, str]:
    asset_type = row.get("asset_type", "")
    normalized_asset = "transcript" if asset_type.startswith("transcript_") else "audio" if asset_type.startswith("audio_") else asset_type
    return {
        "source_id": row.get("candidate_id") or row.get("source_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "asset_type": normalized_asset,
        "source_type": row.get("source_type", ""),
        "source_url": row.get("resolved_asset_url") or row.get("source_url", ""),
        "download_status": status,
        "blocked_reason": blocked_reason,
        "local_path": local_path,
        "sha256": sha256,
        "bytes": str(byte_count),
        "content_type": content_type,
        "commit_allowed": "false",
        "training_allowed": "false",
        "eval_allowed": row.get("eval_allowed", "true"),
        "approval_ref": row.get("approval_ref", ""),
        "provenance_path": provenance_path,
    }


def download_resolved_assets(*, manifest: Path, workspace: Path, fetcher: Callable[[str], tuple[int, str, bytes]] = default_fetcher) -> dict[str, int]:
    rows = read_csv(manifest)
    log_rows: list[dict[str, str]] = []
    transcript_attempts = audio_attempts = transcript_successes = audio_successes = blocked = 0
    for row in rows:
        url = row.get("resolved_asset_url") or row.get("source_url") or ""
        asset_type = row.get("asset_type", "")
        if asset_type.startswith("transcript_"):
            transcript_attempts += 1
        if asset_type.startswith("audio_"):
            audio_attempts += 1
        block_reason = block_reason_for_url(url, row.get("source_type", ""))
        if row.get("download_allowed") != "true":
            block_reason = block_reason or "download_not_allowed"
        if block_reason:
            blocked += 1
            log_rows.append(_log_row(row, status="blocked", blocked_reason=block_reason))
            continue
        try:
            status_code, content_type, payload = fetcher(url)
        except Exception as exc:  # pragma: no cover - live network defensive path.
            blocked += 1
            log_rows.append(_log_row(row, status="blocked", blocked_reason=f"fetch_failed:{type(exc).__name__}"))
            continue
        if status_code >= 400:
            blocked += 1
            log_rows.append(_log_row(row, status="blocked", blocked_reason=f"http_{status_code}", content_type=content_type))
            continue
        target = _target_path(workspace, row)
        target.parent.mkdir(parents=True, exist_ok=True)
        if asset_type == "transcript_html":
            payload_to_write = _safe_text_from_html(payload).encode("utf-8")
        else:
            payload_to_write = payload
        target.write_bytes(payload_to_write)
        sha256 = bytes_sha256(payload_to_write)
        provenance_path = target.parent / "provenance.json"
        write_json(
            provenance_path,
            {
                "case_id": row.get("case_id", ""),
                "asset_type": asset_type,
                "source_url": url,
                "sha256": sha256,
                "commit_allowed": False,
                "training_allowed": False,
                "eval_allowed": row.get("eval_allowed", "true") == "true",
                "approval_ref": row.get("approval_ref", ""),
            },
        )
        if asset_type.startswith("transcript_"):
            transcript_successes += 1
        if asset_type.startswith("audio_"):
            audio_successes += 1
        log_rows.append(_log_row(row, status="downloaded", local_path=str(target), sha256=sha256, byte_count=len(payload_to_write), content_type=content_type, provenance_path=str(provenance_path)))
    audit_log = workspace / "_audit" / "resolved_download_log.csv"
    write_csv(audit_log, log_rows, DOWNLOAD_LOG_FIELDS)
    summary = {
        "manifest_rows": len(rows),
        "transcript_attempts": transcript_attempts,
        "transcript_successes": transcript_successes,
        "audio_attempts": audio_attempts,
        "audio_successes": audio_successes,
        "blocked": blocked,
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, int]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Resolved Download Summary\n\n"
        f"- Manifest rows: {summary['manifest_rows']}\n"
        f"- Transcript downloads attempted/succeeded: {summary['transcript_attempts']}/{summary['transcript_successes']}\n"
        f"- Audio downloads attempted/succeeded: {summary['audio_attempts']}/{summary['audio_successes']}\n"
        f"- Blocked rows: {summary['blocked']}\n"
        "- Raw files committed: false\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download permitted resolved transcript/audio assets into Desktop workspace only.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args(argv)
    print(json.dumps(download_resolved_assets(manifest=args.manifest, workspace=args.workspace), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
