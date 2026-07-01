#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import _load_targets, build_webcast_metadata_queue, write_markdown, write_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build webcast/YouTube metadata-only queue.")
    parser.add_argument("--targets", default="data/corpus/nyse_5y_target_universe.example.yml")
    parser.add_argument("--out", default="data/corpus/webcast_metadata_queue.yml")
    parser.add_argument("--report", default="reports/agent5/webcast_metadata_queue.md")
    args = parser.parse_args(argv)
    rows = build_webcast_metadata_queue(_load_targets(Path(args.targets)))
    write_yaml(Path(args.out), "queue", rows)
    write_markdown(Path(args.report), "Webcast Metadata Queue", [f"- Rows: `{len(rows)}`", "- YouTube/webcast raw media: `blocked without authorization`", "- Transcript download: `blocked without authorization`"])
    print(f"Webcast metadata queue written: {len(rows)} metadata-only row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
