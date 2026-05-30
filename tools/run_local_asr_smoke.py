#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.asr_backends import detect_local_asr_backend


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report local ASR dependency readiness without cloud calls.")
    parser.add_argument("--backend", default="")
    args = parser.parse_args(argv)
    status = detect_local_asr_backend(args.backend)
    payload = {
        "backend": status["backend"],
        "dependency_status": status["dependency_status"],
        "cloud_asr_used": False,
        "raw_asr_committed": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
