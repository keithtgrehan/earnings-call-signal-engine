from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Any

BACKENDS = {
    "faster-whisper": "faster-whisper",
    "whisper.cpp": "whisper-cpp",
    "openai-whisper": "whisper",
}

INSTALL_INSTRUCTIONS = {
    "faster-whisper": "python3 -m pip install faster-whisper and provide a local model/cache before running ASR",
    "whisper.cpp": "install whisper.cpp, build whisper-cli, and provide a local ggml model path",
    "openai-whisper": "python3 -m pip install -U openai-whisper; requires ffmpeg and a local/cached Whisper model",
}


def detect_local_asr_backend(preferred: str = "") -> dict[str, str]:
    names = [preferred] if preferred else list(BACKENDS)
    for name in names:
        executable = BACKENDS.get(name, name)
        if executable and shutil.which(executable):
            return {
                "backend": name,
                "executable": executable,
                "dependency_status": "available",
                "install_instructions": INSTALL_INSTRUCTIONS.get(name, ""),
            }
        if name == "faster-whisper" and importlib.util.find_spec("faster_whisper"):
            return {
                "backend": name,
                "executable": "",
                "dependency_status": "available_python_package",
                "install_instructions": INSTALL_INSTRUCTIONS[name],
            }
        if name == "openai-whisper" and importlib.util.find_spec("whisper"):
            return {
                "backend": name,
                "executable": shutil.which("whisper") or "",
                "dependency_status": "available_python_package",
                "install_instructions": INSTALL_INSTRUCTIONS[name],
            }
    backend = preferred or "local_asr"
    return {
        "backend": backend,
        "executable": "",
        "dependency_status": "dependency_missing",
        "install_instructions": "; ".join(INSTALL_INSTRUCTIONS.values()),
    }


def ffmpeg_status() -> dict[str, str]:
    return {
        "ffmpeg": shutil.which("ffmpeg") or "",
        "ffprobe": shutil.which("ffprobe") or "",
        "ffmpeg_status": "available" if shutil.which("ffmpeg") else "dependency_missing",
        "ffprobe_status": "available" if shutil.which("ffprobe") else "dependency_missing",
    }


def probe_audio(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"ffprobe_status": "dependency_missing", "duration_sec": "", "sample_rate_hz": "", "channels": ""}
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=sample_rate,channels:format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=0",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        return {"ffprobe_status": "failed", "duration_sec": "", "sample_rate_hz": "", "channels": ""}
    payload: dict[str, str] = {"ffprobe_status": "ok", "duration_sec": "", "sample_rate_hz": "", "channels": ""}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "duration":
            payload["duration_sec"] = value
        elif key == "sample_rate":
            payload["sample_rate_hz"] = value
        elif key == "channels":
            payload["channels"] = value
    return payload
