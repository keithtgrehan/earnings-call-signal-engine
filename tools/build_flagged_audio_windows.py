#!/usr/bin/env python3
"""Build an empty/safe flagged-audio-window readiness manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import read_csv, write_csv

FIELDS = ["case_id", "audio_sha256", "start_time_sec", "end_time_sec", "reason", "label_type", "emotion_label", "stress_label", "deception_label"]
REPORT_PATH = ROOT / "reports" / "acquisition" / "flagged_audio_windows_readiness.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build flagged audio review-window readiness manifest.")
    parser.add_argument("--registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_audio_registry.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "acquisition" / "flagged_audio_windows_manifest.csv")
    args = parser.parse_args(argv)
    rows = read_csv(args.registry)
    write_csv(args.out, [], FIELDS)
    summary = {"audio_rows": len(rows), "flagged_windows": 0, "out": str(args.out), "neutral_metadata_only": True}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Flagged Audio Windows Readiness\n\n"
        f"- Audio rows: {summary['audio_rows']}\n"
        "- Flagged windows: 0\n"
        "- Label scope: neutral review windows only\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
