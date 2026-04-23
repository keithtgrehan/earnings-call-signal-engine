#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


CANONICAL_CASE_ID = "LLY_2025_Q2_call08"
REQUIRED_ARTIFACTS = (
    "transcript.json",
    "transcript.txt",
    "sentiment_segments.csv",
    "chunks_scored.jsonl",
    "guidance.csv",
    "metrics.json",
    "report.md",
    "run_meta.json",
)
COUNT_FILES = {
    "guidance_rows": "guidance.csv",
    "uncertainty_rows": "uncertainty_signals.csv",
    "reassurance_rows": "reassurance_signals.csv",
    "analyst_skepticism_rows": "analyst_skepticism.csv",
}
EXAMPLE_OUTPUTS = (
    "report.md",
    "metrics.json",
    "guidance.csv",
)
COST_KEYS = {
    "cost",
    "cost_usd",
    "price_usd",
    "total_cost",
    "total_cost_usd",
    "token_cost",
    "token_cost_usd",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_out_dir(root: Path) -> Path:
    return root / "outputs" / CANONICAL_CASE_ID


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _nonempty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def _find_cost(payload: Any) -> Any | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in COST_KEYS and value not in (None, "", []):
                return value
            nested = _find_cost(value)
            if nested is not None:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = _find_cost(item)
            if nested is not None:
                return nested
    return None


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _lookup_benchmark_row(repo_root: Path) -> dict[str, Any]:
    labels_path = repo_root / "data" / "gold_guidance_calls" / "labels.csv"
    source_path = f"data/gold_guidance_calls/raw_calls/{CANONICAL_CASE_ID}.txt"
    with labels_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("source_path") == source_path:
                return {
                    "call_id": row.get("call_id"),
                    "ticker": row.get("ticker"),
                    "company": row.get("company"),
                    "event_date": row.get("event_date"),
                    "guidance_change_label": row.get("guidance_change_label"),
                    "label_confidence": _coerce_float(row.get("label_confidence")),
                    "notes": row.get("notes"),
                    "source_path": row.get("source_path"),
                }
    raise RuntimeError(f"Could not find benchmark row for {CANONICAL_CASE_ID} in labels.csv")


def build_proof(out_dir: Path) -> dict[str, Any]:
    repo_root = _repo_root()
    benchmark_row = _lookup_benchmark_row(repo_root)
    command = [
        sys.executable,
        "scripts/verify_outputs.py",
        "--out-dir",
        str(out_dir.relative_to(repo_root)),
        "--require-run-meta",
    ]
    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = round(time.perf_counter() - started, 6)

    metrics = _read_json(out_dir / "metrics.json")
    run_meta = _read_json(out_dir / "run_meta.json")
    cost_value = _find_cost(run_meta)
    if cost_value is None:
        cost_value = _find_cost(metrics)
    if cost_value is None:
        cost_value = "not yet measured"
    cost_status = "measured" if isinstance(cost_value, (int, float)) else "not_yet_measured"

    return {
        "schema_version": "1.0.0",
        "proof_generated_at": datetime.now(UTC).isoformat(),
        "canonical_case_id": CANONICAL_CASE_ID,
        "canonical_demo_command": "python scripts/verify_outputs.py --out-dir outputs/LLY_2025_Q2_call08 --require-run-meta",
        "canonical_output_dir": "outputs/LLY_2025_Q2_call08",
        "wall_clock_seconds": elapsed,
        "cost_per_case": cost_value,
        "cost_status": cost_status,
        "benchmark_label": benchmark_row,
        "artifacts_verified": result.returncode == 0,
        "required_artifacts": {
            name: _nonempty(out_dir / name) for name in REQUIRED_ARTIFACTS
        },
        "signal_counts": {
            key: _count_rows(out_dir / filename) for key, filename in COUNT_FILES.items()
        },
        "example_outputs": [
            f"outputs/{CANONICAL_CASE_ID}/{name}" for name in EXAMPLE_OUTPUTS
        ],
        "run_meta": {
            "generated_at": run_meta.get("generated_at"),
            "run_id": run_meta.get("run_id"),
            "version": run_meta.get("version"),
        },
        "verification_stdout": result.stdout.strip(),
        "verification_stderr": result.stderr.strip(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable proof artifact for the canonical LLY demo."
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory for the canonical case. Defaults to outputs/LLY_2025_Q2_call08.",
    )
    parser.add_argument(
        "--proof-path",
        default=None,
        help="Where to write the proof JSON. Defaults to <out-dir>/portfolio_proof.json.",
    )
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    out_dir = (
        (repo_root / args.out_dir).resolve()
        if args.out_dir
        else _canonical_out_dir(repo_root)
    )
    proof_path = (
        (repo_root / args.proof_path).resolve()
        if args.proof_path
        else out_dir / "portfolio_proof.json"
    )

    proof = build_proof(out_dir)
    proof_path.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote proof artifact: {proof_path}")
    print(json.dumps(proof, indent=2))
    return 0 if proof["artifacts_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
