#!/usr/bin/env python3
"""Run EarningsCall provider readiness/discovery over first30 cases."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.first30_transcript_common import AUDIT_DIR, FIRST30_INGESTION_MANIFEST_PATH, read_csv, write_csv  # noqa: E402
from tools.providers.base import DEFAULT_REGISTRY, DESKTOP_WORKSPACE, load_provider_registry  # noqa: E402
from tools.providers.earningscall_adapter import EarningsCallAdapter  # noqa: E402

ASSETS_OUT = ROOT / "reports" / "provider_discovery" / "earningscall_assets.csv"
GAPS_OUT = ROOT / "reports" / "provider_discovery" / "earningscall_asset_gaps.csv"
STATUS_MD = ROOT / "reports" / "provider_discovery" / "earningscall_provider_status.md"
PREFLIGHT_MD = ROOT / "reports" / "provider_discovery" / "earningscall_provider_preflight.md"
PROVIDER_CANDIDATES = ROOT / "data" / "acquisition" / "provider_first30_asset_candidates.csv"
AUDIO_GAPS = ROOT / "data" / "acquisition" / "first30_audio_candidates.csv"

ASSET_FIELDS = [
    "provider",
    "case_id",
    "ticker",
    "fiscal_year",
    "fiscal_quarter",
    "asset_type",
    "metadata_status",
    "download_status",
    "raw_download_allowed",
    "license_config_ref",
    "training_allowed",
    "provider_url",
    "raw_storage_root",
    "notes",
]

GAP_FIELDS = ["case_id", "ticker", "transcript_status", "audio_status", "next_action"]


def _first30_rows(path: Path) -> list[dict[str, str]]:
    return [row for row in read_csv(path) if row.get("control_fixture") != "true"]


def _candidate_rows(asset_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "provider": row["provider"],
            "case_id": row["case_id"],
            "ticker": row["ticker"],
            "fiscal_year": row["fiscal_year"],
            "fiscal_quarter": row["fiscal_quarter"],
            "asset_type": row["asset_type"],
            "metadata_discovery_status": row["metadata_status"],
            "raw_download_allowed": row["raw_download_allowed"],
            "license_config_ref": row["license_config_ref"],
            "training_allowed": row["training_allowed"],
            "candidate_status": "raw_allowed" if row["raw_download_allowed"] else ("not_configured" if row["metadata_status"] == "NOT_CONFIGURED" else "metadata_only"),
            "notes": row["notes"],
        }
        for row in asset_rows
    ]


def _write_status_reports(
    *,
    status: dict[str, Any],
    summary: dict[str, Any],
    gaps: list[dict[str, Any]],
    audio_gap_rows: list[dict[str, str]],
) -> None:
    STATUS_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# EarningsCall Provider Status",
        "",
        f"- Provider status: `{status['status']}`",
        f"- API key env: `{status['api_key_env']}`",
        f"- API key configured: {str(status['api_key_configured']).lower()}",
        f"- SDK status: `{status['sdk_status']}`",
        f"- REST fallback configured: {str(status['rest_fallback_configured']).lower()}",
        f"- license_config_ref: `{status['license_config_ref'] or 'missing'}`",
        f"- raw_download_allowed: {str(status['raw_download_allowed']).lower()}",
        f"- raw_transcript_download_allowed: {str(status['raw_transcript_download_allowed']).lower()}",
        f"- raw_audio_download_allowed: {str(status['raw_audio_download_allowed']).lower()}",
        f"- raw_storage_root: `{status['raw_storage_root'] or 'missing'}`",
        f"- raw_storage_desktop_only: {str(status['raw_storage_desktop_only']).lower()}",
        f"- training_allowed: {str(status['training_allowed']).lower()}",
        "",
        "## Discovery Summary",
        "",
        f"- First30 cases checked: {summary['cases']}",
        f"- Asset rows: {summary['asset_rows']}",
        f"- Raw downloads attempted: false",
        f"- Raw provider data committed: false",
    ]
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    blockers = Counter(row["next_action"] for row in gaps)
    preflight = [
        "# EarningsCall Provider Preflight",
        "",
        f"- Key present: {str(status['api_key_configured']).lower()}",
        f"- license_config_ref present: {str(bool(status['license_config_ref'])).lower()}",
        f"- raw_download_allowed: {str(status['raw_download_allowed']).lower()}",
        f"- transcript raw allowed: {str(status['raw_transcript_download_allowed']).lower()}",
        f"- audio raw allowed: {str(status['raw_audio_download_allowed']).lower()}",
        f"- local storage path: `{status['raw_storage_root'] or DESKTOP_WORKSPACE / 'provider_raw' / 'earningscall'}`",
        f"- training rights: {str(status['training_allowed']).lower()}",
        f"- first30 audio gap rows: {len(audio_gap_rows)}",
        "- VZ/CRM vendor-marker status: still blocked unless clean source or reviewed provider license exists",
        "",
        "## Exact Blockers",
        "",
    ]
    for reason, count in sorted(blockers.items()):
        preflight.append(f"- `{reason}`: {count}")
    PREFLIGHT_MD.write_text("\n".join(preflight) + "\n", encoding="utf-8")


def earningscall_first30_discovery(
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    manifest_path: Path = FIRST30_INGESTION_MANIFEST_PATH,
    assets_out: Path = ASSETS_OUT,
    gaps_out: Path = GAPS_OUT,
    provider_candidates_out: Path = PROVIDER_CANDIDATES,
    audit_dir: Path = AUDIT_DIR,
) -> dict[str, Any]:
    providers = load_provider_registry(registry_path)
    config = providers.get("earningscall")
    if config is None:
        raise SystemExit("earningscall provider missing from registry")
    adapter = EarningsCallAdapter(config)
    status = adapter.provider_status()
    cases = _first30_rows(manifest_path)
    asset_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    for case in cases:
        transcript = adapter.get_transcript_metadata(**case)
        audio = adapter.get_audio_metadata(**case)
        asset_rows.extend([transcript, audio])
        if status["status"] == "NOT_CONFIGURED":
            next_action = "set_EARNINGSCALL_API_KEY_and_license_config_ref"
        elif transcript["metadata_status"] == "SDK_MISSING" or audio["metadata_status"] == "SDK_MISSING":
            next_action = "install_optional_sdk_or_configure_reviewed_rest_templates"
        elif not config.license_config_ref:
            next_action = "metadata_only_add_license_config_ref_before_raw_pull"
        elif not config.raw_download_allowed:
            next_action = "metadata_only_enable_raw_download_allowed_only_if_license_permits"
        else:
            next_action = "raw_download_ready_if_asset_urls_resolve"
        gap_rows.append(
            {
                "case_id": case.get("case_id", ""),
                "ticker": case.get("ticker", ""),
                "transcript_status": transcript.get("metadata_status", ""),
                "audio_status": audio.get("metadata_status", ""),
                "next_action": next_action,
            }
        )
    write_csv(assets_out, asset_rows, ASSET_FIELDS)
    write_csv(gaps_out, gap_rows, GAP_FIELDS)
    write_csv(provider_candidates_out, _candidate_rows(asset_rows), [
        "provider",
        "case_id",
        "ticker",
        "fiscal_year",
        "fiscal_quarter",
        "asset_type",
        "metadata_discovery_status",
        "raw_download_allowed",
        "license_config_ref",
        "training_allowed",
        "candidate_status",
        "notes",
    ])
    write_csv(audit_dir / "earningscall_assets.csv", asset_rows, ASSET_FIELDS)
    audio_gap_rows = read_csv(AUDIO_GAPS)
    summary = {
        "provider_status": status["status"],
        "api_key_configured": status["api_key_configured"],
        "license_config_ref": status["license_config_ref"],
        "raw_download_allowed": status["raw_download_allowed"],
        "cases": len(cases),
        "asset_rows": len(asset_rows),
        "gap_rows": len(gap_rows),
        "raw_provider_pull_attempted": False,
        "assets_out": str(assets_out),
        "gaps_out": str(gaps_out),
        "provider_candidates_out": str(provider_candidates_out),
    }
    _write_status_reports(status=status, summary=summary, gaps=gap_rows, audio_gap_rows=audio_gap_rows)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run EarningsCall first30 provider discovery with fail-closed raw guards.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--assets-out", type=Path, default=ASSETS_OUT)
    parser.add_argument("--gaps-out", type=Path, default=GAPS_OUT)
    parser.add_argument("--provider-candidates-out", type=Path, default=PROVIDER_CANDIDATES)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    parser.add_argument("--status-only", action="store_true", help="Write the same fail-closed status reports without attempting raw downloads.")
    args = parser.parse_args(argv)
    print(json.dumps(earningscall_first30_discovery(registry_path=args.registry, manifest_path=args.manifest, assets_out=args.assets_out, gaps_out=args.gaps_out, provider_candidates_out=args.provider_candidates_out, audit_dir=args.audit_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
