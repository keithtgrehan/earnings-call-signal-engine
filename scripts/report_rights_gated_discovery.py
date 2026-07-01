#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from agent5_rights_gated_builders import _load_targets, summarize_blocked, write_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write rights-gated discovery summary reports.")
    parser.add_argument("--targets", default="data/corpus/nyse_5y_target_universe.example.yml")
    args = parser.parse_args(argv)
    rows = _load_targets(Path(args.targets))
    write_markdown(Path("reports/agent5/rights_gated_discovery_summary.md"), "Rights-Gated Discovery Summary", [f"- Metadata target rows: `{len(rows)}`", "- Unknown rights fail closed.", "- No raw transcript/audio/video/slides content was downloaded."])
    write_markdown(Path("reports/agent5/blocked_cases_by_reason.md"), "Blocked Cases By Reason", summarize_blocked(rows))
    write_markdown(Path("reports/agent5/manual_action_queue.md"), "Manual Action Queue", ["- Review source terms and robots for official IR sources.", "- Register manual-local files by path and sha256 only when rights allow.", "- Keep vendor and YouTube raw ingest blocked unless explicit config exists."])
    write_markdown(Path("reports/agent5/asset_availability_summary.md"), "Asset Availability Summary", ["- Transcript/audio/video/slides statuses are metadata-only placeholders.", "- Target rows do not prove availability."])
    print("Rights-gated discovery reports written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
