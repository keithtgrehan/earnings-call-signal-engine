#!/usr/bin/env python3
"""Build audio RAG readiness metadata without cloud ASR or raw text commits."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "acquisition"
DEFAULT_POLICY = ROOT / "configs" / "nyse_100_asset_acquisition_policy.example.yml"
ALLOWED_AUDIO_RIGHTS = {"safe_to_download", "manual_local_review_only", "rights_cleared"}

AUDIO_RAG_FIELDS = [
    "record_id",
    "case_id",
    "ticker",
    "audio_asset_id",
    "audio_local_path",
    "source_sha256",
    "rights_status",
    "eval_use_allowed",
    "asr_status",
    "asr_text_path",
    "chunk_manifest_path",
    "notes",
    "created_at",
    "raw_text_committed",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def read_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"asr_enabled": False, "asr_provider": "none"}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"asr_enabled": False, "asr_provider": "none"}


def build_audio_rag_manifest(*, workspace: Path, audit_path: Path, out_path: Path, policy_path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    audit_rows = read_csv(audit_path)
    policy = read_policy(policy_path)
    asr_enabled = coerce_bool(policy.get("asr_enabled"))
    rows: list[dict[str, Any]] = []
    for row in audit_rows:
        if row.get("asset_type") != "audio":
            continue
        audio_path = Path(row.get("audio_local_path") or row.get("local_path") or "")
        rights_status = row.get("rights_status", "")
        eval_allowed = coerce_bool(row.get("allow_eval_use"))
        if row.get("download_status") != "downloaded" or rights_status not in ALLOWED_AUDIO_RIGHTS or not eval_allowed or not audio_path.exists():
            continue
        asr_status = "todo_asr_disabled"
        notes = "ASR disabled by policy; audio RAG requires explicit local ASR enablement."
        if asr_enabled:
            asr_status = "todo_local_asr_not_configured"
            notes = "ASR enabled in policy, but no local ASR runner is wired in this metadata-only tool."
        rows.append(
            {
                "record_id": f"{row.get('case_id', 'unknown')}_{row.get('asset_id', 'audio')}_audio_rag",
                "case_id": row.get("case_id", ""),
                "ticker": row.get("ticker", ""),
                "audio_asset_id": row.get("asset_id", ""),
                "audio_local_path": str(audio_path),
                "source_sha256": row.get("sha256", ""),
                "rights_status": rights_status,
                "eval_use_allowed": "true",
                "asr_status": asr_status,
                "asr_text_path": "",
                "chunk_manifest_path": "",
                "notes": notes,
                "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
                "raw_text_committed": "false",
            }
        )
    write_csv(out_path, rows, AUDIO_RAG_FIELDS)
    summary = {
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "audit_rows": len(audit_rows),
        "audio_rag_records": len(rows),
        "audio_rag_ready_calls": 0 if not asr_enabled else len({row["case_id"] for row in rows if row["asr_status"] == "asr_complete"}),
        "todo_records": sum(1 for row in rows if row["asr_status"].startswith("todo")),
        "asr_enabled": asr_enabled,
        "cloud_asr_called": False,
        "youtube_audio_processed": False,
        "raw_text_committed": False,
        "rights_status_counts": dict(Counter(row["rights_status"] for row in rows)),
        "out_manifest": str(out_path),
    }
    write_reports(summary)
    return summary


def write_reports(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "audio_rag_readiness.md").write_text(
        "\n".join(
            [
                "# Audio RAG Readiness",
                "",
                f"- Audit rows read: {summary['audit_rows']}",
                f"- Audio RAG records: {summary['audio_rag_records']}",
                f"- Audio RAG-ready calls: {summary['audio_rag_ready_calls']}",
                f"- TODO records: {summary['todo_records']}",
                f"- ASR enabled: {str(summary['asr_enabled']).lower()}",
                "- Cloud ASR called: false",
                "- YouTube audio processed: false",
                "- Raw ASR text committed: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORT_DIR / "audio_rag_readiness.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build repo-safe NYSE 100 audio RAG readiness metadata.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_audio_rag_manifest(
        workspace=Path(args.workspace),
        audit_path=Path(args.audit),
        out_path=Path(args.out),
        policy_path=Path(args.policy),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
