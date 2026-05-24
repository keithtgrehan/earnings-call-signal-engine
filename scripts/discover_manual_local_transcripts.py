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
    Path("/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/"),
    Path("/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/"),
    Path("/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/data/corpus/manual_cases/"),
]


def _search_dirs() -> list[Path]:
    transcript_dir = APPROVED_DIRS[0]
    dirs = [transcript_dir] if transcript_dir.exists() else []
    if not dirs and APPROVED_DIRS[1].exists():
        dirs.append(APPROVED_DIRS[1])
    return dirs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover manual-local transcript path/hash metadata only.")
    parser.add_argument("--out", default="data/review/staging/manual_local_discovery_candidates.jsonl")
    parser.add_argument("--report", default="reports/manual_local_transcript_discovery.md")
    args = parser.parse_args(argv)
    rows = discover_manual_local_paths(search_dirs=_search_dirs(), approved_dirs=APPROVED_DIRS, allowed_extensions={".txt", ".md", ".pdf"}, source_kind="transcript")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f"# Manual-Local Transcript Discovery\n\n- Metadata rows: `{len(rows)}`\n- Files copied: `0`\n- Bodies parsed: `false`\n- OCR PDFs: `false`\n", encoding="utf-8")
    print(f"Manual-local transcript discovery wrote {len(rows)} metadata row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
