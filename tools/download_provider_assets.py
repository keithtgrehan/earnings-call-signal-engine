#!/usr/bin/env python3
"""Download provider raw assets only when provider/license guardrails permit it."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import AUDIT_DIR, MANUAL_TRANSCRIPT_REGISTRY_FIELDS, MANUAL_TRANSCRIPT_REGISTRY_PATH, file_sha256, now_iso, write_csv, write_json  # noqa: E402
from tools.providers.base import DEFAULT_REGISTRY, DESKTOP_WORKSPACE, load_provider_registry, validate_raw_pull  # noqa: E402
from tools.providers.earningscall_adapter import EarningsCallAdapter  # noqa: E402

ASSETS_IN = ROOT / "reports" / "provider_discovery" / "earningscall_assets.csv"
REPORT_PATH = ROOT / "reports" / "provider_discovery" / "provider_raw_download_status.md"
MANUAL_AUDIO_REGISTRY = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"

DOWNLOAD_LOG_FIELDS = [
    "provider",
    "case_id",
    "ticker",
    "asset_type",
    "attempted",
    "download_status",
    "blocked_reason",
    "local_path",
    "sha256",
    "bytes",
    "commit_allowed",
    "training_allowed",
    "raw_provider_committed",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _append_unique(path: Path, rows: list[dict[str, str]], fields: list[str], key_fields: tuple[str, ...]) -> None:
    existing = read_csv(path)
    by_key = {tuple(row.get(field, "") for field in key_fields): row for row in existing}
    for row in rows:
        by_key[tuple(row.get(field, "") for field in key_fields)] = row
    write_csv(path, [by_key[key] for key in sorted(by_key)], fields)


def _target_path(root: Path, row: dict[str, str]) -> Path:
    suffix = ".txt" if row.get("asset_type") == "transcript" else ".mp3"
    return root / row.get("case_id", "unknown") / f"{row.get('case_id', 'unknown')}_{row.get('asset_type', 'asset')}{suffix}"


def download_provider_assets(
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    assets_in: Path = ASSETS_IN,
    workspace: Path = DESKTOP_WORKSPACE,
    audit_dir: Path = AUDIT_DIR,
) -> dict[str, Any]:
    providers = load_provider_registry(registry_path)
    config = providers.get("earningscall")
    if config is None:
        raise SystemExit("earningscall provider missing from registry")
    adapter = EarningsCallAdapter(config)
    root = Path(config.raw_storage_root or workspace / "provider_raw" / "earningscall")
    log_rows: list[dict[str, str]] = []
    transcript_rows: list[dict[str, str]] = []
    audio_rows: list[dict[str, str]] = []
    for row in read_csv(assets_in):
        asset_type = row.get("asset_type", "")
        if asset_type not in {"transcript", "audio"}:
            continue
        target = _target_path(root, row)
        errors = validate_raw_pull(config, target, workspace=workspace, asset_type=asset_type)
        log = {
            "provider": "earningscall",
            "case_id": row.get("case_id", ""),
            "ticker": row.get("ticker", ""),
            "asset_type": asset_type,
            "attempted": "false",
            "download_status": "blocked",
            "blocked_reason": ";".join(errors) if errors else "",
            "local_path": "",
            "sha256": "",
            "bytes": "0",
            "commit_allowed": "false",
            "training_allowed": "false",
            "raw_provider_committed": "false",
        }
        if errors:
            log_rows.append(log)
            continue
        url = row.get("provider_url", "")
        result = (
            adapter.download_transcript_if_allowed(row, url=url, output_path=target)
            if asset_type == "transcript"
            else adapter.download_audio_if_allowed(row, url=url, output_path=target)
        )
        log["attempted"] = "true"
        log["download_status"] = result.get("status", "BLOCKED")
        log["blocked_reason"] = ";".join(result.get("errors", []))
        if result.get("raw_written"):
            local_path = Path(result["local_path"])
            digest = file_sha256(local_path)
            provenance = local_path.with_suffix(local_path.suffix + ".provenance.json")
            write_json(
                provenance,
                {
                    "provider": "earningscall",
                    "case_id": row.get("case_id", ""),
                    "asset_type": asset_type,
                    "local_path": str(local_path),
                    "sha256": digest,
                    "commit_allowed": False,
                    "training_allowed": False,
                    "raw_provider_committed": False,
                },
            )
            log.update({"local_path": str(local_path), "sha256": digest, "bytes": str(result.get("bytes", 0))})
            registry_row = {
                "case_id": row.get("case_id", ""),
                "ticker": row.get("ticker", ""),
                "company_name": "",
                "asset_type": asset_type,
                "local_path": str(local_path),
                "sha256": digest,
                "source_url": row.get("provider_url", ""),
                "provenance_path": str(provenance),
                "rights_status": "provider_license_guarded",
                "eval_allowed": "true",
                "commit_allowed": "false",
                "training_allowed": "false",
                "approval_ref": config.license_config_ref,
                "registered_timestamp": now_iso(),
                "notes": "Registered from EarningsCall provider raw under Desktop-only storage.",
            }
            if asset_type == "transcript":
                transcript_rows.append(registry_row)
            else:
                audio_rows.append(registry_row)
        log_rows.append(log)
    if transcript_rows:
        _append_unique(MANUAL_TRANSCRIPT_REGISTRY_PATH, transcript_rows, MANUAL_TRANSCRIPT_REGISTRY_FIELDS, ("case_id", "asset_type"))
    if audio_rows:
        _append_unique(MANUAL_AUDIO_REGISTRY, audio_rows, MANUAL_AUDIO_FIELDS, ("case_id", "asset_type"))
    audit_dir.mkdir(parents=True, exist_ok=True)
    write_csv(audit_dir / "provider_raw_download_log.csv", log_rows, DOWNLOAD_LOG_FIELDS)
    summary = {
        "asset_rows": len(log_rows),
        "download_attempts": sum(1 for row in log_rows if row["attempted"] == "true"),
        "download_succeeded": sum(1 for row in log_rows if row["download_status"] == "DOWNLOADED_DESKTOP_ONLY"),
        "blocked_rows": sum(1 for row in log_rows if row["download_status"] == "blocked"),
        "registered_transcripts": len(transcript_rows),
        "registered_audio": len(audio_rows),
        "raw_provider_committed": False,
        "desktop_audit": str(audit_dir / "provider_raw_download_log.csv"),
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Provider Raw Download Status",
        "",
        f"- Asset rows checked: {summary['asset_rows']}",
        f"- Download attempts: {summary['download_attempts']}",
        f"- Download succeeded: {summary['download_succeeded']}",
        f"- Blocked rows: {summary['blocked_rows']}",
        f"- Registered transcripts: {summary['registered_transcripts']}",
        f"- Registered audio: {summary['registered_audio']}",
        "- Raw provider committed: false",
        f"- Desktop audit: `{summary['desktop_audit']}`",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download provider raw assets only when guarded license config permits it.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--assets", type=Path, default=ASSETS_IN)
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    args = parser.parse_args(argv)
    print(json.dumps(download_provider_assets(registry_path=args.registry, assets_in=args.assets, workspace=args.workspace, audit_dir=args.audit_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
