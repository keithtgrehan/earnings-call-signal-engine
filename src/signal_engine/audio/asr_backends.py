from __future__ import annotations

import shutil

BACKENDS = {
    "faster-whisper": "faster-whisper",
    "whisper.cpp": "whisper-cpp",
    "openai-whisper": "whisper",
}


def detect_local_asr_backend(preferred: str = "") -> dict[str, str]:
    names = [preferred] if preferred else list(BACKENDS)
    for name in names:
        executable = BACKENDS.get(name, name)
        if executable and shutil.which(executable):
            return {"backend": name, "executable": executable, "dependency_status": "available"}
    return {"backend": preferred or "local_asr", "executable": "", "dependency_status": "dependency_missing"}
