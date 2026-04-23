#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


CANONICAL_CASE_ID = "LLY_2025_Q2_call08"
CANONICAL_COMMAND = (
    "python scripts/verify_outputs.py --out-dir outputs/LLY_2025_Q2_call08 --require-run-meta"
)
CANONICAL_OUTPUT_DIR = "outputs/LLY_2025_Q2_call08"
BANNED_PHRASES = (
    "AI-powered",
    "state-of-the-art",
    "significant improvement",
    "alpha",
)
AUDIT_FILES = (
    "README.md",
    "docs/demo-path.md",
    "docs/portfolio-proof.md",
    "docs/current-status.md",
    "docs/evaluation-summary.md",
)
CASE_ID_REQUIRED_FILES = {
    "README.md",
    "docs/demo-path.md",
    "docs/portfolio-proof.md",
    "docs/current-status.md",
}
PLANNED_TOKENS = re.compile(r"\b(planned|future|later|candidate|roadmap)\b", re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit portfolio-facing docs for canonical demo consistency."
    )
    parser.parse_args(argv)

    root = _repo_root()
    failures: list[str] = []

    for relative_path in AUDIT_FILES:
        path = root / relative_path
        text = path.read_text(encoding="utf-8")

        if relative_path in CASE_ID_REQUIRED_FILES and CANONICAL_CASE_ID not in text:
            failures.append(f"{relative_path}: missing canonical case id {CANONICAL_CASE_ID}")

        for phrase in BANNED_PHRASES:
            if re.search(re.escape(phrase), text, re.IGNORECASE):
                failures.append(f"{relative_path}: banned wording found: {phrase}")

        for index, line in enumerate(text.splitlines(), start=1):
            if (
                CANONICAL_CASE_ID in line or "canonical proof" in line.lower()
            ) and PLANNED_TOKENS.search(line):
                failures.append(
                    f"{relative_path}:{index}: canonical proof described as planned/future language"
                )

    readme_text = (root / "README.md").read_text(encoding="utf-8")
    if CANONICAL_COMMAND not in readme_text:
        failures.append("README.md: missing canonical demo command")
    if CANONICAL_OUTPUT_DIR not in readme_text:
        failures.append("README.md: missing canonical output directory")

    demo_text = (root / "docs/demo-path.md").read_text(encoding="utf-8")
    if CANONICAL_COMMAND not in demo_text:
        failures.append("docs/demo-path.md: missing canonical demo command")
    if CANONICAL_OUTPUT_DIR not in demo_text:
        failures.append("docs/demo-path.md: missing canonical output directory")

    if failures:
        print("Portfolio docs audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Portfolio docs audit passed.")
    print(f"Canonical case: {CANONICAL_CASE_ID}")
    print(f"Canonical command: {CANONICAL_COMMAND}")
    print(f"Canonical output directory: {CANONICAL_OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
