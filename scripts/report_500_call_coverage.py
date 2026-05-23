#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import _load_targets, write_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report metadata-only 500-call coverage.")
    parser.add_argument("--targets", default="data/corpus/nyse_5y_target_universe.example.yml")
    parser.add_argument("--out", default="reports/agent5/500_call_coverage.md")
    args = parser.parse_args(argv)
    rows = _load_targets(Path(args.targets))
    write_markdown(Path(args.out), "500 Call Coverage", [f"- Metadata target slots: `{len(rows)}`", "- Coverage is readiness mapping only.", "- Transcript availability and rights clearance remain manual blockers."])
    print(f"500-call coverage report written for {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
