#!/usr/bin/env python3
"""Report neutral local audio feature readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signal_engine.audio.features import NEUTRAL_FEATURE_NAMES
from tools.user_authorized_ingest_common import read_csv

REPORT_PATH = ROOT / "reports" / "acquisition" / "audio_feature_readiness.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report neutral local audio feature readiness.")
    parser.add_argument("--registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_audio_registry.csv")
    args = parser.parse_args(argv)
    rows = read_csv(args.registry)
    summary = {
        "audio_rows": len(rows),
        "ffmpeg_available": bool(shutil.which("ffmpeg")),
        "ffprobe_available": bool(shutil.which("ffprobe")),
        "neutral_features": sorted(NEUTRAL_FEATURE_NAMES),
        "emotion_deception_stress_labels": False,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Audio Feature Readiness\n\n"
        f"- Audio rows: {summary['audio_rows']}\n"
        f"- ffmpeg available: {str(summary['ffmpeg_available']).lower()}\n"
        f"- ffprobe available: {str(summary['ffprobe_available']).lower()}\n"
        "- Labels generated: neutral metadata only\n"
        "- Emotion/deception/stress/biometric labels: false\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
