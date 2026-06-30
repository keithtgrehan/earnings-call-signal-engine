#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from signal_engine.llm.safety import contains_secret_like_value, redact_secret_values

GOLD_WRITE_KEYS = {"writes_gold", "gold_label", "gold_labels", "promoted_to_gold", "auto_promote_gold"}


def _load_artifact(path: Path) -> Any:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return None


def _scan(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key == "canonical_output" and item is not False:
                errors.append(f"{child_path} must be false")
            if key in GOLD_WRITE_KEYS and item not in (False, None, "", []):
                errors.append(f"{child_path} indicates a gold-label write or promotion")
            _scan(item, child_path, errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan(item, f"{path}[{index}]", errors)
    elif contains_secret_like_value(value):
        errors.append(f"{path} contains secret-like value {redact_secret_values(str(value))}")


def validate_artifact_root(root: Path, *, allow_missing: bool = False) -> list[str]:
    if not root.exists():
        return [] if allow_missing else [f"{root} does not exist"]
    if not root.is_dir():
        return [f"{root} is not a directory"]
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in {".json", ".jsonl"}:
            continue
        try:
            payload = _load_artifact(path)
        except Exception as exc:
            errors.append(f"{path}: invalid JSON artifact: {type(exc).__name__}")
            continue
        _scan(payload, str(path), errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check generated LLM artifacts for fail-closed safety markers.")
    parser.add_argument("--root", default="artifacts/llm")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args(argv)

    errors = validate_artifact_root(Path(args.root), allow_missing=args.allow_missing)
    if errors:
        print(f"LLM artifact check failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {redact_secret_values(error)}")
        return 1
    print("LLM artifact check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
