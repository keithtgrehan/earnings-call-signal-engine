#!/usr/bin/env python3
"""Download user-authorized NYSE 100 transcript/audio assets to Desktop only."""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import mimetypes
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import (
    AUDIO_SUFFIXES,
    DEFAULT_WORKSPACE,
    DOWNLOAD_LOG_FIELDS,
    USER_AUTHORIZED_PERMITTED_FIELDS,
    VIDEO_SUFFIXES,
    approved_row_errors,
    as_bool,
    bytes_sha256,
    call_folder_from_audit,
    file_sha256,
    hard_barrier_reason,
    is_relative_to,
    is_youtube_url,
    now_iso,
    read_csv,
    read_policy,
    slugify,
    url_suffix,
    write_csv,
    write_json,
)

REPORT_DIR = ROOT / "reports" / "acquisition"
DEFAULT_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_user_authorized_permitted_downloads.csv"
DEFAULT_POLICY = ROOT / "configs" / "nyse_100_user_authorized_ingest_policy.yml"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)

    def text(self) -> str:
        return "\n".join(self.parts).strip() + "\n"


def read_source_bytes(source_url: str, user_agent: str) -> tuple[bytes, str]:
    parsed = urlparse(source_url)
    if parsed.scheme == "file":
        local = Path(unquote(parsed.path))
        data = local.read_bytes()
        guessed, _ = mimetypes.guess_type(str(local))
        return data, guessed or "application/octet-stream"
    request = Request(source_url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=20) as response:
        return response.read(), response.headers.get_content_type() or "application/octet-stream"


def html_to_text(data: bytes) -> bytes:
    parser = TextExtractor()
    parser.feed(data.decode("utf-8", errors="replace"))
    return parser.text().encode("utf-8")


def looks_like_transcript(text: str) -> bool:
    lower = text.lower()
    markers = [
        "operator",
        "prepared remarks",
        "question-and-answer",
        "question and answer",
        "earnings call transcript",
        "conference call",
    ]
    return len(text) >= 500 and sum(marker in lower for marker in markers) >= 2


def likely_direct_transcript_url(source_url: str) -> bool:
    parsed = urlparse(source_url)
    if parsed.scheme == "file":
        return True
    suffix = url_suffix(source_url)
    path = parsed.path.lower()
    if suffix in {".txt", ".html", ".htm", ".pdf"}:
        return True
    return any(marker in path for marker in ("transcript", "earnings", "event", "webcast", "quarter", "results"))


def likely_direct_audio_url(source_url: str) -> bool:
    parsed = urlparse(source_url)
    if parsed.scheme == "file":
        return True
    suffix = url_suffix(source_url)
    if suffix in AUDIO_SUFFIXES:
        return True
    if suffix in VIDEO_SUFFIXES:
        return False
    path = parsed.path.lower()
    return any(marker in path for marker in ("audio", ".mp3", ".m4a", ".wav"))


