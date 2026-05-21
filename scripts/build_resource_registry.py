#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from resource_registry_common import read_structured, stable_provenance_hash, write_json

ROOT = Path(__file__).resolve().parents[1]


def _resources_from_config(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("resources"), list):
        raise ValueError("Config must be a YAML/JSON object with a resources list.")
    resources: list[dict[str, Any]] = []
    for raw in payload["resources"]:
        if not isinstance(raw, dict):
            raise ValueError("Every resource config entry must be an object.")
        record = dict(raw)
        if not str(record.get("provenance_hash", "")).strip() or record.get("provenance_hash") == "auto":
            record["provenance_hash"] = stable_provenance_hash(record)
        resources.append(record)
    return resources


def build_registry(config_path: Path) -> dict[str, Any]:
    payload = read_structured(config_path)
    return {
        "registry_version": "resource_registry_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_config": str(config_path),
        "network_access_performed": False,
        "resources": _resources_from_config(payload),
        "notes": [
            "Starter registry only; no raw data was downloaded.",
            "Raw-body storage remains blocked unless terms and provenance explicitly allow it.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a starter rights/resource registry without downloading raw data.")
    parser.add_argument("--config", default=str(ROOT / "configs" / "resource_registry.example.yml"))
    parser.add_argument("--out", default=str(ROOT / "data" / "corpus" / "resource_registry.example.json"))
    args = parser.parse_args(argv)

    registry = build_registry(Path(args.config))
    write_json(Path(args.out), registry)
    print(f"Wrote {len(registry['resources'])} resource record(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
