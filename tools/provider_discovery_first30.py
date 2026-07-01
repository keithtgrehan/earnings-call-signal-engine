#!/usr/bin/env python3
"""Build first30 provider discovery readiness manifests."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.providers.aiera_adapter import AieraAdapter  # noqa: E402
from tools.providers.api_ninjas_adapter import ApiNinjasAdapter  # noqa: E402
from tools.providers.base import DEFAULT_REGISTRY, ProviderAdapter, load_provider_registry  # noqa: E402
from tools.providers.earningscall_adapter import EarningsCallAdapter  # noqa: E402
from tools.providers.fmp_adapter import FmpAdapter  # noqa: E402
from tools.providers.quartr_adapter import QuartrAdapter  # noqa: E402
from tools.providers.sec_edgar_adapter import SecEdgarAdapter  # noqa: E402

DEFAULT_CANDIDATES = ROOT / "data" / "acquisition" / "transcript_candidates_first30.csv"
DEFAULT_ASSETS = ROOT / "reports" / "provider_discovery" / "provider_assets.csv"
DEFAULT_GAPS = ROOT / "reports" / "provider_discovery" / "provider_asset_gaps.csv"
DEFAULT_ACQUISITION_CANDIDATES = ROOT / "data" / "acquisition" / "provider_first30_asset_candidates.csv"

ASSET_FIELDS = [
    "provider",
    "case_id",
    "ticker",
    "fiscal_year",
    "fiscal_quarter",
    "asset_type",
    "discovery_status",
    "raw_download_allowed",
    "license_config_ref",
    "training_allowed",
    "notes",
]

GAP_FIELDS = ["case_id", "ticker", "provider_count", "configured_provider_count", "best_status", "next_action"]

ACQUISITION_CANDIDATE_FIELDS = [
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
]

ADAPTERS: dict[str, type[ProviderAdapter]] = {
    "earningscall": EarningsCallAdapter,
    "quartr": QuartrAdapter,
    "aiera": AieraAdapter,
    "fmp": FmpAdapter,
    "api_ninjas": ApiNinjasAdapter,
    "sec_edgar": SecEdgarAdapter,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: str(value).lower() if isinstance(value, bool) else value for key, value in row.items()})


def provider_discovery_first30(
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    candidate_path: Path = DEFAULT_CANDIDATES,
    assets_out: Path = DEFAULT_ASSETS,
    gaps_out: Path = DEFAULT_GAPS,
    acquisition_candidates_out: Path = DEFAULT_ACQUISITION_CANDIDATES,
) -> dict[str, Any]:
    providers = load_provider_registry(registry_path)
    cases = [row for row in read_csv(candidate_path) if row.get("control_fixture") != "true"]
    asset_rows: list[dict[str, Any]] = []
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        for provider_id, config in providers.items():
            adapter_cls = ADAPTERS.get(provider_id, ProviderAdapter)
            adapter = adapter_cls(config)
            metadata = adapter.discover_metadata(case)
            row = {
                "provider": provider_id,
                "case_id": case.get("case_id", ""),
                "ticker": case.get("ticker", ""),
                "fiscal_year": case.get("fiscal_year", ""),
                "fiscal_quarter": case.get("fiscal_quarter", ""),
                "asset_type": metadata.get("asset_type", "transcript_or_audio_metadata"),
                "discovery_status": metadata.get("status", config.status),
                "raw_download_allowed": config.raw_download_allowed,
                "license_config_ref": config.license_config_ref,
                "training_allowed": config.training_allowed,
                "notes": "metadata-only discovery; raw pull blocked unless key/license/raw Desktop guardrails pass",
            }
            asset_rows.append(row)
            by_case[row["case_id"]].append(row)
    gap_rows: list[dict[str, Any]] = []
    for case_id, rows in sorted(by_case.items()):
        configured = [row for row in rows if row["discovery_status"] not in {"NOT_CONFIGURED", "DISABLED"}]
        best_status = configured[0]["discovery_status"] if configured else "NOT_CONFIGURED"
        next_action = (
            "Add provider key and license_config_ref before raw pull"
            if not configured
            else "Use configured provider for metadata discovery; raw pull still requires license_config_ref and raw_download_allowed=true"
        )
        gap_rows.append(
            {
                "case_id": case_id,
                "ticker": rows[0].get("ticker", ""),
                "provider_count": len(rows),
                "configured_provider_count": len(configured),
                "best_status": best_status,
                "next_action": next_action,
            }
        )
    write_csv(assets_out, asset_rows, ASSET_FIELDS)
    write_csv(gaps_out, gap_rows, GAP_FIELDS)
    acquisition_rows = [
        {
            "provider": row["provider"],
            "case_id": row["case_id"],
            "ticker": row["ticker"],
            "fiscal_year": row["fiscal_year"],
            "fiscal_quarter": row["fiscal_quarter"],
            "asset_type": row["asset_type"],
            "metadata_discovery_status": row["discovery_status"],
            "raw_download_allowed": row["raw_download_allowed"],
            "license_config_ref": row["license_config_ref"],
            "training_allowed": row["training_allowed"],
            "candidate_status": "metadata_only" if row["discovery_status"] not in {"NOT_CONFIGURED", "DISABLED"} else "not_configured",
            "notes": "Provider raw pull is blocked unless key, license_config_ref, raw_download_allowed, and Desktop-only target are all present.",
        }
        for row in asset_rows
    ]
    write_csv(acquisition_candidates_out, acquisition_rows, ACQUISITION_CANDIDATE_FIELDS)
    return {
        "cases": len(cases),
        "providers": len(providers),
        "asset_rows": len(asset_rows),
        "gap_rows": len(gap_rows),
        "raw_provider_pull_attempted": False,
        "assets_out": str(assets_out),
        "gaps_out": str(gaps_out),
        "acquisition_candidates_out": str(acquisition_candidates_out),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first30 provider discovery readiness manifests.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--assets-out", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--gaps-out", type=Path, default=DEFAULT_GAPS)
    parser.add_argument("--acquisition-candidates-out", type=Path, default=DEFAULT_ACQUISITION_CANDIDATES)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            provider_discovery_first30(
                registry_path=args.registry,
                candidate_path=args.candidates,
                assets_out=args.assets_out,
                gaps_out=args.gaps_out,
                acquisition_candidates_out=args.acquisition_candidates_out,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
