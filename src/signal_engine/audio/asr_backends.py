from __future__ import annotations

import importlib.util
import os
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
    "faster-whisper": "PYENV_VERSION=3.11.3 python3 -m pip install faster-whisper; download or place a local model such as Systran/faster-whisper-tiny outside the repo, then run PYENV_VERSION=3.11.3 python3 tools/run_local_asr_batch.py --backend faster-whisper --model /path/to/local/faster-whisper-model",
    "whisper.cpp": "install whisper.cpp, build whisper-cli, and provide a local ggml model path",
    "openai-whisper": "python3 -m pip install -U openai-whisper; requires ffmpeg and a local/cached Whisper model",
}

DESKTOP_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
LOCAL_MODEL_CACHE = Path(".local/asr_models")


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


def faster_whisper_model_candidates(*, workspace: Path = DESKTOP_WORKSPACE, repo_root: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    env_path = os.environ.get("FASTER_WHISPER_MODEL_PATH")
    if env_path:
        roots.append(Path(env_path))
    roots.append(workspace / "_models" / "faster-whisper")
    if repo_root:
        roots.append(repo_root / LOCAL_MODEL_CACHE)
    roots.append(LOCAL_MODEL_CACHE)
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            candidates.append(root)
            continue
        if (root / "model.bin").exists() or (root / "config.json").exists():
            candidates.append(root)
        for child in root.rglob("model.bin"):
            candidates.append(child.parent)
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve())
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    return deduped


def faster_whisper_model_status(*, workspace: Path = DESKTOP_WORKSPACE, repo_root: Path | None = None) -> dict[str, str]:
    candidates = faster_whisper_model_candidates(workspace=workspace, repo_root=repo_root)
    env_path = os.environ.get("FASTER_WHISPER_MODEL_PATH", "")
    if candidates:
        return {
            "model_status": "available",
            "model_path": str(candidates[0]),
            "model_source": "FASTER_WHISPER_MODEL_PATH" if env_path and str(candidates[0]).startswith(str(Path(env_path).expanduser())) else "local_cache",
        }
    return {
        "model_status": "missing",
        "model_path": "",
        "model_source": "",
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
