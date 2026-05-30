#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess


def probe_audio(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "ffprobe_status": "missing_file", "duration_sec": "", "sample_rate_hz": "", "channels": ""}
    if not shutil.which("ffprobe"):
        return {"path": str(path), "ffprobe_status": "dependency_missing", "duration_sec": "", "sample_rate_hz": "", "channels": ""}
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=sample_rate,channels",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=20)
    if completed.returncode != 0:
        return {"path": str(path), "ffprobe_status": "probe_failed", "duration_sec": "", "sample_rate_hz": "", "channels": ""}
    payload = json.loads(completed.stdout or "{}")
    stream = (payload.get("streams") or [{}])[0]
    return {
        "path": str(path),
        "ffprobe_status": "ok",
        "duration_sec": str(payload.get("format", {}).get("duration", "")),
        "sample_rate_hz": str(stream.get("sample_rate", "")),
        "channels": str(stream.get("channels", "")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe local audio metadata with ffprobe when installed.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(probe_audio(args.path), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
