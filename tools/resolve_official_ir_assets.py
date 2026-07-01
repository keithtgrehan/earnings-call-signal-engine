#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import urllib.robotparser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import RESOLVED_ASSET_FIELDS, read_csv, resolve_official_ir_rows, write_csv, write_resolution_report
from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE

DEFAULT_QUEUE = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_resolved_asset_candidates.csv"
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "official_ir_asset_resolution.md"


class RobotsCache:
    def __init__(self) -> None:
        self.cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    def allowed(self, url: str) -> bool:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        if not parsed.scheme or not parsed.netloc:
            return False
        parser = self.cache.get(root)
        if parser is None:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(root + "/robots.txt")
            previous_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                parser.read()
            except Exception:
                return True
            finally:
                socket.setdefaulttimeout(previous_timeout)
            self.cache[root] = parser
        return parser.can_fetch("SignalEngine/2.0 asset resolver", url)


def run(queue: Path, out: Path, report: Path, workspace: Path, *, max_pages: int | None = None) -> dict[str, int]:
    rows = [row for row in read_csv(queue) if (row.get("source_type") == "official_ir" or "ir" in row.get("source_type", ""))]
    robots = RobotsCache()
    candidates = resolve_official_ir_rows(rows, robots_allowed=robots.allowed, per_domain_delay_sec=0.25, max_pages=max_pages)
    write_csv(out, candidates, RESOLVED_ASSET_FIELDS)
    write_csv(workspace / "_audit" / "resolved_asset_candidates.csv", candidates, RESOLVED_ASSET_FIELDS)
    write_resolution_report(report, candidates)
    return {"input_rows": len(rows), "candidate_rows": len(candidates)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve official IR landing pages to direct transcript/audio candidates.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--max-pages", type=int)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.queue, args.out, args.report, args.workspace, max_pages=args.max_pages), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
