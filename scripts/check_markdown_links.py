#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_FILES = (
    "README.md",
    "docs/demo-path.md",
    "docs/portfolio-proof.md",
    "docs/current-status.md",
    "docs/evaluation-summary.md",
)
LEGACY_OPTIONAL_PREFIX = "outputs/LLY_2025_Q2_call08/"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check markdown links and local file paths for the portfolio-facing docs."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_FILES),
        help="Markdown files to check. Defaults to the canonical portfolio docs.",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    failures: list[str] = []
    warnings: list[str] = []

    for relative_path in args.paths:
        path = (root / relative_path).resolve()
        if not path.exists():
            failures.append(f"{relative_path}: file does not exist")
            continue
        text = path.read_text(encoding="utf-8")
        for target_text in re.findall(r"!\[[^\]]*\]\(([^)]+)\)|\[[^\]]*\]\(([^)]+)\)", text):
            target_text = next(part for part in target_text if part)
            if target_text.startswith(("http://", "https://", "#", "mailto:")):
                continue
            local_target = target_text.split("#", 1)[0]
            if not local_target:
                continue
            target = (path.parent / local_target).resolve()
            if not target.exists():
                target_posix = target.relative_to(root).as_posix()
                if target_posix.startswith(LEGACY_OPTIONAL_PREFIX):
                    warnings.append(
                        f"{relative_path}: missing optional legacy proof target {local_target}"
                    )
                    continue
                failures.append(f"{relative_path}: missing target {local_target}")
        for code_target in re.findall(r"`(outputs/LLY_2025_Q2_call08/[^`]+)`", text):
            target = (root / code_target).resolve()
            if not target.exists():
                continue

    if failures:
        print("Markdown link check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    if warnings:
        print("Markdown link check warnings:")
        for warning in warnings:
            print(f"- {warning}")
    print("Markdown link check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
