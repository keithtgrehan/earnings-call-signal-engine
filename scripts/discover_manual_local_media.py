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

from signal_engine.manual_local_discovery import discover_manual_local_paths

APPROVED_DIRS = [
    Path("/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/audio/"),
    Path("/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/video/"),
    Path("/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/media/"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover manual-local audio/video path/hash metadata only.")
    parser.add_argument("--out", default="data/review/staging/manual_local_media_candidates.jsonl")
    parser.add_argument("--report", default="reports/manual_local_media_discovery.md")
    args = parser.parse_args(argv)
    rows = discover_manual_local_paths(search_dirs=APPROVED_DIRS, approved_dirs=APPROVED_DIRS, allowed_extensions={".mp3", ".mp4", ".wav", ".m4a", ".mov"}, source_kind="media")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            row = {**row, "event_window_todo": "create transcript-aligned sparse event window if later registered"}
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f"# Manual-Local Media Discovery\n\n- Metadata rows: `{len(rows)}`\n- Files copied: `0`\n- ASR run: `false`\n- Video processing: `false`\n- YouTube downloads: `false`\n", encoding="utf-8")
    print(f"Manual-local media discovery wrote {len(rows)} metadata row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
