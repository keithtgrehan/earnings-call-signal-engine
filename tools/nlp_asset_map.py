#!/usr/bin/env python
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.nlp_assets.lookup import (
    filter_by_category,
    filter_by_download_status,
    filter_by_priority,
    find_by_signal_engine_area,
)
from signal_engine.nlp_assets.registry import VALID_CATEGORIES, load_assets


def _print_assets(assets: list[dict[str, Any]]) -> None:
    for asset in assets:
        print(f"{asset['id']}\t{asset['name']}\t{asset['category']}\t{asset['download_status']}\t{asset['priority']}")
        print(f"  source: {asset['source_url']}")
        print(f"  use: {', '.join(asset['intended_use'])}")
        print(f"  risk: {asset['limitations'][0]}")


def _validate() -> None:
    subprocess.run([sys.executable, "tools/nlp_assets/validate_assets.py"], cwd=ROOT, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explore Signal Engine NLP assets and dataset/tool readiness.")
    parser.add_argument("--list", action="store_true", help="List all registry assets.")
    parser.add_argument("--category", choices=sorted(VALID_CATEGORIES), help="Filter by category.")
    parser.add_argument("--downloaded", action="store_true", help="Show downloaded safe-cache assets.")
    parser.add_argument("--manual-required", action="store_true", help="Show manual-required or gated assets.")
    parser.add_argument("--signal-engine-area", help="Find assets relevant to a Signal Engine area.")
    parser.add_argument("--priority", choices=["high", "medium", "low"], help="Filter by priority.")
    parser.add_argument("--validate", action="store_true", help="Run registry validation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [
        args.list,
        bool(args.category),
        args.downloaded,
        args.manual_required,
        bool(args.signal_engine_area),
        bool(args.priority),
        args.validate,
    ]
    if sum(selected) != 1:
        parser.error("Choose exactly one action.")

    if args.list:
        _print_assets(load_assets())
    elif args.category:
        _print_assets(filter_by_category(args.category))
    elif args.downloaded:
        _print_assets(filter_by_download_status("downloaded"))
    elif args.manual_required:
        assets = filter_by_download_status("manual_required") + filter_by_download_status("gated")
        _print_assets(assets)
    elif args.signal_engine_area:
        _print_assets(find_by_signal_engine_area(args.signal_engine_area))
    elif args.priority:
        _print_assets(filter_by_priority(args.priority))
    elif args.validate:
        _validate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
