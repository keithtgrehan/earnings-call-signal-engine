#!/usr/bin/env python3
"""Validate a retrieval bakeoff manifest without running providers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval.bakeoff import load_bakeoff_manifest  # noqa: E402

DEFAULT_MANIFEST = ROOT / "configs" / "retrieval_bakeoff.example.yml"


def validate_manifest(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, object]:
    manifest = load_bakeoff_manifest(manifest_path if manifest_path.is_absolute() else ROOT / manifest_path, root=ROOT)
    payload = manifest.payload
    return {
        "status_label": payload["status_label"],
        "bakeoff_id": payload["bakeoff_id"],
        "manifest_path": str(manifest_path),
        "provider_slots": payload["provider_slots"],
        "metrics_planned": payload["metrics_planned"],
        "reviewed_query_set_path": payload["reviewed_query_set"]["path"],
        "reviewed_query_set": payload["reviewed_query_set"]["reviewed"],
        "smoke_only": payload["reviewed_query_set"]["smoke_only"],
        "network_allowed": payload["network_allowed"],
        "benchmark_complete": False,
        "evaluated_retrieval_quality": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a retrieval bakeoff manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        summary = validate_manifest(args.manifest)
    except Exception as exc:
        print(f"Retrieval bakeoff manifest validation blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
