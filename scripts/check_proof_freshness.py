#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


CANONICAL_CASE_ID = "LLY_2025_Q2_call08"
PROOF_DEFAULT = f"outputs/{CANONICAL_CASE_ID}/portfolio_proof.json"
SOURCE_FILES = (
    f"outputs/{CANONICAL_CASE_ID}/metrics.json",
    f"outputs/{CANONICAL_CASE_ID}/run_meta.json",
    f"outputs/{CANONICAL_CASE_ID}/guidance.csv",
    f"outputs/{CANONICAL_CASE_ID}/uncertainty_signals.csv",
    f"outputs/{CANONICAL_CASE_ID}/reassurance_signals.csv",
    f"outputs/{CANONICAL_CASE_ID}/analyst_skepticism.csv",
    "data/gold_guidance_calls/labels.csv",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _format_runtime(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.6f} seconds"
    return "not yet measured"


def _format_cost(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value}"
    text = str(value).strip()
    return text or "not yet measured"


def _format_label_confidence(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "not recorded"


def _benchmark_line(proof: dict[str, object]) -> str:
    benchmark = proof.get("benchmark_label", {})
    if not isinstance(benchmark, dict):
        benchmark = {}
    label = benchmark.get("guidance_change_label", "unknown")
    company = benchmark.get("company", "unknown company")
    call_id = benchmark.get("call_id", "unknown call")
    event_date = benchmark.get("event_date", "unknown date")
    confidence = _format_label_confidence(benchmark.get("label_confidence"))
    return (
        f"- Frozen benchmark label: `{label}` for {company} "
        f"(`{call_id}`, {event_date}, confidence {confidence})."
    )


def _render_expected_block(proof: dict[str, object]) -> str:
    signal_counts = proof.get("signal_counts", {})
    if not isinstance(signal_counts, dict):
        signal_counts = {}
    return "\n".join(
        [
            "## Proof (current state)",
            "<!-- proof:begin -->",
            _benchmark_line(proof),
            (
                f"- Proof check runtime: {_format_runtime(proof.get('wall_clock_seconds'))} "
                "for `verify_outputs.py` against the committed bundle."
            ),
            f"- Recorded run cost: {_format_cost(proof.get('cost_per_case'))}.",
            (
                "- Extracted signals in the committed bundle: "
                f"{signal_counts.get('guidance_rows', 'not yet measured')} guidance rows, "
                f"{signal_counts.get('uncertainty_rows', 'not yet measured')} uncertainty rows, "
                f"{signal_counts.get('reassurance_rows', 'not yet measured')} reassurance rows, "
                f"{signal_counts.get('analyst_skepticism_rows', 'not yet measured')} analyst-skepticism row(s)."
            ),
            "- Example outputs: reviewer report at `outputs/LLY_2025_Q2_call08/report.md`.",
            "- Example outputs: structured scorecard at `outputs/LLY_2025_Q2_call08/metrics.json`.",
            "- Example outputs: extracted guidance table at `outputs/LLY_2025_Q2_call08/guidance.csv`.",
            "<!-- proof:end -->",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate that the canonical proof artifact exists, is fresh, and matches the README proof block."
    )
    parser.add_argument(
        "--proof-path",
        default=PROOF_DEFAULT,
        help="Path to the canonical proof artifact.",
    )
    parser.add_argument(
        "--readme-path",
        default="README.md",
        help="Path to the README whose proof block should match the proof artifact.",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    proof_path = (root / args.proof_path).resolve()
    readme_path = (root / args.readme_path).resolve()

    if not proof_path.exists():
        print(f"Proof freshness check failed: missing proof artifact {proof_path}")
        return 1

    missing_sources = [path for path in SOURCE_FILES if not (root / path).exists()]
    if missing_sources:
        print("Proof freshness check failed: missing canonical source artifacts:")
        for path in missing_sources:
            print(f"- {path}")
        return 1

    proof_mtime = proof_path.stat().st_mtime
    newer_sources = [
        path for path in SOURCE_FILES if (root / path).stat().st_mtime > proof_mtime
    ]
    if newer_sources:
        print("Proof freshness check failed: proof artifact is older than canonical inputs:")
        for path in newer_sources:
            print(f"- {path}")
        return 1

    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    if proof.get("canonical_case_id") != CANONICAL_CASE_ID:
        print("Proof freshness check failed: canonical case id mismatch in proof artifact.")
        return 1

    expected_block = _render_expected_block(proof)
    readme = readme_path.read_text(encoding="utf-8")
    if expected_block not in readme:
        print("Proof freshness check failed: README proof block does not match the proof artifact.")
        return 1

    print("Proof freshness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
