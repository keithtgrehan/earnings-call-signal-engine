#!/usr/bin/env python3
"""Run or compare the optional NLP sidecar evaluation pack."""

from __future__ import annotations

import argparse
import json

from earnings_call_sentiment.nlp_sidecars import (
    AVAILABLE_MODEL_NAMES,
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_LENGTH,
    DEFAULT_MODELS,
    DEFAULT_ZERO_SHOT_LABEL_CONFIG,
    SUPPORTED_UNIT_TYPES,
    build_artifact_inputs,
    run_sidecar_models,
    write_case_evaluation_summary,
)
from earnings_call_sentiment.nlp_sidecars.config import default_output_root, load_model_defaults


def build_parser() -> argparse.ArgumentParser:
    defaults = load_model_defaults()
    parser = argparse.ArgumentParser(description="Optional NLP sidecar evaluation pack.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one or more optional sidecar models.")
    run_parser.add_argument("--case-id", required=True, help="Stable case id used for output naming.")
    run_parser.add_argument("--demo-case-root", help="Demo-case root with processed artifacts.")
    run_parser.add_argument("--chunks-csv", help="Explicit chunks_scored.csv path.")
    run_parser.add_argument("--guidance-csv", help="Explicit guidance.csv path.")
    run_parser.add_argument("--qa-pairs-json", help="Explicit qa_pairs.json path.")
    run_parser.add_argument(
        "--units",
        nargs="+",
        choices=SUPPORTED_UNIT_TYPES,
        default=list(SUPPORTED_UNIT_TYPES),
        help="Unit types to score.",
    )
    run_parser.add_argument(
        "--models",
        nargs="+",
        choices=AVAILABLE_MODEL_NAMES,
        default=list(DEFAULT_MODELS),
        help="Optional sidecar models to run.",
    )
    run_parser.add_argument("--device", default=defaults["device"], help="Runtime device: auto, cpu, or cuda.")
    run_parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Inference batch size.")
    run_parser.add_argument("--max-length", type=int, default=DEFAULT_MAX_LENGTH, help="Tokenizer max length.")
    run_parser.add_argument(
        "--smoke-limit",
        type=int,
        help="Optional per-unit-type cap for reduced overnight smoke runs.",
    )
    run_parser.add_argument(
        "--zero-shot-config",
        default=DEFAULT_ZERO_SHOT_LABEL_CONFIG,
        help="Zero-shot label config name or explicit JSON path.",
    )
    run_parser.add_argument(
        "--output-root",
        default=str(default_output_root()),
        help="Base output root. Per-model outputs land under outputs/<case_id>/model_sidecars/.",
    )
    run_parser.add_argument("--prewarm", action="store_true", help="Prewarm model runtimes before scoring.")
    run_parser.add_argument("--no-resume", action="store_true", help="Do not skip existing successful outputs.")
    run_parser.add_argument("--force", action="store_true", help="Force rerun even if outputs already exist.")

    compare_parser = subparsers.add_parser("compare", help="Refresh evaluation summaries from existing outputs.")
    compare_parser.add_argument("--case-id", required=True, help="Stable case id used for output naming.")
    compare_parser.add_argument(
        "--output-root",
        default=str(default_output_root()),
        help="Base output root containing outputs/<case_id>/model_sidecars/.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compare":
        payload = write_case_evaluation_summary(case_id=args.case_id, output_root=args.output_root)
        print(json.dumps({"case_id": args.case_id, "evaluation": {k: str(v) for k, v in payload.items()}}, indent=2))
        return 0

    artifact_inputs = build_artifact_inputs(
        case_id=args.case_id,
        demo_case_root=args.demo_case_root,
        chunks_csv=args.chunks_csv,
        guidance_csv=args.guidance_csv,
        qa_pairs_json=args.qa_pairs_json,
    )
    payload = run_sidecar_models(
        case_id=args.case_id,
        artifact_inputs=artifact_inputs,
        unit_types=list(args.units),
        model_names=list(args.models),
        output_root=args.output_root,
        device=args.device,
        batch_size=args.batch_size,
        max_length=args.max_length,
        smoke_limit=args.smoke_limit,
        prewarm=bool(args.prewarm),
        resume=not bool(args.no_resume),
        force=bool(args.force),
        zero_shot_config=args.zero_shot_config,
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
