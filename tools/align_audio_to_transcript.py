#!/usr/bin/env python3
"""Create an audio/transcript alignment readiness report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import read_csv

REPORT_PATH = ROOT / "reports" / "acquisition" / "audio_alignment_readiness.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report audio alignment readiness.")
    parser.add_argument("--audio-registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_audio_registry.csv")
    parser.add_argument("--transcript-registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv")
    args = parser.parse_args(argv)
    audio_rows = read_csv(args.audio_registry)
    transcript_rows = read_csv(args.transcript_registry)
    matched_cases = sorted({row.get("case_id", "") for row in audio_rows}.intersection({row.get("case_id", "") for row in transcript_rows}))
    summary = {"audio_rows": len(audio_rows), "transcript_rows": len(transcript_rows), "alignment_ready_cases": len(matched_cases), "raw_text_committed": False}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Audio Alignment Readiness\n\n"
        f"- Audio rows: {summary['audio_rows']}\n"
        f"- Transcript rows: {summary['transcript_rows']}\n"
        f"- Alignment-ready cases: {summary['alignment_ready_cases']}\n"
        "- Raw transcript/ASR text committed: false\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
