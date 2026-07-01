#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import RESOLVED_ASSET_FIELDS, read_csv, write_csv, write_resolution_report
from signal_engine.providers.api_ninjas_provider import ApiNinjasProvider
from signal_engine.providers.base import BaseProvider, ProviderConfig
from signal_engine.providers.earningscall_provider import EarningsCallProvider
from signal_engine.providers.finnhub_provider import FinnhubProvider
from signal_engine.providers.fmp_provider import FmpProvider
from signal_engine.providers.quartr_provider import QuartrProvider
from signal_engine.providers.sec_edgar_provider import SecEdgarProvider

DEFAULT_TARGETS = ROOT / "data" / "acquisition" / "nyse_100_5y_call_targets.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_provider_resolved_assets.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "provider_ingestion_status.md"


def default_providers() -> list[BaseProvider]:
    return [EarningsCallProvider(), FmpProvider(), ApiNinjasProvider(), FinnhubProvider(), QuartrProvider(), SecEdgarProvider()]


def discover_provider_assets(
    *,
    rows: list[dict[str, str]],
    config: ProviderConfig,
    providers: list[BaseProvider] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, str]] = []
    statuses: dict[str, str] = {}
    messages: dict[str, str] = {}
    for provider in providers or default_providers():
        result = provider.discover_assets(config, rows)
        statuses[result.provider_name] = result.status.value
        messages[result.provider_name] = result.message
        candidates.extend(result.candidates)
    return {"provider_status": statuses, "provider_messages": messages, "candidates": candidates}


def write_provider_report(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Provider Ingestion Status", ""]
    for provider, status in sorted(result["provider_status"].items()):
        lines.append(f"- {provider}: {status} - {result['provider_messages'].get(provider, '')}")
    lines.append("")
    lines.append(f"- Candidate rows: {len(result['candidates'])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run provider asset discovery with fail-closed license handling.")
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--license-config-ref", default="")
    parser.add_argument("--provider-raw-use-allowed", action="store_true")
    args = parser.parse_args(argv)
    config = ProviderConfig(env=dict(os.environ), license_config_ref=args.license_config_ref, provider_raw_use_allowed=args.provider_raw_use_allowed)
    result = discover_provider_assets(rows=read_csv(args.targets), config=config)
    write_csv(args.out, result["candidates"], RESOLVED_ASSET_FIELDS)
    write_provider_report(REPORT_PATH, result)
    print(json.dumps({"candidates": len(result["candidates"]), "provider_status": result["provider_status"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
