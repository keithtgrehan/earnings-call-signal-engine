#!/usr/bin/env python3
"""Report local ASR readiness without cloud upload or raw ASR text commits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import read_csv

REPORT_PATH = ROOT / "reports" / "acquisition" / "audio_rag_readiness.md"


def local_asr_engine() -> str:
    for name in ("faster-whisper", "whisper", "whisperx"):
        if shutil.which(name):
            return name
    return ""


def build_asr_readiness(*, registry: Path) -> dict:
    rows = read_csv(registry)
    engine = local_asr_engine()
    summary = {
        "audio_registry_rows": len(rows),
        "local_asr_available": bool(engine),
        "local_asr_engine": engine,
        "local_asr_run": False,
        "cloud_asr_used": False,
        "raw_asr_text_committed": False,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Audio RAG Readiness\n\n"
        f"- Audio registry rows: {summary['audio_registry_rows']}\n"
        f"- Local ASR available: {str(summary['local_asr_available']).lower()}\n"
        f"- Local ASR engine: `{engine or 'none'}`\n"
        "- Local ASR run: false\n"
        "- Cloud ASR used: false\n"
        "- Raw ASR text committed: false\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local ASR readiness.")
    parser.add_argument("--registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_audio_registry.csv")
    args = parser.parse_args(argv)
    print(json.dumps(build_asr_readiness(registry=args.registry), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
