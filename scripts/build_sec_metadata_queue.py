#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import _load_targets, build_sec_metadata_queue, write_markdown, write_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build SEC/EDGAR metadata-only queue; no filing bodies are downloaded.")
    parser.add_argument("--targets", default="data/corpus/nyse_5y_target_universe.example.yml")
    parser.add_argument("--out", default="data/corpus/sec_metadata_queue.yml")
    parser.add_argument("--report", default="reports/agent5/sec_metadata_queue.md")
    args = parser.parse_args(argv)
    rows = build_sec_metadata_queue(_load_targets(Path(args.targets)))
    write_yaml(Path(args.out), "queue", rows)
    write_markdown(Path(args.report), "SEC Metadata Queue", [f"- Rows: `{len(rows)}`", "- Raw filing body downloads: `false`", "- Fair access rate limit metadata: `10 rps max`"])
    print(f"SEC metadata queue written: {len(rows)} metadata-only row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
