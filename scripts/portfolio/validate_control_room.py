#!/usr/bin/env python3
"""Validate the Portfolio Product V1 control-room contract."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_DOCS = (
    "README.md",
    "STATUS.md",
    "MASTER_PLAN.md",
    "PRODUCT_SPEC.md",
    "ARCHITECTURE.md",
    "EVALUATION_CONTRACT.md",
    "THREAT_MODEL.md",
    "DECISIONS.md",
    "TASK_CONTRACT.md",
    "RELEASE_CHECKLIST.md",
)

REQUIRED_REPO_FILES = (
    "AGENTS.md",
    ".github/ISSUE_TEMPLATE/portfolio_task.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/portfolio-v1.yml",
    "scripts/portfolio/setup-worktree.sh",
    "scripts/portfolio/preflight.sh",
    "scripts/portfolio/release-check.sh",
)

REQUIRED_MARKERS = {
    "AGENTS.md": (
        "## Portfolio Product V1 Control Room",
        "make portfolio-v1-check",
    ),
    "docs/portfolio_v1/README.md": (
        "## Codex Operating Loop",
        "## Approval Boundaries",
    ),
    "docs/portfolio_v1/STATUS.md": (
        "## Next Three Tasks",
        "## Latest Validation",
    ),
    "docs/portfolio_v1/TASK_CONTRACT.md": (
        "## Reusable Contract",
        "## Control-Room Acceptance",
        "Only Keith may provide approval evidence",
    ),
    "docs/portfolio_v1/EVALUATION_CONTRACT.md": (
        "## Successful Analysis",
        "## Reporting Rules",
    ),
}

RELEASE_ARTIFACTS = (
    "docs/portfolio_v1/CASE_STUDY.md",
    "docs/portfolio_v1/EXECUTIVE_BUSINESS_CASE.md",
    "docs/portfolio_v1/DEMO.md",
    "reports/portfolio_v1/model_scorecard.json",
)

PINNED_ACTION_PATTERN = re.compile(r"^\s*uses:\s*[^\s@]+@[0-9a-f]{40}(?:\s+#.*)?$", re.MULTILINE)
ANY_ACTION_PATTERN = re.compile(r"^\s*uses:\s*", re.MULTILINE)


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate(root: Path, *, release: bool = False) -> list[str]:
    errors: list[str] = []
    docs_root = root / "docs" / "portfolio_v1"

    for name in REQUIRED_DOCS:
        path = docs_root / name
        if not path.is_file():
            errors.append(f"missing control-room document: {path.relative_to(root)}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"empty control-room document: {path.relative_to(root)}")

    for relative in REQUIRED_REPO_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing repository automation file: {relative}")

    for relative, markers in REQUIRED_MARKERS.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{relative}: missing required marker {marker!r}")

    workflow = root / ".github" / "workflows" / "portfolio-v1.yml"
    if workflow.is_file():
        workflow_text = workflow.read_text(encoding="utf-8")
        action_count = len(ANY_ACTION_PATTERN.findall(workflow_text))
        pinned_count = len(PINNED_ACTION_PATTERN.findall(workflow_text))
        if action_count != pinned_count:
            errors.append(".github/workflows/portfolio-v1.yml: every external action must be pinned to a 40-character SHA")

    if release:
        for relative in RELEASE_ARTIFACTS:
            if not (root / relative).is_file():
                errors.append(f"missing release artifact: {relative}")
        checklist = docs_root / "RELEASE_CHECKLIST.md"
        if checklist.is_file() and "- [ ]" in checklist.read_text(encoding="utf-8"):
            errors.append("docs/portfolio_v1/RELEASE_CHECKLIST.md: unchecked release gates remain")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--release", action="store_true", help="Also require final proof artifacts and a complete release checklist.")
    parser.add_argument("--status", action="store_true", help="Print the current status after validation.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    errors = validate(root, release=args.release)
    if errors:
        print("Portfolio V1 control-room validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    mode = "release" if args.release else "foundation"
    print(f"Portfolio V1 {mode} contract passed.")
    if args.status:
        print()
        print((root / "docs" / "portfolio_v1" / "STATUS.md").read_text(encoding="utf-8").rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
