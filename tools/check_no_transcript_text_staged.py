#!/usr/bin/env python3
"""Reject staged raw transcript, processed transcript, and label packet artifacts."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_PATTERN = re.compile(
    r"(^|/)(raw/transcript\.txt|processed/transcript_clean\.txt|processed/transcript_sectioned\.json|labels/human_labeling_packet\.md|labels/weak_label_candidates\.jsonl)$"
)


def is_forbidden_transcript_artifact(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return bool(FORBIDDEN_PATTERN.search(normalized))


def staged_paths(cwd: Path | None = None) -> list[str]:
    result = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=cwd, text=True, capture_output=True, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    forbidden = [path for path in staged_paths(Path.cwd()) if is_forbidden_transcript_artifact(path)]
    if forbidden:
        print("Forbidden transcript text artifacts are staged:", file=sys.stderr)
        for path in forbidden:
            print(f"- {path}", file=sys.stderr)
        return 1
    print("No transcript text staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