def _blocked_row(row: dict[str, str], reason: str, provenance_path: Path) -> dict[str, Any]:
    return {
        "source_id": row.get("source_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "asset_type": row.get("asset_type", ""),
        "source_type": row.get("source_type", ""),
        "source_url": row.get("source_url", ""),
        "download_status": "blocked",
        "blocked_reason": reason,
        "local_path": "",
        "sha256": "",
        "bytes": "",
        "content_type": "",
        "commit_allowed": "false",
        "training_allowed": "false",
        "eval_allowed": row.get("allow_eval_use", "false"),
        "approval_ref": row.get("approval_ref", ""),
        "provenance_path": str(provenance_path),
    }


def _downloaded_row(row: dict[str, str], local_path: Path, content_type: str, provenance_path: Path) -> dict[str, Any]:
    return {
        "source_id": row.get("source_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "asset_type": row.get("asset_type", ""),
        "source_type": row.get("source_type", ""),
        "source_url": row.get("source_url", ""),
        "download_status": "downloaded",
        "blocked_reason": "",
        "local_path": str(local_path),
        "sha256": file_sha256(local_path),
        "bytes": str(local_path.stat().st_size),
        "content_type": content_type,
        "commit_allowed": "false",
        "training_allowed": "false",
        "eval_allowed": row.get("allow_eval_use", "true"),
        "approval_ref": row.get("approval_ref", ""),
        "provenance_path": str(provenance_path),
    }


def _write_attempt_provenance(path: Path, row: dict[str, str], status: str, reason: str, local_path: str = "") -> None:
    write_json(
        path,
        {
            "created_at": now_iso(),
            "source_id": row.get("source_id", ""),
            "case_id": row.get("case_id", ""),
            "asset_type": row.get("asset_type", ""),
            "source_url": row.get("source_url", ""),
            "download_status": status,
            "blocked_reason": reason,
            "local_path": local_path,
            "commit_allowed": False,
            "training_allowed": False,
            "approval_ref": row.get("approval_ref", ""),
        },
    )


def _save_transcript(row: dict[str, str], data: bytes, content_type: str, call_folder: Path) -> tuple[Path | None, str, str]:
    suffix = url_suffix(row.get("source_url", ""))
    if suffix == ".pdf" or "pdf" in content_type:
        return None, "pdf_text_extraction_not_enabled", content_type
    if "html" in content_type or suffix in {"", ".html", ".htm"}:
        data = html_to_text(data)
        content_type = "text/plain"
    text = data.decode("utf-8", errors="replace")
    if not looks_like_transcript(text):
        return None, "content_not_transcript_like", content_type
    target = call_folder / "transcript" / f"{slugify(row.get('case_id', 'unknown'))}_{slugify(row.get('source_id', 'source'))}.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target, "", "text/plain"


def _save_audio(row: dict[str, str], data: bytes, content_type: str, call_folder: Path) -> tuple[Path | None, str, str]:
    suffix = url_suffix(row.get("source_url", ""))
    if is_youtube_url(row.get("source_url", "")):
        return None, "youtube_audio_video_blocked", content_type
    if suffix in VIDEO_SUFFIXES:
        return None, "video_url_rejected_for_audio", content_type
    if suffix and suffix not in AUDIO_SUFFIXES:
        return None, "not_direct_audio_url", content_type
    if not suffix and not content_type.startswith("audio/"):
        return None, "not_direct_audio_url", content_type
    extension = suffix if suffix in AUDIO_SUFFIXES else mimetypes.guess_extension(content_type) or ".audio"
    target = call_folder / "audio" / f"{slugify(row.get('case_id', 'unknown'))}_{slugify(row.get('source_id', 'source'))}{extension}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target, "", content_type


def download_user_authorized_assets(*, manifest_path: Path, policy_path: Path, workspace: Path) -> dict[str, Any]:
    policy = read_policy(policy_path)
    rows = read_csv(manifest_path)
    workspace.mkdir(parents=True, exist_ok=True)
    audit_dir = workspace / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    log_rows: list[dict[str, Any]] = []
    request_delay = 1.0 / float(policy.get("max_requests_per_second") or 1)
    user_agent = str(policy.get("user_agent") or "SignalEngine/2.0 user-authorized acquisition")
    last_request_at = 0.0
    cache: dict[tuple[str, str], tuple[bytes, str] | tuple[None, str]] = {}

    for row in rows:
        call_folder = call_folder_from_audit(workspace, row.get("case_id", ""))
        provenance_path = call_folder / "provenance" / f"{slugify(row.get('source_id', 'source'))}.user_authorized.provenance.json"
        errors = approved_row_errors(row)
        reason = ";".join(errors) if errors else hard_barrier_reason(row, policy)
        if reason:
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        if call_folder.resolve().is_relative_to(ROOT.resolve()):
            reason = "desktop_only_storage_required"
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        asset_type = row.get("asset_type", "")
        if asset_type == "audio" and not as_bool(policy.get("allow_audio_downloads", True)):
            reason = "audio_downloads_disabled"
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        if asset_type == "transcript" and not as_bool(policy.get("allow_transcript_downloads", True)):
            reason = "transcript_downloads_disabled"
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        if asset_type == "transcript" and not likely_direct_transcript_url(row.get("source_url", "")):
            reason = "not_direct_transcript_url"
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        if asset_type == "audio" and not likely_direct_audio_url(row.get("source_url", "")):
            reason = "not_direct_audio_url"
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        key = (asset_type, row.get("source_url", ""))
        if key not in cache:
            elapsed = time.monotonic() - last_request_at
            if elapsed < request_delay:
                time.sleep(request_delay - elapsed)
            try:
                data, content_type = read_source_bytes(row.get("source_url", ""), user_agent)
                cache[key] = (data, content_type)
                last_request_at = time.monotonic()
            except Exception as exc:  # noqa: BLE001 - recorded as audit data.
                cache[key] = (None, f"download_failed:{exc}")
        cached = cache[key]
        if cached[0] is None:
            reason = str(cached[1])
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        data = cached[0]
        content_type = str(cached[1])
        if asset_type == "transcript":
            target, reason, content_type = _save_transcript(row, data, content_type, call_folder)
        elif asset_type == "audio":
            target, reason, content_type = _save_audio(row, data, content_type, call_folder)
        else:
            target, reason, content_type = None, "unsupported_asset_type", content_type
        if target is None:
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        if is_relative_to(target, ROOT):
            target.unlink(missing_ok=True)
            reason = "raw_asset_inside_repo_blocked"
            _write_attempt_provenance(provenance_path, row, "blocked", reason)
            log_rows.append(_blocked_row(row, reason, provenance_path))
            continue
        _write_attempt_provenance(provenance_path, row, "downloaded", "", str(target))
        log_rows.append(_downloaded_row(row, target, content_type, provenance_path))

    log_path = audit_dir / "user_authorized_download_log.csv"
    write_csv(log_path, log_rows, DOWNLOAD_LOG_FIELDS)
    summary = {
        "download_log_rows": len(log_rows),
        "transcript_downloads_attempted": sum(1 for row in log_rows if row.get("asset_type") == "transcript"),
        "transcript_downloads_succeeded": sum(1 for row in log_rows if row.get("asset_type") == "transcript" and row.get("download_status") == "downloaded"),
        "audio_downloads_attempted": sum(1 for row in log_rows if row.get("asset_type") == "audio"),
        "audio_downloads_succeeded": sum(1 for row in log_rows if row.get("asset_type") == "audio" and row.get("download_status") == "downloaded"),
        "blocked_reasons": dict(Counter(row.get("blocked_reason", "") for row in log_rows if row.get("download_status") != "downloaded")),
        "log_path": str(log_path),
    }
    write_reports(summary)
    return summary


def write_reports(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# User-Authorized Download Log",
        "",
        f"- Transcript downloads attempted: {summary['transcript_downloads_attempted']}",
        f"- Transcript downloads succeeded: {summary['transcript_downloads_succeeded']}",
        f"- Audio downloads attempted: {summary['audio_downloads_attempted']}",
        f"- Audio downloads succeeded: {summary['audio_downloads_succeeded']}",
        f"- Log: `{summary['log_path']}`",
        "",
        "## Blocked Reasons",
        "",
    ]
    if summary["blocked_reasons"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in summary["blocked_reasons"].items())
    else:
        lines.append("- none")
    (REPORT_DIR / "user_authorized_download_log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download user-authorized transcript/audio assets to Desktop only.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args(argv)
    print(download_user_authorized_assets(manifest_path=args.manifest, policy_path=args.policy, workspace=args.workspace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
