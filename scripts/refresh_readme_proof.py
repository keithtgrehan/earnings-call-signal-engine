#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CANONICAL_CASE_ID = "PVH_2025_Q1_call09"
SOURCE_FILES = (
    f"outputs/{CANONICAL_CASE_ID}/metrics.json",
    f"outputs/{CANONICAL_CASE_ID}/run_meta.json",
    f"outputs/{CANONICAL_CASE_ID}/guidance.csv",
    f"outputs/{CANONICAL_CASE_ID}/uncertainty_signals.csv",
    f"outputs/{CANONICAL_CASE_ID}/reassurance_signals.csv",
    f"outputs/{CANONICAL_CASE_ID}/analyst_skepticism.csv",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _format_runtime(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.6f} seconds"
    return "not yet measured"


def _format_cost(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value}"
    text = str(value).strip()
    return text or "not yet measured"


def _proof_section(proof: dict[str, Any]) -> str:
    signal_counts = proof.get("signal_counts", {})
    return "\n".join(
        [
            "## Proof (current state)",
            "<!-- proof:begin -->",
            f"- PVH runtime per case: {_format_runtime(proof.get('wall_clock_seconds'))}.",
            f"- PVH cost per case: {_format_cost(proof.get('cost_per_case'))}.",
            (
                "- PVH extracted signals: "
                f"{signal_counts.get('guidance_rows', 'not yet measured')} guidance rows, "
                f"{signal_counts.get('uncertainty_rows', 'not yet measured')} uncertainty rows, "
                f"{signal_counts.get('reassurance_rows', 'not yet measured')} reassurance rows, "
                f"{signal_counts.get('analyst_skepticism_rows', 'not yet measured')} analyst-skepticism row(s)."
            ),
            "- Example outputs: reviewer report at `outputs/PVH_2025_Q1_call09/report.md`.",
            "- Example outputs: structured scorecard at `outputs/PVH_2025_Q1_call09/metrics.json`.",
            "- Example outputs: extracted guidance table at `outputs/PVH_2025_Q1_call09/guidance.csv`.",
            "<!-- proof:end -->",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the README proof block from the canonical proof artifact."
    )
    parser.add_argument(
        "--proof-path",
        default="outputs/PVH_2025_Q1_call09/portfolio_proof.json",
        help="Path to the machine-readable proof artifact.",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    proof_path = (root / args.proof_path).resolve()
    if not proof_path.exists():
        raise RuntimeError(
            f"Missing proof artifact: {proof_path}. Run scripts/build_portfolio_proof.py first."
        )

    proof_mtime = proof_path.stat().st_mtime
    newer_sources = [
        path for path in SOURCE_FILES if (root / path).exists() and (root / path).stat().st_mtime > proof_mtime
    ]
    if newer_sources:
        joined = ", ".join(newer_sources)
        raise RuntimeError(
            f"Proof artifact is stale relative to canonical inputs: {joined}. Run scripts/build_portfolio_proof.py first."
        )

    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    if proof.get("canonical_case_id") != CANONICAL_CASE_ID:
        raise RuntimeError("Proof artifact canonical case id does not match the PVH demo.")

    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    section = _proof_section(proof)
    updated = re.sub(
        r"(?ms)^## Proof \(current state\)\n.*?(?=^## )",
        section + "\n\n",
        readme,
        count=1,
    )
    if updated == readme:
        raise RuntimeError("Could not find README proof section to refresh.")
    readme_path.write_text(updated, encoding="utf-8")
    print(f"Updated README proof block from {args.proof_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
