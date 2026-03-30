#!/usr/bin/env python3
"""Build the bounded Netflix multimodal evidence panel bundle."""

from __future__ import annotations

import argparse
import json

from earnings_call_sentiment.netflix_multimodal_panel import write_review_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the bounded Netflix multimodal evidence panel bundle.")
    parser.add_argument("--video-path", help="Optional explicit Netflix MP4 path.")
    parser.add_argument("--device", default="auto", help="Runtime device for optional sidecars.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["finbert_tone", "financial_roberta", "deberta_zero_shot", "mpnet_embeddings"],
        help="Optional sidecar models to run on the curated Netflix moments.",
    )
    parser.add_argument(
        "--visual-sample-fps",
        type=float,
        default=0.25,
        help="Sample rate for the bounded visual pass.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = write_review_bundle(
        video_path=args.video_path,
        models=list(args.models),
        device=args.device,
        sample_fps=args.visual_sample_fps,
    )
    print(json.dumps(payload["bundle_paths"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
