#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import _load_targets, build_slides_availability_map, write_markdown, write_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build official IR slides availability map without PDF downloads.")
    parser.add_argument("--targets", default="data/corpus/nyse_5y_target_universe.example.yml")
    parser.add_argument("--out", default="data/corpus/slides_availability_map.yml")
    parser.add_argument("--report", default="reports/agent5/slides_availability_matrix.md")
    args = parser.parse_args(argv)
    rows = build_slides_availability_map(_load_targets(Path(args.targets)))
    write_yaml(Path(args.out), "slides", rows)
    write_markdown(Path(args.report), "Slides Availability Matrix", [f"- Rows: `{len(rows)}`", "- PDF download attempted: `false`", "- Raw slide ingest: `blocked until terms permit`"])
    print(f"Slides availability map written: {len(rows)} metadata-only row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
