#!/usr/bin/env python3
"""Create a safe retrieval bakeoff plan without provider execution or metrics."""

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

from signal_engine.retrieval.bakeoff import (  # noqa: E402
    build_bakeoff_plan_summary,
    load_bakeoff_manifest,
    repo_path,
    write_plan_json,
    write_plan_markdown,
)

DEFAULT_MANIFEST = ROOT / "configs" / "retrieval_bakeoff.example.yml"


def plan_retrieval_bakeoff(*, manifest_path: Path = DEFAULT_MANIFEST, dry_run: bool = True) -> dict[str, object]:
    if dry_run is not True:
        raise ValueError("only --dry-run mode is supported; bakeoff execution is not enabled")
    manifest_file = manifest_path if manifest_path.is_absolute() else ROOT / manifest_path
    manifest = load_bakeoff_manifest(manifest_file, root=ROOT)
    summary = build_bakeoff_plan_summary(manifest, root=ROOT)
    outputs = manifest.payload["plan_outputs"]
    write_plan_json(repo_path(Path(str(outputs["json_report"])), root=ROOT), summary)
    write_plan_markdown(repo_path(Path(str(outputs["markdown_report"])), root=ROOT), summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a dry-run retrieval bakeoff plan.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dry-run", action="store_true", help="Required. No providers, embeddings, vector DBs, or metrics are run.")
    args = parser.parse_args(argv)
    try:
        summary = plan_retrieval_bakeoff(manifest_path=args.manifest, dry_run=args.dry_run)
    except Exception as exc:
        print(f"Retrieval bakeoff plan blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
