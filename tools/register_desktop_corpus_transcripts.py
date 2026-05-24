#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import register_manual_local_transcripts


def main() -> None:
    parser = argparse.ArgumentParser(description="Register Desktop transcript files by path and sha256 only.")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = register_manual_local_transcripts(args.workspace, out_path=args.out)
    report = Path("reports/acquisition/manual_local_registration_status.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Manual-Local Registration Status\n\n"
        f"- Registered transcripts: {len(rows)}\n"
        "- Raw transcript text copied into git: 0\n",
        encoding="utf-8",
    )
    print({"registered": len(rows), "out": str(args.out)})


if __name__ == "__main__":
    main()
