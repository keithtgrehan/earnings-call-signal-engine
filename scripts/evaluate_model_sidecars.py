#!/usr/bin/env python3
"""Evaluate optional model-sidecar outputs for one processed case."""

from __future__ import annotations

import argparse
import json

from earnings_call_sentiment.model_sidecars.evaluate import write_evaluation_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare optional model-sidecar outputs across models. "
            "This is a behavior and utility comparison only."
        )
    )
    parser.add_argument(
        "--case-id",
        required=True,
        help="Processed case id whose sidecar outputs should be evaluated.",
    )
    parser.add_argument(
        "--sidecar-root",
        default="./outputs",
        help=(
            "Base sidecar output root. The evaluator reads from "
            "<sidecar-root>/<case_id>/model_sidecars/."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts = write_evaluation_outputs(
        args.case_id,
        sidecar_root=args.sidecar_root,
    )
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "artifacts": {key: str(value) for key, value in artifacts.items()},
                "notes": [
                    "This report compares optional model sidecars only.",
                    "Deterministic transcript-first outputs remain the source of truth.",
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
