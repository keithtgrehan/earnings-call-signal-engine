#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SIGNAL_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("guidance_revision", "positive", (r"\brais(?:e|ing|ed)\b.*\b(?:guidance|outlook|forecast|revenue)\b",)),
    ("analyst_pressure", "negative", (r"\bwhy should investors believe\b", r"\bcan you explain why\b")),
    ("management_hedging", "mixed", (r"\bdepends on\b", r"\bsubject to\b", r"\btiming remains dependent\b")),
    ("uncertainty", "negative", (r"\buncertain\b", r"\bvisibility remains limited\b", r"\bnot clear\b")),
    ("opportunity_commitment", "positive", (r"\bwe will continue investing\b", r"\bcommitted to\b", r"\bwe will expand\b")),
    ("risk_friction", "negative", (r"\bmasking slower\b", r"\bpressure\b.*\bmargin\b", r"\brisk\b.*\bunresolved\b")),
)


def evidence_units(text: str) -> list[str]:
    units = [line.strip() for line in text.splitlines() if line.strip()]
    if units:
        return units
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def first_match(units: list[str], patterns: tuple[str, ...]) -> str | None:
    for unit in units:
        for pattern in patterns:
            if re.search(pattern, unit, flags=re.IGNORECASE):
                return unit
    return None


def predict(text: str, *, case_id: str) -> list[dict[str, str]]:
    units = evidence_units(text)
    predictions: list[dict[str, str]] = []
    for signal_type, direction, patterns in SIGNAL_RULES:
        evidence = first_match(units, patterns)
        if evidence:
            predictions.append(
                {
                    "case_id": case_id,
                    "signal_type": signal_type,
                    "direction": direction,
                    "evidence_text": evidence,
                }
            )
    return predictions


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic weak-label keyword baseline on a local transcript text file.")
    parser.add_argument("--input", required=True, help="Local .txt file supplied manually by the user.")
    parser.add_argument("--case-id", required=True, help="Case ID to attach to predictions.")
    parser.add_argument("--out", required=True, help="JSONL prediction output path.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if input_path.suffix.lower() != ".txt":
        parser.error("--input must be a local .txt file")
    if not input_path.exists():
        parser.error(f"--input does not exist: {input_path}")
    if not args.case_id.strip():
        parser.error("--case-id is required")

    predictions = predict(input_path.read_text(encoding="utf-8"), case_id=args.case_id)
    write_jsonl(Path(args.out), predictions)
    print(f"Weak-label baseline wrote {len(predictions)} deterministic prediction(s).")
    print("These are weak deterministic labels only; they are not validated training data or real ML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
