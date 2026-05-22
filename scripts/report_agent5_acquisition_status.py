#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from validate_agent5_source_queue import main as validate_source_queue_main
from validate_manual_local_registry import main as validate_manual_registry_main
from validate_nyse_30_pilot import build_summary as build_nyse_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a small Agent 5 acquisition status report.")
    parser.add_argument("--targets", default="configs/nyse_30_pilot_targets.yml")
    parser.add_argument("--out", default="reports/agent5/acquisition_status.md")
    args = parser.parse_args(argv)
    target_summary = build_nyse_summary(Path(args.targets))
    source_status = validate_source_queue_main(["--targets", args.targets])
    registry_status = validate_manual_registry_main([])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(
            [
                "# Agent 5 Acquisition Status",
                "",
                "Status is metadata-only. No raw transcript, audio, video, provider, or vendor content was downloaded.",
                "",
                f"- NYSE 30 target rows: `{target_summary['row_count']}`",
                f"- NYSE 30 target validation: `{target_summary['status']}`",
                f"- Source queue validation exit code: `{source_status}`",
                f"- Manual-local registry validation exit code: `{registry_status}`",
                "- Manual-local files must be registered by path and sha256 hash only.",
                "- Licensed vendor and YouTube raw ingest remain blocked by default.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Agent 5 acquisition status written to {out}.")
    return 0 if target_summary["status"] == "valid" and source_status == 0 and registry_status == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
