#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import _load_targets, build_official_ir_candidate_map, write_markdown, write_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build official IR candidate URL map without network access.")
    parser.add_argument("--targets", default="data/corpus/nyse_5y_target_universe.example.yml")
    parser.add_argument("--out", default="data/corpus/official_ir_candidate_map.yml")
    parser.add_argument("--report", default="reports/agent5/official_ir_candidate_map.md")
    args = parser.parse_args(argv)
    rows = build_official_ir_candidate_map(_load_targets(Path(args.targets)))
    write_yaml(Path(args.out), "candidates", rows)
    write_markdown(Path(args.report), "Official IR Candidate Map", [f"- Candidate placeholders: `{len(rows)}`", "- Network access: `not used`", "- Raw flags: `false until terms/robots/source review`"])
    print(f"Official IR candidate map written: {len(rows)} metadata-only candidate(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
