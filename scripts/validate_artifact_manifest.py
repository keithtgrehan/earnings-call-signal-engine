#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.artifacts.manifest import validate_artifact_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate artifact manifest contract.")
    parser.add_argument("--path", default="reports/gold_label_audit/artifact_manifest.json")
    args = parser.parse_args(argv)
    path = Path(args.path)
    if not path.exists():
        print(f"Artifact manifest NOT_READY: {path} is missing.")
        return 0
    errors = validate_artifact_manifest(json.loads(path.read_text(encoding="utf-8")))
    if errors:
        print(f"Artifact manifest validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Artifact manifest validation passed: {path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
