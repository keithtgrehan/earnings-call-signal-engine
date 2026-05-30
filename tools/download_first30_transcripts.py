#!/usr/bin/env python3
"""Download and parse approved first30 transcripts into Desktop-only files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import (  # noqa: E402
    DESKTOP_WORKSPACE,
    DOWNLOAD_LOG_FIELDS,
    DOWNLOAD_STATUS_REPORT_PATH,
    FIRST30_INGESTION_FIELDS,
    FIRST30_INGESTION_MANIFEST_PATH,
    MANUAL_TRANSCRIPT_REGISTRY_FIELDS,
    MANUAL_TRANSCRIPT_REGISTRY_PATH,
    PARSED_TRANSCRIPT_FIELDS,
    PARSED_TRANSCRIPT_REGISTRY_PATH,
    APPROVAL_REF,
    dedupe_registry_rows,
    fetch_url,
    file_sha256,
    looks_like_transcript,
    looks_like_vendor_raw,
    parse_downloaded_transcript,
    parsed_text_path,
    provenance_path,
    raw_file_path,
    read_csv,
    registry_row_from_parsed,
    text_sha256,
    write_csv,
    write_json,
)


def _base_log_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "candidate_id": row.get("candidate_id", ""),
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "source_url": row.get("source_url", ""),
        "attempted": "false",
        "download_status": "not_attempted",
        "blocked_reason": row.get("blocked_reason", ""),
        "raw_local_path": "",
        "raw_sha256": "",
        "bytes": "0",
        "content_type": "",
        "text_parse_status": "not_attempted",
        "parsed_text_path": "",
        "parsed_text_sha256": "",
        "commit_allowed": "false",
        "training_allowed": "false",
        "eval_allowed": "false",
        "approval_ref": row.get("approval_ref", ""),
        "provenance_path": "",
    }


def _parsed_registry_row(
    row: dict[str, str],
    *,
    raw_path: Path,
    raw_sha: str,
    text_path: Path | None,
    text_digest: str,
    parse_status: str,
    parser: str,
    content_type: str,
    byte_count: int,
    notes: str,
) -> dict[str, str]:
    return {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "source_url": row.get("source_url", ""),
        "raw_local_path": str(raw_path),
        "raw_sha256": raw_sha,
        "parsed_text_path": str(text_path) if text_path else "",
        "parsed_text_sha256": text_digest,
        "text_parse_status": parse_status,
        "parser": parser,
        "content_type": content_type,
        "bytes": str(byte_count),
        "rights_status": "safe_to_download",
        "eval_allowed": "true" if parse_status == "parsed" else "false",
        "commit_allowed": "false",
        "training_allowed": "false",
        "approval_ref": row.get("approval_ref", APPROVAL_REF),
        "registered_timestamp": __import__("tools.first30_transcript_common", fromlist=["now_iso"]).now_iso(),
        "notes": notes,
    }


def _write_download_report(summary: dict[str, Any], failures: list[dict[str, str]], out_path: Path = DOWNLOAD_STATUS_REPORT_PATH) -> None:
    lines = [
        "# First30 Transcript Download Status",
        "",
        f"- Manifest rows: {summary['manifest_rows']}",
        f"- Download attempts: {summary['download_attempts']}",
        f"- Download succeeded: {summary['download_succeeded']}",
        f"- Parsed text succeeded: {summary['parsed_succeeded']}",
        f"- Registered transcript rows: {summary['registered_transcripts']}",
        f"- Raw files committed: false",
        f"- Raw files Desktop-only: true",
        f"- Repo registry: `{summary['manual_registry']}`",
        f"- Desktop audit log: `{summary['desktop_download_log']}`",
        "",
        "## Failure Reasons",
        "",
    ]
    reason_counts = Counter(row.get("blocked_reason") or row.get("download_status") for row in failures)
    if reason_counts:
        for reason, count in sorted(reason_counts.items()):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Failed Rows", ""])
    if failures:
        for row in failures:
            lines.append(f"- `{row.get('case_id')}` `{row.get('ticker')}`: {row.get('blocked_reason') or row.get('download_status')}")
    else:
        lines.append("- none")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def download_one(row: dict[str, str], workspace: Path) -> tuple[dict[str, str], dict[str, str] | None, dict[str, str] | None]:
    log = _base_log_row(row)
    if row.get("download_allowed") != "true":
        log["download_status"] = "blocked"
        log["blocked_reason"] = row.get("blocked_reason") or "download_not_allowed"
        return log, None, None
    log["attempted"] = "true"
    try:
        payload, content_type = fetch_url(row["source_url"])
    except Exception as exc:  # pragma: no cover - network-dependent
        log["download_status"] = "failed"
        log["blocked_reason"] = f"download_error:{type(exc).__name__}"
        return log, None, None
    raw_path = raw_file_path(row, content_type, workspace)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(payload)
    raw_sha = file_sha256(raw_path)
    text, parse_status, parser = parse_downloaded_transcript(raw_path, payload, content_type)
    log.update(
        {
            "download_status": "downloaded",
            "raw_local_path": str(raw_path),
            "raw_sha256": raw_sha,
            "bytes": str(len(payload)),
            "content_type": content_type,
            "text_parse_status": parse_status,
        }
    )
    if parse_status != "parsed":
        parsed_row = _parsed_registry_row(
            row,
            raw_path=raw_path,
            raw_sha=raw_sha,
            text_path=None,
            text_digest="",
            parse_status=parse_status,
            parser=parser,
            content_type=content_type,
            byte_count=len(payload),
            notes="Parser unavailable or produced empty text; raw PDF metadata registered only.",
        )
        return log, parsed_row, None
    if looks_like_vendor_raw(text):
        log["download_status"] = "blocked_after_download"
        log["blocked_reason"] = "vendor_copyright_marker_detected"
        log["text_parse_status"] = "blocked_vendor_marker"
        parsed_row = _parsed_registry_row(
            row,
            raw_path=raw_path,
            raw_sha=raw_sha,
            text_path=None,
            text_digest="",
            parse_status="blocked_vendor_marker",
            parser=parser,
            content_type=content_type,
            byte_count=len(payload),
            notes="Downloaded for Desktop-only assessment; not registered because vendor copyright marker was detected.",
        )
        return log, parsed_row, None
    text_path = parsed_text_path(row, workspace)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text, encoding="utf-8")
    text_digest = text_sha256(text)
    provenance = provenance_path(row, workspace)
    write_json(
        provenance,
        {
            "case_id": row.get("case_id", ""),
            "candidate_id": row.get("candidate_id", ""),
            "source_url": row.get("source_url", ""),
            "raw_local_path": str(raw_path),
            "raw_sha256": raw_sha,
            "parsed_text_path": str(text_path),
            "parsed_text_sha256": text_digest,
            "parser": parser,
            "content_type": content_type,
            "commit_allowed": False,
            "training_allowed": False,
            "raw_text_committed": False,
            "approval_ref": row.get("approval_ref", APPROVAL_REF),
        },
    )
    transcript_like = looks_like_transcript(text)
    notes = "Parsed transcript text registered; raw source remains in Desktop workspace."
    if not transcript_like:
        notes = "Parsed text registered but transcript markers are weak; manual review required before evaluation claims."
    parsed_row = _parsed_registry_row(
        row,
        raw_path=raw_path,
        raw_sha=raw_sha,
        text_path=text_path,
        text_digest=text_digest,
        parse_status="parsed",
        parser=parser,
        content_type=content_type,
        byte_count=len(payload),
        notes=notes,
    )
    registry_row = registry_row_from_parsed(row, text_path, text_digest, provenance)
    log.update(
        {
            "parsed_text_path": str(text_path),
            "parsed_text_sha256": text_digest,
            "eval_allowed": "true",
            "provenance_path": str(provenance),
        }
    )
    return log, parsed_row, registry_row


def download_first30_transcripts(
    *,
    manifest_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    workspace: Path = DESKTOP_WORKSPACE,
    registry_path: Path = MANUAL_TRANSCRIPT_REGISTRY_PATH,
    parsed_registry_path: Path = PARSED_TRANSCRIPT_REGISTRY_PATH,
) -> dict[str, Any]:
    rows = read_csv(manifest_path)
    logs: list[dict[str, str]] = []
    parsed_rows: list[dict[str, str]] = []
    registry_rows: list[dict[str, str]] = []
    for row in sorted(rows, key=lambda item: int(item.get("priority_rank", "999"))):
        log, parsed_row, registry_row = download_one(row, workspace)
        logs.append(log)
        if parsed_row:
            parsed_rows.append(parsed_row)
        if registry_row:
            registry_rows.append(registry_row)
    existing_registry = read_csv(registry_path)
    final_registry = dedupe_registry_rows(existing_registry, registry_rows)
    existing_parsed = {row.get("case_id", ""): row for row in read_csv(parsed_registry_path)}
    for row in parsed_rows:
        existing_parsed[row.get("case_id", "")] = row
    final_parsed = [existing_parsed[key] for key in sorted(existing_parsed)]
    write_csv(registry_path, final_registry, MANUAL_TRANSCRIPT_REGISTRY_FIELDS)
    write_csv(parsed_registry_path, final_parsed, PARSED_TRANSCRIPT_FIELDS)
    blocked_after_parse = {row.get("case_id", ""): row.get("blocked_reason", "post_parse_block") for row in logs if row.get("download_status") == "blocked_after_download"}
    if blocked_after_parse:
        for row in rows:
            case_id = row.get("case_id", "")
            if case_id in blocked_after_parse:
                row["download_allowed"] = "false"
                row["blocked_reason"] = blocked_after_parse[case_id]
                row["approval_ref"] = ""
                row["next_action"] = "blocked_pending_license_or_clean_source"
        write_csv(manifest_path, rows, FIRST30_INGESTION_FIELDS)
        write_csv(workspace / "_audit" / "first30_transcript_ingestion_manifest.csv", rows, FIRST30_INGESTION_FIELDS)
    desktop_log = workspace / "_audit" / "first30_transcript_download_log.csv"
    write_csv(desktop_log, logs, DOWNLOAD_LOG_FIELDS)
    failures = [row for row in logs if row.get("download_status") not in {"downloaded"} or row.get("text_parse_status") != "parsed"]
    summary = {
        "manifest_rows": len(rows),
        "download_attempts": sum(1 for row in logs if row.get("attempted") == "true"),
        "download_succeeded": sum(1 for row in logs if row.get("download_status") == "downloaded"),
        "parsed_succeeded": sum(1 for row in logs if row.get("text_parse_status") == "parsed"),
        "registered_transcripts": len(final_registry),
        "new_registered_transcripts": len(registry_rows),
        "manual_registry": str(registry_path),
        "parsed_registry": str(parsed_registry_path),
        "desktop_download_log": str(desktop_log),
        "failures": len(failures),
    }
    _write_download_report(summary, failures)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download and parse approved first30 transcript candidates.")
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    parser.add_argument("--registry", type=Path, default=MANUAL_TRANSCRIPT_REGISTRY_PATH)
    parser.add_argument("--parsed-registry", type=Path, default=PARSED_TRANSCRIPT_REGISTRY_PATH)
    args = parser.parse_args(argv)
    summary = download_first30_transcripts(
        manifest_path=args.manifest,
        workspace=args.workspace,
        registry_path=args.registry,
        parsed_registry_path=args.parsed_registry,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
