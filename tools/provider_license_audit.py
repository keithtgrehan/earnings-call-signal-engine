#!/usr/bin/env python3
"""Audit provider registry readiness without pulling raw provider data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.providers.base import DEFAULT_REGISTRY, load_provider_registry  # noqa: E402

REPORT_PATH = ROOT / "reports" / "provider_discovery" / "provider_license_audit.md"


def provider_license_audit(*, registry_path: Path = DEFAULT_REGISTRY, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    providers = load_provider_registry(registry_path)
    rows: list[dict[str, Any]] = []
    for provider_id, config in providers.items():
        rows.append(
            {
                "provider": provider_id,
                "priority": config.priority,
                "status": config.status,
                "api_key_env": config.api_key_env,
                "api_key_configured": config.api_key_configured,
                "metadata_discovery_allowed": config.metadata_discovery_allowed,
                "raw_download_allowed": config.raw_download_allowed,
                "license_config_ref": config.license_config_ref,
                "training_allowed": config.training_allowed,
            }
        )
    summary = {
        "providers": len(rows),
        "not_configured": sum(1 for row in rows if row["status"] == "NOT_CONFIGURED"),
        "raw_enabled": sum(1 for row in rows if row["raw_download_allowed"]),
        "training_allowed": sum(1 for row in rows if row["training_allowed"]),
        "rows": rows,
        "report_path": str(report_path),
    }
    write_report(summary, report_path)
    return summary


def write_report(summary: dict[str, Any], report_path: Path = REPORT_PATH) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Provider License Audit",
        "",
        f"- Providers: {summary['providers']}",
        f"- NOT_CONFIGURED providers: {summary['not_configured']}",
        f"- Raw-enabled providers: {summary['raw_enabled']}",
        f"- Training-allowed providers: {summary['training_allowed']}",
        "- Raw provider pull attempted: false",
        "- Raw provider data committed: false",
        "",
        "## Providers",
        "",
    ]
    for row in summary["rows"]:
        lines.append(
            f"- `{row['provider']}` priority={row['priority']} status=`{row['status']}` "
            f"key_env=`{row['api_key_env'] or 'none'}` raw_download_allowed={str(row['raw_download_allowed']).lower()} "
            f"license_config_ref=`{row['license_config_ref'] or 'missing'}`"
        )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit provider registry/license readiness.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    print(json.dumps(provider_license_audit(registry_path=args.registry, report_path=args.report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
