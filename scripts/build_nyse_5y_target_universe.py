#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import build_nyse_5y_universe, write_markdown, write_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build metadata-only NYSE five-year target universe.")
    parser.add_argument("--out", default="data/corpus/nyse_5y_target_universe.example.yml")
    parser.add_argument("--report", default="reports/agent5/nyse_5y_target_universe.md")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args(argv)
    rows = build_nyse_5y_universe(limit=args.limit)
    write_yaml(Path(args.out), "targets", rows)
    write_markdown(
        Path(args.report),
        "NYSE 5Y Target Universe",
        [
            "Metadata-only target slots; rows are not proof of transcript availability.",
            "",
            f"- Rows: `{len(rows)}`",
            "- Exchange: `NYSE`",
            "- Raw transcript/audio/video/slides ingest: `blocked by default`",
        ],
    )
    print(f"NYSE 5Y target universe written: {len(rows)} metadata-only row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
