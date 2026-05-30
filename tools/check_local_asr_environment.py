#!/usr/bin/env python3
"""Check local ASR dependencies without using cloud services."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.asr_backends import detect_local_asr_backend, ffmpeg_status  # noqa: E402

DESKTOP_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
REPORT_PATH = ROOT / "reports" / "acquisition" / "asr_environment_status.md"


def check_local_asr_environment(*, workspace: Path = DESKTOP_WORKSPACE) -> dict[str, Any]:
    ffmpeg = ffmpeg_status()
    backends = {name: detect_local_asr_backend(name) for name in ("faster-whisper", "whisper.cpp", "openai-whisper")}
    available = [name for name, row in backends.items() if row.get("dependency_status") in {"available", "available_python_package"}]
    summary = {
        "ffmpeg": ffmpeg,
        "backends": backends,
        "available_backends": available,
        "status": "available" if available and ffmpeg.get("ffmpeg_status") == "available" and ffmpeg.get("ffprobe_status") == "available" else "dependency_missing",
        "cloud_asr_used": False,
        "install_instructions": {
            "faster-whisper": "PYENV_VERSION=3.11.3 python3 -m pip install faster-whisper; place a local faster-whisper model outside the repo and run PYENV_VERSION=3.11.3 python3 tools/run_local_asr_batch.py --backend faster-whisper --model /path/to/local/faster-whisper-model",
            "whisper.cpp": "Install whisper.cpp locally, build whisper-cli, and provide a local ggml model path.",
            "openai-whisper": "PYENV_VERSION=3.11.3 python3 -m pip install -U openai-whisper",
            "ffmpeg": "brew install ffmpeg",
        },
    }
    audit = workspace / "_audit" / "asr_environment_status.json"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    return {**summary, "desktop_audit": str(audit)}


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ASR Environment Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- ffmpeg: `{summary['ffmpeg'].get('ffmpeg_status')}`",
        f"- ffprobe: `{summary['ffmpeg'].get('ffprobe_status')}`",
        f"- Available backends: {', '.join(summary['available_backends']) if summary['available_backends'] else 'none'}",
        "- Cloud ASR used: false",
        "",
        "## Install Commands",
        "",
    ]
    for name, command in summary["install_instructions"].items():
        lines.append(f"- `{name}`: {command}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local ASR dependencies.")
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    args = parser.parse_args(argv)
    print(json.dumps(check_local_asr_environment(workspace=args.workspace), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
