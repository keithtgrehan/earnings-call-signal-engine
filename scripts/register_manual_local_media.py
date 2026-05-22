#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from resource_registry_common import read_structured, write_json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.media.registration import build_media_registration, validate_media_registration


def _validate_config(path: Path) -> list[str]:
    payload = read_structured(path)
    rows = payload.get("registrations", []) if isinstance(payload, dict) else []
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for error in validate_media_registration(row):
            errors.append(f"row {index}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register manual-local media metadata without copying media.")
    parser.add_argument("--path")
    parser.add_argument("--media-type", choices=["audio", "video"])
    parser.add_argument("--source-type", default="manual_local")
    parser.add_argument("--rights-tier", default="manual_supplied")
    parser.add_argument("--config", default="configs/media_ingest_policy.example.yml")
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    if args.path:
        row = build_media_registration(
            media_path_ref=args.path,
            media_type=args.media_type or "audio",
            source_type=args.source_type,
            rights_tier=args.rights_tier,
        )
        errors = validate_media_registration(row)
        if args.out:
            write_json(Path(args.out), {"registration": row, "errors": errors})
    else:
        errors = _validate_config(Path(args.config))
    if errors:
        print(f"Media registration validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Media registration dry-run passed; no media was copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
