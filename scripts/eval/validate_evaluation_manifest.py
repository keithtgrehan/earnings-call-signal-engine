#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_VARIANTS = {
    "deterministic_only",
    "deterministic_plus_retrieval",
    "deterministic_plus_byok_reviewer",
    "deterministic_plus_audio_metadata",
    "deterministic_plus_event_study_context",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate evaluation variant manifest without provider calls.")
    parser.add_argument("--path", default="reports/evaluation/evaluation_variant_run.example.json")
    args = parser.parse_args(argv)
    path = Path(args.path)
    if not path.exists():
        print(f"Evaluation manifest NOT_READY: {path} is missing.")
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if payload.get("variant") not in ALLOWED_VARIANTS:
        errors.append("variant is not allowed")
    if payload.get("provider_calls") is not False:
        errors.append("provider_calls must be false for local checks")
    if errors:
        print(f"Evaluation manifest validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Evaluation manifest validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
