#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import build_desktop_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local text chunks only for rights-cleared Desktop transcripts.")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()
    rows = build_desktop_chunks(args.workspace, registry_path=args.registry)
    print({"chunks": len(rows)})


if __name__ == "__main__":
    main()
