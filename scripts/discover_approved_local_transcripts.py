#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Iterable

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


def existing_default_search_dirs() -> list[Path]:
    dirs: list[Path] = []
    for path in APPROVED_DIRS:
        expanded = path.expanduser()
        if expanded.exists():
            dirs.append(expanded)
    transcript_dir = APPROVED_DIRS[0].expanduser()
    parent_dir = APPROVED_DIRS[1].expanduser()
    if transcript_dir in dirs and parent_dir in dirs:
        dirs.remove(parent_dir)
    return dirs


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_report(path: Path, rows: list[dict[str, object]], search_dirs: Iterable[Path]) -> None:
    counts = Counter(str(row.get("status", "unknown")) for row in rows)
    rights_counts = Counter(str(row.get("rights_status", "unknown")) for row in rows)
    lines = [
        "# Manual-Local Transcript Discovery",
        "",
        f"- Metadata rows: `{len(rows)}`",
        f"- Candidate rows: `{counts.get('candidate_metadata_only', 0)}`",
        f"- Blocked rows: `{sum(count for status, count in counts.items() if status.startswith('blocked'))}`",
        f"- Unknown-rights rows: `{rights_counts.get('unknown', 0)}`",
        "- Files copied: `0`",
        "- Bodies parsed: `false`",
        "- OCR PDFs: `false`",
        "",
        "## Search Directories",
        "",
    ]
    lines.extend(f"- `{path}`" for path in search_dirs)
    lines.extend(["", "## Next Manual Action", "", "Fill the manual-local batch candidate CSV with source URL and rights context before registration."])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def discover_approved_transcripts(
    *,
    search_dirs: Iterable[Path],
    approved_dirs: Iterable[Path],
    out_path: Path,
    report_path: Path,
    max_depth: int = 6,
    max_files: int = 1000,
) -> list[dict[str, object]]:
    rows = discover_manual_local_paths(
        search_dirs=[Path(path).expanduser() for path in search_dirs],
        approved_dirs=[Path(path).expanduser() for path in approved_dirs],
        allowed_extensions={".txt", ".md", ".pdf"},
        source_kind="transcript",
        max_depth=max_depth,
        max_files=max_files,
    )
    _write_jsonl(out_path, rows)
    _write_report(report_path, rows, search_dirs)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover approved manual-local transcript path/hash metadata only.")
    parser.add_argument("--search-dir", action="append", dest="search_dirs")
    parser.add_argument("--approved-dir", action="append", dest="approved_dirs")
    parser.add_argument("--out", default="data/review/staging/manual_local_discovery_candidates.jsonl")
    parser.add_argument("--report", default="reports/manual_local_transcript_discovery.md")
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--max-files", type=int, default=1000)
    args = parser.parse_args(argv)
    search_dirs = [Path(path) for path in args.search_dirs] if args.search_dirs else existing_default_search_dirs()
    approved_dirs = [Path(path) for path in args.approved_dirs] if args.approved_dirs else APPROVED_DIRS
    rows = discover_approved_transcripts(
        search_dirs=search_dirs,
        approved_dirs=approved_dirs,
        out_path=Path(args.out),
        report_path=Path(args.report),
        max_depth=args.max_depth,
        max_files=args.max_files,
    )
    print(f"Approved manual-local transcript discovery wrote {len(rows)} metadata row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
