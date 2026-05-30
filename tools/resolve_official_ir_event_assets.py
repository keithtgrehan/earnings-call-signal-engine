#!/usr/bin/env python3
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

from signal_engine.acquisition.asset_resolver import (  # noqa: E402
    RESOLVED_ASSET_FIELDS,
    read_csv,
    resolve_official_ir_event_rows,
    write_csv,
    write_resolution_report,
)
from tools.resolve_official_ir_assets import RobotsCache  # noqa: E402
from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE  # noqa: E402

DEFAULT_QUEUE = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_resolved_asset_candidates.csv"
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "official_ir_event_asset_resolution.md"


def _dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.get("case_id", ""), row.get("source_url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def run(queue: Path, out: Path, report: Path, workspace: Path, *, max_pages_per_row: int = 3) -> dict[str, int]:
    rows = _dedupe_rows([row for row in read_csv(queue) if row.get("source_type") == "official_ir" or "ir" in row.get("source_type", "")])
    robots = RobotsCache()
    candidates = resolve_official_ir_event_rows(rows, robots_allowed=robots.allowed, per_domain_delay_sec=0.25, max_pages_per_row=max_pages_per_row)
    write_csv(out, candidates, RESOLVED_ASSET_FIELDS)
    write_csv(workspace / "_audit" / "resolved_asset_candidates.csv", candidates, RESOLVED_ASSET_FIELDS)
    write_resolution_report(report, candidates, title="Official IR Event Asset Resolution")
    return {"input_rows": len(rows), "candidate_rows": len(candidates)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve official IR event/archive pages to direct transcript/audio candidates.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--max-pages-per-row", type=int, default=3)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.queue, args.out, args.report, args.workspace, max_pages_per_row=args.max_pages_per_row), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
