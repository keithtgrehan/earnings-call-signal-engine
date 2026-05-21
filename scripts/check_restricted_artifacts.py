#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from resource_registry_common import (
    coerce_bool,
    looks_like_restricted_artifact,
    normalize_resource_rows,
    read_structured,
)


def _staged_paths(cwd: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _load_registry(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return normalize_resource_rows(read_structured(path))


def _allowed_by_registry(path: str, registry_rows: list[dict[str, Any]]) -> bool:
    normalized = path.replace("\\", "/")
    for row in registry_rows:
        source_path = str(row.get("source_url_or_path", "")).replace("\\", "/")
        if not source_path:
            continue
        if normalized == source_path or normalized.endswith(source_path) or source_path.endswith(normalized):
            return coerce_bool(row.get("allowed_commit")) is True and coerce_bool(row.get("raw_body_allowed")) is True
    return False


def find_restricted_artifacts(paths: list[str], registry_rows: list[dict[str, Any]]) -> list[str]:
    flagged: list[str] = []
    for path in paths:
        if looks_like_restricted_artifact(path) and not _allowed_by_registry(path, registry_rows):
            flagged.append(path)
    return flagged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail closed when restricted raw transcript/audio/video artifacts are staged or listed.")
    parser.add_argument("paths", nargs="*", help="Paths to check. If omitted, --staged is assumed.")
    parser.add_argument("--staged", action="store_true", help="Check staged git paths.")
    parser.add_argument("--dry-run", action="store_true", help="Check staged paths without any mutation. This is the default behavior.")
    parser.add_argument("--registry", help="Optional resource registry YAML/JSON with explicit raw commit permission.")
    parser.add_argument("--cwd", default=".")
    args = parser.parse_args(argv)

    cwd = Path(args.cwd)
    paths = args.paths
    if args.staged or args.dry_run or not paths:
        paths = _staged_paths(cwd)
    registry_rows = _load_registry(Path(args.registry)) if args.registry else []
    flagged = find_restricted_artifacts(paths, registry_rows)
    if flagged:
        print("Restricted raw artifacts require explicit provenance-backed commit permission:", file=sys.stderr)
        for path in flagged:
            print(f"- {path}", file=sys.stderr)
        return 1
    print(f"Restricted artifact check passed: {len(paths)} path(s) checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
